#!/usr/bin/env python3
"""Gera o bloco de dados da aba "Execução Orçamentária" dentro do index.html.

Uso:  python3 tools/gerar_dados_execucao.py  "CAE - Execução Orçamentária.txt"  [index.html]

O arquivo de entrada é a exportação (CSV com marcadores "## Sheet name: ...") da planilha
do CAE. Só a aba "Execução Orçamentária" entra no painel; a aba "NE" é lida apenas para
descobrir a data da última nota de empenho (data de referência).
"""
import sys, io, re, json
import pandas as pd

SIGLAS = {  # UGR -> (sigla, nome por extenso)
 '120127':('CISCEA','Comissão de Implantação do Sistema de Controle do Espaço Aéreo'),
 '120048':('PAME','Parque de Material de Eletrônica da Aeronáutica'),
 '120042':('HFAG','Hospital de Força Aérea do Galeão'),
 '120040':('HCA','Hospital Central da Aeronáutica'),
 '120648':('SDAP','SDAP (nome por extenso a confirmar)'),
 '120100':('SDAB','Subdiretoria de Abastecimento'),
 '120043':('LAQFA','Laboratório Químico-Farmacêutico da Aeronáutica'),
 '120008':('CINDACTA I','1º Centro Integrado de Defesa Aérea e Controle de Tráfego Aéreo'),
 '120072':('CINDACTA II','2º Centro Integrado de Defesa Aérea e Controle de Tráfego Aéreo'),
 '120021':('CINDACTA III','3º Centro Integrado de Defesa Aérea e Controle de Tráfego Aéreo'),
 '120094':('CINDACTA IV','4º Centro Integrado de Defesa Aérea e Controle de Tráfego Aéreo'),
 '120036':('DECEA','Departamento de Controle do Espaço Aéreo'),
 '120069':('CRCEA','Centro Regional de Controle do Espaço Aéreo'),
 '120041':('HAAF','Hospital de Aeronáutica dos Afonsos'),
 '120115':('COMAE','Comando de Operações Aeroespaciais'),
 '120096':('HFAB','Hospital de Força Aérea de Brasília'),
 '120066':('HFASP','Hospital de Força Aérea de São Paulo'),
 '120133':('DIRAD','Diretoria de Administração da Aeronáutica'),
 '120631':('BANT','Base Aérea de Natal'),
 '120162':('OASD','Odontoclínica de Aeronáutica Santos Dumont'),
 '120067':('ICEA','Instituto de Controle do Espaço Aéreo'),
 '120058':('DIRSA','Diretoria de Saúde da Aeronáutica'),
 '120154':('HAMN','Hospital de Aeronáutica de Manaus'),
 '120129':('CEMAL','Centro de Medicina Aeroespacial'),
 '120014':('BAFZ','Base Aérea de Fortaleza'),
 '120089':('HABE','Hospital de Aeronáutica de Belém'),
 '120019':('HARF','Hospital de Aeronáutica de Recife'),
 '120136':('DIRAP','Diretoria de Administração do Pessoal'),
 '120138':('MUSAL','Museu Aeroespacial'),
 '120638':('BACG','Base Aérea de Campo Grande'),
 '120112':('OABR','Odontoclínica de Aeronáutica de Brasília'),
 '120025':('EPCAR','Escola Preparatória de Cadetes do Ar'),
 '120023':('BASV','Base Aérea de Salvador'),
 '120625':('GAP-DF','Grupamento de Apoio do Distrito Federal'),
 '120645':('GAP-GL','Grupamento de Apoio do Galeão'),
 '120064':('EEAR','Escola de Especialistas de Aeronáutica'),
 '120633':('GAP-SP','Grupamento de Apoio de São Paulo'),
 '120669':('BASC','Base Aérea de Santa Cruz'),
 '120044':('BRV','Base de Recepção de Veteranos'),
 '120060':('AFA','Academia da Força Aérea'),
 '120016':('GAP-SJ','Grupamento de Apoio de São José dos Campos'),
 '120641':('BAPV','Base Aérea de Porto Velho'),
 '120629':('GAP-CO','Grupamento de Apoio de Canoas'),
 '120632':('GAP-RF','Grupamento de Apoio de Recife'),
 '120024':('CIAAR','Centro de Instrução e Adaptação da Aeronáutica'),
 '120624':('BAAN','Base Aérea de Anápolis'),
 '120636':('GAP-LS','Grupamento de Apoio de Lagoa Santa'),
 '120077':('HACO','Hospital de Aeronáutica de Canoas'),
 '120006':('GAP-BR','Grupamento de Apoio de Brasília'),
 '120623':('GAP-AF','Grupamento de Apoio dos Afonsos'),
 '120630':('GAP-MN','Grupamento de Apoio de Manaus'),
 '120073':('BAFL','Base Aérea de Florianópolis'),
 '120628':('GAP-BE','Grupamento de Apoio de Belém'),
 '120643':('BASM','Base Aérea de Santa Maria'),
 '120118':('OARF','Odontoclínica de Aeronáutica de Recife'),
 '120001':('GABAER','Gabinete do Comandante da Aeronáutica'),
 '120121':('EATRJ','Escritório de Assessoria de Transição do RJ'),
 '120039':('GAP-RJ','Grupamento de Apoio do Rio de Janeiro'),
 '120013':('CLA','Centro de Lançamento de Alcântara'),
 '120637':('BABV','Base Aérea de Boa Vista'),
 '120165':('IMAE','Instituto de Medicina Aeroespacial Brig. Méd. Roberto Teixeira'),
 '120195':('CAE','Centro de Aquisições Específicas'),
 '120111':('EMAER','Estado-Maior da Aeronáutica'),
 '120107':('COMPREP','Comando de Preparo'),
 '120110':('DCTA','Departamento de Ciência e Tecnologia Aeroespacial'),
 '120026':('PAMALS','Parque de Material Aeronáutico de Lagoa Santa'),
 '120057':('CGABEG','Centro Gerontológico da Aeronáutica Brig. Eduardo Gomes'),
 '120062':('BASP','Base Aérea de São Paulo'),
 '-8':('S/Inf.','Sem informação'),
 '120035':('CTLA','Centro de Transporte Logístico da Aeronáutica'),
 '120088':('COMARA','Comissão de Aeroportos da Região Amazônica'),
 '120130':('COMGAP','Comando-Geral de Apoio'),
}
VALS=['Provisão Recebida','Destaque Recebido','Crédito Disponível','Crédito Empenhado a Liquidar',
      'Crédito Empenhado em Liquidação','Crédito Empenhado Liquidado a Pagar','Crédito Empenhado Liquidado Pago']

def num(x):
    x=x.replace('R$','').strip().replace('.','').replace(',','.')
    return round(float(x),2) if x not in ('','-') else 0.0

def main(src, html='index.html'):
    txt=open(src,encoding='utf-8').read()
    parts=re.split(r'^## Sheet name: (.*)$',txt,flags=re.M)
    sheets={parts[i].strip():parts[i+1] for i in range(1,len(parts),2)}
    df=pd.read_csv(io.StringIO('\n'.join(l for l in sheets['Execução Orçamentária'].split('\n') if l.strip())),dtype=str,keep_default_na=False)
    for c in VALS: df[c]=df[c].map(num)
    rec=df['Provisão Recebida']+df['Destaque Recebido']
    chk=(df['Crédito Disponível']+df['Crédito Empenhado a Liquidar']+df['Crédito Empenhado em Liquidação']
         +df['Crédito Empenhado Liquidado a Pagar']+df['Crédito Empenhado Liquidado Pago']-rec).abs()
    assert (chk<0.02).all(), 'Linhas em que as colunas não fecham com o crédito recebido'
    faltam=sorted(set(df['UGR'])-set(SIGLAS)); assert not faltam, f'UGR sem sigla: {faltam}'
    tabs={k:[] for k in ('gc','uo','acao','fonte','pi','nd')}
    def idx(k,v):
        t=tabs[k]
        if v not in t: t.append(v)
        return t.index(v)
    # ND: agrupa por código (o nome varia de grafia entre linhas)
    nd_nome={}
    for c,n in zip(df['ND'],df['ND-Nome']): nd_nome.setdefault(c,n.replace('- ','- ').replace('TERCEIROS- ','TERCEIROS - '))
    rows=[]
    for _,r in df.iterrows():
        rows.append([r['UGR'],idx('gc',r['Grande Cmdo']),idx('uo',[r['Unidade Orçamentária'],r['Unidade Orçamentária-Nome']]),
            idx('acao',[r['Ação Governo'],r['Ação Governo-Nome']]),idx('fonte',[r['Fonte'],r['Fonte-Nome']]),
            idx('pi',[r['PI'],r['PI-Nome']]),idx('nd',[r['ND'],nd_nome[r['ND']]])]+[r[c] for c in VALS])
    datas=re.findall(r'^(\d\d)/(\d\d)/(\d{4}),',sheets.get('NE',''),re.M)
    ref='/'.join(max(datas,key=lambda d:(d[2],d[1],d[0]))) if datas else ''
    out={'ref':ref,'ugs':{k:v for k,v in SIGLAS.items() if k in set(df['UGR'])},'t':tabs,
         'cols':['ugr','gc','uo','acao','fonte','pi','nd','prov','dest','disp','aliq','emliq','liqpag','pago'],'rows':rows}
    blob=json.dumps(out,ensure_ascii=False,separators=(',',':'))
    s=open(html,encoding='utf-8').read()
    novo=f'<script id="execData" type="application/json">{blob}</script>'
    if 'id="execData"' in s: s=re.sub(r'<script id="execData" type="application/json">.*?</script>',lambda m:novo,s,flags=re.S)
    else: s=s.replace('<script src="https://cdnjs.cloudflare.com',novo+'\n<script src="https://cdnjs.cloudflare.com',1)
    open(html,'w',encoding='utf-8').write(s)
    print(f'{len(rows)} linhas · {len(out["ugs"])} UGs · ref {ref} · {len(blob)/1024:.0f} KB')

if __name__=='__main__': main(sys.argv[1], *(sys.argv[2:3] or ['index.html']))
