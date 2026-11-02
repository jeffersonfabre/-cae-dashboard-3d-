#!/usr/bin/env python3
"""Monta o .txt de exportação a partir de blocos JSON lidos do Google Sheets e regenera os dados do index.html.

Uso:  python3 tools/atualizar_do_sheets.py  PASTA_COM_BLOCOS  [index.html]

PASTA_COM_BLOCOS contém arquivos JSON {range, values} salvos pela leitura da planilha:
  - os que começam com 'Execu' no 'range' (aba Execução Orçamentária)
  - os que começam com 'NE!'  (aba NE, em blocos de linhas consecutivas, na ordem do range)
"""
import sys, os, json, re, csv, io, glob, subprocess

def carregar(pasta):
    blocos=[]
    for f in glob.glob(os.path.join(pasta,'*.json'))+glob.glob(os.path.join(pasta,'*.txt')):
        try: d=json.load(open(f,encoding='utf-8'))
        except Exception: continue
        if isinstance(d,dict) and 'range' in d and 'values' in d: blocos.append(d)
    return blocos

def linha_inicial(rng):
    m=re.search(r'!\$?[A-Z]+\$?(\d+)',rng); return int(m.group(1)) if m else 1

def aba(rng): return rng.split('!')[0].strip("'")

def para_csv(blocos):
    por_aba={}
    for b in blocos: por_aba.setdefault(aba(b['range']),[]).append(b)
    saida=[]
    for nome in ('Execução Orçamentária','NE'):
        bl=sorted(por_aba.get(nome,[]),key=lambda b:linha_inicial(b['range']))
        assert bl, f'Faltam blocos da aba {nome}'
        # confere se os blocos são contínuos (sem buracos)
        prox=1
        for b in bl:
            ini=linha_inicial(b['range']); assert ini==prox, f'Aba {nome}: bloco começa na linha {ini}, esperado {prox}'
            prox=ini+int(re.search(r':\$?[A-Z]+\$?(\d+)',b['range']).group(1))-ini+1
        linhas=[r for b in bl for r in b['values']]
        cab=next(r for r in linhas if r)               # primeira linha não vazia = cabeçalho
        n=len(cab); buf=io.StringIO(); w=csv.writer(buf,lineterminator='\n')
        for r in linhas:
            if not any(str(c).strip() for c in r): continue
            w.writerow(list(r)+['']*(n-len(r)))
        saida.append(f'## Sheet name: {nome}\n'+buf.getvalue())
    return '\n'.join(saida)

if __name__=='__main__':
    pasta=sys.argv[1]; html=sys.argv[2] if len(sys.argv)>2 else 'index.html'
    txt=para_csv(carregar(pasta))
    destino=os.path.join(pasta,'export.txt'); open(destino,'w',encoding='utf-8').write(txt)
    here=os.path.dirname(os.path.abspath(__file__)); raiz=os.path.dirname(here)
    blob=lambda t:''.join(re.findall(r'<script id="(?:execData|neData)" type="application/json">.*?</script>',t,re.S))
    antes=blob(open(html,encoding='utf-8').read())
    subprocess.run([sys.executable,'-I',os.path.join(here,'gerar_dados_execucao.py'),destino,html],check=True)
    if blob(open(html,encoding='utf-8').read())==antes: print('SEM_MUDANCA: dados iguais aos já publicados'); sys.exit(0)
    # dados mudaram -> incrementa a versão (patch) em index.html, sw.js e README.md
    h=open(html,encoding='utf-8').read(); m=re.search(r'<span>v(\d+)\.(\d+)\.(\d+)</span>',h)
    ant='.'.join(m.groups()); novo=f'{m.group(1)}.{m.group(2)}.{int(m.group(3))+1}'
    for arq in (html,os.path.join(raiz,'sw.js'),os.path.join(raiz,'README.md')):
        if os.path.exists(arq):
            t=open(arq,encoding='utf-8').read(); open(arq,'w',encoding='utf-8').write(t.replace('v'+ant,'v'+novo))
    print(f'MUDOU: dados atualizados; versão v{ant} -> v{novo}')
