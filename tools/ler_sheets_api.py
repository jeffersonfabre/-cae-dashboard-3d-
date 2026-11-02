#!/usr/bin/env python3
"""Lê as abas da planilha do CAE pela API do Google Sheets e grava blocos JSON {range, values}
para tools/atualizar_do_sheets.py.

Uso:  GOOGLE_SERVICE_ACCOUNT_JSON='{...}' SPREADSHEET_ID=... python3 tools/ler_sheets_api.py PASTA_SAIDA
A planilha precisa estar compartilhada (Leitor) com o e-mail da conta de serviço.
"""
import os, sys, json
import google.auth.transport.requests
from google.oauth2 import service_account

ABAS = {'Execução Orçamentária': 'AA', 'NE': 'AH'}   # aba -> última coluna lida
MIN_LINHAS = {'Execução Orçamentária': 100, 'NE': 1000}  # trava de segurança contra leitura quebrada

def main(saida):
    info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
    cred = service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
    sess = google.auth.transport.requests.AuthorizedSession(cred)
    sid = os.environ['SPREADSHEET_ID']
    os.makedirs(saida, exist_ok=True)
    for aba, col in ABAS.items():
        rng = f"'{aba}'!A1:{col}30000"
        r = sess.get(f'https://sheets.googleapis.com/v4/spreadsheets/{sid}/values/{rng}',
                     params={'valueRenderOption': 'FORMATTED_VALUE'}, timeout=300)
        r.raise_for_status()
        d = r.json(); vals = d.get('values', [])
        assert len(vals) >= MIN_LINHAS[aba], f'Aba {aba}: só {len(vals)} linhas lidas — abortando para não publicar dados quebrados'
        nome = aba.replace(' ', '_')
        # o range gravado precisa começar na linha 1 e terminar na última linha lida
        json.dump({'range': f"{aba}!A1:{col}{len(vals)}", 'values': vals},
                  open(os.path.join(saida, f'{nome}.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'{aba}: {len(vals)} linhas lidas')

if __name__ == '__main__':
    main(sys.argv[1])
