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
.sc-ok{background:rgba(14,159,110,.18);color:#4ADE9E}.sc-bad{background:rgba(220,38,38,.2);color:#F87F7F}
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
.cls-ok{background:var(--ok-soft);color:var(--ok)}.cls-bad{background:var(--bad-soft);color:var(--bad)}
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
@media(max-width:900px){#app{flex-direction:column}.rail{width:100%}.grid2,.grid3{grid-template-columns:1fr}.main{padding:20px}}
</style>
<div id="app">
 <div class="rail">
  <div class="rail-brand"><h1>Underwriting Copilot</h1><p>Extraction · Conflict Screen · Risk Score · Decision</p></div>
  <div class="overview-link" id="overviewLink" onclick="goOverview()">⌂ &nbsp;Portfolio & Model Card</div>
  <div class="rail-sub"><span>Case Queue</span><span id="queueCount"></span></div>
  <input class="search-box" id="searchBox" placeholder="Search name or ID…" oninput="onSearch(this.value)">
  <div class="case-list" id="caseList"></div>
  <div class="pagination"><button id="prevBtn" onclick="pg(-1)">‹ Prev</button><span id="pageLabel"></span><button id="nextBtn" onclick="pg(1)">Next ›</button></div>
 </div>
 <div class="main"><div id="mainContent"></div></div>
</div>
<script>
const DATA = /*__DATA__*/;
const M = DATA.metrics, CASES = DATA.cases;
CASES.forEach(c=>{c.risk_score=Math.round(0.5*c.rule_score+0.5*c.ml_score);});
const THRESH = 50;
const riskClass=s=>s>=THRESH?["HIGH RISK","bad"]:["ACCEPTABLE RISK","ok"];
const band=s=>s<=25?["Low","var(--ok)"]:s<THRESH?["Moderate","var(--ok)"]:s<=70?["Elevated","var(--warn)"]:["High","var(--bad)"];
let filtered=CASES.slice(),page=0,activeId=CASES[0].id,view="case",activeTab=4;const PAGE=20;
const fmt$=n=>n==null?"—":"$"+Math.round(n).toLocaleString();
function onSearch(q){q=q.trim().toLowerCase();filtered=q?CASES.filter(c=>c.name.toLowerCase().includes(q)||c.id.toLowerCase().includes(q)):CASES.slice();page=0;rail();}
function pg(d){const mx=Math.max(0,Math.ceil(filtered.length/PAGE)-1);page=Math.min(mx,Math.max(0,page+d));rail();}
function goOverview(){view="overview";render();}
function sel(id){activeId=id;view="case";activeTab=4;render();}
function selTab(n){activeTab=n;render();}
function render(){rail();main();}
function rail(){
 document.getElementById('overviewLink').className="overview-link"+(view==="overview"?" active":"");
 document.getElementById('queueCount').textContent=filtered.length+" cases";
 const items=filtered.slice(page*PAGE,page*PAGE+PAGE);
 document.getElementById('caseList').innerHTML=items.map(c=>{
  const risky=c.risk_score>=THRESH;
  return `<div class="case-item ${c.id===activeId&&view==='case'?'active':''}" onclick="sel('${c.id}')">
   <div><div class="ci-name">${c.name}</div><div class="ci-id">${c.id}${c.has_docs?' <span class="doctag">· PDF</span>':''}</div></div>
   <div class="score-chip ${risky?'sc-bad':'sc-ok'}">${c.risk_score}</div></div>`;}).join('');
 const mx=Math.max(0,Math.ceil(filtered.length/PAGE)-1);
 document.getElementById('pageLabel').textContent=(page+1)+" / "+(mx+1);
 document.getElementById('prevBtn').disabled=page<=0;document.getElementById('nextBtn').disabled=page>=mx;
}
function main(){
 const el=document.getElementById('mainContent');
 if(view==="overview"){el.innerHTML=overview();return;}
 const c=CASES.find(x=>x.id===activeId);if(!c){el.innerHTML=overview();return;}
 const rc=riskClass(c.risk_score);
 el.innerHTML=`<div class="case-head">
   <div><h2>${c.name}</h2>
    <div class="case-meta"><span>${c.id}</span><span>${c.occupation}</span><span>${c.city}, ${c.state}</span><span>${c.policy}</span></div></div>
   <div class="headline-score">
    <div><div class="hs-num" style="color:var(--${rc[1]})">${c.risk_score}<span style="font-size:16px;color:var(--mut)">/100</span></div>
     <div class="hs-lab">Composite Risk Score</div></div>
    <div class="hs-class cls-${rc[1]}">${rc[0]}</div></div></div>
  <div class="tabs">${[[1,'Application'],[2,'Documents'],[3,'Extraction & Conflicts'],[4,'Risk Score'],[5,'Decision']]
   .map(t=>`<div class="tab ${t[0]===activeTab?'active':''}" onclick="selTab(${t[0]})">${t[1]}</div>`).join('')}</div>
  ${panel(c)}`;
}
function gauge(score){
 const L=251.33, off=L*(1-score/100);
 const col=score>=THRESH?(score>70?'var(--bad)':'var(--warn)'):'var(--ok)';
 const tickA=Math.PI*(1-THRESH/100), tx=100+86*Math.cos(tickA), ty=100-86*Math.sin(tickA), tx2=100+72*Math.cos(tickA), ty2=100-72*Math.sin(tickA);
 return `<svg class="gauge" viewBox="0 0 200 112">
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="var(--line)" stroke-width="15" stroke-linecap="round"/>
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="${col}" stroke-width="15" stroke-linecap="round"
   stroke-dasharray="${L}" stroke-dashoffset="${off}"/>
  <line x1="${tx}" y1="${ty}" x2="${tx2}" y2="${ty2}" stroke="var(--ink)" stroke-width="2.5" stroke-dasharray="3 3"/>
  <text x="100" y="88" text-anchor="middle" font-family="Space Grotesk" font-size="30" font-weight="700" fill="var(--ink)">${score}</text>
  <text x="100" y="104" text-anchor="middle" font-family="Inter" font-size="9" fill="var(--mut)">threshold at ${THRESH}</text></svg>`;
}
function overview(){
 const tc={"Low (0–25)":0,"Moderate (26–49)":0,"Elevated (50–70)":0,"High (71–100)":0};
 CASES.forEach(c=>{const s=c.risk_score;if(s<=25)tc["Low (0–25)"]++;else if(s<THRESH)tc["Moderate (26–49)"]++;else if(s<=70)tc["Elevated (50–70)"]++;else tc["High (71–100)"]++;});
 const risky=CASES.filter(c=>c.risk_score>=THRESH).length;
 const mx=Math.max(...Object.values(tc),1);const cols=["var(--ok)","var(--ok)","var(--warn)","var(--bad)"];
 const gb=M.risk_models.gradient_boosting,lr=M.risk_models.logistic_regression;
 const fi=M.risk_models.gb_feature_importance;const mxf=Math.max(...Object.values(fi));
 return `<div class="case-head"><div><h2>Portfolio & Model Card</h2>
  <div class="case-meta"><span>${M.n_applicants.toLocaleString()} applicants scored</span><span>${M.n_packets} PDF packets</span><span>${risky} of ${CASES.length} shown cases ≥ ${THRESH}</span></div></div></div>
 <div class="tabs"></div>
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
  <div class="note">Scores at or above ${THRESH} are classified HIGH RISK and cannot be auto-approved.</div></div>
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
    ["Family History (4c)",c.family?"Yes — parent, see attending records":"None disclosed"],["Hazardous Activities (4d)","No"],
    ["Blood Pressure",c.bp],["Total Cholesterol",c.chol+" mg/dL"]]);
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
  const rc=riskClass(c.risk_score);const b=band(c.risk_score);
  const sub=(l,v,col)=>`<div class="sub-score"><div class="ss-l">${l}</div><div class="ss-v">${v}</div>
   <div class="bar-track"><div class="bar-fill" style="width:${v}%;background:${col}"></div></div></div>`;
  return `<div class="card"><h3>Composite Risk Score</h3>
   <div class="gauge-wrap">${gauge(c.risk_score)}
    <div class="gauge-info">
     <div class="g-band cls-${rc[1]}">${rc[0]} · ${b[0]} band</div>
     <div class="g-note">${c.risk_score>=THRESH
       ?`This case scores at or above the ${THRESH}-point risk line, so it cannot be auto-approved — it routes to a human underwriter regardless of any other signal.`
       :`This case scores below the ${THRESH}-point risk line and is eligible for straight-through approval, provided no major data conflicts are found.`}</div>
     <div class="sub-scores">
      ${sub("Rule engine (50%)",c.rule_score,"var(--acc)")}
      ${sub("ML — gradient boosting (50%)",Math.round(c.ml_score),"var(--acc)")}
      ${sub("ML — logistic (reference)",Math.round(c.ml_score_lr),"var(--mut)")}
     </div></div></div></div>
  <div class="card explain"><h3>How this score works</h3>
   <p><b>Formula:</b> Risk Score = 50% × Rule Engine score + 50% × ML probability. The rule engine is fully auditable — every point traces to a documented factor weight below. The ML component is a gradient-boosting model trained on ${M.risk_models.n_train.toLocaleString()} records (AUC ${(M.risk_models.gradient_boosting.auc*100).toFixed(1)}% on ${M.risk_models.n_test.toLocaleString()} held-out cases), which captures factor interactions the rules miss. Blending them means one bad model can never single-handedly approve a risky case.</p>
   <p><b>The ${THRESH}-point line:</b> at or above ${THRESH} the case is classified HIGH RISK and always goes to a human. Below ${THRESH} it may be auto-approved — unless the conflict screen found a major cross-document discrepancy, which overrides everything.</p>
   <div class="bands">
    <span class="band-chip" style="background:var(--ok-soft);color:var(--ok)">0–25 Low</span>
    <span class="band-chip" style="background:var(--ok-soft);color:var(--ok)">26–49 Moderate</span>
    <span class="band-chip" style="background:var(--warn-soft);color:var(--warn)">50–70 Elevated</span>
    <span class="band-chip" style="background:var(--bad-soft);color:var(--bad)">71–100 High</span>
   </div></div>
  <div class="card"><h3>Rule Engine — Factor Breakdown</h3>
   ${c.rule_factors.map(f=>`<div class="factor-row"><div><div class="factor-label">${f[0]}</div><div class="factor-detail">${f[1]}</div></div>
    <div class="factor-pts">${f[2]>0?'+':''}${f[2]}</div></div>`).join('')}
   ${c.label!=null?`<div class="note">Ground-truth label: <b>${c.label==1?'High Risk':'Not High Risk'}</b> — synthetic data lets every score be verified against a known answer.</div>`:''}</div>`;
 }
 if(activeTab===5){
  const cls=c.decision.startsWith("APPROVED")?"ok":c.tier==="high"?"bad":"warn";
  return `<div class="card"><h3>System Decision</h3><div class="decision-wrap">
   <div class="stamp ${cls}">${c.decision}</div>
   <div class="decision-detail"><h3>${c.rate_class}</h3>
    ${c.reasons.map(r=>`<p>· ${r}</p>`).join('')}
    <p class="mono" style="font-size:11px">Risk ${c.risk_score}/100 · Rule ${c.rule_score} · GB ${c.ml_score.toFixed(0)} · ${c.conflicts.length} conflict(s)</p></div></div></div>
  <div class="card"><div class="ai-head"><h3 style="margin:0">Underwriting Summary — grounded in extracted fields only</h3></div>
   <div class="ai-text">${c.ai_summary}</div></div>`;
 }
}
render();
</script>
"""

THRESH = 50

def _money(n):
    return "$" + format(int(round(n)), ",")

def case_summary(c):
    """Pre-generated underwriter narrative, grounded strictly in case fields."""
    risk = round(0.5 * c["rule_score"] + 0.5 * c["ml_score"])
    smoker = c["smoker"].lower()
    smoke_txt = ("a current smoker" if smoker == "smoker"
                 else "a former smoker" if "former" in smoker else "a non-smoker")
    cond = c["conditions"]
    cond_txt = ("no declared medical conditions" if str(cond).strip().lower() in ("none", "nan", "")
                else f"declared conditions of {cond}")
    s = [
        f"{c['name']} is a {c['age']}-year-old {c['occupation']} applying for a "
        f"{c['policy']} policy with {_money(c['coverage'])} in requested coverage.",
        f"The applicant is {smoke_txt} with a BMI of {c['bmi']:.1f} and {cond_txt}.",
        f"Financially, the file shows a credit score of {c['credit']} and a "
        f"debt-to-income ratio of {c['dti'] * 100:.1f}%.",
        f"The composite risk score is {risk}/100 against the {THRESH}-point threshold "
        f"(rule engine {c['rule_score']}, gradient boosting {c['ml_score']:.0f}), "
        f"placing the case {'above' if risk >= THRESH else 'below'} the high-risk line.",
    ]
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
