/*DATALIB*/
const CAEData=(()=>{
  function parseCSV(text){
    const rows=[]; let row=[], cur='', q=false, i=0; const n=text.length;
    if(text.charCodeAt(0)===0xFEFF) i=1;
    for(; i<n; i++){ const c=text[i];
      if(q){ if(c==='"'){ if(text[i+1]==='"'){ cur+='"'; i++; } else q=false; } else cur+=c; }
      else if(c==='"') q=true;
      else if(c===','){ row.push(cur); cur=''; }
      else if(c==='\n'||c==='\r'){ if(c==='\r'&&text[i+1]==='\n') i++; row.push(cur); cur=''; rows.push(row); row=[]; }
      else cur+=c; }
    if(cur!==''||row.length){ row.push(cur); rows.push(row); }
    return rows;
  }
  // aceita "R$ 1.234,56", "16519,28", "16519.28", "-1.234,5"
  function num(s){ if(typeof s==='number') return s; s=String(s==null?'':s).trim(); if(!s) return 0;
    const neg=/^\(.*\)$/.test(s)||/-/.test(s); s=s.replace(/[R$\s()\-+]/g,'');
    if(s.includes(',')) s=s.replace(/\./g,'').replace(',','.'); else if(/^\d{1,3}(\.\d{3})+$/.test(s)) s=s.replace(/\./g,'');
    const v=parseFloat(s); return isNaN(v)?0:(neg?-v:v); }
  const r2=v=>Math.round(v*100)/100;
  function table(rows,must){
    const h=rows.findIndex(r=>must.every(m=>r.includes(m)));
    if(h<0) throw new Error('Cabeçalho não encontrado: '+must.join(', '));
    const cols={}; rows[h].forEach((c,i)=>{ c=String(c).trim(); if(!(c in cols)) cols[c]=i; });
    const data=rows.slice(h+1).filter(r=>r.some(c=>String(c).trim()!==''));
    return {cols, data, get:(r,n)=>{ const i=cols[n]; return i==null?'':String(r[i]==null?'':r[i]).trim(); }};
  }
  function dict(){ const m=new Map(), list=[]; return {list, idx(v){ const k=typeof v==='string'?v:JSON.stringify(v); let i=m.get(k); if(i==null){ i=list.length; m.set(k,i); list.push(v);} return i; }}; }
  function isoDate(s){ s=String(s||'').trim(); let m=/^(\d{2})\/(\d{2})\/(\d{4})/.exec(s); if(m) return m[3]+'-'+m[2]+'-'+m[1]; m=/^(\d{4})-(\d{2})-(\d{2})/.exec(s); return m?m[0]:''; }

  const VALS=['Provisão Recebida','Destaque Recebido','Crédito Disponível','Crédito Empenhado a Liquidar','Crédito Empenhado em Liquidação','Crédito Empenhado Liquidado a Pagar','Crédito Empenhado Liquidado Pago'];
  function execucao(rows,siglas){
    const t=table(rows,['Grande Cmdo','UGR','Provisão Recebida','Crédito Disponível']), g=t.get;
    const D={gc:dict(),uo:dict(),acao:dict(),fonte:dict(),pi:dict(),nd:dict(),po:dict()}, ndNome={}, out=[], nomes={};
    for(const r of t.data){ const ugr=g(r,'UGR'); if(!ugr) continue; nomes[ugr]=nomes[ugr]||g(r,'UGR-Nome');
      const nd=g(r,'ND'); if(!(nd in ndNome)) ndNome[nd]=g(r,'ND-Nome').replace('TERCEIROS- ','TERCEIROS - ');
      out.push([ugr,D.gc.idx(g(r,'Grande Cmdo')),D.uo.idx([g(r,'Unidade Orçamentária'),g(r,'Unidade Orçamentária-Nome')]),
        D.acao.idx([g(r,'Ação Governo'),g(r,'Ação Governo-Nome')]),D.fonte.idx([g(r,'Fonte'),g(r,'Fonte-Nome')]),
        D.pi.idx([g(r,'PI'),g(r,'PI-Nome')]),D.nd.idx([nd,ndNome[nd]]),...VALS.map(v=>r2(num(g(r,v)))),g(r,'PTRES'),D.po.idx([g(r,'PO'),g(r,'Plano Orçamentário-Nome')])]); }
    const ugs={}; for(const r of out) if(!ugs[r[0]]) ugs[r[0]]=siglas[r[0]]||[r[0],nomes[r[0]]||r[0]];
    return {ugs,t:{gc:D.gc.list,uo:D.uo.list,acao:D.acao.list,fonte:D.fonte.list,pi:D.pi.list,nd:D.nd.list,po:D.po.list},
      cols:['ugr','gc','uo','acao','fonte','pi','nd','prov','dest','disp','aliq','emliq','liqpag','pago','ptres','po'],rows:out};
  }
  function notas(rows,siglas){
    const t=table(rows,['Data','NE','UGR','Valor a NE']), g=t.get;
    const porNE=new Map();
    for(const r of t.data){ const ne=g(r,'NE'); if(!ne) continue;
      let o=porNE.get(ne); if(!o){ o={r,linhas:[]}; porNE.set(ne,o); }
      o.linhas.push([r2(num(g(r,'Valor a NE'))),r2(num(g(r,'Empenho a Liquidar'))),r2(num(g(r,'Empenho em Liquidação'))),r2(num(g(r,'Empenho Liquidado a Pagar'))),r2(num(g(r,'Empenho Liquidado Pago')))]); }
    const D={ugr:dict(),gc:dict(),ptres:dict(),fonte:dict(),pi:dict(),nd:dict(),esfera:dict(),acao:dict(),po:dict(),forn:dict(),amparo:dict(),lic:dict()}, nomes={}, out=[];
    for(const [ne,{r,linhas}] of porNE){
      const ugr=g(r,'UGR'); nomes[ugr]=nomes[ugr]||g(r,'UGR-Nome');
      out.push([isoDate(g(r,'Data')),ne.replace(/^\d+(\d{4}NE\d+)$/,'$1'),D.ugr.idx(ugr),D.gc.idx(g(r,'Grande Cmdo')),D.ptres.idx(g(r,'PTRES')),
        D.fonte.idx([g(r,'Fonte Recursos'),g(r,'Fonte Recursos-Nome')]),D.pi.idx([g(r,'PI'),g(r,'PI-Nome')]),D.nd.idx([g(r,'ND Detalhada'),g(r,'ND Detalhada-Nome')]),
        g(r,'Descrição'),r2(num(g(r,'Valor a NE'))),
        D.esfera.idx([g(r,'Esfera'),g(r,'Esfera-Nome')]),D.acao.idx([g(r,'Ação Governo'),g(r,'Ação Governo-Nome')]),D.po.idx([g(r,'PO'),g(r,'PO-Nome')]),
        D.forn.idx([g(r,'Fornecedor-CNPJ'),g(r,'Fornecedor-Nome'),g(r,'Fornecedor-Endereço'),g(r,'Fornecedor-Município'),g(r,'Fornecedor-UF'),g(r,'Fornecedor-CEP'),g(r,'Fornecedor-Telefone')]),
        D.amparo.idx(g(r,'Amparo Legal')),g(r,'Processo'),D.lic.idx(g(r,'Licitação')),linhas]); }
    out.sort((a,b)=>a[0]<b[0]?1:a[0]>b[0]?-1:a[1]<b[1]?1:a[1]>b[1]?-1:0);
    const ugs={}; for(const c of D.ugr.list) ugs[c]=siglas[c]||[c,nomes[c]||c];
    const dts=out.map(r=>r[0]).filter(Boolean), mx=dts.reduce((m,d)=>d>m?d:m,'');
    const dd={}; for(const k in D) dd[k]=D[k].list;
    return {ref:mx?mx.slice(8)+'/'+mx.slice(5,7)+'/'+mx.slice(0,4):'',ugs,t:dd,
      cols:['data','ne','ugr','gc','ptres','fonte','pi','nd','desc','valor','esfera','acao','po','forn','amparo','proc','lic','linhas'],rows:out};
  }
  function rp(csv){ // aba "RP Mensal Grd Cmdo": linhas = mês de lançamento, colunas = Grande Comando
    const t=table(parseCSV(csv),['Mês Lançamento','Total']), ks=Object.keys(t.cols).filter(k=>k&&k!=='Mês Lançamento'&&k!=='Total');
    const meses=[], rows=[];
    for(const r of t.data){ const m=t.get(r,'Mês Lançamento'); if(!/^[A-Za-zÀ-ú]{3}\/\d{4}$/.test(m)) continue; meses.push(m.toUpperCase()); rows.push([...ks.map(k=>r2(num(t.get(r,k)))),r2(num(t.get(r,'Total')))]); }
    return {meses,cmdos:ks,rows};
  }
  function contratos(csv){ // aba "DC - Contratos Publicados" (ASSGOV): cabeçalho na linha de 'SITUAÇÃO' / 'Nº DO CONTRATO'
    const all=parseCSV(csv), t=table(all,['SITUAÇÃO','Nº DO CONTRATO']);
    let ref=''; for(const r of all.slice(0,8)){ const i=r.indexOf('ATUALIZADO EM'); if(i>=0){ ref=String(r[i+1]||'').trim(); break; } }
    const G=['Nº DO CONTRATO','RECEITA/DESPESA','Nº DA COMPRA','MODALIDADE','PROCESSO','OBJETO','INFORMAÇÕES COMPLEMENTARES','CATEGORIA','FORNECEDOR','CNPJ/CPF'], V=['VALOR INICIAL','VALOR GLOBAL','VALOR ACUMULADO'];
    const money=v=>v===''?null:r2(num(v)), rows=[];
    for(const r of t.data){ const n=t.get(r,'Nº DO CONTRATO'); if(!n) continue;
      rows.push([...G.map(k=>t.get(r,k)),isoDate(t.get(r,'ASSINATURA')),isoDate(t.get(r,'INÍCIO DA VIGÊNCIA')),isoDate(t.get(r,'FIM DA VIGÊNCIA')),
        ...V.map(k=>money(t.get(r,k))),t.get(r,'Nº DE PARCELAS'),money(t.get(r,'VALOR DA PARCELA')),t.get(r,'UNIDADES REQUISITANTES'),t.get(r,'CONCILIAÇÃO DAS FONTES'),t.get(r,'Nº CONTROLE PNCP CONTRATO'),t.get(r,'ATUALIZAÇÃO DA FONTE')]); }
    return {ref,cols:['num','tipo','compra','modal','proc','objeto','info','cat','forn','cnpj','assin','ini','fim','vini','vglob','vacum','parc','vparc','unid','concil','pncp','fonteAtual'],rows};
  }
  function transformar(execCSV,neCSV,siglas,rpCSV,ctCSV){
    const ne=notas(parseCSV(neCSV),siglas), ex=execucao(parseCSV(execCSV),siglas);
    ex.ref=ne.ref; Object.assign(ex.ugs,ne.ugs);
    let r=null; if(rpCSV){ try{ r=rp(rpCSV); if(!r.meses.length) r=null; }catch(e){ r=null; } }
    let c=null; if(ctCSV){ try{ c=contratos(ctCSV); if(!c.rows.length) c=null; }catch(e){ c=null; } }
    return {ex,ne,rp:r,ct:c};
  }
  return {parseCSV,num,transformar,execucao,notas,rp,contratos};
})();
/*/DATALIB*/
