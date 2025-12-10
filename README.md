# 🚛 API do Projeto Carreta Digital

Esta API, desenvolvida em **Python** com **Flask**, atua como o backend de dados para o aplicativo móvel do Projeto Carreta Digital.

O objetivo principal desta aplicação é fornecer uma interface de dados para o aplicativo oficial (desenvolvido em **Dart/Flutter**), permitindo que colaboradores e gestores visualizem insights estratégicos, monitorem o atingimento de metas e acompanhem os indicadores de desempenho (KPIs) do projeto em tempo real.

# 🎯 Objetivo e Contexto

A API conecta o aplicativo móvel à base de dados central no Google Sheets (`TABELA - BASE DE DADOS`), processando milhares de registros para entregar métricas consolidadas sobre:

* **Atingimento da Meta:** Monitoramento do progresso rumo à meta de **23.500** alunos.

* **Impacto Geográfico:** Visualização da presença do projeto nos estados e municípios.

* **Perfil do Público:** Análise demográfica e de inclusão (PCDs).🚀 

# 🚀Funcionalidades Principais

* **Conexão Segura:** Autenticação com a API do Google Sheets via Service Account (OAuth2).

* **Processamento de Dados:** Utiliza `pandas` para limpeza, normalização e cálculo de métricas complexas.

* **Integração Mobile:** Fornece endpoints JSON otimizados para consumo pelo aplicativo Flutter.

* **Geolocalização:** Mapeamento de coordenadas (Latitude/Longitude) para plotagem de mapas de calor no app.

* **CORS Habilitado:** Configurado para permitir requisições de diferentes origens, facilitando o desenvolvimento e testes do app.

# 🛠️ Tecnologias Utilizadas

**Backend**

* [Python 3.x:](https://www.python.org/): Linguagem base.

* [Flask](https://flask.palletsprojects.com/): Framework web para criação da API.

* [Pandas](https://pandas.pydata.org/): Manipulação e análise de dados tabulares.

* [Gspread](https://docs.gspread.org/): Cliente para interação com Google Sheets.

**Hospedagem do Backend:** 

* [Render.com](https://render.com/)

**Frontend (Consumidor)**

* **Dart / Flutter:** Tecnologia utilizada no desenvolvimento do aplicativo móvel que consome esta API.

# ⚙️ Pré-requisitos e Configuração

**1. Clonar o Repositório**

git clone [https://seu-repositorio.git](https://seu-repositorio.git)
cd nome-da-pasta

**2. Configurar o Ambiente Virtual (Recomendado)**

A pasta `.venv` (conforme estrutura do projeto) é onde as bibliotecas ficam isoladas.

```
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

**3. Instalar Dependências**

Com o ambiente virtual ativo, instale os pacotes listados em `requirements.txt`:

```
pip install -r requirements.txt
```

**4. Configurar Credenciais do Google (CRÍTICO) ⚠️**

Para que a aplicação acesse a planilha do projeto, é necessário um arquivo de credenciais de **Conta de Serviço (Service Account)**.

1. Obtenha o arquivo JSON da Service Account autorizada no Google Cloud.
2. Renomeie o arquivo para `credentials.json`.
3. Coloque-o na raiz do projeto.
4. **Importante:** A planilha da `BASE DE DADOS` deve estar compartilhada com o e-mail dessa Service Account.

# ▶️ Como Executar

**Testar Conexão (Diagnóstico)**

Antes de rodar a API, use o script de teste para validar o acesso à planilha:

```
python teste_abas.py
```

**Rodar a API**

Para iniciar o servidor de desenvolvimento:

```
python app.py
```

O servidor iniciará em: `http://0.0.0.0:5000`

> **Nota de Performance:** O carregamento inicial pode levar de 3 a 5 segundos devido à leitura e processamento das milhares de linhas da base de dados.

# 📚 Documentação da API

`GET /dados`

Endpoint principal consumido pelo App Flutter. Retorna todos os KPIs, gráficos e dados geográficos.

**Exemplo de Resposta (JSON):**

```
{
  "kpis": {
    "total_alunos": 1500,
    "meta_projeto": 23500,
    "porcentagem_concluida": 6.38,
    "total_estados": 5,
    "total_escolas": 42,
    "total_municipios": 12
  },
  "graficos": {
    "alunos_por_curso": {
      "Informática": 500,
      "Gestão": 300
    },
    "alunos_por_estado": {
      "RIO DE JANEIRO": 800
    },
    "generos": {
      "Masculino": 700,
      "Feminino": 790,
      "Outros": 10
    },
    "total_pcd": 5
  },
  "mapa": [
    {
      "estado": "RIO DE JANEIRO",
      "qtd": 800,
      "lat": -22.9068,
      "lng": -43.1729
    }
  ]
}
```

# 📂 Estrutura de Arquivos

```
/
├── .venv/                 # Ambiente virtual
├── .gitignore             # Arquivos ignorados (ex: credentials.json)
├── app.py                 # API Flask (Lógica de Negócio)
├── credentials.json       # Credenciais Google (Não versionado)
├── requirements.txt       # Dependências
├── teste_abas.py          # Script de teste de conexão
└── README.md              # Documentação
```

# 📝 Licença

Esta aplicação é de uso interno do **Projeto Carreta Digital** e foi desenvolvida por **Lucas Fiche**.