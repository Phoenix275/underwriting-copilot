"""dashboard.py — Underwriter dashboard v3 (modern redesign).

Adds a composite Risk Score (0-100): 50% auditable rule engine + 50% ML
(gradient boosting) probability. Threshold at 50: below = ACCEPTABLE RISK,
50 and above = HIGH RISK. A "How this score works" explainer panel documents
the formula, the bands, and the models. Dark-rail modern UI.
"""
import json, os

OUT = os.path.join(os.path.dirname(__file__), "..", "output")

TEMPLATE = r"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#F4F6F9;--card:#FFFFFF;--ink:#0E1526;--mut:#66738A;--line:#E4E8EF;--rail:#0E1526;--rail-2:#1A2336;
--ok:#0E9F6E;--ok-soft:#E3F5EE;--warn:#D97706;--warn-soft:#FBF0DD;--bad:#DC2626;--bad-soft:#FBE7E7;--acc:#3B5BDB;--acc-soft:#E8EDFB}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,system-ui,sans-serif;font-size:14px}
#app{display:flex;min-height:100vh;max-width:1400px;margin:0 auto;box-shadow:0 0 40px rgba(14,21,38,.08)}
.rail{width:300px;background:var(--rail);color:#fff;flex-shrink:0;display:flex;flex-direction:column}
.rail-brand{padding:22px 20px 16px;border-bottom:1px solid rgba(255,255,255,.08)}
.rail-brand h1{font-family:'Space Grotesk',sans-serif;font-size:17px;margin:0;font-weight:700;letter-spacing:.2px}
.rail-brand p{margin:6px 0 0;font-family:'JetBrains Mono',monospace;font-size:9.5px;color:#7C8AA5;letter-spacing:.8px;text-transform:uppercase}
.overview-link{margin:12px 12px 4px;padding:10px 12px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;color:#C7D0E0;display:flex;gap:8px;align-items:center}
.overview-link:hover{background:var(--rail-2)}.overview-link.active{background:var(--acc);color:#fff}
.rail-sub{padding:14px 20px 6px;font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:1px;text-transform:uppercase;color:#7C8AA5;display:flex;justify-content:space-between}
.search-box{margin:4px 12px 8px;padding:9px 12px;width:calc(100% - 24px);border:1px solid rgba(255,255,255,.12);border-radius:8px;font:13px Inter,sans-serif;background:var(--rail-2);color:#fff;outline:none}
.search-box::placeholder{color:#66738A}
.case-list{flex:1;overflow-y:auto;padding:0 12px}
.case-item{padding:10px 12px;border-radius:8px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:2px}
.case-item:hover{background:var(--rail-2)}.case-item.active{background:var(--rail-2);outline:1px solid var(--acc)}
.ci-name{font-size:13px;font-weight:600;color:#E9EDF4}.ci-id{font-family:'JetBrains Mono',monospace;font-size:9.5px;color:#7C8AA5;margin-top:2px}
.doctag{color:#8FA6E8}
.score-chip{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;padding:3px 8px;border-radius:6px;min-width:34px;text-align:center}
.sc-ok{background:rgba(14,159,110,.18);color:#4ADE9E}.sc-bad{background:rgba(220,38,38,.2);color:#F87F7F}.sc-warn{background:rgba(217,119,6,.2);color:#FBBF6E}
.pagination{display:flex;justify-content:space-between;align-items:center;padding:10px 16px;border-top:1px solid rgba(255,255,255,.08);font-family:'JetBrains Mono',monospace;font-size:10px;color:#7C8AA5}
.pagination button{font-family:inherit;font-size:11px;background:var(--rail-2);border:none;border-radius:6px;padding:5px 11px;cursor:pointer;color:#C7D0E0}
.pagination button:disabled{opacity:.35;cursor:default}
.main{flex:1;min-width:0;padding:26px 32px 48px}
.case-head{display:flex;justify-content:space-between;align-items:flex-start;gap:20px;flex-wrap:wrap}
.case-head h2{font-family:'Space Grotesk',sans-serif;font-size:26px;margin:0 0 4px;font-weight:700}
.case-meta{font-family:'JetBrains Mono',monospace;font-size:11.5px;color:var(--mut);display:flex;gap:14px;flex-wrap:wrap}
.headline-score{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 20px;display:flex;align-items:center;gap:16px;box-shadow:0 1px 2px rgba(14,21,38,.05)}
.hs-num{font-family:'Space Grotesk',sans-serif;font-size:34px;font-weight:700;line-height:1}
.hs-lab{font-size:11px;color:var(--mut)}.hs-class{font-size:12px;font-weight:700;padding:5px 12px;border-radius:99px}
.cls-ok{background:var(--ok-soft);color:var(--ok)}.cls-bad{background:var(--bad-soft);color:var(--bad)}.cls-warn{background:var(--warn-soft);color:var(--warn)}
.tabs{display:flex;gap:6px;margin:22px 0 18px;flex-wrap:wrap}
.tab{font-size:12.5px;font-weight:600;padding:8px 14px;cursor:pointer;color:var(--mut);border-radius:99px;border:1px solid transparent}
.tab:hover{background:var(--card)}.tab.active{background:var(--card);color:var(--ink);border-color:var(--line);box-shadow:0 1px 2px rgba(14,21,38,.05)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;box-shadow:0 1px 2px rgba(14,21,38,.05);margin-bottom:16px}
.card h3{font-family:'Space Grotesk',sans-serif;font-size:13px;margin:0 0 14px;text-transform:uppercase;letter-spacing:.8px;color:var(--mut);font-weight:600}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:2px 34px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.field{border-bottom:1px solid var(--line);padding:10px 0}.field:last-child,.grid2 .field:nth-last-child(2){border-bottom:none}
.field label{display:block;font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:.8px;text-transform:uppercase;color:var(--mut);margin-bottom:3px}
.field .val{font-size:14px;font-weight:500}.mono{font-family:'JetBrains Mono',monospace}
.stat{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;box-shadow:0 1px 2px rgba(14,21,38,.05)}
.stat .sv{font-family:'Space Grotesk',sans-serif;font-size:30px;font-weight:700}.stat .sl{font-size:11px;color:var(--mut);margin-top:3px;line-height:1.4}
.doc-row{display:flex;align-items:center;gap:12px;padding:13px 16px;background:var(--bg);border:1px solid var(--line);border-radius:10px;margin-bottom:10px}
.doc-row .dot{width:9px;height:9px;border-radius:50%;background:var(--ok);flex-shrink:0}.doc-row .dot.miss{background:var(--mut)}
.dname{font-size:13.5px;font-weight:600;flex:1}.dstatus{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:var(--ok)}
table.xt{width:100%;border-collapse:collapse}
table.xt th{text-align:left;font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:.6px;text-transform:uppercase;color:var(--mut);border-bottom:1px solid var(--line);padding:6px 10px 8px 0}
table.xt td{padding:10px 10px 10px 0;border-bottom:1px solid var(--line);font-size:13px}
.conflict-card{border-left:4px solid var(--bad);background:var(--bad-soft);border-radius:0 10px 10px 0;padding:12px 16px;margin:10px 0}
.conflict-card.minor{border-left-color:var(--warn);background:var(--warn-soft)}
.conflict-card b{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.5px}
.conflict-card p{margin:5px 0 0;font-size:12.5px}
.gauge-wrap{display:flex;gap:28px;align-items:center;flex-wrap:wrap}
.gauge{width:230px}.gauge-info{flex:1;min-width:240px}
.g-num{font-family:'Space Grotesk',sans-serif;font-size:42px;font-weight:700}
.g-band{font-size:13px;font-weight:700;padding:6px 14px;border-radius:99px;display:inline-block;margin:6px 0 10px}
.g-note{font-size:12.5px;color:var(--mut);line-height:1.6}
.sub-scores{display:flex;gap:14px;margin-top:18px;flex-wrap:wrap}
.sub-score{flex:1;min-width:170px;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:13px 15px}
.ss-l{font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:.7px;text-transform:uppercase;color:var(--mut)}
.ss-v{font-family:'Space Grotesk',sans-serif;font-size:23px;font-weight:700;margin:3px 0 6px}
.bar-track{height:6px;background:var(--line);border-radius:4px;overflow:hidden}.bar-fill{height:100%;border-radius:4px}
.factor-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--line);gap:16px}
.factor-row:last-child{border-bottom:none}
.factor-label{font-size:13px;font-weight:500}.factor-detail{font-family:'JetBrains Mono',monospace;font-size:10.5px;color:var(--mut);margin-top:2px}
.factor-pts{font-family:'JetBrains Mono',monospace;font-size:13px;font-weight:600;min-width:44px;text-align:right}
.explain{background:linear-gradient(135deg,var(--acc-soft),#F4F0FB);border:1px solid #D6DEF5}
.explain p{font-size:13px;line-height:1.7;margin:0 0 10px;color:#26324D}
.explain .bands{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.band-chip{font-family:'JetBrains Mono',monospace;font-size:10.5px;font-weight:600;padding:5px 10px;border-radius:6px}
.stamp{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:16px;letter-spacing:1.2px;border:2.5px solid;padding:12px 20px;border-radius:10px;display:inline-block;text-transform:uppercase}
.stamp.ok{color:var(--ok);border-color:var(--ok);background:var(--ok-soft)}.stamp.warn{color:var(--warn);border-color:var(--warn);background:var(--warn-soft)}.stamp.bad{color:var(--bad);border-color:var(--bad);background:var(--bad-soft)}
.decision-wrap{display:flex;gap:26px;align-items:flex-start;flex-wrap:wrap}
.decision-detail h3{font-family:'Space Grotesk',sans-serif;font-size:16px;margin:0 0 8px;text-transform:none;letter-spacing:0;color:var(--ink)}
.decision-detail p{font-size:13px;color:var(--mut);margin:0 0 5px;line-height:1.55}
.ai-btn{font-family:Inter,sans-serif;font-size:12.5px;font-weight:600;background:var(--ink);color:#fff;border:none;padding:9px 16px;border-radius:8px;cursor:pointer}
.ai-btn:disabled{opacity:.5}.ai-text{font-size:14px;line-height:1.7}.ai-empty{font-size:13px;color:var(--mut);font-style:italic}
.ai-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.hist-bar-row{display:flex;align-items:center;gap:12px;margin:9px 0}.hist-label{width:120px;font-size:12px;font-weight:600}
.hist-track{flex:1;height:18px;background:var(--bg);border-radius:6px;overflow:hidden}.hist-fill{height:100%;border-radius:6px}
.hist-count{width:60px;text-align:right;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--mut)}
.coef-bar-row{display:flex;align-items:center;gap:12px;margin:8px 0}.coef-label{width:180px;font-size:12.5px;font-weight:500}
.coef-track{flex:1;height:12px;background:var(--bg);border-radius:6px;position:relative}.coef-fill{position:absolute;top:0;bottom:0;border-radius:6px;background:var(--acc)}
.coef-val{width:56px;font-family:'JetBrains Mono',monospace;font-size:11px;text-align:right;color:var(--mut)}
.note{font-size:12px;color:var(--mut);line-height:1.65;margin-top:12px}
.unique-banner{border-left:4px solid var(--warn);background:var(--warn-soft);border-radius:0 10px 10px 0;padding:12px 16px;margin:12px 0;font-size:13px}
.unique-banner b{font-family:'JetBrains Mono',monospace;font-size:10.5px;letter-spacing:.6px}
.verdict-banner{border-radius:14px;padding:22px 26px;margin-bottom:16px;border:2px solid}
.verdict-banner.v-green{background:var(--ok-soft);border-color:var(--ok)}
.verdict-banner.v-yellow{background:var(--warn-soft);border-color:var(--warn)}
.verdict-banner.v-red{background:var(--bad-soft);border-color:var(--bad)}
.verdict-banner .vb-word{font-family:'Space Grotesk',sans-serif;font-size:26px;font-weight:700;letter-spacing:1px}
.v-green .vb-word{color:var(--ok)}.v-yellow .vb-word{color:var(--warn)}.v-red .vb-word{color:var(--bad)}
.verdict-banner .vb-sub{font-size:13px;color:var(--ink);margin-top:6px;line-height:1.55}
.form-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px 16px}
.form-grid label{display:block;font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:.8px;text-transform:uppercase;color:var(--mut);margin-bottom:4px}
.form-grid input,.form-grid select,.fg-wide textarea{width:100%;padding:9px 11px;border:1px solid var(--line);border-radius:8px;font:13px Inter,sans-serif;background:var(--bg);color:var(--ink);outline:none}
.form-grid input:focus,.form-grid select:focus,.fg-wide textarea:focus{border-color:var(--acc)}
.fg-wide{grid-column:1/-1}
.drop-zone{border:2px dashed var(--line);border-radius:12px;padding:26px;text-align:center;cursor:pointer;color:var(--mut);font-size:13.5px;margin-bottom:16px}
.drop-zone:hover{border-color:var(--acc);color:var(--acc)}
.drop-zone.loaded{border-color:var(--ok);color:var(--ok);border-style:solid}
.score-btn{font-family:Inter,sans-serif;font-size:14px;font-weight:700;background:var(--acc);color:#fff;border:none;padding:12px 26px;border-radius:10px;cursor:pointer;margin-top:16px}
.legend-row{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}
.legend-chip{display:flex;align-items:center;gap:8px;font-size:12.5px;font-weight:600;padding:8px 14px;border-radius:10px}
.legend-chip .swatch{width:12px;height:12px;border-radius:50%}
@media(max-width:900px){#app{flex-direction:column}.rail{width:100%}.grid2,.grid3,.form-grid{grid-template-columns:1fr}.main{padding:20px}}
</style>
<div id="app">
 <div class="rail">
  <div class="rail-brand"><h1>Underwriting Copilot</h1><p>Extraction · Conflict Screen · Risk Score · Decision</p></div>
  <div class="overview-link" id="overviewLink" onclick="goOverview()">⌂ &nbsp;Portfolio & Model Card</div>
  <div class="overview-link" id="scoreLink" onclick="goScore()">＋ &nbsp;Score New Application</div>
  <div class="rail-sub"><span>Case Queue</span><span id="queueCount"></span></div>
  <input class="search-box" id="searchBox" placeholder="Search name or ID…" oninput="onSearch(this.value)">
  <div class="case-list" id="caseList"></div>
  <div class="pagination"><button id="prevBtn" onclick="pg(-1)">‹ Prev</button><span id="pageLabel"></span><button id="nextBtn" onclick="pg(1)">Next ›</button></div>
 </div>
 <div class="main"><div id="mainContent"></div></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
const DATA = /*__DATA__*/;
const M = DATA.metrics, CASES = DATA.cases;
const A_LINE = 40, D_LINE = 70;  // <40 approve · 40–69 manual review · ≥70 decline
const VM={green:["APPROVE","ok"],yellow:["MANUAL REVIEW","warn"],red:["DECLINE","bad"]};
const bandOf=s=>s<A_LINE?"green":s<D_LINE?"yellow":"red";
const band=s=>s<=25?["Low","var(--ok)"]:s<A_LINE?["Moderate","var(--ok)"]:s<D_LINE?["Elevated","var(--warn)"]:["High","var(--bad)"];
let filtered=CASES.slice(),page=0,activeId=CASES[0].id,view="case",activeTab=4;const PAGE=20;
const fmt$=n=>n==null?"—":"$"+Math.round(n).toLocaleString();
function onSearch(q){q=q.trim().toLowerCase();filtered=q?CASES.filter(c=>c.name.toLowerCase().includes(q)||c.id.toLowerCase().includes(q)):CASES.slice();page=0;rail();}
function pg(d){const mx=Math.max(0,Math.ceil(filtered.length/PAGE)-1);page=Math.min(mx,Math.max(0,page+d));rail();}
function goOverview(){view="overview";render();}
function goScore(){view="score";render();}
function sel(id){activeId=id;view="case";activeTab=4;render();}
function selTab(n){activeTab=n;render();}
function render(){rail();main();}
function rail(){
 document.getElementById('overviewLink').className="overview-link"+(view==="overview"?" active":"");
 document.getElementById('scoreLink').className="overview-link"+(view==="score"?" active":"");
 document.getElementById('queueCount').textContent=filtered.length+" cases";
 const items=filtered.slice(page*PAGE,page*PAGE+PAGE);
 document.getElementById('caseList').innerHTML=items.map(c=>{
  const sc=c.verdict==='red'?'sc-bad':c.verdict==='yellow'?'sc-warn':'sc-ok';
  return `<div class="case-item ${c.id===activeId&&view==='case'?'active':''}" onclick="sel('${c.id}')">
   <div><div class="ci-name">${c.name}</div><div class="ci-id">${c.id}${c.has_docs?' <span class="doctag">· PDF</span>':''}</div></div>
   <div class="score-chip ${sc}">${c.risk_score}</div></div>`;}).join('');
 const mx=Math.max(0,Math.ceil(filtered.length/PAGE)-1);
 document.getElementById('pageLabel').textContent=(page+1)+" / "+(mx+1);
 document.getElementById('prevBtn').disabled=page<=0;document.getElementById('nextBtn').disabled=page>=mx;
}
function main(){
 const el=document.getElementById('mainContent');
 if(view==="overview"){el.innerHTML=overview();return;}
 if(view==="score"){el.innerHTML=scoreView();wireScoreForm();return;}
 const c=CASES.find(x=>x.id===activeId);if(!c){el.innerHTML=overview();return;}
 const vm=VM[c.verdict];
 el.innerHTML=`<div class="case-head">
   <div><h2>${c.name}</h2>
    <div class="case-meta"><span>${c.id}</span><span>${c.occupation}</span><span>${c.city}, ${c.state}</span><span>${c.policy}</span></div></div>
   <div class="headline-score">
    <div><div class="hs-num" style="color:var(--${vm[1]})">${c.risk_score}<span style="font-size:16px;color:var(--mut)">/100</span></div>
     <div class="hs-lab">Composite Risk Score</div></div>
    <div class="hs-class cls-${vm[1]}">${vm[0]}</div></div></div>
  <div class="tabs">${[[1,'Application'],[2,'Documents'],[3,'Extraction & Conflicts'],[4,'Risk Score'],[5,'Decision']]
   .map(t=>`<div class="tab ${t[0]===activeTab?'active':''}" onclick="selTab(${t[0]})">${t[1]}</div>`).join('')}</div>
  ${panel(c)}`;
}
function gauge(score){
 const L=251.33, off=L*(1-score/100);
 const col='var(--'+VM[bandOf(score)][1]+')';
 const tick=v=>{const a=Math.PI*(1-v/100);return `<line x1="${100+86*Math.cos(a)}" y1="${100-86*Math.sin(a)}" x2="${100+72*Math.cos(a)}" y2="${100-72*Math.sin(a)}" stroke="var(--ink)" stroke-width="2.5" stroke-dasharray="3 3"/>`;};
 return `<svg class="gauge" viewBox="0 0 200 112">
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="var(--line)" stroke-width="15" stroke-linecap="round"/>
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="${col}" stroke-width="15" stroke-linecap="round"
   stroke-dasharray="${L}" stroke-dashoffset="${off}"/>
  ${tick(A_LINE)}${tick(D_LINE)}
  <text x="100" y="88" text-anchor="middle" font-family="Space Grotesk" font-size="30" font-weight="700" fill="var(--ink)">${score}</text>
  <text x="100" y="104" text-anchor="middle" font-family="Inter" font-size="9" fill="var(--mut)">approve &lt;${A_LINE} · decline ≥${D_LINE}</text></svg>`;
}
function overview(){
 const vc={green:0,yellow:0,red:0};CASES.forEach(c=>vc[c.verdict]++);
 const tc={"Low (0–25)":0,"Moderate (26–39)":0,"Elevated (40–69)":0,"High (70–100)":0};
 CASES.forEach(c=>{const s=c.risk_score;if(s<=25)tc["Low (0–25)"]++;else if(s<A_LINE)tc["Moderate (26–39)"]++;else if(s<D_LINE)tc["Elevated (40–69)"]++;else tc["High (70–100)"]++;});
 const mx=Math.max(...Object.values(tc),1);const cols=["var(--ok)","var(--ok)","var(--warn)","var(--bad)"];
 const gb=M.risk_models.gradient_boosting,lr=M.risk_models.logistic_regression;
 const fi=M.risk_models.gb_feature_importance;const mxf=Math.max(...Object.values(fi));
 return `<div class="case-head"><div><h2>Portfolio & Model Card</h2>
  <div class="case-meta"><span>${M.n_applicants.toLocaleString()} applicants scored</span><span>${M.n_packets} PDF packets</span></div></div></div>
 <div class="card" style="margin-top:18px"><h3>Verdicts — Traffic-Light Decisioning</h3>
  <div class="legend-row">
   <div class="legend-chip cls-ok"><span class="swatch" style="background:var(--ok)"></span>APPROVE · ${vc.green} — clear-cut acceptable risk, auto-approved</div>
   <div class="legend-chip cls-warn"><span class="swatch" style="background:var(--warn)"></span>MANUAL REVIEW · ${vc.yellow} — a human underwriter looks at the person as a whole</div>
   <div class="legend-chip cls-bad"><span class="swatch" style="background:var(--bad)"></span>DECLINE · ${vc.red} — application contradicts evidence or risk exceeds appetite</div>
  </div></div>
 <div class="grid3">
  <div class="stat"><div class="sv">${(M.extraction.field_level_accuracy*100).toFixed(1)}%</div><div class="sl">Extraction accuracy — field level vs ground truth</div></div>
  <div class="stat"><div class="sv">${(M.conflict_screening.detection_recall*100).toFixed(0)}%</div><div class="sl">Injected-conflict detection recall (${M.conflict_screening.tp}/${M.conflict_screening.tp+M.conflict_screening.fn} caught, ${M.conflict_screening.fp} false alarms)</div></div>
  <div class="stat"><div class="sv">${(gb.auc*100).toFixed(1)}%</div><div class="sl">Gradient Boosting AUC on ${M.risk_models.n_test.toLocaleString()} held-out records</div></div>
  <div class="stat"><div class="sv">${(lr.auc*100).toFixed(1)}%</div><div class="sl">Logistic Regression AUC (auditable baseline)</div></div>
  <div class="stat"><div class="sv">${(M.decisioning.straight_through_rate*100).toFixed(1)}%</div><div class="sl">Straight-through rate — decided with no human touch</div></div>
  <div class="stat"><div class="sv">${M.risk_models.n_train.toLocaleString()}</div><div class="sl">Training records (test: ${M.risk_models.n_test.toLocaleString()}, base risk rate ${(M.risk_models.positive_rate*100).toFixed(0)}%)</div></div>
 </div>
 <div class="card" style="margin-top:16px"><h3>Composite Risk Score Distribution</h3>
  ${Object.entries(tc).map(([t,n],i)=>`<div class="hist-bar-row"><div class="hist-label">${t}</div>
   <div class="hist-track"><div class="hist-fill" style="width:${n/mx*100}%;background:${cols[i]}"></div></div><div class="hist-count">${n}</div></div>`).join('')}
  <div class="note">Below ${A_LINE} with clean signals → green auto-approve. ${A_LINE}–${D_LINE-1}, any major conflict, model disagreement, or disclosed unique circumstances → yellow manual review. At or above ${D_LINE}, or material misrepresentation → red decline.</div></div>
 <div class="card"><h3>Gradient Boosting — Feature Importance</h3>
  ${Object.entries(fi).sort((a,b)=>b[1]-a[1]).map(([f,v])=>`<div class="coef-bar-row"><div class="coef-label">${f}</div>
   <div class="coef-track"><div class="coef-fill" style="left:0;width:${v/mxf*100}%"></div></div><div class="coef-val">${v.toFixed(3)}</div></div>`).join('')}
  <div class="note">Extraction accuracy is measured on machine-generated text PDFs; on scanned documents it will drop — that is the gap Google Document AI closes in the GCP deployment. Because the data is synthetic with a known ground-truth label, every number above is verifiable, and model performance represents an upper bound rather than a production guarantee.</div></div>`;
}
function panel(c){
 if(activeTab===1){
  const sec=(title,fields)=>`<div class="card"><h3>${title}</h3><div class="grid2">
   ${fields.map(f=>`<div class="field"><label>${f[0]}</label><div class="val">${f[1]}</div></div>`).join('')}</div></div>`;
  return sec("Section 1 — Applicant Information",[
    ["Full Name",c.name],["Date of Birth",c.dob+" (age "+c.age+")"],
    ["Occupation",c.occupation],["Employer",c.employer],
    ["Employment Status",c.emp_status||"—"],["Years Employed",(c.years_emp!=null?c.years_emp+" years":"—")],
    ["Location",c.city+", "+c.state],["Policy Requested",c.policy]])
  +sec("Section 2 — Financial Declaration",[
    ["Declared Annual Income",fmt$(c.income)],["Coverage Requested",fmt$(c.coverage)],
    ["Monthly Expenses",fmt$(c.expenses)],["Existing Debt",fmt$(c.debt)],
    ["Avg Bank Balance",fmt$(c.bank)],["Credit Score",c.credit],
    ["Debt-to-Income Ratio",(c.dti*100).toFixed(1)+"%"],["Coverage-to-Income Multiple",(c.coverage/c.income).toFixed(1)+"×"]])
  +sec("Section 3 — Medical & Lifestyle Profile",[
    ["Height / Weight",c.height+" cm / "+c.weight+" kg"],["BMI",c.bmi],
    ["Tobacco Use (4a)",c.smoker],["Chronic Conditions (4b)",c.conditions],
    ["Family History (4c)",c.family?"Yes — parent, see attending records":"None disclosed"],["Hazardous Activities (4d)",c.hazard&&c.hazard!=="None"?"Yes — "+c.hazard:"No"],
    ["Driving Violations, 3yr (4e)",c.violations!=null?c.violations:"—"],["Alcohol Use (4f)",c.alcohol||"—"],
    ["Blood Pressure",c.bp],["Total Cholesterol",c.chol+" mg/dL"]])
  +(c.unique?`<div class="unique-banner"><b>UNIQUE CIRCUMSTANCES DISCLOSED (Q5)</b><p style="margin:5px 0 0">“${c.unique}” — this disclosure automatically routes the file to a human underwriter so the person is assessed as a whole, not just by the score.</p></div>`:'');
 }
 if(activeTab===2){
  const docs=c.has_docs?[["Application Form (Parts A–B, health questionnaire)","Parsed ✓"],["Payslip / Earnings Statement","Parsed ✓"],["Paramedical Exam Report + consumer report","Parsed ✓"]]
   :[["Application Form","Not in packet sample"],["Payslip / Earnings Statement","Not in packet sample"],["Paramedical Exam Report","Not in packet sample"]];
  return `<div class="card"><h3>Document Packet</h3>`+docs.map(d=>`<div class="doc-row"><div class="dot ${c.has_docs?'':'miss'}"></div><div class="dname">${d[0]}</div><div class="dstatus">${d[1]}</div></div>`).join('')
   +(c.has_docs?'':'<div class="note">This applicant is in the scored portfolio but outside the PDF-packet sample; scores are computed from structured data. In production, every case flows through document extraction.</div>')+`</div>`;
 }
 if(activeTab===3){
  if(!c.has_docs)return '<div class="card"><div class="note">No PDF packet for this applicant in the sample — open a case tagged · PDF in the queue for the full extraction view.</div></div>';
  const e=c.extraction;
  const rows=[["Name (form)",e.name],["DOB (form)",e.form_dob],["DOB (paramed / ID)",e.paramed_dob],
   ["Declared income (form)",fmt$(e.form_income)],["Income (payslip, annualized)",fmt$(e.payslip_income)],
   ["Declared debt (form)",fmt$(e.form_debt)],["Debt (credit bureau)",fmt$(e.bureau_debt)],
   ["Tobacco (form 4a)",e.form_tobacco_yes?"YES":"NO"],["Cotinine (lab)",e.cotinine],
   ["Height / Weight",e.height_cm+" cm / "+e.weight_kg+" kg"],["Blood pressure",e.blood_pressure],["Cholesterol",e.cholesterol+" mg/dL"]];
  const confl=c.conflicts.length?c.conflicts.map(k=>`<div class="conflict-card ${k.severity==='minor'?'minor':''}">
   <b>${k.severity.toUpperCase()} · ${k.type.replace(/_/g,' ').toUpperCase()}</b><p>${k.description}</p></div>`).join('')
   :'<div class="note">No cross-document conflicts detected. All four checks passed — every applicant runs through the identical checklist.</div>';
  return `<div class="card"><h3>Extracted Fields (3 documents)</h3><table class="xt"><tr><th>Field</th><th>Value</th></tr>
   ${rows.map(r=>`<tr><td>${r[0]}</td><td class="mono">${r[1]??'—'}</td></tr>`).join('')}</table></div>
   <div class="card"><h3>Cross-Document Conflict Screen</h3>${confl}</div>`;
 }
 if(activeTab===4){
  const vm=VM[c.verdict];const b=band(c.risk_score);
  const sub=(l,v,col)=>`<div class="sub-score"><div class="ss-l">${l}</div><div class="ss-v">${v}</div>
   <div class="bar-track"><div class="bar-fill" style="width:${v}%;background:${col}"></div></div></div>`;
  return `<div class="card"><h3>Composite Risk Score</h3>
   <div class="gauge-wrap">${gauge(c.risk_score)}
    <div class="gauge-info">
     <div class="g-band cls-${vm[1]}">${vm[0]} · ${b[0]} band</div>
     <div class="g-note">${c.verdict==='red'
       ?`This case is in the red band — either the score is at or above the ${D_LINE}-point decline line, or the application materially contradicts the evidence.`
       :c.verdict==='yellow'
       ?`This case is yellow — a human underwriter must review the application and the person as a whole before any decision is issued.`
       :`This case is green — it scores below the ${A_LINE}-point approval line with clean signals and is eligible for straight-through approval.`}</div>
     <div class="sub-scores">
      ${sub("Rule engine (50%)",c.rule_score,"var(--acc)")}
      ${sub("ML — gradient boosting (50%)",Math.round(c.ml_score),"var(--acc)")}
      ${sub("ML — logistic (reference)",Math.round(c.ml_score_lr),"var(--mut)")}
     </div></div></div></div>
  <div class="card explain"><h3>How this score works</h3>
   <p><b>Formula:</b> Risk Score = 50% × Rule Engine score + 50% × ML probability. The rule engine is fully auditable — every point traces to a documented factor weight below. The ML component is a gradient-boosting model trained on ${M.risk_models.n_train.toLocaleString()} records (AUC ${(M.risk_models.gradient_boosting.auc*100).toFixed(1)}% on ${M.risk_models.n_test.toLocaleString()} held-out cases), which captures factor interactions the rules miss. Blending them means one bad model can never single-handedly approve a risky case.</p>
   <p><b>The traffic light:</b> below ${A_LINE} with clean signals the case is <b style="color:var(--ok)">GREEN — APPROVE</b>, clear-cut and auto-approved. From ${A_LINE} to ${D_LINE-1}, or whenever there is a major data conflict, model disagreement, or the applicant disclosed unique circumstances, the case is <b style="color:var(--warn)">YELLOW — MANUAL REVIEW</b>: a human underwriter must look at the application and the person as a whole. At ${D_LINE} or above, or when the application materially contradicts the medical/identity evidence, the case is <b style="color:var(--bad)">RED — DECLINE</b>.</p>
   <div class="bands">
    <span class="band-chip" style="background:var(--ok-soft);color:var(--ok)">0–${A_LINE-1} Approve</span>
    <span class="band-chip" style="background:var(--warn-soft);color:var(--warn)">${A_LINE}–${D_LINE-1} Manual Review</span>
    <span class="band-chip" style="background:var(--bad-soft);color:var(--bad)">${D_LINE}–100 Decline</span>
   </div></div>
  <div class="card"><h3>Rule Engine — Factor Breakdown</h3>
   ${c.rule_factors.map(f=>`<div class="factor-row"><div><div class="factor-label">${f[0]}</div><div class="factor-detail">${f[1]}</div></div>
    <div class="factor-pts">${f[2]>0?'+':''}${f[2]}</div></div>`).join('')}
   ${c.label!=null?`<div class="note">Ground-truth label: <b>${c.label==1?'High Risk':'Not High Risk'}</b> — synthetic data lets every score be verified against a known answer.</div>`:''}</div>`;
 }
 if(activeTab===5){
  const cls=VM[c.verdict][1];
  return `<div class="card"><h3>System Decision</h3><div class="decision-wrap">
   <div class="stamp ${cls}">${c.decision}</div>
   <div class="decision-detail"><h3>${c.rate_class}</h3>
    ${c.reasons.map(r=>`<p>· ${r}</p>`).join('')}
    <p class="mono" style="font-size:11px">Risk ${c.risk_score}/100 · Rule ${c.rule_score} · GB ${c.ml_score.toFixed(0)} · ${c.conflicts.length} conflict(s)</p></div></div>
   ${c.unique?`<div class="unique-banner"><b>UNIQUE CIRCUMSTANCES</b><p style="margin:5px 0 0">“${c.unique}”</p></div>`:''}</div>
  <div class="card"><div class="ai-head"><h3 style="margin:0">Underwriting Summary — grounded in extracted fields only</h3></div>
   <div class="ai-text">${c.ai_summary}</div></div>`;
 }
}

/* ---------- live scoring: same rule engine + trained logistic model, in-browser ---------- */
function ruleScoreJS(f){
 const factors=[];
 let p=f.age<30?0:f.age<=45?5:f.age<=55?10:18;factors.push(["Applicant age",f.age+" years",p]);
 p=f.smoker==="Smoker"?25:f.smoker==="Former smoker"?8:0;factors.push(["Tobacco use",f.smoker,p]);
 p=(f.bmi<18.5||f.bmi>=35)?15:f.bmi>=30?8:f.bmi>=25?3:0;factors.push(["Body mass index",f.bmi.toFixed(1)+" BMI",p]);
 const conds=f.conditions.trim()&&f.conditions.trim().toLowerCase()!=="none"?f.conditions.split(",").map(s=>s.trim()).filter(Boolean):[];
 p=conds.reduce((s,c)=>s+(c.toLowerCase().includes("diabetes")?15:8),0);factors.push(["Medical conditions",conds.join(", ")||"None",p]);
 p=f.family?6:0;factors.push(["Family medical history",f.family?"Notable":"None disclosed",p]);
 const dti=f.income>0?f.debt/f.income:0;
 p=dti<0.2?0:dti<0.35?5:dti<0.5?12:20;factors.push(["Debt-to-income ratio",(dti*100).toFixed(1)+"%",p]);
 p=f.credit>750?0:f.credit>=700?3:f.credit>=650?8:15;factors.push(["Credit score",String(f.credit),p]);
 p=f.hazard?10:0;factors.push(["Hazardous activities",f.hazard?(f.hazardDetail||"Yes"):"None disclosed",p]);
 p=f.violations===0?0:f.violations<=2?4:10;factors.push(["Driving record",f.violations+" violation(s) in 3 years",p]);
 p=f.alcohol==="Heavy"?12:f.alcohol==="Moderate"?2:0;factors.push(["Alcohol use",f.alcohol,p]);
 return [Math.min(factors.reduce((s,x)=>s+x[2],0),100),factors];
}
function mlScoreJS(f){
 const ex=M.risk_models.lr_export;
 const conds=f.conditions.trim()&&f.conditions.trim().toLowerCase()!=="none"?f.conditions.split(",").filter(s=>s.trim()).length:0;
 const dti=Math.min(Math.max(f.income>0?f.debt/f.income:0,0),3);
 const x={Age:f.age,BMI:f.bmi,smoker_now:f.smoker==="Smoker"?1:0,smoker_former:f.smoker==="Former smoker"?1:0,
  n_conditions:conds,"Family History Flag":f.family?1:0,"Debt-to-Income Ratio":dti,"Credit Score":f.credit,
  hazardous_activity:f.hazard?1:0,driving_violations:f.violations,alcohol_heavy:f.alcohol==="Heavy"?1:0};
 let z=ex.intercept;
 ex.features.forEach((name,i)=>{z+=ex.coef[i]*((x[name]-ex.scaler_mean[i])/ex.scaler_std[i]);});
 return 100/(1+Math.exp(-z));
}
function decideJS(rule,ml,unique){
 const comp=Math.round(0.5*rule+0.5*ml);const reasons=[];
 let verdict,decision,rate;
 if(comp>=D_LINE){verdict="red";decision="DECLINE";rate="Declined — Risk Exceeds Appetite";
  reasons.push(`Composite risk score ${comp}/100 is in the ${D_LINE}+ decline band`);}
 else if(unique||comp>=A_LINE||Math.abs(rule-ml)>20){verdict="yellow";decision="MANUAL REVIEW";
  rate=unique?"Referred — Unique Circumstances Disclosed":"Referred — Senior Underwriter Review";
  if(unique)reasons.push("Applicant disclosed unique circumstances: "+unique);
  if(comp>=A_LINE)reasons.push(`Composite score ${comp} sits in the ${A_LINE}–${D_LINE-1} referral band`);
  if(Math.abs(rule-ml)>20)reasons.push(`Rule engine (${rule}) and ML model (${ml.toFixed(0)}) disagree materially`);}
 else{verdict="green";decision="APPROVE";rate=comp<=25?"Preferred Rate Class":"Standard Rate Class";
  reasons.push(`Composite score ${comp} is below the ${A_LINE}-point approval line; engines agree and no special circumstances were disclosed`);}
 return {verdict,decision,rate,comp,reasons};
}
function scoreView(){
 return `<div class="case-head"><div><h2>Score a New Application</h2>
  <div class="case-meta"><span>Upload an application PDF or key the fields in</span><span>scored live with the same engines as the portfolio</span></div></div></div>
 <div class="card" style="margin-top:18px"><h3>1 · Application PDF (optional)</h3>
  <div class="drop-zone" id="dropZone" onclick="document.getElementById('pdfInput').click()">Click to upload an application form PDF — name, DOB, income, debt and coverage are extracted automatically</div>
  <input type="file" id="pdfInput" accept="application/pdf" style="display:none">
 </div>
 <div class="card"><h3>2 · Applicant Inputs — confirm or complete</h3>
  <div class="form-grid">
   <div><label>Full name</label><input id="f_name" placeholder="Jane Doe"></div>
   <div><label>Age</label><input id="f_age" type="number" min="18" max="85" value="40"></div>
   <div><label>Credit score</label><input id="f_credit" type="number" min="300" max="850" value="715"></div>
   <div><label>Annual income (USD)</label><input id="f_income" type="number" value="60000"></div>
   <div><label>Total debt (USD)</label><input id="f_debt" type="number" value="20000"></div>
   <div><label>Coverage requested (USD)</label><input id="f_coverage" type="number" value="300000"></div>
   <div><label>BMI</label><input id="f_bmi" type="number" step="0.1" value="25"></div>
   <div><label>Tobacco use</label><select id="f_smoker"><option>Non-smoker</option><option>Former smoker</option><option>Smoker</option></select></div>
   <div><label>Alcohol use</label><select id="f_alcohol"><option>None</option><option selected>Moderate</option><option>Heavy</option></select></div>
   <div><label>Existing conditions (comma-separated)</label><input id="f_conditions" placeholder="None"></div>
   <div><label>Family history of serious illness</label><select id="f_family"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div><label>Driving violations (3 yr)</label><input id="f_violations" type="number" min="0" max="10" value="0"></div>
   <div><label>Hazardous activities</label><select id="f_hazard" onchange="document.getElementById('hazardWrap').style.display=this.value==='1'?'block':'none'"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div class="fg-wide" id="hazardWrap" style="display:none"><label>If yes, describe the activity</label><input id="f_hazard_detail" placeholder="e.g. Skydiving, scuba diving, motorcycle racing"></div>
   <div><label>Unique circumstances to disclose?</label><select id="f_unique" onchange="document.getElementById('uniqueWrap').style.display=this.value==='1'?'block':'none'"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div class="fg-wide" id="uniqueWrap" style="display:none"><label>Tell us — a human underwriter will read this</label><textarea id="f_unique_text" rows="2" placeholder="e.g. Recent job change, caregiving gap, rebuilt finances after bankruptcy…"></textarea></div>
  </div>
  <button class="score-btn" onclick="scoreNow()">Score Application</button></div>
 <div id="scoreResult"></div>`;
}
function wireScoreForm(){
 const inp=document.getElementById('pdfInput');if(!inp)return;
 inp.addEventListener('change',async ev=>{
  const file=ev.target.files[0];if(!file)return;
  const dz=document.getElementById('dropZone');dz.textContent='Reading '+file.name+'…';
  try{
   if(typeof pdfjsLib==='undefined')throw new Error('pdf.js unavailable (offline?)');
   pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
   const buf=await file.arrayBuffer();
   const pdf=await pdfjsLib.getDocument({data:buf}).promise;
   let text='';
   for(let i=1;i<=pdf.numPages;i++){const pg=await pdf.getPage(i);const tc=await pg.getTextContent();
    text+=tc.items.map(it=>it.str).join('\n')+'\n';}
   const got=[];
   const grab=(label,re)=>{const m=text.match(new RegExp(label+"[\\s\\S]{0,60}?("+re+")","i"));return m?m[1]:null;};
   const name=grab("FULL NAME","[A-Z][a-zA-Z'’-]+(?:\\s+[A-Z][a-zA-Z'’-]+)+");
   if(name){document.getElementById('f_name').value=name;got.push('name');}
   const dob=grab("DATE OF BIRTH","\\d{4}-\\d{2}-\\d{2}");
   if(dob){const age=Math.floor((Date.now()-new Date(dob))/31557600000);
    if(age>0&&age<110){document.getElementById('f_age').value=age;got.push('age (from DOB '+dob+')');}}
   const inc=grab("DECLARED ANNUAL INCOME","[\\d,]{4,}");
   if(inc){document.getElementById('f_income').value=parseFloat(inc.replace(/,/g,''));got.push('income');}
   const debt=grab("DECLARED TOTAL DEBT","[\\d,]{3,}");
   if(debt){document.getElementById('f_debt').value=parseFloat(debt.replace(/,/g,''));got.push('debt');}
   const cov=grab("COVERAGE AMOUNT REQUESTED","[\\d,]{4,}");
   if(cov){document.getElementById('f_coverage').value=parseFloat(cov.replace(/,/g,''));got.push('coverage');}
   dz.className='drop-zone loaded';
   dz.textContent=got.length?('✓ '+file.name+' — extracted '+got.join(', ')+'. Confirm the remaining fields below, then score.')
    :('✓ '+file.name+' read, but no known fields matched — key the values in below.');
  }catch(err){dz.textContent='Could not read PDF ('+err.message+') — enter the fields manually below.';}
 });
}
function scoreNow(){
 const v=id=>document.getElementById(id).value;
 const f={name:v('f_name')||'New Applicant',age:+v('f_age'),credit:+v('f_credit'),income:+v('f_income'),
  debt:+v('f_debt'),coverage:+v('f_coverage'),bmi:+v('f_bmi'),smoker:v('f_smoker'),alcohol:v('f_alcohol'),
  conditions:v('f_conditions')||'None',family:+v('f_family'),violations:+v('f_violations'),
  hazard:v('f_hazard')==='1',hazardDetail:v('f_hazard_detail'),
  unique:v('f_unique')==='1'?(v('f_unique_text').trim()||'Disclosed — details pending'):null};
 const [rule,factors]=ruleScoreJS(f);
 const ml=mlScoreJS(f);
 const d=decideJS(rule,ml,f.unique);
 const esc=s=>String(s).replace(/</g,'&lt;');
 const vbSub={green:"Clear-cut acceptable risk. This applicant should be approved — every signal is clean and the score is comfortably below the approval line.",
  yellow:"A human underwriter needs to review this application and the person as a whole before a decision is issued.",
  red:"This application should be declined — the risk clearly exceeds appetite at the disclosed values."};
 document.getElementById('scoreResult').innerHTML=`
  <div class="verdict-banner v-${d.verdict}"><div class="vb-word">${d.decision} — ${esc(f.name)}</div>
   <div class="vb-sub"><b>${d.rate}.</b> ${vbSub[d.verdict]}</div></div>
  <div class="card"><h3>Live Composite Score</h3>
   <div class="gauge-wrap">${gauge(d.comp)}
    <div class="gauge-info">
     <div class="g-band cls-${VM[d.verdict][1]}">${VM[d.verdict][0]}</div>
     ${d.reasons.map(r=>`<div class="g-note">· ${esc(r)}</div>`).join('')}
     <div class="sub-scores">
      <div class="sub-score"><div class="ss-l">Rule engine (50%)</div><div class="ss-v">${rule}</div><div class="bar-track"><div class="bar-fill" style="width:${rule}%;background:var(--acc)"></div></div></div>
      <div class="sub-score"><div class="ss-l">ML — logistic (50%)</div><div class="ss-v">${ml.toFixed(0)}</div><div class="bar-track"><div class="bar-fill" style="width:${ml}%;background:var(--acc)"></div></div></div>
     </div></div></div></div>
  ${f.unique?`<div class="unique-banner"><b>UNIQUE CIRCUMSTANCES DISCLOSED</b><p style="margin:5px 0 0">“${esc(f.unique)}” — shown to the reviewing underwriter alongside the score.</p></div>`:''}
  ${f.hazard&&f.hazardDetail?`<div class="unique-banner"><b>HAZARDOUS ACTIVITY DETAIL</b><p style="margin:5px 0 0">“${esc(f.hazardDetail)}”</p></div>`:''}
  <div class="card"><h3>Factor Breakdown (rule engine)</h3>
   ${factors.map(x=>`<div class="factor-row"><div><div class="factor-label">${esc(x[0])}</div><div class="factor-detail">${esc(x[1])}</div></div><div class="factor-pts">${x[2]>0?'+':''}${x[2]}</div></div>`).join('')}
   <div class="note">The ML half uses the trained logistic-regression coefficients exported from the pipeline (the browser cannot run gradient boosting; logistic is its auditable stand-in, AUC ${(M.risk_models.logistic_regression.auc*100).toFixed(1)}%). Portfolio cases are scored offline with the full dual engine.</div></div>`;
 document.getElementById('scoreResult').scrollIntoView({behavior:'smooth'});
}
render();
</script>
"""

APPROVE_LINE, DECLINE_LINE = 40, 70

def _money(n):
    return "$" + format(int(round(n)), ",")

def case_summary(c):
    """Pre-generated underwriter narrative, grounded strictly in case fields."""
    risk = c["risk_score"]
    smoker = c["smoker"].lower()
    smoke_txt = ("a current smoker" if smoker == "smoker"
                 else "a former smoker" if "former" in smoker else "a non-smoker")
    cond = c["conditions"]
    cond_txt = ("no declared medical conditions" if str(cond).strip().lower() in ("none", "nan", "")
                else f"declared conditions of {cond}")
    band = ("green approval band" if risk < APPROVE_LINE
            else "yellow manual-review band" if risk < DECLINE_LINE else "red decline band")
    life = []
    if c.get("hazard") and c["hazard"] != "None":
        life.append(f"participates in {c['hazard'].lower()}")
    if c.get("violations"):
        life.append(f"has {c['violations']} driving violation(s) in the last three years")
    if c.get("alcohol") == "Heavy":
        life.append("reports heavy alcohol use")
    s = [
        f"{c['name']} is a {c['age']}-year-old {c['occupation']} applying for a "
        f"{c['policy']} policy with {_money(c['coverage'])} in requested coverage.",
        f"The applicant is {smoke_txt} with a BMI of {c['bmi']:.1f} and {cond_txt}"
        + (", and " + "; ".join(life) if life else "") + ".",
        f"Financially, the file shows a credit score of {c['credit']} and a "
        f"debt-to-income ratio of {c['dti'] * 100:.1f}%.",
        f"The composite risk score is {risk}/100 "
        f"(rule engine {c['rule_score']}, gradient boosting {c['ml_score']:.0f}), "
        f"placing the case in the {band}.",
    ]
    if c.get("unique"):
        s.append(f"The applicant disclosed unique circumstances — “{c['unique']}” — "
                 f"which routes the file to a human underwriter for whole-person review.")
    if c["conflicts"]:
        det = "; ".join(f"{k['severity']} {k['type'].replace('_', ' ')} — {k['description']}"
                        for k in c["conflicts"])
        s.append(f"The cross-document screen flagged {len(c['conflicts'])} conflict(s): {det}. "
                 f"These discrepancies independently support routing the file to a human underwriter.")
    elif c["has_docs"]:
        s.append("The cross-document conflict screen found no discrepancies across the packet.")
    s.append(f"System decision: {c['decision']} — {c['rate_class']} "
             f"({'; '.join(c['reasons'])}).")
    return " ".join(s)

def build():
    with open(os.path.join(OUT, "portfolio.json")) as f:
        data = json.load(f)
    for c in data["cases"]:
        c["ai_summary"] = case_summary(c)
    html = TEMPLATE.replace("/*__DATA__*/", json.dumps(data))
    path = os.path.join(OUT, "underwriting_copilot_mvp.html")
    with open(path, "w") as f:
        f.write(html)
    print(f"dashboard written: {path} ({os.path.getsize(path)//1024} KB, {len(data['cases'])} cases embedded)")

if __name__ == "__main__":
    build()
