#!/usr/bin/env node
// Gera o "snapshot" dos dados (reserva embutida no index.html) a partir da planilha-banco.
//   node tools/gerar_snapshot.mjs --fetch [--bump]        baixa os CSV públicos da planilha
//   node tools/gerar_snapshot.mjs exec.csv ne.csv [--bump]  usa CSV locais
// A lógica de transformação é a MESMA do site (bloco /*DATALIB*/ do index.html, espelhado em tools/dados.lib.js).
import fs from 'node:fs'; import vm from 'node:vm'; import path from 'node:path'; import { fileURLToPath } from 'node:url';
const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ID = '19Za-0_spkX6aiCL0e8h-pTljgTLzwSAb8GwBmXxEy3g', GID = { exec: 1963592069, ne: 892020825 };
const args = process.argv.slice(2), bump = args.includes('--bump'), pos = args.filter(a => !a.startsWith('--'));
const htmlPath = path.join(raiz, 'index.html');
let html = fs.readFileSync(htmlPath, 'utf8');
const lib = /\/\*DATALIB\*\/[\s\S]*?\/\*\/DATALIB\*\//.exec(html)[0];
const CAEData = vm.runInNewContext(lib + ';CAEData');
const siglas = JSON.parse(fs.readFileSync(path.join(raiz, 'tools/siglas.json'), 'utf8'));
async function baixar(gid) {
  const r = await fetch(`https://docs.google.com/spreadsheets/d/${ID}/export?format=csv&gid=${gid}`);
  const t = await r.text();
  if (!r.ok || t.trimStart().startsWith('<')) throw new Error('Planilha não está pública ou indisponível (HTTP ' + r.status + ')');
  return t;
}
const execCSV = args.includes('--fetch') ? await baixar(GID.exec) : fs.readFileSync(pos[0], 'utf8');
const neCSV = args.includes('--fetch') ? await baixar(GID.ne) : fs.readFileSync(pos[1], 'utf8');
const { ex, ne } = CAEData.transformar(execCSV, neCSV, siglas); ex.siglas = siglas;
if (ne.rows.length < 1000 || ex.rows.length < 100) throw new Error(`Leitura suspeita (${ne.rows.length} NEs, ${ex.rows.length} linhas de execução) — abortando`);
const tag = (id, o) => `<script id="${id}" type="application/json">${JSON.stringify(o)}</script>`;
const re = id => new RegExp(`<script id="${id}" type="application/json">[\\s\\S]*?</script>`);
const antes = html.match(re('execData'))?.[0] + html.match(re('neData'))?.[0];
html = html.replace(re('execData'), () => tag('execData', ex)).replace(re('neData'), () => tag('neData', ne));
const depois = html.match(re('execData'))[0] + html.match(re('neData'))[0];
if (antes === depois) { console.log('SEM_MUDANCA: dados iguais ao snapshot publicado'); process.exit(0); }
let msg = `MUDOU: ${ne.rows.length} NEs · ${ex.rows.length} linhas de execução · ref ${ne.ref}`;
if (bump) {
  const m = /<span>v(\d+)\.(\d+)\.(\d+)<\/span>/.exec(html), ant = m.slice(1, 4).join('.'), novo = `${m[1]}.${m[2]}.${+m[3] + 1}`;
  html = html.replaceAll('v' + ant, 'v' + novo);
  for (const f of ['sw.js', 'README.md']) { const p = path.join(raiz, f); if (fs.existsSync(p)) fs.writeFileSync(p, fs.readFileSync(p, 'utf8').replaceAll('v' + ant, 'v' + novo)); }
  msg += ` · versão v${ant} -> v${novo}`;
}
fs.writeFileSync(htmlPath, html);
console.log(msg);
