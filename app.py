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

    # 5. Cálculos Estatísticos
    # --- CÁLCULOS SELECIONADOS PARA O APP ---

    # 1. KPIs GERAIS
    total_alunos = len(df)
    
    # Defina a meta aqui (ou leia de outra aba se preferir)
    META_DO_PROJETO = 23500 
    porcentagem_meta = (total_alunos / META_DO_PROJETO) if META_DO_PROJETO > 0 else 0

    # 2. ESCOLAS E ESTADOS
    total_escolas = 0
    if 'ESCOLA' in df.columns:
        total_escolas = df['ESCOLA'].nunique()
        # Top 5 Escolas
        top_escolas = df['ESCOLA'].value_counts().head(5).to_dict()
    else:
        top_escolas = {}

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
    dados_mapa = [] # Lista nova para o mapa

    if 'ESTADO' in df.columns:
        # Limpeza
        df['ESTADO'] = df['ESTADO'].astype(str).str.replace(', Brasil', '').str.strip()
        df_estados = df[df['ESTADO'] != '']
        
        total_estados = df_estados['ESTADO'].nunique()
        top_estados = df_estados['ESTADO'].value_counts().head(5).to_dict()
        
        # LÓGICA DO MAPA:
        # Conta quantos alunos tem em CADA estado (não só no top 5)
        contagem_todos_estados = df_estados['ESTADO'].value_counts().to_dict()
        
        for estado, qtd in contagem_todos_estados.items():
            # Remove acentos para bater com a chave do dicionário (ex: MARANHÃO -> MARANHAO)
            chave = estado.upper().replace('Ã', 'A').replace('Õ', 'O').replace('Ç', 'C').replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U').replace('Â', 'A').replace('Ê', 'E')
            
            if chave in COORDENADAS_ESTADOS:
                coords = COORDENADAS_ESTADOS[chave]
                dados_mapa.append({
                    "estado": estado,
                    "qtd": qtd,
                    "lat": coords['lat'],
                    "lng": coords['lng']
                })

    # 3. CURSOS 
    cursos = {}
    if 'CURSO' in df.columns:
        cursos = df['CURSO'].value_counts().head(5).to_dict()

    # 4. IMPACTO SOCIAL (Gênero e PCD)
    generos = {}
    if 'SEXO' in df.columns:
        generos = df['SEXO'].value_counts().to_dict()

    total_pcd = 0
    if 'PESSOA COM DEFICIÊNCIA (PCD)' in df.columns:
        col_pcd = 'PESSOA COM DEFICIÊNCIA (PCD)'
        # Conta quantos "Sim" (ajuste conforme sua planilha: 'Sim', 'SIM', 'S')
        total_pcd = df[df[col_pcd].astype(str).str.upper() == 'SIM'].shape[0]

    return {
        "kpis": {
            "total_alunos": int(total_alunos),
            "meta_projeto": int(META_DO_PROJETO),
            "porcentagem_concluida": float(f"{porcentagem_meta:.2f}"), 
            "total_estados": int(total_estados),
            "total_escolas": int(total_escolas),
            "total_pcd": int(total_pcd)
        },
        "graficos": {
            "top_cursos": cursos,
            "top_estados": top_estados,
            "top_escolas": top_escolas,
            "generos": generos
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