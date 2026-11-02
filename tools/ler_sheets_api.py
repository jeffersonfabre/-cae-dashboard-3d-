#!/usr/bin/env python3
"""Lê as abas da planilha-banco de dados do CAE e grava blocos JSON {range, values}
para tools/atualizar_do_sheets.py.

Dois modos (escolhido automaticamente):
  1) Planilha pública/“qualquer pessoa com o link” (sem credencial): baixa cada aba em CSV.
  2) Planilha privada: se existir GOOGLE_SERVICE_ACCOUNT_JSON, lê pela API do Google Sheets
     (a planilha precisa estar compartilhada, como Leitor, com a conta de serviço).

Uso:  SPREADSHEET_ID=... python3 tools/ler_sheets_api.py PASTA_SAIDA
"""
import os, sys, json, csv, io

# aba -> (última coluna, gid na planilha-banco "BD Site Dashboad CAE")
ABAS = {'Execução Orçamentária': ('AA', 1963592069), 'NE': ('AH', 892020825)}
MIN_LINHAS = {'Execução Orçamentária': 100, 'NE': 1000}   # trava contra leitura quebrada

def ler_api(sid, aba, col):
    import google.auth.transport.requests
    from google.oauth2 import service_account
    info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
    cred = service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    sess = google.auth.transport.requests.AuthorizedSession(cred)
    r = sess.get(f'https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/' + f"'{aba}'!A1:{col}30000",
                 params={'valueRenderOption': 'FORMATTED_VALUE'}, timeout=300)
    r.raise_for_status()
    return r.json().get('values', [])

def ler_publico(sid, gid):
    import requests
    r = requests.get(f'https://docs.google.com/spreadsheets/d/{sid}/export', params={'format': 'csv', 'gid': gid}, timeout=300)
    r.raise_for_status()
    ctype = r.headers.get('content-type', '')
    texto = r.content.decode('utf-8-sig')
    assert 'csv' in ctype.lower() and not texto.lstrip().startswith('<'), \
        'A planilha não está pública (recebi uma página de login). Compartilhe como "Qualquer pessoa com o link: Leitor" ou configure GOOGLE_SERVICE_ACCOUNT_JSON.'
    return [row for row in csv.reader(io.StringIO(texto))]

def main(saida):
    sid = os.environ['SPREADSHEET_ID']
    usar_api = bool(os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '').strip())
    os.makedirs(saida, exist_ok=True)
    for aba, (col, gid) in ABAS.items():
        vals = ler_api(sid, aba, col) if usar_api else ler_publico(sid, gid)
        while vals and not any(str(c).strip() for c in vals[-1]): vals.pop()   # tira linhas vazias do fim
        assert len(vals) >= MIN_LINHAS[aba], f'Aba {aba}: só {len(vals)} linhas lidas — abortando para não publicar dados quebrados'
        json.dump({'range': f"{aba}!A1:{col}{len(vals)}", 'values': vals},
                  open(os.path.join(saida, aba.replace(' ', '_') + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        print(f"{aba}: {len(vals)} linhas lidas ({'API' if usar_api else 'CSV público'})")

if __name__ == '__main__':
    main(sys.argv[1])
