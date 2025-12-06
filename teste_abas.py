import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuração para conexão com a planilha
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)

# Abre a planilha pelo ID
id_planilha = "1XZkJVMtfeXUvylE04VHO-KCsz8C9l5apj_sthZb4Uzo"
sh = client.open_by_key(id_planilha)

print(f"--- Planilha: {sh.title} ---")
for i, worksheet in enumerate(sh.worksheets()):
    print(f"Aba {i}: '{worksheet.title}' - Linhas totais: {worksheet.row_count}")