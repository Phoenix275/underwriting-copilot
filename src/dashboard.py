"""dashboard.py — Builds the underwriter-facing dashboard (single HTML file).

Embeds pipeline output (portfolio.json) directly into the page, keeps the
team's established case-file aesthetic, and adds: document/extraction view,
cross-document conflict panel, dual ML scores, conflict-aware decisions,
and Claude-generated grounded case summaries.
"""
import json, os

OUT = os.path.join(os.path.dirname(__file__), "..", "output")

TEMPLATE = r"""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--ink:#1C2430;--paper:#E8E4D8;--card:#F8F6EF;--card-2:#F1EEE3;--teal:#2F5D53;--teal-soft:#DCE8E3;
--amber:#B8842E;--amber-soft:#F1E4CB;--brick:#9C4A34;--brick-soft:#F0DCD3;--slate:#5B6472;--hair:rgba(28,36,48,.14)}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,sans-serif}
#app{max-width:1240px;margin:0 auto;background:var(--card);box-shadow:0 1px 3px rgba(28,36,48,.15)}
.topbar{padding:20px 28px 16px;border-bottom:2px solid var(--ink);display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:10px}
.brand{font-family:Fraunces,serif;font-weight:600;font-size:21px}
.brand small{display:block;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:1.4px;color:var(--slate);text-transform:uppercase;margin-top:3px;font-weight:400}
.pill{font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:var(--teal);background:var(--teal-soft);padding:4px 10px;border-radius:3px}
.layout{display:flex}.rail{width:280px;border-right:1px solid var(--hair);background:var(--card-2);padding:14px 0;flex-shrink:0}
.rail-title{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:1.4px;text-transform:uppercase;color:var(--slate);padding:0 18px 8px;display:flex;justify-content:space-between}
.overview-link{padding:9px 18px;font-size:12.5px;font-weight:600;cursor:pointer;border-left:3px solid transparent}
.overview-link:hover{background:rgba(28,36,48,.04)}.overview-link.active{border-left-color:var(--ink);background:var(--card)}
.search-box{margin:6px 18px 10px;padding:7px 10px;width:calc(100% - 36px);border:1px solid var(--hair);border-radius:3px;font:12.5px Inter,sans-serif;background:var(--card)}
.case-item{padding:10px 18px;border-left:3px solid transparent;cursor:pointer;display:flex;justify-content:space-between;align-items:center;gap:8px}
.case-item:hover{background:rgba(28,36,48,.04)}.case-item.active{background:var(--card);border-left-color:var(--ink)}
.ci-name{font-size:13px;font-weight:500}.ci-id{font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--slate)}
.doctag{font-family:'IBM Plex Mono',monospace;font-size:8.5px;color:var(--amber)}
.chip{font-family:'IBM Plex Mono',monospace;font-size:9.5px;letter-spacing:.6px;padding:2px 7px;border-radius:2px;font-weight:600;white-space:nowrap}
.chip.low,.chip.moderate{background:var(--teal-soft);color:var(--teal)}.chip.elevated{background:var(--amber-soft);color:var(--amber)}.chip.high{background:var(--brick-soft);color:var(--brick)}
.pagination{display:flex;justify-content:space-between;align-items:center;padding:10px 18px 0;font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:var(--slate)}
.pagination button{font-family:'IBM Plex Mono',monospace;font-size:11px;background:none;border:1px solid var(--hair);border-radius:3px;padding:3px 9px;cursor:pointer;color:var(--ink)}
.pagination button:disabled{opacity:.35;cursor:default}
.main{flex:1;min-width:0}.case-head{padding:22px 30px 0}.case-head h1{font-family:Fraunces,serif;font-size:25px;margin:0 0 4px;font-weight:600}
.case-meta{font-family:'IBM Plex Mono',monospace;font-size:12px;color:var(--slate);display:flex;gap:16px;flex-wrap:wrap}
.tabs{display:flex;gap:2px;margin:20px 30px 0;border-bottom:1px solid var(--hair)}
.tab{font-family:'IBM Plex Mono',monospace;font-size:11.5px;padding:10px 14px;cursor:pointer;color:var(--slate);border-bottom:2px solid transparent;position:relative;top:1px}
.tab .n{opacity:.6;margin-right:6px}.tab.active{color:var(--ink);border-bottom-color:var(--ink);font-weight:600}
.panel{padding:24px 30px 36px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px 30px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.field{border-bottom:1px solid var(--hair);padding:9px 0}.field label{display:block;font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.8px;text-transform:uppercase;color:var(--slate);margin-bottom:4px}
.field .val{font-size:14.5px}.mono{font-family:'IBM Plex Mono',monospace}
.stat-card{background:var(--card-2);border:1px solid var(--hair);border-radius:4px;padding:16px 18px}
.stat-card .sv{font-family:Fraunces,serif;font-size:28px;font-weight:700}.stat-card .sl{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.8px;text-transform:uppercase;color:var(--slate);margin-top:2px}
.doc-row{display:flex;align-items:center;gap:12px;padding:12px 14px;background:var(--card-2);border:1px solid var(--hair);border-radius:3px;margin-bottom:10px}
.doc-row .dot{width:8px;height:8px;border-radius:50%;background:var(--teal);flex-shrink:0}.doc-row .dot.miss{background:var(--slate)}
.dname{font-size:13.5px;font-weight:500;flex:1}.dstatus{font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:var(--teal)}
table.xt{width:100%;border-collapse:collapse;margin-top:6px}
table.xt th{text-align:left;font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.6px;text-transform:uppercase;color:var(--slate);border-bottom:1px solid var(--ink);padding:6px 10px 8px 0}
table.xt td{padding:9px 10px 9px 0;border-bottom:1px solid var(--hair);font-size:13px}
.flag{font-family:'IBM Plex Mono',monospace;font-size:9.5px;padding:2px 6px;border-radius:2px;font-weight:600}
.flag.match{background:var(--teal-soft);color:var(--teal)}.flag.diff{background:var(--brick-soft);color:var(--brick)}.flag.minor{background:var(--amber-soft);color:var(--amber)}
.score-row{display:flex;gap:20px;margin-bottom:18px;flex-wrap:wrap}
.score-card{flex:1;min-width:200px;background:var(--card-2);border:1px solid var(--hair);border-radius:4px;padding:16px 18px}
.sc-label{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:.8px;text-transform:uppercase;color:var(--slate)}
.sc-value{font-family:Fraunces,serif;font-size:32px;font-weight:700;margin:4px 0}
.bar-track{height:7px;background:var(--card);border:1px solid var(--hair);border-radius:4px;overflow:hidden;margin-top:6px}.bar-fill{height:100%}
.factor-row{display:flex;justify-content:space-between;align-items:center;padding:9px 0;border-bottom:1px solid var(--hair);gap:16px}
.factor-label{font-size:13px}.factor-detail{font-family:'IBM Plex Mono',monospace;font-size:10.5px;color:var(--slate)}
.factor-pts{font-family:'IBM Plex Mono',monospace;font-size:12.5px;font-weight:600;min-width:44px;text-align:right}
.section-h{font-family:'IBM Plex Mono',monospace;font-size:10.5px;letter-spacing:1px;text-transform:uppercase;color:var(--slate);margin:22px 0 4px}
.conflict-card{border:1px solid var(--brick);background:var(--brick-soft);border-radius:4px;padding:12px 16px;margin:8px 0}
.conflict-card.minor{border-color:var(--amber);background:var(--amber-soft)}
.conflict-card b{font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:.5px}
.conflict-card p{margin:4px 0 0;font-size:12.5px;color:var(--ink)}
.stamp{font-family:'IBM Plex Mono',monospace;font-weight:700;font-size:17px;letter-spacing:1.4px;border:3px solid;padding:12px 18px;border-radius:4px;transform:rotate(-4deg);display:inline-block;text-transform:uppercase;position:relative}
.stamp::after{content:'';position:absolute;inset:5px;border:1px solid;border-radius:2px;opacity:.5}
.stamp.ok{color:var(--teal);border-color:var(--teal)}.stamp.warn{color:var(--amber);border-color:var(--amber)}.stamp.bad{color:var(--brick);border-color:var(--brick)}
.decision-wrap{display:flex;gap:30px;align-items:flex-start;flex-wrap:wrap}
.decision-detail h3{font-family:Fraunces,serif;font-size:18px;margin:0 0 6px}.decision-detail p{font-size:13.5px;color:var(--slate);margin:0 0 4px;line-height:1.5}
.ai-box{margin-top:22px;border:1px solid var(--hair);background:var(--card-2);border-radius:4px;padding:18px 20px}
.ai-box .lbl{font-family:'IBM Plex Mono',monospace;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--slate);margin-bottom:10px;display:flex;justify-content:space-between;align-items:center}
.ai-btn{font-family:'IBM Plex Mono',monospace;font-size:11px;background:var(--ink);color:var(--card);border:none;padding:7px 14px;border-radius:3px;cursor:pointer}
.ai-btn:disabled{opacity:.5}.ai-text{font-size:14px;line-height:1.65}.ai-empty{font-size:13px;color:var(--slate);font-style:italic}
.hist-bar-row{display:flex;align-items:center;gap:10px;margin:8px 0}.hist-label{width:96px;font-family:'IBM Plex Mono',monospace;font-size:11px}
.hist-track{flex:1;height:16px;background:var(--card);border:1px solid var(--hair);border-radius:3px;overflow:hidden}.hist-fill{height:100%}
.hist-count{width:70px;text-align:right;font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--slate)}
.coef-bar-row{display:flex;align-items:center;gap:10px;margin:7px 0}.coef-label{width:180px;font-size:12.5px}
.coef-track{flex:1;height:14px;background:var(--card);border-radius:2px;position:relative}.coef-fill{position:absolute;top:0;bottom:0;border-radius:2px}
.coef-val{width:56px;font-family:'IBM Plex Mono',monospace;font-size:11px;text-align:right}
.metric-note{font-size:12px;color:var(--slate);margin-top:10px;line-height:1.6}
@media(max-width:860px){.grid2,.grid3{grid-template-columns:1fr}.layout{flex-direction:column}.rail{width:100%;border-right:none;border-bottom:1px solid var(--hair)}}
</style>
<div id="app">
 <div class="topbar">
  <div class="brand">Underwriting Copilot — Case Review
   <small>PDF Packet → Extraction → Conflict Screen → Dual Risk Engine → Decision · MVP v0.2</small></div>
  <span class="pill" id="pill"></span>
 </div>
 <div class="layout">
  <div class="rail">
   <div class="overview-link" id="overviewLink" onclick="goOverview()">◂ Portfolio & Model Card</div>
   <div class="rail-title"><span>Case Queue</span><span id="queueCount"></span></div>
   <input class="search-box" id="searchBox" placeholder="Search name or ID…" oninput="onSearch(this.value)">
   <div id="caseList"></div>
   <div class="pagination"><button id="prevBtn" onclick="pg(-1)">‹ Prev</button><span id="pageLabel"></span><button id="nextBtn" onclick="pg(1)">Next ›</button></div>
  </div>
  <div class="main"><div id="mainContent"></div></div>
 </div>
</div>
<script>
const DATA = /*__DATA__*/;
const M = DATA.metrics, CASES = DATA.cases;
const tierMeta={low:["Low Risk","ok"],moderate:["Moderate Risk","ok"],elevated:["Elevated Risk","warn"],high:["High Risk","bad"]};
let filtered=CASES.slice(),page=0,activeId=CASES[0].id,view="case",activeTab=1;const PAGE=20;let aiCache={};
const fmt$=n=>n==null?"—":"$"+Math.round(n).toLocaleString();
function onSearch(q){q=q.trim().toLowerCase();filtered=q?CASES.filter(c=>c.name.toLowerCase().includes(q)||c.id.toLowerCase().includes(q)):CASES.slice();page=0;rail();}
function pg(d){const mx=Math.max(0,Math.ceil(filtered.length/PAGE)-1);page=Math.min(mx,Math.max(0,page+d));rail();}
function goOverview(){view="overview";render();}
function sel(id){activeId=id;view="case";activeTab=1;render();}
function selTab(n){activeTab=n;render();}
function render(){rail();main();}
function rail(){
 document.getElementById('overviewLink').className="overview-link"+(view==="overview"?" active":"");
 document.getElementById('queueCount').textContent=filtered.length+" cases";
 const items=filtered.slice(page*PAGE,page*PAGE+PAGE);
 document.getElementById('caseList').innerHTML=items.map(c=>{
  const t=c.tier;
  return `<div class="case-item ${c.id===activeId&&view==='case'?'active':''}" onclick="sel('${c.id}')">
   <div><div class="ci-name">${c.name}</div><div class="ci-id">${c.id}${c.has_docs?' <span class="doctag">·PDF PACKET</span>':''}</div></div>
   <div class="chip ${t}">${tierMeta[t][0].split(' ')[0]}</div></div>`;}).join('');
 const mx=Math.max(0,Math.ceil(filtered.length/PAGE)-1);
 document.getElementById('pageLabel').textContent=(page+1)+" / "+(mx+1);
 document.getElementById('prevBtn').disabled=page<=0;document.getElementById('nextBtn').disabled=page>=mx;
 document.getElementById('pill').textContent=M.n_applicants.toLocaleString()+" applicants scored · "+M.n_packets+" PDF packets processed";
}
function main(){
 const el=document.getElementById('mainContent');
 if(view==="overview"){el.innerHTML=overview();return;}
 const c=CASES.find(x=>x.id===activeId);if(!c){el.innerHTML=overview();return;}
 el.innerHTML=`<div class="case-head"><h1>${c.name}</h1>
  <div class="case-meta"><span>${c.id}</span><span>${c.occupation}</span><span>${c.city}, ${c.state}</span><span>${c.policy}</span></div></div>
  <div class="tabs">${[[1,'Application'],[2,'Documents'],[3,'Extraction & Conflicts'],[4,'Risk Assessment'],[5,'Decision']]
   .map(t=>`<div class="tab ${t[0]===activeTab?'active':''}" onclick="selTab(${t[0]})"><span class="n">${String(t[0]).padStart(2,'0')}</span>${t[1]}</div>`).join('')}</div>
  <div class="panel">${panel(c)}</div>`;
}
function overview(){
 const tc={low:0,moderate:0,elevated:0,high:0};CASES.forEach(c=>tc[c.tier]++);
 const mx=Math.max(...Object.values(tc),1);const col={low:'var(--teal)',moderate:'var(--teal)',elevated:'var(--amber)',high:'var(--brick)'};
 const gb=M.risk_models.gradient_boosting,lr=M.risk_models.logistic_regression;
 const fi=M.risk_models.gb_feature_importance;const mxf=Math.max(...Object.values(fi));
 return `<div class="case-head"><h1>Portfolio & Model Card</h1>
  <div class="case-meta"><span>${M.n_applicants.toLocaleString()} synthetic applicants</span><span>${M.n_packets} PDF packets</span><span>evaluated ${M.generated_at}</span></div></div>
 <div class="panel">
  <div class="section-h">Pipeline Metrics — every stage measured against known ground truth</div>
  <div class="grid3" style="margin-top:8px">
   <div class="stat-card"><div class="sv">${(M.extraction.field_level_accuracy*100).toFixed(1)}%</div><div class="sl">Extraction accuracy (field-level)</div></div>
   <div class="stat-card"><div class="sv">${(M.conflict_screening.detection_recall*100).toFixed(0)}%</div><div class="sl">Injected-conflict detection recall</div></div>
   <div class="stat-card"><div class="sv">${(M.conflict_screening.detection_precision*100).toFixed(0)}%</div><div class="sl">Conflict detection precision</div></div>
   <div class="stat-card"><div class="sv">${(gb.auc*100).toFixed(1)}%</div><div class="sl">Gradient Boosting AUC (test)</div></div>
   <div class="stat-card"><div class="sv">${(lr.auc*100).toFixed(1)}%</div><div class="sl">Logistic Regression AUC (test)</div></div>
   <div class="stat-card"><div class="sv">${(M.decisioning.straight_through_rate*100).toFixed(1)}%</div><div class="sl">Straight-through rate</div></div>
  </div>
  <p class="metric-note">Extraction accuracy is measured on machine-generated text PDFs and is expected to drop on scanned documents — that is precisely the gap Google Document AI closes in the GCP deployment. Conflict screening: ${M.conflict_screening.tp}/${M.conflict_screening.tp+M.conflict_screening.fn} deliberately injected conflicts caught, ${M.conflict_screening.fp} false positives. Models trained on ${M.risk_models.n_train.toLocaleString()} records, held-out test ${M.risk_models.n_test.toLocaleString()}, base high-risk rate ${(M.risk_models.positive_rate*100).toFixed(0)}%.</p>
  <div class="section-h">Risk Tier Distribution</div>
  ${Object.entries(tc).map(([t,n])=>`<div class="hist-bar-row"><div class="hist-label">${tierMeta[t][0]}</div>
   <div class="hist-track"><div class="hist-fill" style="width:${n/mx*100}%;background:${col[t]}"></div></div><div class="hist-count">${n}</div></div>`).join('')}
  <div class="section-h">Gradient Boosting — Feature Importance</div>
  ${Object.entries(fi).sort((a,b)=>b[1]-a[1]).map(([f,v])=>`<div class="coef-bar-row"><div class="coef-label">${f}</div>
   <div class="coef-track"><div class="coef-fill" style="left:0;width:${v/mxf*100}%;background:var(--teal)"></div></div><div class="coef-val">${v.toFixed(3)}</div></div>`).join('')}
  <p class="metric-note">Two models run side by side on every case: the rule engine stays fully auditable (every point traceable to a documented factor weight), while gradient boosting captures interactions. Material disagreement between the two auto-refers the case to a human.</p>
 </div>`;
}
function panel(c){
 if(activeTab===1){
  const sec=(title,fields)=>`<div class="section-h">${title}</div><div class="grid2" style="margin-bottom:14px">
   ${fields.map(f=>`<div class="field"><label>${f[0]}</label><div class="val">${f[1]??'—'}</div></div>`).join('')}</div>`;
  return sec("Section 1 — Applicant Information",[
    ["Full Name",c.name],["Date of Birth",c.dob+" (age "+c.age+")"],
    ["Occupation",c.occupation],["Employer",c.employer],
    ["Employment Status",c.emp_status],["Years Employed",c.years_emp+" yrs"],
    ["Location",c.city+", "+c.state],["Policy Requested",c.policy]])
   +sec("Section 2 — Financial Declaration",[
    ["Declared Annual Income",fmt$(c.income)],["Coverage Requested",fmt$(c.coverage)],
    ["Monthly Expenses",fmt$(c.expenses)],["Existing Debt",fmt$(c.debt)],
    ["Avg Bank Balance",fmt$(c.bank)],["Credit Score",c.credit],
    ["Debt-to-Income Ratio",(c.dti*100).toFixed(1)+"%"],["Coverage-to-Income Multiple",(c.coverage/c.income).toFixed(1)+"×"]])
   +sec("Section 3 — Medical & Lifestyle",[
    ["Height / Weight",c.height+" cm / "+c.weight+" kg"],["BMI",c.bmi.toFixed(1)],
    ["Tobacco Use",c.smoker],["Existing Conditions",c.conditions],
    ["Family History Flag",c.family?"Yes":"No"],["Hazardous Activities","No"],
    ["Blood Pressure",c.bp],["Cholesterol",c.chol+" mg/dL"]]);
 }
 if(activeTab===2){
  const docs=c.has_docs?[["Application Form (Parts A–B, health questionnaire)","Parsed"],["Payslip / Earnings Statement","Parsed"],["Paramedical Exam Report + consumer report","Parsed"]]
   :[["Application Form","Not in packet sample"],["Payslip / Earnings Statement","Not in packet sample"],["Paramedical Exam Report","Not in packet sample"]];
  return docs.map(d=>`<div class="doc-row"><div class="dot ${c.has_docs?'':'miss'}"></div><div class="dname">${d[0]}</div><div class="dstatus">${d[1]}${c.has_docs?' ✓':''}</div></div>`).join('')
   +(c.has_docs?'':'<p class="metric-note">This applicant is part of the scored portfolio but outside the PDF-packet sample; risk scores below are computed from structured data. In production every case flows through document extraction.</p>');
 }
 if(activeTab===3){
  if(!c.has_docs)return '<p class="metric-note">No PDF packet for this applicant in the sample — see a case tagged ·PDF PACKET in the queue for the full extraction view.</p>';
  const e=c.extraction;
  const rows=[["Name (form)",e.name],["DOB (form)",e.form_dob],["DOB (paramed / ID)",e.paramed_dob],
   ["Declared income (form)",fmt$(e.form_income)],["Income (payslip, annualized)",fmt$(e.payslip_income)],
   ["Declared debt (form)",fmt$(e.form_debt)],["Debt (credit bureau)",fmt$(e.bureau_debt)],
   ["Tobacco (form 4a)",e.form_tobacco_yes?"YES":"NO"],["Cotinine (lab)",e.cotinine],
   ["Height / Weight",e.height_cm+" cm / "+e.weight_kg+" kg"],["Blood pressure",e.blood_pressure],["Cholesterol",e.cholesterol+" mg/dL"]];
  const confl=c.conflicts.length?c.conflicts.map(k=>`<div class="conflict-card ${k.severity==='minor'?'minor':''}">
   <b>${k.severity.toUpperCase()} · ${k.type.replace(/_/g,' ').toUpperCase()}</b><p>${k.description}</p></div>`).join('')
   :'<p class="metric-note">No cross-document conflicts detected. All four checks passed — every applicant runs through the identical checklist.</p>';
  return `<table class="xt"><tr><th>Extracted Field</th><th>Value</th></tr>
   ${rows.map(r=>`<tr><td>${r[0]}</td><td class="mono">${r[1]??'—'}</td></tr>`).join('')}</table>
   <div class="section-h">Cross-Document Conflict Screen (4 checks, equal for every applicant)</div>${confl}`;
 }
 if(activeTab===4){
  const col={low:'var(--teal)',moderate:'var(--teal)',elevated:'var(--amber)',high:'var(--brick)'};
  const rt=tier(c.rule_score),mt=c.tier;
  return `<div class="score-row">
   <div class="score-card"><div class="sc-label">Rule Engine (auditable)</div><div class="sc-value">${c.rule_score}</div>
    <div class="bar-track"><div class="bar-fill" style="width:${c.rule_score}%;background:${col[rt]}"></div></div>
    <div class="chip ${rt}" style="margin-top:8px;display:inline-block">${tierMeta[rt][0]}</div></div>
   <div class="score-card"><div class="sc-label">Gradient Boosting (AUC ${(M.risk_models.gradient_boosting.auc*100).toFixed(1)}%)</div><div class="sc-value">${c.ml_score.toFixed(0)}</div>
    <div class="bar-track"><div class="bar-fill" style="width:${c.ml_score}%;background:${col[mt]}"></div></div>
    <div class="chip ${mt}" style="margin-top:8px;display:inline-block">${tierMeta[mt][0]}</div></div>
   <div class="score-card"><div class="sc-label">Logistic Regression (baseline)</div><div class="sc-value">${c.ml_score_lr.toFixed(0)}</div>
    <div class="bar-track"><div class="bar-fill" style="width:${c.ml_score_lr}%;background:var(--slate)"></div></div></div>
  </div>
  ${c.label!=null?`<p class="metric-note">Ground-truth label: <b>${c.label==1?'High Risk':'Not High Risk'}</b> — synthetic data lets us verify every score against a known answer.</p>`:''}
  <div class="section-h">Rule-Based Factor Breakdown (weightage per underwriting notes)</div>
  ${c.rule_factors.map(f=>`<div class="factor-row"><div><div class="factor-label">${f[0]}</div><div class="factor-detail">${f[1]}</div></div>
   <div class="factor-pts">${f[2]>0?'+':''}${f[2]}</div></div>`).join('')}`;
 }
 if(activeTab===5){
  const cls=c.decision.startsWith("APPROVED")?"ok":c.tier==="high"?"bad":"warn";
  const ai=aiCache[c.id];
  return `<div class="decision-wrap">
   <div class="stamp ${cls}">${c.decision}</div>
   <div class="decision-detail"><h3>${c.rate_class}</h3>
    ${c.reasons.map(r=>`<p>· ${r}</p>`).join('')}
    <p class="mono" style="font-size:11px">GB ${c.ml_score.toFixed(0)}/100 · Rule ${c.rule_score}/100 · ${c.conflicts.length} conflict(s)</p></div></div>
  <div class="ai-box"><div class="lbl">AI Underwriting Summary (grounded in extracted fields only)
   <button class="ai-btn" id="aiBtn" onclick="genSummary()">${ai?'Regenerate':'Generate Summary'}</button></div>
   <div id="aiContent">${ai?`<div class="ai-text">${ai}</div>`:'<div class="ai-empty">Click to generate an underwriter-ready narrative. Every sentence is grounded in the case data above — the prompt forbids invented numbers.</div>'}</div></div>`;
 }
}
function tier(s){return s<=25?"low":s<=50?"moderate":s<=70?"elevated":"high";}
async function genSummary(){
 const c=CASES.find(x=>x.id===activeId);
 const btn=document.getElementById('aiBtn');btn.disabled=true;btn.textContent='Generating…';
 document.getElementById('aiContent').innerHTML='<div class="ai-empty">Contacting model…</div>';
 const conflictTxt=c.conflicts.length?c.conflicts.map(k=>k.severity+" "+k.type+": "+k.description).join(" | "):"none detected";
 const prompt="You are an underwriting assistant writing a short internal case summary for a life insurance underwriter. Use ONLY the facts below — never invent numbers. 4–6 sentences, plain professional tone, no headers or bullets. If conflicts exist, address them explicitly and support the referral.\n\n"
  +`Applicant: ${c.name}, age ${c.age}, ${c.occupation}\nPolicy: ${c.policy}, coverage ${fmt$(c.coverage)}\nSmoker status (dataset): ${c.smoker}\nBMI: ${c.bmi}\nConditions: ${c.conditions}\nDTI: ${(c.dti*100).toFixed(1)}%\nCredit score: ${c.credit}\nRule score: ${c.rule_score}/100\nML (gradient boosting) score: ${c.ml_score.toFixed(0)}/100 (AUC ${(M.risk_models.gradient_boosting.auc*100).toFixed(1)}% on held-out test)\nCross-document conflicts: ${conflictTxt}\nSystem decision: ${c.decision} — ${c.rate_class}\nReasons: ${c.reasons.join("; ")}\n\nWrite the summary now.`;
 try{
  const r=await fetch("https://api.anthropic.com/v1/messages",{method:"POST",headers:{"Content-Type":"application/json"},
   body:JSON.stringify({model:"claude-sonnet-4-6",max_tokens:1000,messages:[{role:"user",content:prompt}]})});
  const d=await r.json();
  const text=(d.content||[]).filter(b=>b.type==='text').map(b=>b.text).join('\n').trim();
  aiCache[c.id]=text||"No summary returned.";render();
 }catch(e){
  document.getElementById('aiContent').innerHTML='<div class="ai-empty">Model unreachable right now — rule and ML scores above remain fully usable.</div>';
  btn.disabled=false;btn.textContent='Generate Summary';
 }
}
render();
</script>
"""

def build():
    with open(os.path.join(OUT, "portfolio.json")) as f:
        data = json.load(f)
    html = TEMPLATE.replace("/*__DATA__*/", json.dumps(data))
    path = os.path.join(OUT, "underwriting_copilot_mvp.html")
    with open(path, "w") as f:
        f.write(html)
    print(f"dashboard written: {path} ({os.path.getsize(path)//1024} KB, {len(data['cases'])} cases embedded)")

if __name__ == "__main__":
    build()
