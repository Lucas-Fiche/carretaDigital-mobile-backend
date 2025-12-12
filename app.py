import os # Fornece funções para interagir com o SO
import gspread # Fornece funções para acesso ao Google Sheets
import pandas as pd # Fornece funções para manipulação de dados
from oauth2client.service_account import ServiceAccountCredentials # Fornece funções para criar credenciais de autenticação em APIs do Google
from flask import Flask, jsonify # Fornece a classe principal do Framework Flask e operações para manipular arquivos JSON
from flask_cors import CORS # Fornece suporte a CORS para integração com o Frontend
from dotenv import load_dotenv # Importa a blibioteca para carregar as variáveis do arquivo .env
load_dotenv() # Carrega as variáveis do arquivo .env

# Criando a aplicação Flask em app
app = Flask(__name__)
# Adiciona CORS na aplicação app
CORS(app)

# DEFINIÇÃO DAS COLUNAS COMO VARIÁVEIS GLOBAIS
COL_NOME = 'NOME'
COL_ESCOLA = 'ESCOLA'
COL_ESTADO = 'ESTADO'
COL_MUNICIPIO = 'MUNICÍPIO'
COL_CURSO = 'CURSO'
COL_SEXO = 'SEXO'
COL_PCD = 'PESSOA COM DEFICIÊNCIA (PCD)'
COL_LINK = 'LINK DRIVE'

def carregar_dataframe():
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
    
    # Busca o ID nas variáveis de ambiente no .env
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    
    # Mensagem de erro caso não encontre a variável no .env
    if not spreadsheet_id:
        raise Exception("ID da planilha não configurado")
    
    # Abre a planilha "TABELA - BASE DE DADOS" do Google Sheets a partir do ID armazenado na variável de ambiente
    planilha = client.open_by_key(spreadsheet_id)

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

    return df

def obter_dados(df):

    if df.empty:
        return {"mensagem": "Base de Dados vazia", "kpis": {}}

    # 5. Cálculos ESTRATÉGICOS

    # KPI 1. TOTAL DE ALUNOS
    # Aqui contamos a quantidade de linhas do dataframe e armazenamos na variável total_alunos
    total_alunos = len(df)
    
    # KPI 2. META DO PROJETO
    META_DO_PROJETO = 23500 # Definimos a meta do projeto
    # Dividimos o total de alunos pela meta do projeto se a meta do projeto for maior que zero. Caso contrário, a porcentagem será 0.
    porcentagem_meta = (total_alunos / META_DO_PROJETO) if META_DO_PROJETO > 0 else 0

    # KPI 3. NÚMERO DE ESCOLAS
    # Criamos uma variável total_escolas para armazenar o valor de escolas
    total_escolas = 0
    # Se a coluna ESCOLA existir no dataframe, a variável total_escolas vai receber a contagem de valores únicos (excluindo vazios) dessa coluna.
    if COL_ESCOLA in df.columns:
        total_escolas = df[COL_ESCOLA].nunique() # .nunique() exclui valores vazios por padrão

    # KPI 4. MAPA DE CALOR | TOTAL DE ESTADOS | ALUNOS POR ESTADO 
    # Armazenamos as coordenadas de todos os estados do projeto para marcação no mapa produzido com Flutter
    COORDENADAS_ESTADOS = {
        "DISTRITO FEDERAL": {"lat": -15.7998, "lng": -47.8645},
        "MARANHAO": {"lat": -4.9609, "lng": -45.2744},
        "MATO GROSSO DO SUL": {"lat": -20.7722, "lng": -54.7852},
        "PERNAMBUCO": {"lat": -8.8137, "lng": -36.9541},
        "RIO DE JANEIRO": {"lat": -22.9068, "lng": -43.1729},
        "RIO GRANDE DO SUL": {"lat": -30.0346, "lng": -51.2177},
        "SANTA CATARINA": {"lat": -27.2423, "lng": -50.2189},
    }

    # total_estados armazena a quantidade de estados do projeto
    total_estados = 0
    # top_estados é um dicionário que vai armazenar os top 5 estados com mais alunos como key e a quantidade de alunos como valor
    top_estados = {}
    # faz a contagem de todos os alunos de todos os estados e armazena em um dicionário utilizando o estado como key e os alunos como valor
    contagem_alunos_por_estados = {}
    # lista para armazenar o estado, quantidade de alunos e suas coordenadas.
    dados_mapa = [] 

    if COL_ESTADO in df.columns:
        # Faz a limpeza dos dados da coluna ESTADO, transformando tudo em string (astype(str)) e trocando o texto que segue o formato "Maranhão, Brasil", substituindo ", Brasil" por ""
        df[COL_ESTADO] = df[COL_ESTADO].astype(str).str.replace(', Brasil', '').str.strip()
        # Adiciona a variável df_estados o df formado por tudo que temos na coluna ESTADO que seja diferente de vazio
        df_estados = df[df[COL_ESTADO] != '']
        
        # Armazena em total_estados todos os valores da coluna ESTADO como valores únicos
        total_estados = df_estados[COL_ESTADO].nunique()
        # Pega os valores da coluna ESTADO e ordena de forma decrescente (value_counts()) e depois filtra pelos 5 primeiros (head(5)), transformando em um dicionário, com a key sendo o estado e o valor a contagem
        top_estados = df_estados[COL_ESTADO].value_counts().head(5).to_dict()
        # Faz a mesma coisa que a linha acima, mas sem filtrar pelos 5 melhores, garantindo que a contagem englobe todos os estados
        contagem_alunos_por_estados = df_estados[COL_ESTADO].value_counts().to_dict()
        
        # Para estado (key do dicionário) e qtd (valores de cada key)
        for estado, qtd in contagem_alunos_por_estados.items():
            # Remove acentos para bater com a chave do dicionário de coordenadas (ex: MARANHÃO -> MARANHAO)
            chave = estado.upper().replace('Ã', 'A').replace('Õ', 'O').replace('Ç', 'C').replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U').replace('Â', 'A').replace('Ê', 'E')
            
            # Se o estado estiver no dicionário de COORDENADAS_ESTADOS ele armazena a coordenada na variável coords e adiciona na variável dados_mapa os valores de estado, quantidade, latitude e longitude.
            if chave in COORDENADAS_ESTADOS:
                coords = COORDENADAS_ESTADOS[chave]
                # Esses quatro valores são usados para fazer as marcações do mapa em cima do estado com a quantidade de alunos daquele estado
                dados_mapa.append({
                    "estado": estado,
                    "qtd": int(qtd),
                    "lat": coords['lat'],
                    "lng": coords['lng']
                })

    # KPI 5. MUNICÍPIOS

    # Cria um dicionário e o armazena na variável municipios_por_estado
    municipios_por_estado = {}
    # Cria uma variável para armazenar a contagem de munícipios
    total_municipios = 0
    
    # Se as colunas ESTADO e MUNÍCIPIO estiverem no dataframe, ele prossegue
    if COL_ESTADO in df.columns and COL_MUNICIPIO in df.columns:
        # Aqui é desconsiderado todos os campos vazios dessas colunas
        df_limpo = df[(df[COL_ESTADO] != '') & (df[COL_MUNICIPIO] != '')]
        # Em agrupamento, o .groupby agrupa os dados das colunas ESTADOS e MUNICIPIO do df_limpo de forma hierárquica, agrupando os munícipios dentro de seu respectivo estado. O .size() conta quantos dados temos em cada pilha deixando no formato (ESTADO, MUNICIPIO, CONTAGEM)
        agrupamento = df_limpo.groupby([COL_ESTADO, COL_MUNICIPIO]).size()
        
        # Retorna cada linha do agrupamento com índice (ESTADO, MUNICIPIO) e suas respectivas contagens
        for (estado, municipio), qtd in agrupamento.items():
            # Checa se é a primeira vez que determinado estado aparece no dicionário final, e caso positivo, cria uma chave para o estado com um dicionário vazio dentro
            if estado not in municipios_por_estado:
                # Chave do estado com um dicionário vazio dentro
                municipios_por_estado[estado] = {}
            # Se não for a primeira aparição do estado, ele aproveita um dicionário existente usando como keys estado e municipio e adiciona a quantidade.
            municipios_por_estado[estado][municipio] = int(qtd)

        # Pega os itens do dicionário municipios_por_estado 
        for estado, cidades in municipios_por_estado.items():
            # Na variável total_municipios adiciona a contagem de cidades (Em cidades estão sendo contabilizados munícipios e Regiões Administrativas de Brasília)
            total_municipios += len(cidades)
        
        total_municipios -= 1 # No Distrito Federal, Asa Sul e Asa Norte contam como UMA região administrativa (DF), por isso retiramos 1 da contagem final.

    # KPI 6. CURSOS 
    # Armazena um dicionário na variável alunos_por_curso
    alunos_por_curso = {}
    # Se a coluna CURSO existir, armazenamos na variável alunos_por_curso a contagem decrescente por curso em um dicionário, com a key sendo o curso e o valor o número de alunos. 
    if COL_CURSO in df.columns:
        alunos_por_curso = df[COL_CURSO].value_counts().to_dict()

    # KPI 7. Gênero e PCD
    # Cria na variável contagem_genero um dicionário com as chaves Maculino, Feminino e Outros para armazenar suas respectivas quantidades. 
    contagem_genero = {
        "Masculino": 0,
        "Feminino": 0,
        "Outros": 0,
    }

    # Se SEXO for uma coluna presente no df, prossegue
    if COL_SEXO in df.columns:
        # Transforma todos os valores da coluna SEXO em string e remove os espaços das pontas
        sexo = df[COL_SEXO].astype(str).str.strip()

        # Conta apenas os marcados como masculino e feminino e armazena nas variáveis qtd_masc e qtd_fem
        qtd_masc = int((sexo == 'Masculino').sum())
        qtd_fem = int((sexo == 'Feminino').sum())

        # Preenche o dicionário contagem_genero com a quantidade de cada sexo
        contagem_genero["Masculino"] = qtd_masc
        contagem_genero["Feminino"] = qtd_fem

        # Pega o tamanho do dataframe (número de linhas) e diminui do número de homens e mulheres calculados anteriormente para termos o valor de Outros
        contagem_genero["Outros"] = len(df) - (qtd_masc + qtd_fem)

    # Cria a variável contagem_pcd onde irá armazenar o total de pessoas pcd
    contagem_pcd = 0
    
    if COL_PCD in df.columns:
        # Transforma todos os dados da coluna em string, remove os espaços das pontas, deixa tudo em maiúsculo e, sendo algo como SIM, S ou YES ele faz a soma.
        contagem_pcd = df[COL_PCD].astype(str).str.strip().str.upper().isin(['SIM', 'S', 'YES']).sum()
        
    # Retornos feitos pela API no arquivo JSON
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

def busca_certificado(df):
    nome_pesquisa = request.args.get('nome')
    if not nome_pesquisa:
        return jsonify({"erro": "Informe um nome"}), 400

    try:
        df = carregar_dataframe()
        if COL_NOME not in df.columns or COL_LINK not in df.columns:
            return jsonify({"erro": f"Colunas não encontradas. Colunas disponíveis: {list(df.columns)}"}), 500

        filtro = df[df[COL_NOME].str.contains(nome_pesquisa, case=False, na=False)]
        resultados = []

        for _, linha in filtro.iterrows():
            resultados.append({
                "nome": linha[COL_NOME],
                "curso": linha[COL_CURSO],
                "link": linha[COL_LINK]
            })

            return jsonify({
                "total": len(resultados),
                "resultados": resultados
            })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    
@app.route('/dados')
def dados():
    try:
        df = carregar_dataframe()
        analise = obter_dados(df)
        return jsonify(analise)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    
@app.route('/certificados')
def certificados():
    try:
        df = carregar_dataframe()
        obter_certificados = busca_certificado(df)
        return jsonify(obter_certificados)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    # Rodando na porta 5000
    app.run(debug=True, host='0.0.0.0', port=5000)