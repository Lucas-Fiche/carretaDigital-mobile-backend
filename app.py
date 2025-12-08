import os # Fornece funções para interagir com o SO
import gspread # Fornece funções para acesso ao Google Sheets
import pandas as pd # Fornece funções para manipulação de dados
from oauth2client.service_account import ServiceAccountCredentials # Fornece funções para criar credenciais de autenticação em APIs do Google
from flask import Flask, jsonify # Fornece a classe principal do Framework Flask e operações para manipular arquivos JSON
from flask_cors import CORS # Fornece suporte a CORS para integração com o Frontend

# Criando a aplicação Flask em app
app = Flask(__name__)
# Adiciona CORS na aplicação app
CORS(app)

def obter_dados():
    # 1. Conexão com Google Sheets
    # A lista scope define quais permissões a aplicação deve pedir à API do Google
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # A variável creds_path lê a variável de ambiente GOOGLE_CREDENTIALS_PATH e, se ela não existir, usa 'credentials.json' como padrão.
    creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    # Carrega o arquivo credentials.json da conta de serviço do Google e cria um objeto de credenciais OAuth2
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    # Cria o cliente autenticado do gspread usando essas credenciais.
    client = gspread.authorize(creds)
    
    # 2. Abrir a Planilha pelo ID
    # Abre a planilha "TABELA - BASE DE DADOS" do Google Sheets a partir do ID
    planilha = client.open_by_key("1XZkJVMtfeXUvylE04VHO-KCsz8C9l5apj_sthZb4Uzo")
    # Escolhe a aba específicada "TABELA - BASE DE DADOS"
    aba = planilha.worksheet("TABELA - BASE DE DADOS")
    # Log para confirmar no terminal que a aba desejada está sendo aberta
    print(f"Lendo aba: {aba.title}...") 
    
    # 3. Ler todos os dados (Isso pode levar uns 3 a 5 segundos pois são 14k linhas)
    # Obtém todas as linhas da planilha
    # --> get_all_values() é um método do objeto worksheet do gspread que retorna todas as células preenchidas da aba como uma lista de linhas, onde cada linha é uma lista de strings.
    todas_as_linhas = aba.get_all_values()
    # Log para o terminal mostrando quantas linhas foram lidas da planilha
    print(f"Linhas baixadas: {len(todas_as_linhas)}")

    # Verifica se o número de linhas na lista todas_as_linhas é menor que 2
    if len(todas_as_linhas) < 2:
        return { "mensagem": "Planilha vazia", "total_alunos": 0, "total_estados": 0, "cursos": {} }

    # 4. Processamento com Pandas
    # Armazena na variável cabecalhos a linha de cabeçalhos da planilha
    cabecalhos = todas_as_linhas[0]
    # Armazena na variável dados todas as linhas com dados úteis da planilha
    dados = todas_as_linhas[1:]
    # Cria um dataframe do pandas com os dados da planilha e o cabeçalho especificado como columns
    df = pd.DataFrame(dados, columns=cabecalhos)
    
    # --- LIMPEZA DE CABEÇALHOS ---
    # Garante que tudo fique maiúsculo (.upper) e sem espaços (.strip)
    df.columns = df.columns.str.upper().str.strip()
    # Remove colunas com cabeçalhos vazios
    df = df.loc[:, df.columns != '']

    # 5. Cálculos ESTRATÉGICOS

    # KPI 1. TOTAL DE ALUNOS
    total_alunos = len(df)
    
    # KPI 2. META DO PROJETO
    META_DO_PROJETO = 23500 
    porcentagem_meta = (total_alunos / META_DO_PROJETO) if META_DO_PROJETO > 0 else 0

    # KPI 3. NÚMERO DE ESCOLAS
    total_escolas = 0
    if 'ESCOLA' in df.columns:
        total_escolas = df['ESCOLA'].nunique()

    # KPI 4. MAPA DE CALOR | TOTAL DE ESTADOS | ALUNOS POR ESTADO 
    COORDENADAS_ESTADOS = {
        "DISTRITO FEDERAL": {"lat": -15.7998, "lng": -47.8645},
        "MARANHAO": {"lat": -4.9609, "lng": -45.2744},
        "MATO GROSSO DO SUL": {"lat": -20.7722, "lng": -54.7852},
        "PERNAMBUCO": {"lat": -8.8137, "lng": -36.9541},
        "RIO DE JANEIRO": {"lat": -22.9068, "lng": -43.1729},
        "RIO GRANDE DO SUL": {"lat": -30.0346, "lng": -51.2177},
        "SANTA CATARINA": {"lat": -27.2423, "lng": -50.2189},
    }

    total_estados = 0
    top_estados = {}
    contagem_alunos_por_estados = {}
    dados_mapa = [] 

    if 'ESTADO' in df.columns:
        # Limpeza
        df['ESTADO'] = df['ESTADO'].astype(str).str.replace(', Brasil', '').str.strip()
        df_estados = df[df['ESTADO'] != '']
        
        total_estados = df_estados['ESTADO'].nunique()
        top_estados = df_estados['ESTADO'].value_counts().head(5).to_dict()
        contagem_alunos_por_estados = df_estados['ESTADO'].value_counts().to_dict()
        
        for estado, qtd in contagem_alunos_por_estados.items():
            # Remove acentos para bater com a chave do dicionário (ex: MARANHÃO -> MARANHAO)
            chave = estado.upper().replace('Ã', 'A').replace('Õ', 'O').replace('Ç', 'C').replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U').replace('Â', 'A').replace('Ê', 'E')
            
            if chave in COORDENADAS_ESTADOS:
                coords = COORDENADAS_ESTADOS[chave]
                dados_mapa.append({
                    "estado": estado,
                    "qtd": int(qtd),
                    "lat": coords['lat'],
                    "lng": coords['lng']
                })

    # KPI 5. MUNICÍPIOS
    municipios_por_estado = {}
    total_municipios = 0
    
    if 'ESTADO' in df.columns and 'MUNICÍPIO' in df.columns:
        df_limpo = df[(df['ESTADO'] != '') & (df['MUNICÍPIO'] != '')]
        agrupamento = df_limpo.groupby(['ESTADO', 'MUNICÍPIO']).size()
        
        for (estado, municipio), qtd in agrupamento.items():
            if estado not in municipios_por_estado:
                municipios_por_estado[estado] = {}
            municipios_por_estado[estado][municipio] = int(qtd)

        # CÁLCULO TOTAL CORRIGIDO
        for estado, cidades in municipios_por_estado.items():
            total_municipios += len(cidades)
        
        total_municipios -= 1 # No Distrito Federal, Asa Sul e Asa Norte são UMA região administrativa (DF).

    # KPI 5. CURSOS 
    alunos_por_curso = {}
    if 'CURSO' in df.columns:
        alunos_por_curso = df['CURSO'].value_counts().to_dict()

    # KPI 6. Gênero e PCD
    contagem_genero = {
        "Masculino": 0,
        "Feminino": 0,
        "Outros": 0,
    }

    if 'SEXO' in df.columns:
        sexo = df['SEXO'].astype(str).str.strip()

        # Conta apenas os exatos
        qtd_masc = int((sexo == 'Masculino').sum())
        qtd_fem = int((sexo == 'Feminino').sum())

        # Preenche o dicionário
        contagem_genero["Masculino"] = qtd_masc
        contagem_genero["Feminino"] = qtd_fem

        # Total de linhas - (Homens + Mulheres) = Incompletos/Erros/Vazios
        contagem_genero["Outros"] = len(df) - (qtd_masc + qtd_fem)


    contagem_pcd = 0
    col_pcd = 'PESSOA COM DEFICIÊNCIA (PCD)'
    if 'PESSOA COM DEFICIÊNCIA (PCD)' in df.columns:
        contagem_pcd = df[col_pcd].astype(str).str.strip().str.upper().isin(['SIM', 'S', 'YES']).sum()
        

    return {
        "kpis": {
            "total_alunos": int(total_alunos),
            "meta_projeto": int(META_DO_PROJETO),
            "porcentagem_concluida": float(f"{porcentagem_meta:.2f}"), 
            "total_estados": int(total_estados),
            "total_escolas": int(total_escolas),
            "total_municipios": int(total_municipios),
        },
        "graficos": {
            "alunos_por_curso": alunos_por_curso,
            "alunos_por_estado": contagem_alunos_por_estados,
            "municipios_por_estado": municipios_por_estado,
            "top_estados": top_estados,
            "generos": contagem_genero,
            "total_pcd": int(contagem_pcd)
        },
        "mapa": dados_mapa
    }

@app.route('/dados')
def dados():
    try:
        analise = obter_dados()
        return jsonify(analise)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    # Rodando na porta 5000
    app.run(debug=True, host='0.0.0.0', port=5000)