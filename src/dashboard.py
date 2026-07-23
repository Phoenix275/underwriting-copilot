"""dashboard.py — Underwriter dashboard v3 (modern redesign).

Adds a composite Risk Score (0-100): 50% auditable rule engine + 50% ML
(gradient boosting) probability. Threshold at 50: below = ACCEPTABLE RISK,
50 and above = HIGH RISK. A "How this score works" explainer panel documents
the formula, the bands, and the models. Dark-rail modern UI.
"""
import json, os

OUT = os.path.join(os.path.dirname(__file__), "..", "output")

TEMPLATE = r"""
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#3B3A78;--card:#161619;--ink:#FFFFFF;--mut:#9A9AA5;--line:#2A2A31;--rail:#0D0D0F;--rail-2:#1D1D22;
--ok:#35C77F;--ok-soft:rgba(53,199,127,.16);--warn:#F5B24A;--warn-soft:rgba(245,178,74,.16);--bad:#F2585B;--bad-soft:rgba(242,88,91,.16);--acc:#6A67F7;--acc-soft:rgba(106,103,247,.18)}
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
.headline-score{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;box-shadow:0 1px 2px rgba(14,21,38,.05)}
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
/* Wide tables scroll inside their own card so nothing is clipped by #app's
   overflow:hidden on narrow / half-screen windows. */
@media(max-width:1200px){.card{overflow-x:auto;-webkit-overflow-scrolling:touch}table.xt{min-width:560px}}
/* Below ~1024 the two-pane layout stacks: the rail moves on top so the main
   content gets the full width (half-screen friendly). */
@media(max-width:1024px){#app{flex-direction:column}.rail{width:100%}.grid2,.grid3,.form-grid{grid-template-columns:1fr}.main{padding:20px}}
/* ---- login screen (demo role select) ---- */
#login{position:fixed;inset:0;z-index:1000;background:linear-gradient(135deg,#0E1526,#1A2336);display:flex;align-items:center;justify-content:center;font-family:Inter,system-ui,sans-serif;padding:20px}
.login-card{background:var(--card);border-radius:18px;padding:34px 34px 28px;width:400px;max-width:94vw;box-shadow:0 24px 70px rgba(0,0,0,.45)}
.login-card .brandmark{font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:1.2px;text-transform:uppercase;color:var(--acc);font-weight:600}
.login-card h1{font-family:'Space Grotesk',sans-serif;font-size:23px;margin:8px 0 4px;color:var(--ink)}
.login-card .sub{font-size:12.5px;color:var(--mut);margin:0 0 22px;line-height:1.5}
.login-card label{display:block;font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:.8px;text-transform:uppercase;color:var(--mut);margin:0 0 7px}
.login-card input{width:100%;padding:11px 13px;border:1px solid var(--line);border-radius:9px;font:14px Inter,sans-serif;background:var(--bg);color:var(--ink);outline:none;margin-bottom:20px}
.login-card input:focus{border-color:var(--acc)}
.role-opts{display:flex;gap:11px;margin-bottom:22px}
.role-opt{flex:1;border:1.5px solid var(--line);border-radius:12px;padding:15px 12px;cursor:pointer;text-align:center;transition:border-color .15s,background .15s}
.role-opt:hover{border-color:var(--acc)}
.role-opt.sel{border-color:var(--acc);background:var(--acc-soft)}
.role-opt .ic{font-size:24px;line-height:1}
.role-opt .rn{font-weight:700;font-size:14px;margin-top:8px;color:var(--ink)}
.role-opt .rd{font-size:10.5px;color:var(--mut);margin-top:4px;line-height:1.4}
.login-btn{width:100%;font:700 15px Inter,sans-serif;background:var(--acc);color:#fff;border:none;padding:13px;border-radius:10px;cursor:pointer}
.login-btn:disabled{opacity:.4;cursor:not-allowed}
.login-foot{font-size:11px;color:var(--mut);text-align:center;margin-top:16px;line-height:1.5}
.role-badge{margin:12px 12px 2px;padding:9px 12px;border-radius:9px;background:var(--rail-2);display:flex;align-items:center;justify-content:space-between;gap:8px}
.role-badge .rb-name{font-size:12.5px;font-weight:600;color:#E9EDF4}
.role-badge .rb-role{font-family:'JetBrains Mono',monospace;font-size:8.5px;letter-spacing:.7px;text-transform:uppercase;color:#7C8AA5;margin-top:2px}
.role-badge .signout{cursor:pointer;color:#8FA6E8;font-size:11px;font-weight:600;white-space:nowrap}
.role-badge .signout:hover{color:#fff}
/* ---- "why this decision" bullet list ---- */
.why-head{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.7px;text-transform:uppercase;color:var(--mut);margin:2px 0 4px}
.why-list{list-style:none;margin:2px 0 0;padding:0}
.why-list li{position:relative;padding:8px 0 8px 22px;font-size:13px;line-height:1.5;color:var(--ink);border-bottom:1px solid var(--line)}
.why-list li:last-child{border-bottom:none}
.why-list li::before{content:"";position:absolute;left:3px;top:14px;width:7px;height:7px;border-radius:50%;background:var(--acc)}
/* =================== NEO-BRUTALIST EDITORIAL THEME (redesign) =================== */
body{background:var(--bg);background-image:radial-gradient(var(--line) 1px,transparent 1px);background-size:22px 22px}
#app{max-width:1460px;box-shadow:none;border-left:2px solid var(--ink);border-right:2px solid var(--ink);background:var(--bg)}
h1,h2,.case-head h2,.hs-num,.g-num,.stat .sv,.ss-v,.login-card h1,.decision-detail h3{font-family:'Fraunces',Georgia,serif !important;letter-spacing:-.015em;font-weight:600}
.card,.stat,.headline-score,.explain,.login-card,.verdict-banner{border-radius:0 !important;border:2px solid var(--ink) !important;box-shadow:5px 5px 0 var(--ink) !important}
.card h3{color:var(--ink);border-bottom:2px solid var(--ink);padding-bottom:9px;margin-bottom:14px}
.doc-row,.sub-score,.drop-zone,.conflict-card,.unique-banner,.role-badge,.search-box,.form-grid input,.form-grid select,.fg-wide textarea,.legend-chip,.score-chip,.hs-class,.g-band,.band-chip,.stamp,.tab,.ai-btn,.score-btn,.login-btn,.overview-link,.status-chip,.wf-chip,.pagination button{border-radius:0 !important}
.doc-row,.sub-score{border:1.5px solid var(--ink) !important;box-shadow:none}
.stamp{box-shadow:4px 4px 0 var(--ink)}
.tab{border:1.5px solid var(--ink) !important;background:var(--card);color:var(--ink);text-transform:uppercase;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.5px}
.tab.active{background:var(--acc);color:#fff;border-color:var(--ink);box-shadow:3px 3px 0 var(--ink)}
.ai-btn,.score-btn,.login-btn{border:2px solid var(--ink) !important;box-shadow:3px 3px 0 var(--ink);font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.5px;font-weight:600}
.ai-btn:active,.score-btn:active,.login-btn:active{box-shadow:0 0 0 var(--ink);transform:translate(3px,3px)}
.rail{border-right:2px solid var(--ink)}
.rail-brand h1{font-family:'Fraunces',serif !important;color:#fff}
.overview-link{border:1.5px solid transparent}
.overview-link.active{background:var(--acc);color:#fff}
.headline-score{background:var(--card)}
.hs-class,.g-band,.score-chip,.band-chip{border:1.5px solid var(--ink)}
.verdict-banner{box-shadow:6px 6px 0 var(--ink) !important}
.stat .sv,.g-num,.hs-num{font-weight:700}
/* login extras */
.login-error{color:var(--bad);font-size:12px;font-weight:600;margin:-8px 0 12px;min-height:15px}
.login-card .login-foot .mono{font-family:'JetBrains Mono',monospace;color:var(--ink);font-weight:600}
/* =================== underwriter case-desk workflow =================== */
.status-chip,.wf-chip{display:inline-block;font-family:'JetBrains Mono',monospace;font-weight:600;text-transform:uppercase;letter-spacing:.4px;border:1.5px solid var(--ink)}
.status-chip{font-size:10px;padding:3px 8px}
.wf-chip{font-size:8px;padding:1px 4px;margin-left:6px;vertical-align:middle}
.wf-new{background:#E7DECB;color:#6E6553}
.wf-in_review{background:var(--acc-soft);color:var(--acc)}
.wf-info_requested{background:var(--warn-soft);color:var(--warn)}
.wf-referred{background:#DDE4F3;color:#2F49A8}
.wf-approved{background:var(--ok-soft);color:var(--ok)}
.wf-declined{background:var(--bad-soft);color:var(--bad)}
.desk-row{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--line);font-size:13px}
.desk-l{font-family:'JetBrains Mono',monospace;font-size:10px;letter-spacing:.6px;text-transform:uppercase;color:var(--mut)}
.desk-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.trail-row{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid var(--line);font-size:12.5px;align-items:baseline}
.trail-row:last-child{border-bottom:none}
.trail-when{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--mut);white-space:nowrap;min-width:98px}
.trail-what{flex:1;line-height:1.5}.trail-who{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--acc);white-space:nowrap}
.wf-filter{margin:4px 12px 8px;padding:8px 10px;width:calc(100% - 24px);border:1.5px solid rgba(255,255,255,.2);background:var(--rail-2);color:#fff;font:11px 'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.5px;outline:none}
/* nav spaces + auto-decision banners */
.nav-head{font-family:'JetBrains Mono',monospace;font-size:8.5px;letter-spacing:1.2px;text-transform:uppercase;color:#7C8AA5;padding:14px 16px 4px}
.overview-link{justify-content:space-between}
.overview-link>span{display:flex;align-items:center}
.nav-badge{background:var(--acc);color:#fff;font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:700;padding:1px 8px;border:1.5px solid var(--ink)}
.nav-count{font-family:'JetBrains Mono',monospace;font-size:10px;color:#7C8AA5}
.overview-link.active .nav-badge{background:#fff;color:var(--acc)}.overview-link.active .nav-count{color:#fff}
.auto-banner{border:2px solid var(--ink);padding:14px 16px;margin-bottom:14px;box-shadow:3px 3px 0 var(--ink)}
.auto-banner.ok{background:var(--ok-soft)}.auto-banner.bad{background:var(--bad-soft)}.auto-banner.warn{background:var(--warn-soft)}
.auto-banner .ab-word{font-family:'Fraunces',serif;font-weight:700;font-size:21px;letter-spacing:.4px}
.auto-banner.ok .ab-word{color:var(--ok)}.auto-banner.bad .ab-word{color:var(--bad)}.auto-banner.warn .ab-word{color:var(--warn)}
.auto-banner .ab-sub{font-size:12.5px;color:var(--ink);margin-top:6px;line-height:1.55}
.xt tr[onclick]:hover td{background:var(--acc-soft)}
/* =================== MEDIFLOW — DARK / INDIGO / POPPINS THEME =================== */
*{font-family:'Poppins',system-ui,sans-serif}
body{background:var(--bg) !important;background-image:none !important;color:var(--ink);font-family:'Poppins',sans-serif}
#app{max-width:1440px;margin:18px auto;min-height:calc(100vh - 36px);background:#0A0A0C !important;border:none !important;border-radius:30px !important;overflow:hidden;box-shadow:0 30px 90px rgba(0,0,0,.55)}
h1,h2,h3,.case-head h2,.hs-num,.g-num,.stat .sv,.ss-v,.login-card h1,.decision-detail h3,.rail-brand h1,.auto-banner .ab-word,.vb-word,.sl-word{font-family:'Poppins',sans-serif !important;letter-spacing:0;font-weight:700}
.case-head h2,.login-card h1{text-transform:none;letter-spacing:0;font-weight:700}
.card,.stat,.headline-score,.explain,.login-card{border:1px solid var(--line) !important;box-shadow:none !important;border-radius:22px !important;background:var(--card) !important;color:var(--ink)}
.card h3{color:var(--mut);border-bottom:none;padding-bottom:0;margin-bottom:14px;text-transform:none;letter-spacing:.2px;font-family:'Poppins',sans-serif !important;font-size:15px;font-weight:600}
.explain{background:var(--card) !important}.explain p{color:#C8C8D0}
.note,.g-note,.hs-lab,.case-meta,.field label,.factor-detail,.ss-l,.rail-sub,.ci-id,.dstatus{color:var(--mut) !important}
.doc-row,.sub-score,.drop-zone,.role-badge,.form-grid input,.form-grid select,.fg-wide textarea{border:1px solid var(--line) !important;border-radius:14px !important;box-shadow:none !important;background:#1C1C21 !important;color:var(--ink)}
.form-grid input::placeholder,.fg-wide textarea::placeholder{color:#6B6B76}
.conflict-card,.unique-banner{border-radius:14px !important;box-shadow:none !important}
.search-box{border:1px solid var(--line) !important;background:#1C1C21 !important;color:var(--ink) !important;border-radius:999px !important;padding-left:16px}
.search-box::placeholder{color:#6B6B76 !important}
.tab{border:none !important;background:#1C1C21 !important;color:var(--mut) !important;box-shadow:none !important;border-radius:999px !important;text-transform:none;font-family:'Poppins',sans-serif !important;font-size:13px;letter-spacing:0;font-weight:500;padding:8px 16px}
.tab.active{background:#fff !important;color:#0A0A0C !important}
.ai-btn,.score-btn,.login-btn{border:none !important;box-shadow:none !important;border-radius:999px !important;color:#fff !important;font-family:'Poppins',sans-serif !important;text-transform:none;letter-spacing:0;font-weight:600;font-size:12.5px;padding:9px 18px;background:#26262E}
.ai-btn:hover,.score-btn:hover,.login-btn:hover{filter:brightness(1.1)}
.ai-btn:active,.score-btn:active,.login-btn:active{transform:translateY(1px);filter:brightness(.92)}
.login-btn,.score-btn{background:var(--acc) !important;color:#fff !important}
.stamp{box-shadow:none !important;border-radius:14px !important;border-width:2px}
/* left rail (dark) */
.rail{border-right:1px solid var(--line) !important;background:var(--rail)}
.rail-brand{background:transparent !important;border-bottom:1px solid var(--line)}
.rail-brand h1{color:#fff !important;font-weight:700}.rail-brand p{color:#7C7C88 !important}
.role-badge{background:#1C1C21 !important;border:1px solid var(--line) !important;border-radius:14px}
.role-badge .rb-name{color:#fff}.role-badge .rb-role{color:var(--mut)}.role-badge .signout{color:var(--acc)}
.rail-sub{color:#7C7C88 !important}
.overview-link{border:none;border-radius:12px !important;color:#C3C3CC !important;margin:3px 12px}
.overview-link:hover{background:#1C1C21 !important}
.overview-link.active{background:var(--acc) !important;color:#fff !important}
.overview-link.active .nav-badge{background:#fff !important;color:var(--acc) !important;border:none !important}
.overview-link.active .nav-count{color:#fff !important}
.nav-head{color:#63636E !important}
.case-item{border-radius:14px !important}
.case-item:hover{background:#1C1C21 !important}
.case-item.active{background:#1C1C21 !important;outline:1.5px solid var(--acc) !important}
.ci-name{color:#fff !important}.doctag{color:var(--acc) !important}
.pagination{color:var(--mut) !important;border-top:1px solid var(--line)}
.pagination button{background:#1C1C21 !important;color:#fff !important;border:none !important;border-radius:999px}
.headline-score{background:#141417 !important;border:1px solid var(--line) !important;border-radius:20px}
.headline-score .hs-lab{color:var(--mut) !important}
.hs-class,.g-band,.score-chip,.band-chip,.status-chip,.wf-chip,.pri-chip,.sla-chip{border:none !important;border-radius:999px !important;font-weight:600}
.score-chip{background:#1C1C21}
.verdict-banner{box-shadow:none !important;border-radius:18px !important;border-width:1px !important}
.auto-banner{box-shadow:none !important;border:1px solid var(--line) !important;border-radius:18px !important}
.auto-banner .ab-word{font-family:'Poppins',sans-serif !important}
/* status chips on dark (soft tints) */
.status-chip,.wf-chip{background:#1C1C21 !important}
.wf-new{background:#232329 !important;color:#9A9AA5 !important}
.wf-in_review{background:var(--acc-soft) !important;color:#A9A7FF !important}
.wf-info_requested{background:var(--warn-soft) !important;color:var(--warn) !important}
.wf-referred{background:rgba(106,103,247,.16) !important;color:#A9A7FF !important}
.wf-approved{background:var(--ok-soft) !important;color:var(--ok) !important}
.wf-declined{background:var(--bad-soft) !important;color:#FF8A8C !important}
.nav-badge{background:var(--acc) !important;color:#fff !important;border:none !important;border-radius:999px}
.sc-ok{background:var(--ok-soft) !important;color:var(--ok) !important}
.sc-warn{background:var(--warn-soft) !important;color:var(--warn) !important}
.sc-bad{background:var(--bad-soft) !important;color:#FF8A8C !important}
/* priority + SLA + tier (pills, Poppins) */
.pri-chip{display:inline-block;font-family:'Poppins',sans-serif;font-size:9.5px;font-weight:700;letter-spacing:.3px;padding:3px 9px;text-transform:uppercase;color:#fff}
.sla-chip{display:inline-block;font-family:'Poppins',sans-serif;font-size:10px;font-weight:600;letter-spacing:0;padding:3px 9px;white-space:nowrap}
.sla-ok{background:#232329;color:#9A9AA5}
.sla-warn{background:var(--warn-soft);color:var(--warn)}
.sla-breach{background:var(--bad);color:#fff}
.tier-tag{font-family:'Poppins',sans-serif;font-size:10px;letter-spacing:0;text-transform:none;color:#8A8A95}
.ci-meta{display:flex;gap:6px;align-items:center;margin-top:5px;flex-wrap:wrap}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:999px;overflow:hidden;background:#1C1C21;padding:3px}
.seg button{font-family:'Poppins',sans-serif;font-size:11px;font-weight:600;text-transform:none;letter-spacing:0;padding:6px 15px;border:none;background:transparent;color:var(--mut);cursor:pointer;border-radius:999px}
.seg button.on{background:#fff;color:#0A0A0C}
.rank-num{font-family:'Poppins',sans-serif;font-size:12px;font-weight:700;color:var(--mut);min-width:20px;text-align:right}
/* score band scale */
.scale-wrap{margin:14px 0 4px}
.scale-ticks{position:relative;height:20px;font-family:'Poppins',sans-serif;font-weight:700;font-size:14px;color:var(--ink)}
.scale-ticks span{position:absolute;transform:translateX(-50%)}
.scale-ticks span:first-child{transform:none}.scale-ticks span:last-child{transform:translateX(-100%)}
.scale-track{display:flex;height:30px;border:none;border-radius:999px;overflow:hidden}
.scale-seg{height:100%}.scale-seg+.scale-seg{border-left:2px solid #0A0A0C}
.scale-labels{display:flex;margin-top:12px}
.slab{text-align:center;padding:0 4px}
.sl-word{font-family:'Poppins',sans-serif;font-weight:700;letter-spacing:0;font-size:15px}
.sl-sub{font-size:11px;color:var(--mut);font-style:normal;margin-top:2px;line-height:1.3}
.override-note{display:flex;gap:12px;align-items:flex-start;background:var(--warn-soft);border:none;border-radius:16px;padding:14px 16px;margin-top:18px}
.override-note .on-ic{font-size:18px;color:var(--warn);flex-shrink:0}
.override-note b{color:var(--warn)}
/* login (dark indigo) */
#login{background:linear-gradient(160deg,#3B3A78,#0A0A0C) !important}
.login-card input{background:#1C1C21 !important;color:#fff !important;border:1px solid var(--line) !important;border-radius:12px !important}
.login-card .sub,.login-foot{color:var(--mut)}.brandmark{color:var(--acc)}
.hist-track,.coef-track{background:#1C1C21 !important}
.legend-chip{border-radius:12px}
.stat{border-radius:18px !important}
/* =================== PRD v2 — exec / admin / evidence / requirements =================== */
.mix-bar{display:flex;height:34px;border-radius:999px;overflow:hidden;margin:6px 0 4px}
.mix-seg{display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#0A0A0C;white-space:nowrap}
.appetite{display:flex;gap:20px;align-items:center;flex-wrap:wrap;margin-top:4px}
.appetite .lever{flex:1;min-width:200px;background:#1C1C21;border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.appetite .lever b{font-size:13px}
.gauge-line{height:10px;background:#1C1C21;border-radius:999px;overflow:hidden;margin:8px 0 4px}
.gauge-line .fill{height:100%;border-radius:999px}
.feed-row{display:flex;gap:14px;align-items:baseline;padding:11px 0;border-bottom:1px solid var(--line);font-size:13px}
.feed-row:last-child{border-bottom:none}
.feed-when{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--mut);white-space:nowrap;min-width:104px}
.feed-what{flex:1;line-height:1.5}.feed-who{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--acc);white-space:nowrap}
.ev-form{border-top:1px solid var(--line);margin-top:14px;padding-top:14px}
.ev-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
.ev-opt{display:flex;gap:8px;align-items:baseline;background:#1C1C21;border:1px solid var(--line);border-radius:12px;padding:10px 12px;font-size:12.5px;cursor:pointer}
.ev-opt input{margin-top:2px}
.ev-rat{width:100%;padding:10px 12px;border:1px solid var(--line);border-radius:12px;background:#1C1C21;color:var(--ink);font:13px 'Poppins',sans-serif;outline:none;margin-bottom:10px}
.ev-flags{background:var(--warn-soft);border-radius:12px;padding:12px 14px;margin-bottom:10px;font-size:12.5px}
.ev-flags ul{margin:6px 0 0;padding-left:18px}.ev-flags li{margin:3px 0}
.imm-note{display:flex;gap:10px;align-items:flex-start;background:#1C1C21;border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-bottom:14px;font-size:12.5px;color:var(--mut)}
.imm-note b{color:var(--ink)}
.prov{font-family:'JetBrains Mono',monospace;font-size:9px;letter-spacing:.4px;text-transform:uppercase;color:#6B6B76;margin-top:3px}
.doc-view{background:#141417;border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:-4px 0 12px}
.doc-row.open .dstatus{color:var(--acc)}
@media(max-width:900px){.ev-grid{grid-template-columns:1fr}}
/* =================== LIGHT MODE (toggle) =================== */
#themeToggle{position:fixed;top:14px;right:16px;z-index:2000;width:40px;height:40px;border-radius:50%;border:1px solid var(--line);background:var(--card);color:var(--ink);font-size:17px;line-height:1;cursor:pointer;box-shadow:0 6px 18px rgba(20,20,40,.28);display:flex;align-items:center;justify-content:center}
#themeToggle:hover{filter:brightness(1.08)}
:root[data-theme="light"]{
 --bg:#E7E8F0;--card:#FFFFFF;--ink:#1B1B26;--mut:#5B5C69;--line:#E4E6EE;
 --rail:#F5F6F9;--rail-2:#ECEEF3;
 --acc:#5754F0;--acc-soft:rgba(87,84,240,.12);
 --ok:#1B9D5E;--ok-soft:rgba(27,157,94,.14);
 --warn:#B9781A;--warn-soft:rgba(200,130,24,.16);
 --bad:#D0454A;--bad-soft:rgba(208,69,74,.12)}
:root[data-theme="light"] body{background:var(--bg) !important;color:var(--ink)}
:root[data-theme="light"] #app{background:#FFFFFF !important;box-shadow:0 18px 60px rgba(30,32,60,.18)}
:root[data-theme="light"] .rail-brand h1{color:var(--ink) !important}
:root[data-theme="light"] .rail-brand p,:root[data-theme="light"] .rail-sub,:root[data-theme="light"] .nav-head{color:var(--mut) !important}
:root[data-theme="light"] .role-badge{background:var(--rail-2) !important}
:root[data-theme="light"] .role-badge .rb-name{color:var(--ink)}
:root[data-theme="light"] .overview-link{color:#3B3B47 !important}
:root[data-theme="light"] .overview-link:hover{background:var(--rail-2) !important}
:root[data-theme="light"] .ci-name{color:var(--ink) !important}
:root[data-theme="light"] .case-item:hover,:root[data-theme="light"] .case-item.active{background:var(--rail-2) !important}
:root[data-theme="light"] .pagination button{background:var(--rail-2) !important;color:var(--ink) !important}
:root[data-theme="light"] .headline-score{background:#F7F8FC !important}
:root[data-theme="light"] .doc-row,:root[data-theme="light"] .sub-score,:root[data-theme="light"] .drop-zone,:root[data-theme="light"] .form-grid input,:root[data-theme="light"] .form-grid select,:root[data-theme="light"] .fg-wide textarea{background:#F3F4F8 !important;color:var(--ink)}
:root[data-theme="light"] .search-box{background:#F3F4F8 !important;color:var(--ink) !important}
:root[data-theme="light"] .tab{background:#EDEFF4 !important}
:root[data-theme="light"] .tab.active{background:var(--acc) !important;color:#fff !important}
:root[data-theme="light"] .ai-btn,:root[data-theme="light"] .score-btn,:root[data-theme="light"] .login-btn{background:#EAECF2;color:var(--ink) !important}
:root[data-theme="light"] .login-btn,:root[data-theme="light"] .score-btn{background:var(--acc) !important;color:#fff !important}
:root[data-theme="light"] .score-chip{background:#EEF0F4}
:root[data-theme="light"] .sc-bad{background:var(--bad-soft) !important;color:var(--bad) !important}
:root[data-theme="light"] .status-chip,:root[data-theme="light"] .wf-chip{background:#EEF0F4 !important}
:root[data-theme="light"] .wf-new{background:#E9EAEF !important;color:#5B5C69 !important}
:root[data-theme="light"] .wf-in_review,:root[data-theme="light"] .wf-referred{color:var(--acc) !important}
:root[data-theme="light"] .wf-declined{color:var(--bad) !important}
:root[data-theme="light"] .sla-ok{background:#E9EAEF !important;color:#5B5C69 !important}
:root[data-theme="light"] .seg{background:#EEF0F4}
:root[data-theme="light"] .seg button.on{background:var(--acc);color:#fff}
:root[data-theme="light"] .hist-track,:root[data-theme="light"] .coef-track{background:#EEF0F4 !important}
:root[data-theme="light"] .appetite .lever,:root[data-theme="light"] .gauge-line,:root[data-theme="light"] .ev-opt,:root[data-theme="light"] .ev-rat,:root[data-theme="light"] .imm-note,:root[data-theme="light"] .role-badge{background:#F3F4F8 !important}
:root[data-theme="light"] .doc-view{background:#F7F8FC}
:root[data-theme="light"] .explain p{color:#33343E}
:root[data-theme="light"] .scale-seg+.scale-seg{border-left-color:#fff}
:root[data-theme="light"] #login{background:linear-gradient(160deg,#DDE0EC,#F5F6F9) !important}
:root[data-theme="light"] .login-card input{background:#F3F4F8 !important;color:var(--ink) !important}
</style>
<button id="themeToggle" onclick="toggleTheme()" title="Toggle light / dark mode" aria-label="Toggle light or dark mode">🌙</button>
<div id="login">
 <div class="login-card">
  <div class="brandmark">◆ UNDERWRITING COPILOT</div>
  <h1>Sign in to the workbench</h1>
  <p class="sub">Secure access. Underwriters work their assigned case queue; managers get portfolio oversight and the fairness view.</p>
  <label>Username</label>
  <input id="loginUser" placeholder="username" autocomplete="off" oninput="loginErr('')" onkeydown="if(event.key==='Enter')doLogin()">
  <label>Password</label>
  <input id="loginPass" type="password" placeholder="password" onkeydown="if(event.key==='Enter')doLogin()">
  <div id="loginError" class="login-error"></div>
  <button class="login-btn" id="loginBtn" onclick="doLogin()">Sign in →</button>
  <div class="login-foot"><b>Demo accounts</b><br>Senior underwriter — <span class="mono">mrivera / senior</span><br>Mid-tier underwriter — <span class="mono">ewong / review</span><br>New analyst — <span class="mono">dpark / analyst</span><br>Manager — <span class="mono">nsethi / oversight</span><br>Executive (CUO) — <span class="mono">mvale / executive</span><br>Operations admin — <span class="mono">panand / admin</span></div>
 </div>
</div>
<div id="app">
 <div class="rail">
  <div class="rail-brand"><h1>Underwriting Copilot</h1><p>Extraction · Conflict Screen · Risk Score · Decision</p></div>
  <div class="role-badge" id="roleBadge"></div>
  <div id="navLinks"></div>
  <div class="rail-sub"><span id="listTitle">Review Queue</span><span id="queueCount"></span></div>
  <input class="search-box" id="searchBox" placeholder="Search name or ID…" oninput="onSearch(this.value)">
  <div class="case-list" id="caseList" onscroll="railScroll=this.scrollTop"></div>
  <div class="pagination"><button id="prevBtn" onclick="pg(-1)">‹ Prev</button><span id="pageLabel"></span><button id="nextBtn" onclick="pg(1)">Next ›</button></div>
 </div>
 <div class="main"><div id="mainContent"></div></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
<script>
const DATA = /*__DATA__*/;
const M = DATA.metrics, CASES = DATA.cases;
/* ---------- light / dark theme toggle ---------- */
function applyThemeIcon(){var b=document.getElementById('themeToggle');if(b)b.textContent=document.documentElement.getAttribute('data-theme')==='light'?'☀️':'🌙';}
function toggleTheme(){var root=document.documentElement;var light=root.getAttribute('data-theme')!=='light';
 root.setAttribute('data-theme',light?'light':'dark');
 try{localStorage.setItem('uw_theme',light?'light':'dark');}catch(e){}applyThemeIcon();}
(function(){try{if(localStorage.getItem('uw_theme')==='light')document.documentElement.setAttribute('data-theme','light');}catch(e){}applyThemeIcon();})();
// Fixed decision bands (product owner): 0–50 APPROVE · 51–89 MANUAL REVIEW · 90–100 DECLINE.
// A_LINE=51 → approve is score<51 (0–50); D_LINE=90 → review is 51–89, decline is ≥90.
// The pipeline's STP-optimised export is intentionally ignored so the traffic-light lines
// stay on these round numbers; recomputeVerdicts() re-scores every case against them.
const A_LINE=51, D_LINE=90;
const VM={green:["APPROVE","ok"],yellow:["MANUAL REVIEW","warn"],red:["DECLINE","bad"]};
const AFF={pass:["AFFORDABLE","ok"],strain:["STRAINED","warn"],fail:["NOT JUSTIFIED","bad"]};
const bandOf=s=>s<A_LINE?"green":s<D_LINE?"yellow":"red";
const band=s=>s<=25?["Low","var(--ok)"]:s<A_LINE?["Moderate","var(--ok)"]:s<D_LINE?["Elevated","var(--warn)"]:["High","var(--bad)"];
// thresholds moved to 50/90 — recompute every case's verdict client-side so the whole app is consistent (no pipeline rerun)
const MISREP=new Set(['smoker_nondisclosure','dob_mismatch']);
function recomputeVerdicts(){
 CASES.forEach(c=>{
  const comp=c.risk_score,conf=c.conflicts||[];
  const majors=conf.filter(k=>k.severity==='major');
  const misrep=majors.filter(k=>MISREP.has(k.type));
  const reasons=[];let verdict,decision,rate;
  // Score-driven bands: the composite score alone sets the decision. Material
  // misrepresentation is the one hard override (fraud → decline regardless of
  // score). Conflicts, affordability and disclosed circumstances are surfaced
  // as flags for the reviewer but no longer change the band.
  if(misrep.length){verdict='red';decision='DECLINE';rate='Declined — Material Misrepresentation';
    reasons.push('Application materially contradicts medical/identity evidence: '+misrep.map(k=>k.type.replace(/_/g,' ')).join('; '));}
  else if(comp>=D_LINE){verdict='red';decision='DECLINE';rate='Declined — Risk Exceeds Appetite';
    reasons.push(`Composite risk score ${comp}/100 is at or above the ${D_LINE}-point decline line`);}
  else if(comp>=A_LINE){verdict='yellow';decision='MANUAL REVIEW';rate='Referred — Senior Underwriter Review';
    reasons.push(`Composite score ${comp} sits in the ${A_LINE}–${D_LINE-1} manual-review band`);}
  else{verdict='green';decision='APPROVE';rate=comp<=25?'Preferred Rate Class':'Standard Rate Class';
    reasons.push(`Composite score ${comp} is below the ${A_LINE}-point approval line`);}
  if(verdict!=='red'){   // informational flags — do not change the band
    if(majors.length)reasons.push(`Flag: ${majors.length} major data conflict(s) for the reviewer — `+majors.map(k=>k.type.replace(/_/g,' ')).join('; '));
    if(c.unique)reasons.push('Flag: applicant disclosed unique circumstances — '+c.unique);
    if(c.afford&&c.afford.verdict==='fail')reasons.push('Flag: affordability screen refers this case to financial underwriting');
    else if(c.afford&&c.afford.verdict==='strain')reasons.push('Affordability is strained but within tolerance');}
  c.verdict=verdict;c.decision=decision;c.rate_class=rate;c.reasons=reasons;c.referred=verdict==='yellow';
  if(c.ai_summary){ // keep the baked narrative consistent with the recomputed verdict
   const bandTxt=verdict==='green'?'green approval band':verdict==='yellow'?'yellow manual-review band':'red decline band';
   c.ai_summary=c.ai_summary
    .replace(/placing the case in the (?:green approval|yellow manual-review|red decline) band/,'placing the case in the '+bandTxt)
    .replace(/System decision: [\s\S]*$/,`System decision: ${decision} — ${rate} (${reasons.join('; ')}).`);
  }
 });
}
recomputeVerdicts();
// §3.6 — no display label may assert a risk judgement. Neutralise the legacy
// "Notable" family-history value baked into portfolio.json (engine.py is fixed
// at source; this keeps the already-exported data clean without a pipeline rerun).
CASES.forEach(c=>{(c.rule_factors||[]).forEach(f=>{if(f[1]==='Notable')f[1]='Family history disclosed';});});
let filtered=CASES.slice(),page=0,activeId=CASES[0].id,view="case",activeTab=4;const PAGE=20;
let railScroll=0;                              // preserved list scroll (§3.3 back-button restores context)
let prev={view:'space',space:'review'};        // where "back" returns to
let caseNav=[];                                // ordered case IDs of the list a case was opened from — Next/Prev walks this
const fmt$=n=>n==null?"—":"$"+Math.round(n).toLocaleString();
/* ---------- workbench login (credential auth) ---------- */
const ACCOUNTS={
 dpark:{pw:"analyst",name:"Dana Park",role:"underwriter",tier:"analyst"},
 ewong:{pw:"review",name:"Erin Wong",role:"underwriter",tier:"mid"},
 mrivera:{pw:"senior",name:"Marcus Rivera",role:"underwriter",tier:"senior"},
 nsethi:{pw:"oversight",name:"Nadia Sethi",role:"manager"},
 mvale:{pw:"executive",name:"Marcus Vale",role:"executive"},      // Chief Underwriting Officer (fictional persona)
 panand:{pw:"admin",name:"Priya Anand",role:"admin"}              // Operations administrator (fictional persona)
};
// the three underwriters cases get routed to, by experience tier
const UWS={senior:{uid:"mrivera",name:"Marcus Rivera",label:"Senior"},
          mid:{uid:"ewong",name:"Erin Wong",label:"Mid-tier"},
          analyst:{uid:"dpark",name:"Dana Park",label:"New Analyst"}};
let CURRENT_ROLE=null, CURRENT_USER="", CURRENT_UID="", CURRENT_TIER="";
function loginErr(m){const e=document.getElementById('loginError');if(e)e.textContent=m;}
function doLogin(){
 const u=(document.getElementById('loginUser').value||'').trim().toLowerCase();
 const p=document.getElementById('loginPass').value||'';
 const acct=ACCOUNTS[u];
 if(!acct||acct.pw!==p){loginErr('Incorrect username or password.');return;}
 CURRENT_UID=u;CURRENT_USER=acct.name;CURRENT_ROLE=acct.role;CURRENT_TIER=acct.tier||"";
 seedReview();
 document.getElementById('login').style.display='none';
 applyRole();
 if(CURRENT_ROLE==='manager'){queueScope='team';view='manager';}
 else if(CURRENT_ROLE==='executive'){queueScope='team';view='executive';}
 else if(CURRENT_ROLE==='admin'){queueScope='team';view='admin';}
 else{queueScope='mine';space='review';view='space';}
 render();}
function applyRole(){
 // nav (buildNav) shows the oversight links only for managers
 const badge=document.getElementById('roleBadge');
 const sub=CURRENT_ROLE==='underwriter'?((UWS[CURRENT_TIER]||{}).label||'Underwriter')
   :CURRENT_ROLE==='executive'?'Chief Underwriting Officer'
   :CURRENT_ROLE==='admin'?'Operations Administrator':'Manager';
 badge.innerHTML=`<div><div class="rb-name">${CURRENT_USER}</div><div class="rb-role">${sub}</div></div><span class="signout" onclick="signOut()">Sign out</span>`;}
function signOut(){CURRENT_ROLE=null;CURRENT_USER="";CURRENT_UID="";
 document.getElementById('loginUser').value='';document.getElementById('loginPass').value='';loginErr('');
 document.getElementById('login').style.display='flex';}
/* ---------- underwriter case desk: status, assignment, notes, decision log (localStorage) ---------- */
const WF_STATUSES=[["new","New"],["in_review","In Review"],["info_requested","Info Requested"],["referred","Referred"],["approved","Approved"],["declined","Declined"]];
const WF_LABEL=Object.fromEntries(WF_STATUSES);
let wfFilterVal="";
const nowStr=()=>new Date().toISOString().slice(0,16).replace('T',' ');
function wfAll(){try{return JSON.parse(localStorage.getItem('uw_workbench')||'{}');}catch(e){return {};}}
function wfGet(id){const a=wfAll();return a[id]||{status:'new',assignee:null,notes:[],history:[],decision:null};}
function wfSave(id,st){const a=wfAll();a[id]=st;localStorage.setItem('uw_workbench',JSON.stringify(a));}
function wfChip(id){const s=wfGet(id).status;return `<span class="wf-chip wf-${s}">${WF_LABEL[s]}</span>`;}
/* ---------- priority ranking, tier assignment, SLA timer ---------- */
let queueScope='mine';   // 'mine' = cases assigned to me · 'team' = all
function idHash(id){let h=2166136261;for(let i=0;i<id.length;i++){h^=id.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;}
function ageHours(c){const st=wfGet(c.id);const r=(st.receivedAt!=null)?st.receivedAt:(Date.now()-(idHash(c.id)%17)*3600000);return (Date.now()-r)/3600000;}
function priorityScore(c){
 // PRD §3.1.1 — queue order is a composite of coverage and time in queue only.
 // Risk score is deliberately EXCLUDED: ordering by the model's opinion would
 // invert the human-oversight relationship and bury large, ageing cases that
 // happen to score mid-band. Score informs the underwriter; it doesn't decide
 // who gets looked at first.
 const cov=Math.min((c.coverage||0)/1000000,1);   // exposure, normalised, capped at $1M
 const age=Math.min(ageHours(c)/16,1);            // ageing (demo clock spans ~0–16h)
 return Math.round(100*(0.60*cov+0.40*age));
}
function priorityBand(p){return p>=68?['CRITICAL','var(--bad)']:p>=46?['HIGH','var(--warn)']:p>=26?['MEDIUM','var(--acc)']:['LOW','var(--mut)'];}
function assignTier(c){
 // Authority-based routing (PRD §4.5): tier follows face amount and conflict
 // load, NOT the priority score — a junior analyst never gets a high-coverage case.
 const majors=(c.conflicts||[]).filter(k=>k.severity==='major').length;const cov=c.coverage||0;
 if(cov>=750000||majors>=1)return 'senior';   // high exposure / hard conflicts → experienced
 if(cov>=250000)return 'mid';
 return 'analyst';                              // ≤ $250k, clean → new analyst
}
function seedReview(){
 // once per case: stamp a clock-start and route to an underwriter by experience tier
 const all=wfAll();let changed=false;
 CASES.forEach(c=>{if(c.verdict!=='yellow')return;
   const st=all[c.id]||{status:'new',assignee:null,notes:[],history:[],decision:null};
   if(st.receivedAt==null){st.receivedAt=Date.now()-(idHash(c.id)%17)*3600000;changed=true;}
   if(!st.assigneeUid){const t=assignTier(c);const uw=UWS[t];st.assigneeUid=uw.uid;st.assignee=uw.name;st.tier=t;
     if(st.status==='new')st.status='in_review';changed=true;}
   all[c.id]=st;});
 if(changed)localStorage.setItem('uw_workbench',JSON.stringify(all));
}
function fmtAge(h){const H=Math.floor(h);const M=Math.floor((h-H)*60);return H+'h '+String(M).padStart(2,'0')+'m';}
function slaChip(c){const h=ageHours(c);const cls=h>=8?'sla-breach':h>=6?'sla-warn':'sla-ok';
 return `<span class="sla-chip ${cls}">${h>=8?'⚠ SLA · ':''}${fmtAge(h)}</span>`;}
function tierTag(st){const t=UWS[st.tier];return t?`<span class="tier-tag">${st.assignee} · ${t.label}</span>`:'';}
/* ---------- PRD v2 additions: AI recommendation, requirements grid, risk drivers, back-nav ---------- */
function aiRecChip(c){
 // AI RECOMMENDATION column (§3.1): band + score together, never band alone.
 const sc=c.verdict==='red'?'sc-bad':c.verdict==='yellow'?'sc-warn':'sc-ok';
 return `<span class="score-chip ${sc}" style="white-space:nowrap">${c.decision} · ${c.risk_score}</span>`;
}
function requirementsFor(c){
 // Simplified age × amount A&A grid from the meeting notes (§6.1) — which
 // evidence a case of this age/face amount typically requires. Demo-grade,
 // versionable later into a real rule table.
 const a=c.age||0, amt=c.coverage||0, r=[];
 if(a>=50||amt>=250000){r.push('Paramed exam');r.push('Blood profile');}
 if(a>=50&&amt>=1000000)r.push('EKG');
 if(amt>=1000000||a>=66)r.push('APS');
 if(a>=61&&amt>=1000000)r.push('Cognitive assessment');
 return r;
}
function reqOutstandingList(c){
 // required evidence minus what the packet already satisfies (short labels)
 const req=requirementsFor(c);
 const satisfied=c.has_docs?new Set(['Paramed exam','Blood profile']):new Set();
 const short={'Paramed exam':'Exam','Blood profile':'Labs','EKG':'EKG','APS':'APS','Cognitive assessment':'Cognitive'};
 return req.filter(x=>!satisfied.has(x)).map(x=>short[x]||x);
}
function reqOutstanding(c){
 // REQUIREMENTS OUTSTANDING column (§3.1): blocked cases don't read as underwriter delay.
 const out=reqOutstandingList(c);
 if(!out.length)return '<span class="tier-tag">— none pending</span>';
 return `<span class="sla-chip sla-warn" title="${out.join(' · ')}">${out.join(' · ')}</span>`;
}
function caseRecommendation(c){
 // The AI's suggested next step for a manual-review case — an actionable
 // recommendation, not just the band (every queue case is "manual review").
 const out=reqOutstandingList(c);
 if(c.afford&&c.afford.verdict==='fail')return ['Refer — financial underwriting','affordability fails'];
 if((c.conflicts||[]).some(k=>k.severity==='major'))return ['Resolve conflict first','major document conflict'];
 if(out.length)return ['Order '+out[0],'A&A requirement outstanding'];
 if(c.unique)return ['Whole-person review','unique circumstances disclosed'];
 if(c.risk_score<=A_LINE+8)return ['Lean approve','near the approval line'];
 if(c.risk_score>=D_LINE-8)return ['Lean decline','near the decline line'];
 return ['Manual review','mid-band score'];
}
function aiRecoCol(c){const r=caseRecommendation(c);
 return `<div style="font-weight:600;font-size:12.5px;color:var(--ink)">${r[0]}</div><div style="font-size:10.5px;color:var(--mut)">${r[1]} · score ${c.risk_score}</div>`;}
function requirementsCardHTML(c){
 // The requirement set that applied, satisfied vs outstanding (§6.1).
 const req=requirementsFor(c);
 const satisfied=c.has_docs?new Set(['Paramed exam','Blood profile']):new Set();
 if(!req.length)return `<div class="card"><h3>Requirements — Age × Amount grid</h3><div class="note" style="margin:0">No standard evidence is triggered for a ${c.age}-year-old at ${fmt$(c.coverage)} of cover under the current A&amp;A grid.</div></div>`;
 const rows=req.map(r=>{const ok=satisfied.has(r);
   return `<div class="doc-row"><div class="dot ${ok?'':'miss'}"></div><div class="dname">${r}</div><div class="dstatus" style="color:${ok?'var(--ok)':'var(--warn)'}">${ok?'In packet ✓':'Outstanding'}</div></div>`;}).join('');
 return `<div class="card"><h3>Requirements — Age &times; Amount grid</h3>${rows}
   <div class="note">The requirement set that applies to a <b>${c.age}</b>-year-old requesting <b>${fmt$(c.coverage)}</b>, from a simplified version of the meeting's age &times; amount grid. Outstanding items are ordered from the Decision tab with a rationale and an AI pre-check; grid-triggered orders are distinguished from discretionary “for cause” orders in the record.</div></div>`;
}
function topDriversHTML(c){
 // Top-3 risk drivers at the top of the case file (§4.2), generated from the
 // rule engine's factor weights — never hand-authored — with clean signals
 // listed so the explanation isn't one-sided.
 if(!c.rule_factors)return '';
 const drivers=c.rule_factors.filter(f=>f[2]>0).sort((a,b)=>b[2]-a[2]).slice(0,3);
 const clean=c.rule_factors.filter(f=>f[2]===0).slice(0,3);
 const dr=drivers.map((f,i)=>`<div class="factor-row"><div><div class="factor-label">${i+1}. ${f[0]}</div><div class="factor-detail">${f[1]}</div></div><div class="factor-pts" style="color:var(--warn)">+${f[2]}</div></div>`).join('');
 const off=clean.length?`<div class="note" style="margin-top:10px"><b>Offsetting / clean signals:</b> ${clean.map(f=>f[0].toLowerCase()+' ('+f[1]+')').join(' · ')}</div>`:'';
 return `<div class="card"><h3>Top drivers of this score</h3>${drivers.length?dr:'<div class="note" style="margin:0">No positive risk contributors — every rule factor is clean.</div>'}${off}
  <div class="note">The three largest positive contributors to this applicant's composite score, straight from the rule engine's documented factor weights. Full breakdown on the Risk Score tab.</div></div>`;
}
function backLabel(){if(prev.view==='manager')return 'Manager Overview';if(prev.view==='overview')return 'Portfolio & Model Card';return SPACE_LABEL[prev.space]||'Queue';}
function goBack(){view=prev.view;if(prev.space)space=prev.space;render();}
function wfClaim(id){const st=wfGet(id);st.assignee=CURRENT_USER;if(st.status==='new')st.status='in_review';
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:'Claimed case → In Review'});wfSave(id,st);render();}
function wfSetStatus(id,s){const st=wfGet(id);st.status=s;
 st.history.push({by:CURRENT_USER||'system',role:CURRENT_ROLE||'',at:nowStr(),action:'Status set → '+WF_LABEL[s]});wfSave(id,st);render();}
function wfNote(id){const t=(prompt('Add a case note (written to the audit trail):')||'').trim();if(!t)return;
 const st=wfGet(id);st.notes.push({by:CURRENT_USER||'?',at:nowStr(),text:t});
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:'Note added'});wfSave(id,st);render();}
function wfRequestInfo(id){const t=(prompt('What information is outstanding? (NIGO — sent back for completion):')||'').trim();if(!t)return;
 const st=wfGet(id);st.status='info_requested';
 st.notes.push({by:CURRENT_USER||'?',at:nowStr(),text:'INFO REQUESTED: '+t});
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:'Requested info (NIGO) — “'+t+'”'});wfSave(id,st);render();}
function wfDecide(id,kind){
 const labels={approve:'APPROVED',decline:'DECLINED'};
 const rationale=(prompt('Rationale for '+labels[kind]+' — required (logged to the case history):')||'').trim();
 if(!rationale){alert('A rationale is required to record a decision.');return;}
 const st=wfGet(id);st.status=kind==='approve'?'approved':'declined';
 st.decision={action:labels[kind],by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),rationale:rationale};
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:labels[kind]+' — “'+rationale+'”'});
 wfSave(id,st);
 // the human call also feeds the model-training override store (+ manager counts)
 const ov=getOverrides();ov[id]={decision:labels[kind],label:kind==='decline'?1:0,reason:rationale,at:st.decision.at};
 localStorage.setItem('uw_overrides',JSON.stringify(ov));
 render();}
function wfPull(id){const st=wfGet(id);st.pulled=true;st.status='in_review';
 st.assignee=CURRENT_USER;st.assigneeUid=CURRENT_UID;st.tier=CURRENT_TIER;st.receivedAt=Date.now();
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:'Pulled auto-decision into manual review'});
 wfSave(id,st);space='review';render();}
function wfReassign(id){const st=wfGet(id);st.assigneeUid=CURRENT_UID;st.assignee=CURRENT_USER;st.tier=CURRENT_TIER;
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:'Reassigned to '+CURRENT_USER});wfSave(id,st);render();}
function wfReopen(id){const st=wfGet(id);st.decision=null;st.status='in_review';
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:'Reopened for review'});wfSave(id,st);
 const ov=getOverrides();delete ov[id];localStorage.setItem('uw_overrides',JSON.stringify(ov));space='review';render();}
/* ---------- case spaces: manual-review queue vs auto-decisioned record ---------- */
const SPACES=[
 ["review","Review Queue","▣","Cases the system flagged for a human. These are the only cases you action."],
 ["completed","Completed","✓","Manual-review cases you've approved or declined."],
 ["auto_approved","Auto-Approved","⤴","Straight-through approvals — decided automatically, kept as a record."],
 ["auto_declined","Auto-Declined","⤵","Straight-through declines — decided automatically, kept as a record."]];
const SPACE_LABEL=Object.fromEntries(SPACES.map(s=>[s[0],s[1]]));
let space='review';
function bucketOf(c){const st=wfGet(c.id);
 if(c.verdict==='yellow'||st.pulled)return st.decision?'completed':'review';
 return c.verdict==='green'?'auto_approved':'auto_declined';}
function spaceCases(sp){return CASES.filter(c=>bucketOf(c)===sp);}
function currentList(){let l=spaceCases(space);
 if(space==='review'){
  if(CURRENT_ROLE==='underwriter'&&queueScope==='mine')l=l.filter(c=>wfGet(c.id).assigneeUid===CURRENT_UID);
  l=l.slice().sort((a,b)=>priorityScore(b)-priorityScore(a));   // most important first
 }
 if(searchQ)l=l.filter(c=>c.name.toLowerCase().includes(searchQ)||c.id.toLowerCase().includes(searchQ));return l;}
function setScope(s){queueScope=s;page=0;render();}
function trailHTML(st){return st.history.length?st.history.slice().reverse().map(h=>`<div class="trail-row"><span class="trail-when">${h.at}</span><span class="trail-what">${h.action}</span><span class="trail-who">${h.by||''}</span></div>`).join(''):'<div class="note" style="margin:0">No activity yet.</div>';}
function caseDeskHTML(c){
 const st=wfGet(c.id);const isUW=CURRENT_ROLE==='underwriter';
 const auto=(c.verdict!=='yellow')&&!st.pulled;
 const resolved=!!st.decision;
 const notes=st.notes.length?`<div class="card"><h3>Case notes</h3>${st.notes.slice().reverse().map(n=>`<div class="trail-row"><span class="trail-when">${n.at}</span><span class="trail-what">${n.text}</span><span class="trail-who">${n.by}</span></div>`).join('')}</div>`:'';
 if(auto){
  const word=c.verdict==='green'?'AUTO-APPROVED':'AUTO-DECLINED';const spn=c.verdict==='green'?'Auto-Approved':'Auto-Declined';
  return `<div class="card"><h3>Disposition</h3>
    <div class="auto-banner ${c.verdict==='green'?'ok':'bad'}"><div class="ab-word">${word}</div>
     <div class="ab-sub">Straight-through decision — the system ${c.verdict==='green'?'approved':'declined'} this case automatically, so no underwriter action is required. It's filed in the ${spn} space as a record.</div></div>
    <div class="desk-actions"><button class="ai-btn" style="background:var(--acc)" onclick="downloadMemo('${c.id}')">⬇ Decision memo</button>
     ${isUW?`<button class="ai-btn" style="background:var(--mut)" onclick="wfPull('${c.id}')">Pull into review</button>`:''}</div>
    ${st.history.length?`<div style="margin-top:14px">${trailHTML(st)}</div>`:''}</div>${notes}`;
 }
 const owner=st.assignee?`<b>${st.assignee}</b>`:'<span style="color:var(--mut)">Unassigned</span>';
 const decided=resolved?`<div class="auto-banner ${st.decision.action==='APPROVED'?'ok':'bad'}"><div class="ab-word">${st.decision.action}</div><div class="ab-sub">“${st.decision.rationale}” — ${st.decision.by} (${st.decision.role}), ${st.decision.at}</div></div>`:'';
 let controls;
 if(isUW&&!resolved){
  const pb=priorityBand(priorityScore(c));const h=ageHours(c);const slaCls=h>=8?'sla-breach':h>=6?'sla-warn':'sla-ok';
  controls=`
   <div class="desk-row"><span class="desk-l">Priority</span><span><span class="pri-chip" style="background:${pb[1]}">${pb[0]}</span> <span class="mono" style="font-size:11px;color:var(--mut)">score ${priorityScore(c)}/100</span></span></div>
   <div class="desk-row"><span class="desk-l">Assigned to</span><span>${st.assignee||'Unassigned'}${st.tier?` <span class="tier-tag">${(UWS[st.tier]||{}).label}</span>`:''}${(st.assigneeUid&&st.assigneeUid!==CURRENT_UID)?` <button class="ai-btn" style="margin-left:8px;background:var(--mut)" onclick="wfReassign('${c.id}')">Take over</button>`:''}</span></div>
   <div class="desk-row"><span class="desk-l">Time in queue</span><span class="sla-chip ${slaCls}">${h>=8?'⚠ OVER 8h SLA · ':''}${fmtAge(h)}</span></div>
   <div class="desk-row"><span class="desk-l">Status</span><span class="status-chip wf-${st.status}">${WF_LABEL[st.status]}</span></div>
   <div class="desk-actions" style="margin-top:14px">
     <button class="ai-btn" style="background:var(--ok)" onclick="wfDecide('${c.id}','approve')">✓ Approve</button>
     <button class="ai-btn" style="background:var(--bad)" onclick="wfDecide('${c.id}','decline')">✕ Decline</button>
     <button class="ai-btn" style="background:var(--warn)" onclick="toggleEvidence('${c.id}')">Request information</button>
     <button class="ai-btn" onclick="wfNote('${c.id}')">+ Note</button></div>
   ${evidenceFormHTML(c)}
   <div class="note">This case is in your queue because the system flagged it for a human. Approve or decline with a rationale — it's logged to the audit trail and moves the case to Completed. Use <b>Request information</b> to order evidence (APS, labs, MVR…) with an AI pre-check that flags duplicate or non-indicated orders before dispatch.</div>`;
 } else if(isUW&&resolved){
  controls=`<div class="desk-actions" style="margin-top:2px">
     <button class="ai-btn" style="background:var(--acc)" onclick="downloadMemo('${c.id}')">⬇ Decision memo</button>
     <button class="ai-btn" style="background:var(--mut)" onclick="wfReopen('${c.id}')">Reopen</button></div>`;
 } else {
  controls=`<div class="desk-row"><span class="desk-l">Status</span><span class="status-chip wf-${st.status}">${WF_LABEL[st.status]}</span></div>
   <div class="desk-row"><span class="desk-l">Owner</span><span>${owner}</span></div>
   <div class="note">Manager view — read-only. Underwriters action manual-review cases from their queue.</div>`;
 }
 return `<div class="card"><h3>Underwriter Case Desk</h3>${decided}${controls}</div>${notes}<div class="card"><h3>Audit trail</h3>${trailHTML(st)}</div>`;
}
let searchQ="";
function onSearch(q){searchQ=q.trim().toLowerCase();page=0;rail();}
function pg(d){const mx=Math.max(0,Math.ceil(currentList().length/PAGE)-1);page=Math.min(mx,Math.max(0,page+d));rail();}
function goSpace(sp){space=sp;view="space";page=0;render();}
function goOverview(){view="overview";render();}
function goManager(){view="manager";render();}
function goExec(){view="executive";render();}
function goAdmin(){view="admin";render();}
function goScore(){view="score";render();}
function sel(id){if(view!=='case'){prev={view,space};caseNav=currentList().map(x=>x.id);}activeId=id;view="case";const c=CASES.find(x=>x.id===id);activeTab=(c&&bucketOf(c)==='review')?5:4;render();}
function selInNav(id){activeId=id;const c=CASES.find(x=>x.id===id);activeTab=(c&&bucketOf(c)==='review')?5:4;render();}
function caseNavPos(){return caseNav.indexOf(activeId);}
function nextCase(){const i=caseNavPos();if(i<0||i>=caseNav.length-1)return;selInNav(caseNav[i+1]);}
function prevCase(){const i=caseNavPos();if(i<=0)return;selInNav(caseNav[i-1]);}
function selTab(n){activeTab=n;render();}
function render(){rail();main();}
function buildNav(){
 const nav=document.getElementById('navLinks');if(!nav)return;
 // underwriters work case spaces; managers only oversee — no case records at all
 if(CURRENT_ROLE==='manager'){
  nav.innerHTML=`<div class="nav-head">Oversight</div>
    <div class="overview-link ${view==='overview'?'active':''}" onclick="goOverview()"><span>⌂ &nbsp;Portfolio & Model Card</span></div>
    <div class="overview-link ${view==='manager'?'active':''}" onclick="goManager()"><span>▦ &nbsp;Manager Overview</span></div>`;
  return;
 }
 if(CURRENT_ROLE==='executive'){
  nav.innerHTML=`<div class="nav-head">Executive</div>
    <div class="overview-link ${view==='executive'?'active':''}" onclick="goExec()"><span>◆ &nbsp;Executive Overview</span></div>
    <div class="overview-link ${view==='overview'?'active':''}" onclick="goOverview()"><span>⌂ &nbsp;Portfolio & Model Card</span></div>`;
  return;
 }
 if(CURRENT_ROLE==='admin'){
  const ev=evidenceAll().filter(e=>e.status==='PENDING EVIDENCE').length;
  nav.innerHTML=`<div class="nav-head">Operations</div>
    <div class="overview-link ${view==='admin'?'active':''}" onclick="goAdmin()"><span>▤ &nbsp;Decision Feed</span>${ev?`<span class="nav-badge">${ev}</span>`:''}</div>
    <div class="overview-link ${view==='overview'?'active':''}" onclick="goOverview()"><span>⌂ &nbsp;Portfolio & Model Card</span></div>`;
  return;
 }
 const sp=SPACES.map(s=>{const n=spaceCases(s[0]).length;
   const badge=s[0]==='review'?`<span class="nav-badge">${n}</span>`:`<span class="nav-count">${n}</span>`;
   return `<div class="overview-link ${space===s[0]&&view==='space'?'active':''}" onclick="goSpace('${s[0]}')"><span>${s[2]} &nbsp;${s[1]}</span>${badge}</div>`;}).join('');
 // New-application intake removed (PRD §3.4): the Copilot is a review tool, not
 // an intake/point-of-sale system. No route, no nav slot.
 nav.innerHTML=`<div class="nav-head">Case spaces</div>${sp}`;
}
function rail(){
 buildNav();
 const list=currentList();
 document.getElementById('listTitle').textContent=SPACE_LABEL[space]||'Cases';
 document.getElementById('queueCount').textContent=list.length+(space==='review'?' to do':' cases');
 const items=list.slice(page*PAGE,page*PAGE+PAGE);
 document.getElementById('caseList').innerHTML=items.length?items.map((c,i)=>{
  const sc=c.verdict==='red'?'sc-bad':c.verdict==='yellow'?'sc-warn':'sc-ok';
  const st=wfGet(c.id);const isRev=space==='review';
  let meta='';
  if(isRev){
   meta=`<div class="ci-meta">${slaChip(c)}</div>
    <div class="ci-meta">${queueScope==='team'&&st.tier?`<span class="tier-tag">${st.assignee} · ${(UWS[st.tier]||{}).label}</span>`:wfChip(c.id)}</div>`;
  }else{meta=`<div class="ci-id" style="margin-top:2px">${wfChip(c.id)}</div>`;}
  const rank=isRev?`<span class="rank-num">${page*PAGE+i+1}</span> `:'';
  // Case ID is the primary identifier (§3.1) — mono, prominent, above the name;
  // applicant name demotes to a secondary line.
  return `<div class="case-item ${c.id===activeId&&view==='case'?'active':''}" onclick="sel('${c.id}')">
   <div style="min-width:0"><div class="ci-id" style="font-size:12.5px;font-weight:700;color:#E9EDF4;margin:0">${rank}${c.id}${c.has_docs?' <span class="doctag">· PDF</span>':''}</div>
    <div class="ci-name" style="font-size:11.5px;font-weight:500;color:var(--mut)">${c.name}</div>${meta}</div>
   <div class="score-chip ${sc}">${c.risk_score}</div></div>`;}).join(''):'<div class="note" style="padding:16px 12px;color:#9AA0A8">No cases in this space.</div>';
 const mx=Math.max(0,Math.ceil(list.length/PAGE)-1);
 document.getElementById('pageLabel').textContent=(page+1)+" / "+(mx+1);
 document.getElementById('prevBtn').disabled=page<=0;document.getElementById('nextBtn').disabled=page>=mx;
 const cl=document.getElementById('caseList');if(cl)cl.scrollTop=railScroll;   // §3.3 preserve list position
}
function spaceView(){
 const meta=SPACES.find(s=>s[0]===space)||SPACES[0];const list=currentList();
 const isRev=space==='review';
 const toggle=(isRev&&CURRENT_ROLE==='underwriter')?`<div class="seg" style="margin-top:12px">
    <button class="${queueScope==='mine'?'on':''}" onclick="setScope('mine')">My cases</button>
    <button class="${queueScope==='team'?'on':''}" onclick="setScope('team')">Whole team</button></div>`:'';
 let head,rows;
 if(isRev){
  head=`<tr><th>#</th><th>Applicant</th><th>Case ID</th><th>Risk score</th><th>Coverage</th><th>Time in queue</th><th>Requirements</th><th>AI recommendation</th><th></th></tr>`;
  rows=list.slice(0,300).map((c,i)=>{const st=wfGet(c.id);
    const sc=c.verdict==='red'?'sc-bad':c.verdict==='yellow'?'sc-warn':'sc-ok';
    return `<tr onclick="sel('${c.id}')" style="cursor:pointer">
      <td class="rank-num">${i+1}</td>
      <td><b>${c.name}</b><div style="font-size:11px;color:var(--mut)">${c.policy}</div></td>
      <td><span class="mono" style="font-weight:700;font-size:13px;white-space:nowrap">${c.id}</span></td>
      <td><span class="score-chip ${sc}">${c.risk_score}</span></td>
      <td class="mono" style="white-space:nowrap">${fmt$(c.coverage)}</td>
      <td>${slaChip(c)}</td>
      <td>${reqOutstanding(c)}</td>
      <td>${aiRecoCol(c)}</td>
      <td style="text-align:right"><button class="ai-btn" onclick="event.stopPropagation();sel('${c.id}')">Review</button></td></tr>`;}).join('');
 }else{
  const isDone=space==='completed';
  head=isDone
   ?`<tr><th>Case ID</th><th>AI recommendation</th><th>Human decision</th><th>Agreement</th><th></th></tr>`
   :`<tr><th>Case ID</th><th>AI recommendation</th><th>Status</th><th></th></tr>`;
  rows=list.slice(0,300).map(c=>{const st=wfGet(c.id);
    if(isDone&&st.decision){
     // Model recommendation vs human decision, side by side, with the delta made
     // obvious (§3.2) — the agreement/override record an examiner asks for first.
     const human=st.decision.action;                       // APPROVED / DECLINED
     const lean=c.verdict==='green'?'APPROVED':c.verdict==='red'?'DECLINED':null;  // yellow = referred, no auto-lean
     const agree=lean==null?['Human-decided','var(--acc)']:(human===lean?['Agreed with AI','var(--ok)']:['Overrode AI','var(--warn)']);
     return `<tr onclick="sel('${c.id}')" style="cursor:pointer">
      <td class="mono" style="white-space:nowrap">${c.id}<div style="font-size:11px;color:var(--mut)">${c.name}</div></td>
      <td>${aiRecChip(c)}</td>
      <td><span class="status-chip wf-${st.status}">${human}</span></td>
      <td><span class="pri-chip" style="background:${agree[1]}">${agree[0]}</span></td>
      <td style="text-align:right"><button class="ai-btn" onclick="event.stopPropagation();sel('${c.id}')">Open</button></td></tr>`;}
    return `<tr onclick="sel('${c.id}')" style="cursor:pointer">
      <td class="mono" style="white-space:nowrap">${c.id}<div style="font-size:11px;color:var(--mut)">${c.name}</div></td>
      <td>${aiRecChip(c)}</td>
      <td><span class="status-chip wf-${st.status}">${WF_LABEL[st.status]}</span></td>
      <td style="text-align:right"><button class="ai-btn" onclick="event.stopPropagation();sel('${c.id}')">Open</button></td></tr>`;}).join('');
 }
 const breaches=isRev?list.filter(c=>ageHours(c)>=8).length:0;
 const banner=isRev?`<div class="verdict-banner v-yellow" style="margin-top:16px"><div class="vb-word">${list.length} case(s) ranked by coverage &amp; time in queue${breaches?` · ${breaches} over the 8h SLA`:''}</div><div class="vb-sub">Work top-down — most important first. These are the only cases needing a human; auto-approvals and auto-declines are filed separately. Anything over 8 hours in the queue is flagged red.</div></div>`:'';
 // Bulk approve/decline (§4.4) — batch-affirm straight-through decisions into
 // the recorded decision trail, top-right of the auto-decisioned spaces.
 const canBulk=CURRENT_ROLE==='underwriter'&&(space==='auto_approved'||space==='auto_declined')&&list.length;
 const bulkBtn=canBulk?`<button class="ai-btn" style="background:${space==='auto_approved'?'var(--ok)':'var(--bad)'}" onclick="bulkDecide('${space}')">${space==='auto_approved'?'✓ Bulk approve all':'✕ Bulk decline all'} (${list.length})</button>`:'';
 return `<div class="case-head"><div><h2>${meta[1]}</h2>
    <div class="case-meta"><span>${list.length} case(s)</span><span>${meta[3]}</span></div>${toggle}</div>${bulkBtn}</div>
   ${banner}
   <div class="card" style="margin-top:16px">${list.length?`<table class="xt">${head}${rows}</table>`:`<div class="note" style="margin:0">Nothing in this space right now.</div>`}</div>`;
}
function bulkDecide(sp){
 // §4.4 guardrails: itemized confirm before acting, mandatory rationale, and
 // every case written to the decision record individually and flagged "bulk".
 const list=spaceCases(sp).filter(c=>!wfGet(c.id).decision);
 if(!list.length){alert('Nothing left to act on in this space.');return;}
 const kind=sp==='auto_approved'?'approve':'decline';
 const labels={approve:'APPROVED',decline:'DECLINED'};
 const totalCov=list.reduce((s,c)=>s+(c.coverage||0),0);
 const preview=list.slice(0,8).map(c=>`${c.id} · ${fmt$(c.coverage)}`).join('\n')+(list.length>8?`\n…and ${list.length-8} more`:'');
 const ok=confirm(`Bulk ${labels[kind]} ${list.length} case(s), ${fmt$(totalCov)} total coverage:\n\n${preview}\n\nEach case is written to the decision record individually, flagged "bulk".`);
 if(!ok)return;
 const rationale=(prompt('Rationale for this bulk '+labels[kind]+' — required, applied to every case listed above, logged individually:')||'').trim();
 if(!rationale){alert('A rationale is required for a bulk decision.');return;}
 list.forEach(c=>{
  const st=wfGet(c.id);st.pulled=true;st.status=kind==='approve'?'approved':'declined';
  st.decision={action:labels[kind],by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),rationale:rationale,bulk:true};
  st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:labels[kind]+' (bulk) — "'+rationale+'"'});
  wfSave(c.id,st);
  const ov=getOverrides();ov[c.id]={decision:labels[kind],label:kind==='decline'?1:0,reason:rationale,at:st.decision.at};
  localStorage.setItem('uw_overrides',JSON.stringify(ov));
 });
 render();
}
function main(){
 const el=document.getElementById('mainContent');
 if(view==="space"){el.innerHTML=spaceView();return;}
 if(view==="overview"){el.innerHTML=overview();return;}
 if(view==="manager"){el.innerHTML=managerView();return;}
 if(view==="executive"){el.innerHTML=executiveView();return;}
 if(view==="admin"){el.innerHTML=adminView();return;}
 if(view==="score"){el.innerHTML=scoreView();wireScoreForm();return;}
 const c=CASES.find(x=>x.id===activeId);if(!c){el.innerHTML=spaceView();return;}
 const vm=VM[c.verdict];
 const afvm=c.afford?AFF[c.afford.verdict]:null;
 const navPos=caseNavPos();
 const navCtl=navPos>=0?`<div style="display:flex;gap:8px;align-items:center">
    <button class="ai-btn" style="background:var(--rail-2)" ${navPos<=0?'disabled':''} onclick="prevCase()">‹ Prev</button>
    <span class="mono" style="font-size:11px;color:var(--mut)">${navPos+1} of ${caseNav.length}</span>
    <button class="ai-btn" style="background:var(--rail-2)" ${navPos>=caseNav.length-1?'disabled':''} onclick="nextCase()">Next ›</button></div>`:'';
 const reco=caseRecommendation(c);
 el.innerHTML=`
  <div style="margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
   <button class="ai-btn" style="background:var(--rail-2)" onclick="goBack()">← ${backLabel()}</button>
   ${navCtl}</div>
  <div class="case-head">
   <div><h2>${c.name}</h2>
    <div class="case-meta"><span class="mono" style="font-weight:700;color:var(--ink)">${c.id}</span><span>${c.occupation}</span><span>${c.city}, ${c.state}</span><span>${c.policy}</span></div></div>
   <div class="headline-score">
    <div><div class="hs-num" style="color:var(--${vm[1]})">${c.risk_score}<span style="font-size:16px;color:var(--mut)">/100</span></div>
     <div class="hs-lab">Composite Risk Score</div></div>
    <div class="hs-class cls-${vm[1]}">${vm[0]}</div>
    <div style="text-align:center"><div class="hs-num" style="font-size:22px">${fmt$(c.coverage)}</div><div class="hs-lab" style="margin-top:4px">Coverage requested</div></div>
    ${afvm?`<div style="text-align:center"><div class="hs-class cls-${afvm[1]}" style="font-size:13px">${c.afford.label}</div><div class="hs-lab" style="margin-top:4px">Financial Viability</div></div>`:''}
    <div style="text-align:center;padding-left:16px;border-left:1px solid var(--line)"><div style="font-size:14px;font-weight:700;color:var(--ink)">${reco[0]}</div><div class="hs-lab" style="margin-top:4px">AI recommendation · ${reco[1]}</div></div></div></div>
  ${topDriversHTML(c)}
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
function affordCard(af){
 if(!af)return '';
 const stCol={pass:"var(--ok)",strain:"var(--warn)",fail:"var(--bad)"};
 const stLab={pass:"PASS",strain:"STRAINED",fail:"FAIL"};
 return `<div class="card"><h3>Financial Viability — Affordability Screen</h3>
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap">
   <span class="g-band cls-${AFF[af.verdict][1]}">${af.label}</span>
   <span class="mono" style="font-size:12px;color:var(--mut)">est. premium ${fmt$(af.premium)}/yr · ${fmt$(af.premium_monthly)}/mo</span></div>
  ${af.indicators.map(i=>`<div class="factor-row"><div><div class="factor-label">${i.label} <b style="color:${stCol[i.status]}">· ${stLab[i.status]}</b></div><div class="factor-detail">${i.detail}</div></div><div class="factor-pts" style="color:${stCol[i.status]}">${i.value}</div></div>`).join('')}
  <div class="note">Financial underwriting asks a different question from risk scoring: not “how risky is this life?” but “can this applicant sustain the premium, and is the requested amount financially justified?” A failed indicator refers the case to financial underwriting regardless of the mortality risk score.</div></div>`;
}
function overview(){
 const vc={green:0,yellow:0,red:0};CASES.forEach(c=>vc[c.verdict]++);
 const tierLabels={low:"Low (0–25)",mod:`Moderate (26–${A_LINE-1})`,elev:`Elevated (${A_LINE}–${D_LINE-1})`,high:`High (${D_LINE}–100)`};
 const tc={[tierLabels.low]:0,[tierLabels.mod]:0,[tierLabels.elev]:0,[tierLabels.high]:0};
 CASES.forEach(c=>{const s=c.risk_score;if(s<=25)tc[tierLabels.low]++;else if(s<A_LINE)tc[tierLabels.mod]++;else if(s<D_LINE)tc[tierLabels.elev]++;else tc[tierLabels.high]++;});
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
 <div class="card"><h3>Rules layer &amp; model governance</h3>
  <div class="note" style="margin:0 0 10px">Every score is <b>50% auditable rule engine + 50% ML</b> — not rules alone. Hard knockouts (material misrepresentation, appetite) evaluate as <b>rules</b> before the model; the model produces a score; versioned thresholds (${A_LINE}/${D_LINE}) convert score to band. The case file's Decision tab labels which layer produced each outcome.</div>
  <div class="legend-row">
   <div class="legend-chip" style="background:var(--acc-soft);color:var(--acc)"><span class="swatch" style="background:var(--acc)"></span>Feature register — each factor's source &amp; whether its weight is learned or hand-set</div>
   <div class="legend-chip" style="background:var(--acc-soft);color:var(--acc)"><span class="swatch" style="background:var(--acc)"></span>Model versions immutable &amp; revertible — each decision records the version that produced it</div>
   <div class="legend-chip" style="background:var(--acc-soft);color:var(--acc)"><span class="swatch" style="background:var(--acc)"></span>Drift watch — input &amp; score distributions monitored against the training baseline</div>
  </div>
  <div class="note">Medical rule-engine weights are evidence-anchored: <b>points = round(28 × ln(relative-mortality multiple))</b> derived from NHANES + NCHS Linked Mortality data and cross-validated against real applicants — not hand-picked. Gradient boosting is chosen over a GLM for interaction capture, with logistic regression retained as the auditable in-browser stand-in. The rules layer is also the shock absorber for regime change (e.g. a 2020-style shift): a new knockout or threshold ships in days without a full retrain.</div></div>
 <div class="grid3">
  <div class="stat"><div class="sv">${(M.extraction.field_level_accuracy*100).toFixed(1)}%</div><div class="sl">Extraction accuracy — field level vs ground truth</div></div>
  <div class="stat"><div class="sv">${(M.conflict_screening.detection_recall*100).toFixed(0)}%</div><div class="sl">Injected-conflict detection recall (${M.conflict_screening.tp}/${M.conflict_screening.tp+M.conflict_screening.fn} caught, ${M.conflict_screening.fp} false alarms)</div></div>
  <div class="stat"><div class="sv">${(gb.auc*100).toFixed(1)}%</div><div class="sl">Gradient Boosting AUC on ${M.risk_models.n_test.toLocaleString()} held-out records</div></div>
  <div class="stat"><div class="sv">${(lr.auc*100).toFixed(1)}%</div><div class="sl">Logistic Regression AUC (auditable baseline)</div></div>
  <div class="stat"><div class="sv">${(M.decisioning.straight_through_rate*100).toFixed(1)}%</div><div class="sl">Straight-through rate — decided with no human touch</div></div>
  <div class="stat"><div class="sv">${M.risk_models.n_train.toLocaleString()}</div><div class="sl">Training records (test: ${M.risk_models.n_test.toLocaleString()}, base risk rate ${(M.risk_models.positive_rate*100).toFixed(0)}%)</div></div>
 </div>
 ${M.affordability?`<div class="card" style="margin-top:16px"><h3>Financial Viability — Portfolio Affordability</h3>
  <div class="legend-row">
   <div class="legend-chip cls-ok"><span class="swatch" style="background:var(--ok)"></span>AFFORDABLE · ${M.affordability.n_affordable} (${(M.affordability.affordable_rate*100).toFixed(0)}%) — all four indicators pass</div>
   <div class="legend-chip cls-warn"><span class="swatch" style="background:var(--warn)"></span>STRAINED · ${M.affordability.n_strained} (${(M.affordability.strained_rate*100).toFixed(0)}%) — within tolerance, flagged</div>
   <div class="legend-chip cls-bad"><span class="swatch" style="background:var(--bad)"></span>NOT JUSTIFIED · ${M.affordability.n_not_justified} (${(M.affordability.not_justified_rate*100).toFixed(0)}%) — referred to financial underwriting</div>
  </div>
  <table class="xt" style="margin-top:12px"><tr><th>Affordability indicator</th><th>Fail rate</th></tr>
   ${Object.entries(M.affordability.indicator_fail_rates).map(([k,v])=>`<tr><td>${k}</td><td class="mono">${(v*100).toFixed(1)}%</td></tr>`).join('')}</table>
  <div class="note">Four financial-underwriting screens run on every applicant: premium-to-income (≤5%), disposable income after premium, coverage-to-income against an age-banded cap, and debt-service ratio (≤20% of net). Average premium-to-income across the portfolio is ${(M.affordability.avg_premium_to_income*100).toFixed(1)}% on an average estimated premium of ${fmt$(M.affordability.avg_annual_premium)}/yr. Any failed indicator refers the case regardless of mortality-risk score — this is the affordability half of the copilot the project brief asks for.</div></div>`:''}
 <div class="card" style="margin-top:16px"><h3>Composite Risk Score Distribution</h3>
  ${Object.entries(tc).map(([t,n],i)=>`<div class="hist-bar-row"><div class="hist-label">${t}</div>
   <div class="hist-track"><div class="hist-fill" style="width:${n/mx*100}%;background:${cols[i]}"></div></div><div class="hist-count">${n}</div></div>`).join('')}
  <div class="note">Score-driven bands: below ${A_LINE} → green auto-approve. ${A_LINE}–${D_LINE-1} → yellow manual review. At or above ${D_LINE}, or material misrepresentation → red decline. Conflicts, affordability and disclosed circumstances are shown as flags but no longer change the band.</div></div>
 <div class="card"><h3>Continuous Learning — real datasets & run-over-run improvement</h3>
  ${(()=>{const el=M.external_learning||{datasets:[]};const hist=M.model_history||[];
   const ds=el.datasets.filter(d=>!d.error);
   const histMax=Math.max(...hist.map(h=>h.n_train_pool),1);
   return `<div class="note" style="margin:0 0 12px">The models learn a risk prior from <b>${ds.length} public real-world datasets (${(el.total_rows||0).toLocaleString()} records)</b> — heart disease, diabetes, cancer survival, mortality and credit-default studies — blended into every score as the “external prior” feature. On top of that, every pipeline run adds a fresh batch to a growing training pool, so the models retrain on more data each time.</div>
   <table class="xt"><tr><th>Dataset</th><th>Records</th><th>Shared factors</th><th>Prior AUC</th><th>In prior</th></tr>
    ${ds.map(d=>`<tr style="${d.included_in_prior===false?'opacity:.45':''}"><td>${d.name}</td><td class="mono">${d.rows.toLocaleString()}</td><td class="mono">${d.features.join(', ')}</td><td class="mono">${(d.auc*100).toFixed(0)}%</td><td class="mono">${d.included_in_prior===false?'excluded (≈chance)':'✓ weighted'}</td></tr>`).join('')}</table>
   <div style="margin-top:16px"><b style="font-size:12.5px">Training runs</b>
    ${hist.map(h=>`<div class="hist-bar-row"><div class="hist-label">Run ${h.run}</div>
     <div class="hist-track"><div class="hist-fill" style="width:${h.n_train_pool/histMax*100}%;background:var(--acc)"></div></div>
     <div class="hist-count" style="width:190px">${h.n_train_pool.toLocaleString()} records · GB AUC ${(h.gb_auc*100).toFixed(1)}%</div></div>`).join('')}</div>`;})()}
 </div>
 <div class="card"><h3>Calibration — does a predicted risk of X% mean X% are actually high-risk?</h3>
  ${(M.risk_models.calibration||[]).map(b=>`<div class="hist-bar-row"><div class="hist-label">${b.bin}</div>
   <div class="hist-track" style="height:9px;margin-bottom:2px"><div class="hist-fill" style="width:${b.predicted*100}%;background:var(--acc)"></div></div>
   <div class="hist-count" style="width:150px">pred ${(b.predicted*100).toFixed(0)}% · actual ${(b.actual*100).toFixed(0)}% · n=${b.n}</div></div>
  <div class="hist-bar-row" style="margin-top:-4px"><div class="hist-label"></div>
   <div class="hist-track" style="height:9px"><div class="hist-fill" style="width:${b.actual*100}%;background:var(--ink)"></div></div>
   <div class="hist-count" style="width:150px"></div></div>`).join('')}
  <div class="note"><span style="color:var(--acc)">■</span> predicted probability vs <span style="color:var(--ink)">■</span> actual high-risk rate, per prediction band on held-out test data. The closer each pair, the more a score can be read literally as a probability — this is what justifies drawing hard approve/decline lines at ${A_LINE} and ${D_LINE}.</div></div>
 <div class="card"><h3>Fairness — verdict mix &amp; model error rates by group</h3>
  ${(()=>{const frows=f=>`<tr><td>${f.band}</td><td class="mono">${f.n}</td>
    <td class="mono" style="color:var(--ok)">${(f.green*100).toFixed(0)}%</td>
    <td class="mono" style="color:var(--warn)">${(f.yellow*100).toFixed(0)}%</td>
    <td class="mono" style="color:var(--bad)">${(f.red*100).toFixed(0)}%</td>
    <td class="mono">${f.model_fpr!=null?(f.model_fpr*100).toFixed(0)+'%':'—'}</td>
    <td class="mono">${f.model_fnr!=null?(f.model_fnr*100).toFixed(0)+'%':'—'}</td></tr>`;
   const head=`<tr><th>Group</th><th>Cases</th><th>Green</th><th>Yellow</th><th>Red</th><th>Model FPR</th><th>Model FNR</th></tr>`;
   return `<table class="xt">${head}${(M.fairness_by_age||[]).map(frows).join('')}</table>
    ${(M.fairness_by_sex||[]).length?`<div style="margin-top:14px"><b style="font-size:12.5px">By sex</b> <span style="font-size:11.5px;color:var(--mut)">— audited because sex feeds both the external-data and Framingham priors</span></div>
    <table class="xt">${head}${M.fairness_by_sex.map(frows).join('')}</table>`:''}`;})()}
  <div class="note">Age is a legitimate actuarial factor in life insurance, so approval rates are expected to fall with age — the verdict-mix columns make that gradient visible and reviewable instead of hidden. The error-rate columns answer a different question: <b>who does the model get wrong</b>. FPR = share of actually-low-risk people the ML flags high-risk (wrongly penalised); FNR = share of actually-high-risk people it misses. A group can have a fair outcome mix yet bear an unfair share of the errors — a materially higher FPR for one group is a flag for review even when approval rates look balanced.</div></div>
 <div class="card"><h3>Underwriter Feedback Loop</h3>
  <div class="note" style="margin:0 0 12px">Overrides recorded on any case's Decision tab are stored in this browser${(M.decisioning.n_overrides_learned||0)>0?` — and <b>${M.decisioning.n_overrides_learned} human override(s) are already in the training data</b> from previous exports`:''}. Export them, save as <span class="mono">data/overrides.json</span>, and re-run the pipeline: the models retrain on the human decisions.</div>
  <button class="ai-btn" onclick="exportOverrides()">⬇ Export underwriter overrides</button></div>
 <div class="card"><h3>Gradient Boosting — Feature Importance</h3>
  ${Object.entries(fi).sort((a,b)=>b[1]-a[1]).map(([f,v])=>`<div class="coef-bar-row"><div class="coef-label">${f}</div>
   <div class="coef-track"><div class="coef-fill" style="left:0;width:${v/mxf*100}%"></div></div><div class="coef-val">${v.toFixed(3)}</div></div>`).join('')}
  <div class="note">Extraction accuracy is measured on machine-generated text PDFs; on scanned documents it will drop — that is the gap Google Document AI closes in the GCP deployment. Because the data is synthetic with a known ground-truth label, every number above is verifiable, and model performance represents an upper bound rather than a production guarantee.</div></div>`;
}
function managerView(){
 const n=CASES.length;
 const by=v=>CASES.filter(c=>c.verdict===v);
 const G=by('green'),Y=by('yellow'),R=by('red');
 const pct=k=>(k.length/n*100).toFixed(0)+"%";
 const sum=(arr,f)=>arr.reduce((s,c)=>s+f(c),0);
 const avg=(arr,f)=>arr.length?sum(arr,f)/arr.length:0;
 const covAll=sum(CASES,c=>c.coverage), covG=sum(G,c=>c.coverage), covY=sum(Y,c=>c.coverage), covR=sum(R,c=>c.coverage);
 const fmtM=v=>"$"+(v>=1e6?(v/1e6).toFixed(1)+"M":Math.round(v/1e3)+"k");
 const conflicts=CASES.filter(c=>c.conflicts.length), majors=CASES.filter(c=>c.conflicts.some(k=>k.severity==='major'));
 const uniques=CASES.filter(c=>c.unique);
 const ov=getOverrides(); const ovList=Object.entries(ov).filter(([id])=>CASES.some(c=>c.id===id));
 // manual-review queue, biggest exposure first — where senior time goes
 const queue=Y.slice().sort((a,b)=>b.coverage-a.coverage).slice(0,8);
 // verdict mix by policy type
 const pols={};CASES.forEach(c=>{(pols[c.policy]=pols[c.policy]||{g:0,y:0,r:0,n:0});pols[c.policy][c.verdict[0]]++;pols[c.policy].n++;});
 const hist=M.model_history||[]; const lastRun=hist[hist.length-1]||{};
 return `<div class="case-head"><div><h2>Manager Overview</h2>
  <div class="case-meta"><span>${n} cases in queue</span><span>${M.n_applicants.toLocaleString()} scored pipeline-wide</span><span>evaluated ${M.generated_at}</span></div></div></div>
 <div class="grid3" style="margin-top:18px">
  <div class="stat" style="border-top:4px solid var(--ok)"><div class="sv" style="color:var(--ok)">${G.length}</div><div class="sl"><b>APPROVED</b> · ${pct(G)} of queue · no human touch needed</div></div>
  <div class="stat" style="border-top:4px solid var(--warn)"><div class="sv" style="color:var(--warn)">${Y.length}</div><div class="sl"><b>MANUAL REVIEW</b> · ${pct(Y)} · awaiting an underwriter</div></div>
  <div class="stat" style="border-top:4px solid var(--bad)"><div class="sv" style="color:var(--bad)">${R.length}</div><div class="sl"><b>DECLINED</b> · ${pct(R)} · ${majors.length} tied to major conflicts</div></div>
 </div>
 <div class="grid3" style="margin-top:14px">
  <div class="stat"><div class="sv">${(M.decisioning.straight_through_rate*100).toFixed(0)}%</div><div class="sl">Straight-through rate — decided with zero human minutes</div></div>
  <div class="stat"><div class="sv">${fmtM(covAll)}</div><div class="sl">Total coverage requested · <span style="color:var(--ok)">${fmtM(covG)} auto-approved</span> · <span style="color:var(--warn)">${fmtM(covY)} pending</span> · <span style="color:var(--bad)">${fmtM(covR)} declined</span></div></div>
  <div class="stat"><div class="sv">${avg(CASES,c=>c.risk_score).toFixed(0)}</div><div class="sl">Avg composite risk — green ${avg(G,c=>c.risk_score).toFixed(0)} · yellow ${avg(Y,c=>c.risk_score).toFixed(0)} · red ${avg(R,c=>c.risk_score).toFixed(0)}</div></div>
  <div class="stat"><div class="sv">${conflicts.length}</div><div class="sl">Cases with cross-document conflicts (${majors.length} major) — recall ${(M.conflict_screening.detection_recall*100).toFixed(0)}%, ${M.conflict_screening.fp} false alarms</div></div>
  <div class="stat"><div class="sv">${uniques.length}</div><div class="sl">Unique-circumstances disclosures — every one routed to a human</div></div>
  <div class="stat"><div class="sv">${ovList.length}</div><div class="sl">Underwriter overrides recorded in this browser${(M.decisioning.n_overrides_learned||0)>0?` · ${M.decisioning.n_overrides_learned} already trained on`:''} — export from the Model Card</div></div>
  ${M.affordability?`<div class="stat" style="border-top:4px solid var(--warn)"><div class="sv">${CASES.filter(c=>c.afford&&c.afford.verdict==='fail').length}</div><div class="sl"><b>NOT FINANCIALLY JUSTIFIED</b> · coverage or premium out of line with income — referred to financial underwriting (${(M.affordability.not_justified_rate*100).toFixed(0)}% pipeline-wide)</div></div>`:''}
 </div>
 <div class="card" style="margin-top:16px"><h3>Review Queue — largest exposure first (where senior time should go)</h3>
  <table class="xt"><tr><th>Case</th><th>Applicant</th><th>Coverage</th><th>Risk</th><th>Why it's here</th></tr>
   ${queue.map(c=>`<tr style="cursor:pointer" onclick="sel('${c.id}')"><td class="mono">${c.id}</td><td><b>${c.name}</b>, ${c.age} · ${c.occupation}</td>
    <td class="mono">${fmt$(c.coverage)}</td><td><span class="score-chip sc-warn" style="color:var(--warn);background:var(--warn-soft)">${c.risk_score}</span></td>
    <td style="font-size:12px;color:var(--mut)">${ov[c.id]?'<b style="color:var(--acc)">OVERRIDDEN → '+ov[c.id].decision+'</b>':(c.reasons[0]||'')}</td></tr>`).join('')}</table>
  <div class="note">Click any row to open the full case file. ${Y.length-queue.length>0?`${Y.length-queue.length} more manual-review cases in the queue at left.`:''}</div></div>
 <div class="card"><h3>Verdict Mix by Policy Type</h3>
  <table class="xt"><tr><th>Policy</th><th>Cases</th><th>Approve</th><th>Manual review</th><th>Decline</th></tr>
   ${Object.entries(pols).sort((a,b)=>b[1].n-a[1].n).map(([p,v])=>`<tr><td>${p}</td><td class="mono">${v.n}</td>
    <td class="mono" style="color:var(--ok)">${(v.g/v.n*100).toFixed(0)}%</td><td class="mono" style="color:var(--warn)">${(v.y/v.n*100).toFixed(0)}%</td><td class="mono" style="color:var(--bad)">${(v.r/v.n*100).toFixed(0)}%</td></tr>`).join('')}</table></div>
 <div class="card"><h3>System Health</h3>
  <div class="legend-row">
   <div class="legend-chip cls-ok"><span class="swatch" style="background:var(--ok)"></span>Extraction ${(M.extraction.field_level_accuracy*100).toFixed(0)}% field accuracy</div>
   <div class="legend-chip cls-ok"><span class="swatch" style="background:var(--ok)"></span>Conflict recall ${(M.conflict_screening.detection_recall*100).toFixed(0)}%</div>
   <div class="legend-chip cls-ok"><span class="swatch" style="background:var(--ok)"></span>GB model AUC ${(M.risk_models.gradient_boosting.auc*100).toFixed(1)}%</div>
   <div class="legend-chip" style="background:var(--acc-soft);color:var(--acc)"><span class="swatch" style="background:var(--acc)"></span>Trained on ${(lastRun.n_train_pool||M.risk_models.n_train).toLocaleString()} records · run #${lastRun.run||'—'}</div>
   <div class="legend-chip" style="background:var(--acc-soft);color:var(--acc)"><span class="swatch" style="background:var(--acc)"></span>${(M.external_learning||{}).n_usable||0} real-world datasets in the prior</div>
  </div>
  <div class="note">Full evidence — calibration, fairness by age band, feature importance, and dataset provenance — lives on the Portfolio &amp; Model Card page.</div></div>`;
}
/* =================== PRD v2: executive + admin + evidence flow =================== */
const APPETITE_MONTHLY=45000000;   // §5.1 monthly coverage the book wants to take on (config lever)
function finalOf(c){
 // the case's effective disposition: a recorded human decision wins; otherwise
 // the straight-through verdict; referred-but-undecided reads as pending.
 const st=wfGet(c.id);
 if(st.decision)return st.decision.action==='APPROVED'?'approve':'decline';
 if(c.verdict==='green')return 'approve';
 if(c.verdict==='red')return 'decline';
 return 'pending';
}
function allDecisions(){
 // every recorded human decision across the book, newest first (§5.2)
 const wb=wfAll(),out=[];
 CASES.forEach(c=>{const st=wb[c.id];if(st&&st.decision)out.push({id:c.id,name:c.name,coverage:c.coverage,
   action:st.decision.action,by:st.decision.by,role:st.decision.role,at:st.decision.at,
   rationale:st.decision.rationale,model:c.decision});});
 out.sort((a,b)=>(a.at<b.at?1:-1));return out;
}
function evidenceAll(){try{return JSON.parse(localStorage.getItem('uw_evidence')||'[]');}catch(e){return [];}}
function fmtBigMoney(v){return "$"+(v>=1e6?(v/1e6).toFixed(1)+"M":Math.round(v/1e3)+"k");}
function executiveView(){
 // A money view, not a queue (§5.1). Built from the whole book + recorded decisions.
 const n=CASES.length;
 const appr=CASES.filter(c=>finalOf(c)==='approve'),decl=CASES.filter(c=>finalOf(c)==='decline'),pend=CASES.filter(c=>finalOf(c)==='pending');
 const sum=(a,f)=>a.reduce((s,c)=>s+(f(c)||0),0);
 const covAppr=sum(appr,c=>c.coverage),covDecl=sum(decl,c=>c.coverage),covPend=sum(pend,c=>c.coverage),covAll=covAppr+covDecl+covPend;
 const premAppr=sum(appr,c=>c.premium||0);
 const avgCover=appr.length?covAppr/appr.length:0;
 const stp=(M.decisioning.straight_through_rate*100);
 const apprRate=n?appr.length/n*100:0;
 const priorApprRate=Math.max(0,apprRate-4.6);   // illustrative 2025 baseline (see note)
 const avgCycle=CASES.reduce((s,c)=>s+ageHours(c),0)/n;
 const ov=getOverrides();const nOv=Object.keys(ov).filter(id=>CASES.some(c=>c.id===id)).length;
 const nDecided=appr.length+decl.length-pend.length*0; const decidedManual=allDecisions().length;
 const overrideRate=decidedManual?(nOv/decidedManual*100):0;
 const appetitePct=APPETITE_MONTHLY?Math.min(covAppr/APPETITE_MONTHLY*100,100):0;
 const pctG=covAll?covAppr/covAll*100:0,pctP=covAll?covPend/covAll*100:0,pctR=covAll?covDecl/covAll*100:0;
 const tile=(v,l,accent)=>`<div class="stat"${accent?` style="border-top:4px solid ${accent}"`:''}><div class="sv">${v}</div><div class="sl">${l}</div></div>`;
 return `<div class="case-head"><div><h2>Executive Overview</h2>
   <div class="case-meta"><span>Chief Underwriting Officer</span><span>${n} cases in the current book</span><span>evaluated ${M.generated_at}</span></div></div></div>
  <div class="grid3" style="margin-top:18px">
   ${tile(fmtBigMoney(covAppr),'<b>Exposure taken on</b> — total approved cover in the current book','var(--ok)')}
   ${tile(fmtMoneyK(premAppr)+'/yr','<b>Approved premium</b> — annualised, the revenue side of the book','var(--acc)')}
   ${tile(stp.toFixed(0)+'%','<b>Straight-through rate</b> — decided with no human touch')}
  </div>
  <div class="grid3" style="margin-top:14px">
   ${tile(apprRate.toFixed(0)+'%','<b>Approval rate</b> — share of the book approved · <span style="color:var(--mut)">vs. '+priorApprRate.toFixed(0)+'% illustrative 2025 baseline</span>')}
   ${tile(fmtBigMoney(avgCover),'Average approved cover per policy')}
   ${tile(fmtAge(avgCycle),'Average time in queue — proxy for cycle time')}
   ${tile(overrideRate.toFixed(0)+'%','<b>Override rate</b> — human decisions against the model lean ('+nOv+' of '+decidedManual+')')}
   ${tile(appr.length+' / '+pend.length+' / '+decl.length,'Approved / referred-pending / declined (count)')}
   ${tile(fmtBigMoney(covAll),'Total coverage requested across the book')}
  </div>
  <div class="card" style="margin-top:16px"><h3>Decision mix — cover per bucket</h3>
   <div class="mix-bar">
    <div class="mix-seg" style="width:${pctG}%;background:var(--ok)">${pctG>7?fmtBigMoney(covAppr):''}</div>
    <div class="mix-seg" style="width:${pctP}%;background:var(--warn)">${pctP>7?fmtBigMoney(covPend):''}</div>
    <div class="mix-seg" style="width:${pctR}%;background:var(--bad)">${pctR>7?fmtBigMoney(covDecl):''}</div></div>
   <div class="legend-row" style="margin-top:10px">
    <div class="legend-chip cls-ok"><span class="swatch" style="background:var(--ok)"></span>Approved · ${appr.length} · ${fmtBigMoney(covAppr)}</div>
    <div class="legend-chip cls-warn"><span class="swatch" style="background:var(--warn)"></span>Referred / pending · ${pend.length} · ${fmtBigMoney(covPend)}</div>
    <div class="legend-chip cls-bad"><span class="swatch" style="background:var(--bad)"></span>Declined · ${decl.length} · ${fmtBigMoney(covDecl)}</div></div></div>
  <div class="card"><h3>Risk appetite — the levers you own</h3>
   <div class="note" style="margin:0 0 10px">Approved cover this book is <b>${fmtBigMoney(covAppr)}</b> against a monthly appetite target of <b>${fmtBigMoney(APPETITE_MONTHLY)}</b> — <b style="color:${appetitePct>=100?'var(--bad)':'var(--ok)'}">${appetitePct.toFixed(0)}%</b> of appetite. ${appetitePct<80?'The book is running below appetite — the acceptance lines could be loosened.':appetitePct>100?'The book is over appetite — tighten the acceptance lines.':'The book is tracking to appetite.'}</div>
   <div class="gauge-line"><div class="fill" style="width:${appetitePct}%;background:${appetitePct>=100?'var(--bad)':'var(--ok)'}"></div></div>
   <div class="appetite" style="margin-top:14px">
    <div class="lever"><b>Approval line — score < ${A_LINE}</b><div class="note" style="margin:6px 0 0">Below this, cases auto-approve. Lowering it tightens the book; raising it takes on more volume and exposure.</div></div>
    <div class="lever"><b>Decline line — score ≥ ${D_LINE}</b><div class="note" style="margin:6px 0 0">At or above this, cases auto-decline. These two lines are configuration, versioned, and owned by underwriting leadership — not baked into the model.</div></div></div></div>
  <div class="note">YoY figures are illustrative: the synthetic book has no dated prior-year cohort, so the 2025 baseline is a placeholder pending a real historical book. Every other number is computed live from the current cases and recorded decisions.</div>`;
}
function fmtMoneyK(v){return "$"+(v>=1e6?(v/1e6).toFixed(2)+"M":Math.round(v/1e3)+"k");}
function adminView(){
 // Receives every recorded decision, attributed, timestamped, linked (§5.2).
 const dec=allDecisions();
 const wb=wfAll();
 const nApproved=Object.values(wb).filter(s=>s.decision&&s.decision.action==='APPROVED').length;
 const nDeclined=Object.values(wb).filter(s=>s.decision&&s.decision.action==='DECLINED').length;
 const nInfo=Object.values(wb).filter(s=>s.status==='info_requested').length;
 const ev=evidenceAll().slice().reverse();
 const tile=(v,l,accent)=>`<div class="stat"${accent?` style="border-top:4px solid ${accent}"`:''}><div class="sv">${v}</div><div class="sl">${l}</div></div>`;
 const feed=dec.length?dec.map(d=>{const badge=d.model&&d.action?((d.model==='APPROVE'&&d.action==='APPROVED')||(d.model==='DECLINE'&&d.action==='DECLINED')?'<span class="pri-chip" style="background:var(--ok)">AGREED</span>':d.model==='MANUAL REVIEW'?'':'<span class="pri-chip" style="background:var(--warn)">OVERRIDE</span>'):'';
   return `<div class="feed-row"><span class="feed-when">${d.at}</span>
    <span class="feed-what"><b>${d.action}</b> — <span class="mono" style="cursor:pointer;color:var(--acc)" onclick="sel('${d.id}')">${d.id}</span> ${d.name}, ${fmt$(d.coverage)} ${badge}<div style="color:var(--mut);font-size:12px;margin-top:2px">AI: ${d.model} · “${d.rationale||''}”</div></span>
    <span class="feed-who">${d.by||''}</span></div>`;}).join(''):'<div class="note" style="margin:0">No decisions recorded yet. Underwriter decisions land here in real time.</div>';
 const evList=ev.length?ev.map(e=>`<div class="feed-row"><span class="feed-when">${e.at}</span>
    <span class="feed-what"><span class="status-chip wf-info_requested">${e.status}</span> <span class="mono" style="cursor:pointer;color:var(--acc)" onclick="sel('${e.caseId}')">${e.caseId}</span> ${e.name} — ${e.labels}<div style="color:var(--mut);font-size:12px;margin-top:2px">“${e.rationale}”${e.flags&&e.flags.length?` · <span style="color:var(--warn)">${e.flags.length} pre-check flag(s) acknowledged</span>`:''}</div></span>
    <span class="feed-who">${e.by||''}</span></div>`).join(''):'<div class="note" style="margin:0">No outstanding evidence requests.</div>';
 return `<div class="case-head"><div><h2>Decision Feed</h2>
   <div class="case-meta"><span>Operations administrator</span><span>${dec.length} recorded decision(s)</span><span>${ev.length} evidence request(s)</span></div></div></div>
  <div class="grid3" style="margin-top:18px">
   ${tile(nApproved,'<b>Approved</b> — decisions recorded this session','var(--ok)')}
   ${tile(nInfo,'<b>Info / evidence requested</b> — awaiting third parties','var(--warn)')}
   ${tile(nDeclined,'<b>Declined</b> — decisions recorded this session','var(--bad)')}
  </div>
  <div class="card" style="margin-top:16px"><div class="ai-head"><h3 style="margin:0">Decision trail — every recorded decision, newest first</h3>
    <div><button class="ai-btn" onclick="exportDecisions('csv')">⬇ CSV</button> <button class="ai-btn" style="background:var(--acc)" onclick="exportDecisions('json')">⬇ JSON</button></div></div>
   ${feed}
   <div class="note">This is the regulator-ready package — attributed, timestamped, and linked to each case, with the model recommendation beside the human decision. Export as CSV or JSON for compliance.</div></div>
  <div class="card"><h3>Outstanding evidence requests</h3>${evList}
   <div class="note">Raised by underwriters from the case file (§4.3). Each carries the requesting underwriter, a mandatory rationale, and any pre-check flags they proceeded over — so operations can chase the right provider.</div></div>`;
}
function exportDecisions(fmt){
 const d=allDecisions();
 if(!d.length){alert('No decisions recorded yet.');return;}
 let blob,name;
 if(fmt==='csv'){
  const hdr='case_id,applicant,coverage,ai_recommendation,human_decision,decided_by,role,decided_at,rationale\n';
  const rows=d.map(x=>[x.id,'"'+x.name+'"',x.coverage,x.model,x.action,x.by,x.role,x.at,'"'+(x.rationale||'').replace(/"/g,'""')+'"'].join(',')).join('\n');
  blob=new Blob([hdr+rows],{type:'text/csv'});name='decision_trail.csv';
 }else{blob=new Blob([JSON.stringify(d,null,2)],{type:'application/json'});name='decision_trail.json';}
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();
}
/* ---------- evidence request flow with AI pre-check (§4.3) ---------- */
const EVIDENCE_TYPES=[
 ["APS","Attending Physician Statement","Physician / records vendor","Weeks",350,"APS"],
 ["Employment","Employment records","Verification vendor","Days",40,""],
 ["Rx","Pharmacy / prescription history","Rx database vendor","Hours–days",15,""],
 ["MIB","Past insurance history (MIB)","MIB","Hours",8,""],
 ["MVR","Motor vehicle record","State DMV vendor","Hours–days",12,""],
 ["Paramed","Paramedical exam","Paramed vendor","Days–weeks",150,"Paramed exam"],
 ["Labs","Blood profile / labs","Lab vendor","Days",120,"Blood profile"],
 ["EKG","EKG","Paramed vendor","Days–weeks",180,"EKG"],
 ["Cognitive","Cognitive assessment","Paramed / telephonic","Days",90,"Cognitive assessment"],
 ["Financial","Financial questionnaire","Applicant / agent","Days",0,""],
 ["Other","Other (free text — manual routing)","Manual routing","Varies",0,""]
];
function evidenceFormHTML(c,open){
 const req=new Set(requirementsFor(c));
 const rows=EVIDENCE_TYPES.map(e=>{const [k,label,provider,turn,cost,grid]=e;
  const indicated=grid&&req.has(grid);
  return `<label class="ev-opt"><input type="checkbox" value="${k}"><span><b>${label}</b><div class="prov">${provider} · ${turn}${cost?` · ~$${cost}`:''}${indicated?' · A&A-INDICATED':''}</div></span></label>`;}).join('');
 return `<div id="evForm-${c.id}" class="ev-form" style="display:${open?'block':'none'}">
   ${open?'':'<h3 style="margin:0 0 12px">Request additional evidence</h3>'}
   <div class="ev-grid">${rows}</div>
   <textarea id="evRat-${c.id}" class="ev-rat" rows="2" placeholder="Explain why this evidence is needed — required for every request (logged to the audit trail, visible to operations)"></textarea>
   <div id="evCheck-${c.id}"></div>
   <div class="desk-actions"><button class="ai-btn" style="background:var(--acc)" onclick="submitEvidence('${c.id}')">Run pre-check &amp; dispatch</button>
    ${open?'':`<button class="ai-btn" style="background:var(--mut)" onclick="toggleEvidence('${c.id}')">Cancel</button>`}</div></div>`;
}
function toggleEvidence(id){const f=document.getElementById('evForm-'+id);if(!f)return;
 const show=f.style.display==='none';f.style.display=show?'block':'none';if(!show)f.dataset.ack='';}
function toggleDoc(id,key){const el=document.getElementById('doc-'+id+'-'+key);if(!el)return;
 el.style.display=el.style.display==='none'?'block':'none';}
function docContent(c,key){
 // Representative parsed content per document (the demo's inline viewer, §3.7).
 const e=c.extraction||{};const g=(v,d)=>(v!=null?v:d);
 if(key==='app')return [['Full name',c.name],['Date of birth',c.dob+' (age '+c.age+')'],['Sex',c.sex==='M'?'Male':'Female'],['Coverage requested',fmt$(c.coverage)],['Policy',c.policy],['Tobacco declared',c.smoker],['Section 6 declarations','See the Application tab']];
 if(key==='pay')return [['Employer',c.employer],['Annual income (payslip, annualised)',fmt$(g(e.payslip_income,c.income))],['Employment status',c.emp_status||'—'],['Years employed',(c.years_emp!=null?c.years_emp+' yr':'—')]];
 if(key==='paramed')return [['Height / weight',c.height+' cm / '+c.weight+' kg'],['BMI',c.bmi],['Blood pressure',c.bp],['Total cholesterol',c.chol+' mg/dL'],['Cotinine (tobacco lab)',g(e.cotinine,'—')],['Tobacco on form',e.form_tobacco_yes?'YES':'NO']];
 if(key==='bank')return [['Avg monthly deposits',fmt$(e.bank_deposit_monthly)],['Avg monthly outflows',fmt$(e.bank_outflow_monthly)],['Average balance',fmt$(c.bank)]];
 if(key==='tax')return [['Declared income (tax slip 2025)',fmt$(g(e.tax_income,c.income))],['Personal net worth',fmt$(c.net_worth)],['Existing debt (bureau)',fmt$(g(e.bureau_debt,c.debt))]];
 return [];
}
function docViewHTML(c,key,label){
 const rows=docContent(c,key);
 return `<div id="doc-${c.id}-${key}" class="doc-view" style="display:none">
   <div class="prov" style="margin-bottom:8px">Parsed from ${label}</div>
   <table class="xt">${rows.map(r=>`<tr><td style="width:55%">${r[0]}</td><td class="mono">${r[1]??'—'}</td></tr>`).join('')}</table></div>`;
}
function submitEvidence(id){
 const c=CASES.find(x=>x.id===id);const form=document.getElementById('evForm-'+id);
 const items=Array.from(form.querySelectorAll('input:checked')).map(i=>i.value);
 const rationale=(document.getElementById('evRat-'+id).value||'').trim();
 if(!items.length){alert('Select at least one evidence type.');return;}
 if(!rationale){alert('A rationale is required for every evidence request (§4.3).');return;}
 // AI pre-check — advises, never blocks (§4.3)
 const req=new Set(requirementsFor(c));
 const satisfied=c.has_docs?new Set(['Paramed exam','Blood profile']):new Set();
 const flags=[];
 items.forEach(k=>{const e=EVIDENCE_TYPES.find(x=>x[0]===k)||[];const grid=e[5],cost=e[4]||0;
  if(grid&&satisfied.has(grid))flags.push(`${k}: equivalent evidence is already in the packet — likely a duplicate order.`);
  else if(grid&&!req.has(grid))flags.push(`${k}: not indicated by the A&A grid for this age/amount — recorded as a discretionary “for cause” order.`);
  if(cost&&c.coverage&&cost/c.coverage>0.0025)flags.push(`${k}: ~$${cost} is large relative to the ${fmt$(c.coverage)} face amount — confirm it is proportionate.`);});
 const checkEl=document.getElementById('evCheck-'+id);
 if(flags.length&&form.dataset.ack!=='1'){
  checkEl.innerHTML=`<div class="ev-flags"><b>⚠ Pre-check — advisory only</b><ul>${flags.map(f=>`<li>${f}</li>`).join('')}</ul>
    <div class="note" style="margin:6px 0 0">You can proceed over any flag — click dispatch again to confirm. The flags and your rationale are logged together.</div></div>`;
  form.dataset.ack='1';return;
 }
 const st=wfGet(id);st.status='info_requested';st.notes=st.notes||[];
 const labels=items.map(k=>(EVIDENCE_TYPES.find(e=>e[0]===k)||[k,k])[1]).join(', ');
 st.notes.push({by:CURRENT_USER||'?',at:nowStr(),text:'EVIDENCE REQUESTED: '+labels+' — '+rationale+(flags.length?' [pre-check flags acknowledged]':'')});
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:'Requested evidence — '+labels});
 wfSave(id,st);
 const ev=evidenceAll();ev.push({caseId:id,name:c.name,items,labels,rationale,flags,by:CURRENT_USER,at:nowStr(),status:'PENDING EVIDENCE'});
 localStorage.setItem('uw_evidence',JSON.stringify(ev));
 render();
}
function panel(c){
 if(activeTab===1){
  const sec=(title,fields)=>`<div class="card"><h3>${title}</h3><div class="grid2">
   ${fields.map(f=>`<div class="field"><label>${f[0]}</label><div class="val">${f[1]}</div></div>`).join('')}</div></div>`;
  const yn=v=>v?'<b style="color:var(--warn)">Yes</b>':'No';
  const d=c.decl||{};
  const imm=`<div class="imm-note">🔒 <div><b>Application is read-only for every role.</b> Submitted values are evidence, not a working document — there is no edit path in this product, by design (§3.5). A correction is an appended amendment with author, timestamp and reason; the original value is never overwritten. Fields are marked <span class="prov" style="display:inline">declared by applicant</span> or <span class="prov" style="display:inline">extracted from documents</span>.</div></div>`;
  return imm+sec("Section 1 — Applicant Information",[
    ["Full Name",c.name],["Sex",c.sex==="M"?"Male":"Female"],
    ["Date of Birth",c.dob+" (age "+c.age+")"],["Smoker Status (last 12 months)",c.smoker],
    ["Occupation",c.occupation],["Employer",c.employer],
    ["Employment Status",c.emp_status||"—"],["Years Employed",(c.years_emp!=null?c.years_emp+" years":"—")],
    ["Location",c.city+", "+c.state],["Preferred Policy",c.policy]])
  +sec("Section 2 — Amount of Insurance Applying For",[
    ["Coverage Requested ($25k increments)",fmt$(c.coverage)],["Coverage-to-Income Multiple",(c.coverage/c.income).toFixed(1)+"×"],
    ["Existing Coverage (other carrier)",c.existing_cov?fmt$(c.existing_cov):"None"],["Intends to Replace Existing Coverage",c.existing_cov?(c.replacing?"Yes":"No"):"—"],
    ["Estimated Annual Premium",c.premium?fmt$(c.premium)+"/yr ("+fmt$(c.premium/12)+"/mo)":"—"],["Premium as % of Income",c.afford?(c.afford.pti*100).toFixed(1)+"%":"—"]])
  +sec("Section 4 — Financial Information",[
    ["Annual Net Earned Income",fmt$(c.income)],["Personal Net Worth (assets − liabilities)",fmt$(c.net_worth)],
    ["Monthly Expenses",fmt$(c.expenses)],["Existing Debt",fmt$(c.debt)],
    ["Avg Bank Balance",fmt$(c.bank)],["Credit Score",c.credit],
    ["Debt-to-Income Ratio",(c.dti*100).toFixed(1)+"%"],["Employment Status",c.emp_status||"—"]])
  +sec("Section 6 — Personal Declarations",[
    ["Insurance declined / modified / rated (6-1)",yn(d.prior_decline)],["Careless or dangerous driving, 5 yr (6-2a)",yn(d.dangerous_driving)],
    ["2+ moving violations, 2 yr (6-2b)",c.violations>=2?yn(1)+" — "+c.violations+" on record":"No"],["Hazardous activities (6-3)",c.hazard&&c.hazard!=="None"?yn(1)+" — "+c.hazard:"No"],
    ["Foreign travel planned, 12 mo (6-4a)",yn(d.foreign_travel)],["Drug use / alcohol-drug counselling, 5 yr (6-5a)",yn(d.drug_use)],
    ["Criminal offence (6-5b)",yn(d.criminal)],["Bankruptcy declared or contemplated (6-5c)",yn(d.bankruptcy)]])
  +sec("Sections 7–8 — Health Declaration & Medical Information",[
    ["Height / Weight",c.height+" cm / "+c.weight+" kg"],["BMI",c.bmi],
    ["Weight change >10 lb, past 12 mo (S7)",yn(d.weight_change)],["Alcohol Use",c.alcohol||"—"],
    ["Tobacco / cotinine-verified (8-1)",c.smoker],["Medical conditions by body system (8-1)",c.conditions],
    ["Family: parent/sibling diagnosed before 60 (8-4)",c.family?"Yes — heart disease/stroke/cancer, see records":"No"],["Blood Pressure",c.bp],
    ["Total Cholesterol",c.chol+" mg/dL",],["Attending physician on file","Yes — see health declaration"]])
  +(c.unique?`<div class="unique-banner"><b>UNIQUE CIRCUMSTANCES DISCLOSED</b><p style="margin:5px 0 0">“${c.unique}” — this disclosure automatically routes the file to a human underwriter so the person is assessed as a whole, not just by the score.</p></div>`:'');
 }
 if(activeTab===2){
  const docs=[['app','Application Form (Parts A–B, health questionnaire)'],['pay','Payslip / Earnings Statement'],['paramed','Paramedical Exam Report + consumer report'],['bank','Bank Statement (3-month, deposits & expense categories)'],['tax','Tax Slip — 2025 Statement of Income']];
  const packet=docs.map(d=>{const [key,label]=d;
    if(c.has_docs)return `<div class="doc-row" style="cursor:pointer" onclick="this.classList.toggle('open');toggleDoc('${c.id}','${key}')"><div class="dot"></div><div class="dname">${label}</div><div class="dstatus">Parsed ✓ · click to open</div></div>${docViewHTML(c,key,label)}`;
    return `<div class="doc-row"><div class="dot miss"></div><div class="dname">${label}</div><div class="dstatus" style="color:var(--mut)">Not in packet sample</div></div>`;}).join('');
  const reqCard=CURRENT_ROLE==='underwriter'
   ?`<div class="card"><h3>Request more information</h3>
      <div class="note" style="margin:0 0 12px">Order additional evidence — an <b>Attending Physician Statement (APS)</b>, past insurance history (MIB), pharmacy / prescription history, medical records, MVR, exams or labs. Select what you need and <b>explain why it's needed</b>: the reason is mandatory, logged to the audit trail, and sent to operations. An AI pre-check flags duplicate or non-indicated orders before dispatch.</div>
      ${evidenceFormHTML(c,true)}</div>`
   :'';
  return `<div class="card"><h3>Document Packet</h3>${packet}
   ${c.has_docs?'<div class="note">Click any parsed document to open it inline. Documents are read-only (§3.5); on the Extraction tab, each value traces to the document it was read from.</div>':'<div class="note">This applicant is in the scored portfolio but outside the PDF-packet sample; scores are computed from structured data. In production, every case flows through document extraction.</div>'}</div>
   ${requirementsCardHTML(c)}
   ${reqCard}`;
 }
 if(activeTab===3){
  if(!c.has_docs)return '<div class="card"><div class="note">No PDF packet for this applicant in the sample — open a case tagged · PDF in the queue for the full extraction view.</div></div>';
  const e=c.extraction;
  const rows=[["Name (form)",e.name],["DOB (form)",e.form_dob],["DOB (paramed / ID)",e.paramed_dob],
   ["Declared income (form)",fmt$(e.form_income)],["Income (payslip, annualized)",fmt$(e.payslip_income)],
   ["Income (tax slip, 2025)",fmt$(e.tax_income)],["Bank deposits (monthly avg)",fmt$(e.bank_deposit_monthly)],
   ["Bank outflows (monthly avg)",fmt$(e.bank_outflow_monthly)],
   ["Declared debt (form)",fmt$(e.form_debt)],["Debt (credit bureau)",fmt$(e.bureau_debt)],
   ["Tobacco (form 4a)",e.form_tobacco_yes?"YES":"NO"],["Cotinine (lab)",e.cotinine],
   ["Height / Weight",e.height_cm+" cm / "+e.weight_kg+" kg"],["Blood pressure",e.blood_pressure],["Cholesterol",e.cholesterol+" mg/dL"]];
  const confl=c.conflicts.length?c.conflicts.map(k=>`<div class="conflict-card ${k.severity==='minor'?'minor':''}">
   <b>${k.severity.toUpperCase()} · ${k.type.replace(/_/g,' ').toUpperCase()}</b><p>${k.description}</p></div>`).join('')
   :'<div class="note">No cross-document conflicts detected. All six checks passed — every applicant runs through the identical checklist.</div>';
  return `<div class="card"><h3>Extracted Fields (5 documents)</h3><table class="xt"><tr><th>Field</th><th>Value</th></tr>
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
   <p><b>The traffic light:</b> the composite score alone sets the band. Below ${A_LINE} the case is <b style="color:var(--ok)">GREEN — APPROVE</b>, clear-cut and auto-approved. From ${A_LINE} to ${D_LINE-1} it is <b style="color:var(--warn)">YELLOW — MANUAL REVIEW</b>: a human underwriter looks at the application and the person as a whole. At ${D_LINE} or above — or when the application materially misrepresents the medical/identity evidence — it is <b style="color:var(--bad)">RED — DECLINE</b>. Conflicts, affordability and disclosed circumstances are surfaced as flags for the reviewer, but they no longer change the band.</p>
   <div class="scale-wrap">
    <div class="scale-ticks"><span style="left:0%">0</span><span style="left:${A_LINE}%">${A_LINE}</span><span style="left:${D_LINE}%">${D_LINE}</span><span style="left:100%">100</span></div>
    <div class="scale-track">
     <div class="scale-seg" style="width:${A_LINE}%;background:var(--ok)"></div>
     <div class="scale-seg" style="width:${D_LINE-A_LINE}%;background:var(--warn)"></div>
     <div class="scale-seg" style="width:${100-D_LINE}%;background:var(--bad)"></div></div>
    <div class="scale-labels">
     <div class="slab" style="width:${A_LINE}%"><div class="sl-word" style="color:var(--ok)">APPROVE</div><div class="sl-sub">clear-cut, auto-approved</div></div>
     <div class="slab" style="width:${D_LINE-A_LINE}%"><div class="sl-word" style="color:var(--warn)">MANUAL REVIEW</div><div class="sl-sub">a human sees the whole person</div></div>
     <div class="slab" style="width:${100-D_LINE}%"><div class="sl-word" style="color:var(--bad)">DECLINE</div><div class="sl-sub">exceeds appetite / misrepresentation</div></div></div>
   </div>
   <div class="override-note"><span class="on-ic">⚠</span><div><b>Score-driven bands:</b> the composite score sets the decision. Material misrepresentation is the one hard override — it declines regardless of score. Other flags (conflicts, affordability, disclosed circumstances) are shown to the reviewer without changing the band.</div></div></div>
  <div class="card"><h3>Rule Engine — Factor Breakdown</h3>
   ${c.rule_factors.map(f=>`<div class="factor-row"><div><div class="factor-label">${f[0]}</div><div class="factor-detail">${f[1]}</div></div>
    <div class="factor-pts">${f[2]>0?'+':''}${f[2]}</div></div>`).join('')}
   ${c.label!=null?`<div class="note">Ground-truth label: <b>${c.label==1?'High Risk':'Not High Risk'}</b> — synthetic data lets every score be verified against a known answer.</div>`:''}</div>`;
 }
 if(activeTab===5){
  const cls=VM[c.verdict][1];
  const ov=getOverrides()[c.id];
  return `<div class="card"><h3>System Decision</h3><div class="decision-wrap">
   <div class="stamp ${cls}">${c.decision}</div>
   <div class="decision-detail"><h3>${c.rate_class}</h3>
    <div class="why-head">Why this decision</div>
    <ul class="why-list">${c.reasons.map(r=>`<li>${r}</li>`).join('')}</ul>
    <p class="mono" style="font-size:11px;margin-top:10px">Risk ${c.risk_score}/100 · Rule ${c.rule_score} · GB ${c.ml_score.toFixed(0)} · ${c.conflicts.length} conflict(s)</p></div></div>
   ${c.unique?`<div class="unique-banner"><b>UNIQUE CIRCUMSTANCES</b><p style="margin:5px 0 0">“${c.unique}”</p></div>`:''}</div>
  ${affordCard(c.afford)}
  ${caseDeskHTML(c)}
  <div class="card"><div class="ai-head"><h3 style="margin:0">Underwriting Summary — grounded in extracted fields only</h3></div>
   <div class="ai-text">${c.ai_summary}</div></div>`;
 }
}

/* ---------- underwriter overrides: recorded locally, exported for retraining ---------- */
function getOverrides(){try{return JSON.parse(localStorage.getItem('uw_overrides')||'{}');}catch(e){return {};}}
function setOverride(id,label){
 const reason=prompt(label?'Reason for DECLINE override (optional):':'Reason for APPROVE override (optional):')||'';
 const all=getOverrides();
 all[id]={decision:label?'DECLINE':'APPROVE',label:label,reason:reason,at:new Date().toISOString().slice(0,16).replace('T',' ')};
 localStorage.setItem('uw_overrides',JSON.stringify(all));render();
}
function clearOverride(id){const all=getOverrides();delete all[id];localStorage.setItem('uw_overrides',JSON.stringify(all));render();}
function exportOverrides(){
 const all=getOverrides();
 const rows=Object.entries(all).map(([id,o])=>{
  const c=CASES.find(x=>x.id===id);if(!c)return null;
  const d=c.decl||{};
  return {id:id,label:o.label,decision:o.decision,reason:o.reason,at:o.at,fields:{
   "Age":c.age,"BMI":c.bmi,"Smoker Status":c.smoker,"Existing Conditions":c.conditions,
   "Family History Flag":c.family,"Debt-to-Income Ratio":c.dti,"Credit Score":c.credit,
   "Hazardous Activities":c.hazard,"Driving Violations (3yr)":c.violations,
   "Alcohol Use":c.alcohol,"External Risk Prior":c.ext_prior,"Published CVD Prior":c.pub_prior||0.1,
   "Prior Application Declined":d.prior_decline||0,"Dangerous Driving (5yr)":d.dangerous_driving||0,
   "Drug/Alcohol Counselling (5yr)":d.drug_use||0,"Criminal Record":d.criminal||0,
   "Bankruptcy Declared":d.bankruptcy||0,"Foreign Travel Planned":d.foreign_travel||0,
   "Weight Change 10lb (12mo)":d.weight_change||0}};}).filter(Boolean);
 if(!rows.length){alert('No overrides recorded yet — use the Decision tab of any case.');return;}
 const a=document.createElement('a');
 a.href=URL.createObjectURL(new Blob([JSON.stringify(rows,null,2)],{type:'application/json'}));
 a.download='overrides.json';a.click();
 alert(rows.length+' override(s) exported. Save the file to data/overrides.json in the repo and re-run the pipeline — the models will train on these human decisions.');
}
function downloadMemo(id){
 const c=CASES.find(x=>x.id===id);if(!c)return;
 const vm=VM[c.verdict];const ov=getOverrides()[id];
 const colr={ok:'#0E9F6E',warn:'#D97706',bad:'#DC2626'}[vm[1]];
 const html=`<!doctype html><html><head><meta charset="utf-8"><title>Decision Memo — ${c.id}</title>
<style>body{font-family:Georgia,serif;max-width:720px;margin:40px auto;color:#111;line-height:1.55}
h1{font-size:20px;border-bottom:2px solid #111;padding-bottom:8px}h2{font-size:14px;margin:22px 0 6px;text-transform:uppercase;letter-spacing:1px;color:#555}
.verdict{display:inline-block;border:3px solid ${colr};color:${colr};font-weight:700;padding:8px 18px;font-size:18px;letter-spacing:2px}
td{padding:4px 14px 4px 0;font-size:14px}.mut{color:#666;font-size:12px}</style></head><body>
<h1>Underwriting Decision Memo — ${c.name} (${c.id})</h1>
<p class="mut">Generated ${new Date().toISOString().slice(0,10)} · Underwriting Copilot MVP · composite risk ${c.risk_score}/100${CURRENT_USER?` · Reviewed by ${CURRENT_USER} (${CURRENT_ROLE})`:''}</p>
<p><span class="verdict">${ov?ov.decision+' (HUMAN OVERRIDE)':c.decision}</span></p>
${ov&&ov.reason?`<p><b>Override reason:</b> ${ov.reason}</p>`:''}
<h2>Rate class</h2><p>${c.rate_class}</p>
${c.afford?`<h2>Financial viability</h2><p><b>${c.afford.label}</b> — estimated premium ${fmt$(c.afford.premium)}/yr (${(c.afford.pti*100).toFixed(1)}% of income) · coverage ${c.afford.cov_mult.toFixed(1)}× income against a cap of ${c.afford.cov_cap}× · disposable income after premium ${fmt$(c.afford.disposable)}/mo · debt service ${(c.afford.dsr*100).toFixed(0)}% of net.</p>`:''}
<h2>Basis for decision</h2><ul>${c.reasons.map(r=>`<li>${r}</li>`).join('')}</ul>
${c.unique?`<h2>Unique circumstances disclosed</h2><p>“${c.unique}”</p>`:''}
<h2>Summary</h2><p>${c.ai_summary}</p>
<h2>Scores</h2><table><tr><td>Composite risk</td><td><b>${c.risk_score}/100</b></td></tr>
<tr><td>Rule engine</td><td>${c.rule_score}/100</td></tr><tr><td>Gradient boosting</td><td>${c.ml_score.toFixed(0)}/100</td></tr>
<tr><td>External-data prior</td><td>${(c.ext_prior*100).toFixed(0)}%</td></tr>
<tr><td>Cross-document conflicts</td><td>${c.conflicts.length}</td></tr></table>
<h2>Rule factor breakdown</h2><table>${c.rule_factors.map(f=>`<tr><td>${f[0]}</td><td>${f[1]}</td><td><b>+${f[2]}</b></td></tr>`).join('')}</table>
</body></html>`;
 const a=document.createElement('a');
 a.href=URL.createObjectURL(new Blob([html],{type:'text/html'}));
 a.download='decision_memo_'+c.id+'.html';a.click();
}

/* ---------- live scoring: same rule engine + trained logistic model, in-browser ---------- */
function ruleScoreJS(f){
 const factors=[];
 let p=f.age<30?0:f.age<=45?5:f.age<=55?10:18;factors.push(["Applicant age",f.age+" years",p]);
 p=f.smoker==="Smoker"?25:f.smoker==="Former smoker"?8:0;factors.push(["Tobacco use",f.smoker,p]);
 p=(f.bmi<18.5||f.bmi>=35)?15:f.bmi>=30?8:f.bmi>=25?3:0;factors.push(["Body mass index",f.bmi.toFixed(1)+" BMI",p]);
 const conds=f.conditions.trim()&&f.conditions.trim().toLowerCase()!=="none"?f.conditions.split(",").map(s=>s.trim()).filter(Boolean):[];
 p=conds.reduce((s,c)=>s+(c.toLowerCase().includes("diabetes")?15:8),0);factors.push(["Medical conditions",conds.join(", ")||"None",p]);
 p=f.family?6:0;factors.push(["Family medical history",f.family?"Family history disclosed":"None disclosed",p]);
 const dti=f.income>0?f.debt/f.income:0;
 p=dti<0.2?0:dti<0.35?5:dti<0.5?12:20;factors.push(["Debt-to-income ratio",(dti*100).toFixed(1)+"%",p]);
 p=f.credit>750?0:f.credit>=700?3:f.credit>=650?8:15;factors.push(["Credit score",String(f.credit),p]);
 p=f.hazard?10:0;factors.push(["Hazardous activities",f.hazard?(f.hazardDetail||"Yes"):"None disclosed",p]);
 p=f.violations===0?0:f.violations<=2?4:10;factors.push(["Driving record",f.violations+" violation(s) in 3 years",p]);
 p=f.alcohol==="Heavy"?12:f.alcohol==="Moderate"?2:0;factors.push(["Alcohol use",f.alcohol,p]);
 [["priorDecline","Prior insurance declined/modified/rated",8],["dangerousDriving","Careless/dangerous driving or licence suspension",12],
  ["drugUse","Drug use or alcohol/drug counselling",15],["criminal","Criminal offence charged or convicted",8],
  ["bankruptcy","Personal/business bankruptcy",10],["foreignTravel","Foreign travel planned, next 12 months",3],
  ["weightChange","Weight change >10 lb in past 12 months",4]]
  .forEach(([k,label,pts])=>{factors.push([label,f[k]?"Yes":"No",f[k]?pts:0]);});
 return [Math.min(factors.reduce((s,x)=>s+x[2],0),100),factors];
}
function framinghamJS(f){
 // Framingham office-based general-CVD model (D'Agostino 2008) — published
 // coefficients, identical to src/published_models.py
 const P=f.sex==="F"
  ?{a:2.72107,b:0.51125,s:2.81291,sm:0.61868,d:0.77763,s0:0.94833,m:26.0145}
  :{a:3.11296,b:0.79277,s:1.85508,sm:0.70953,d:0.53160,s0:0.88431,m:23.9802};
 const age=Math.min(74,Math.max(30,f.age)),bmi=Math.min(50,Math.max(15,f.bmi)),
       sbp=Math.min(200,Math.max(90,f.sysbp));
 const sum=P.a*Math.log(age)+P.b*Math.log(bmi)+P.s*Math.log(sbp)
  +(f.smoker==="Smoker"?P.sm:0)+(f.conditions.toLowerCase().includes("diabetes")?P.d:0);
 return 1-Math.pow(P.s0,Math.exp(sum-P.m));
}
function extPriorJS(f){
 // identical computation to external_data.prior_scores(): AUC-weighted mean
 const pm=M.risk_models.prior_export||[];if(!pm.length)return 0.5;
 const cx={age:f.age,bmi:f.bmi,smoker:f.smoker==="Smoker"?1:0,
  diabetes:f.conditions.toLowerCase().includes("diabetes")?1:0,sys_bp:f.sysbp,chol:f.chol,
  sex:f.sex==="M"?1:f.sex==="F"?0:0.5};
 let s=0,ws=0;
 pm.forEach(m=>{let z=m.intercept;
  m.features.forEach((n,i)=>{z+=m.coef[i]*((cx[n]-m.mean[i])/m.std[i]);});
  const w=(m.weight!=null?m.weight:1);
  s+=w/(1+Math.exp(-z));ws+=w;});
 return ws>0?s/ws:0.5;
}
function mlScoreJS(f,prior){
 const ex=M.risk_models.lr_export;
 const conds=f.conditions.trim()&&f.conditions.trim().toLowerCase()!=="none"?f.conditions.split(",").filter(s=>s.trim()).length:0;
 const dti=Math.min(Math.max(f.income>0?f.debt/f.income:0,0),3);
 const x={Age:f.age,BMI:f.bmi,smoker_now:f.smoker==="Smoker"?1:0,smoker_former:f.smoker==="Former smoker"?1:0,
  n_conditions:conds,"Family History Flag":f.family?1:0,"Debt-to-Income Ratio":dti,"Credit Score":f.credit,
  hazardous_activity:f.hazard?1:0,driving_violations:f.violations,alcohol_heavy:f.alcohol==="Heavy"?1:0,
  prior_decline:f.priorDecline?1:0,dangerous_driving:f.dangerousDriving?1:0,drug_use:f.drugUse?1:0,
  criminal_record:f.criminal?1:0,bankruptcy:f.bankruptcy?1:0,foreign_travel:f.foreignTravel?1:0,
  weight_change:f.weightChange?1:0,
  external_prior:prior,published_cvd_prior:framinghamJS(f)};
 let z=ex.intercept;
 ex.features.forEach((name,i)=>{z+=ex.coef[i]*((x[name]-ex.scaler_mean[i])/ex.scaler_std[i]);});
 return 100/(1+Math.exp(-z));
}
function premiumJS(age,smoker,coverage,policy){
 // identical to engine.estimate_premium
 const mult={"Term Life - 20yr":1,"Term Life - 30yr":1.45,"Universal Life":5,"Whole Life":8.5};
 let rate=0.9*Math.exp(0.045*(age-30));
 if(smoker==="Smoker")rate*=2.3;else if(smoker==="Former smoker")rate*=1.25;
 return coverage/1000*rate*(mult[policy]||1);
}
function affordJS(f){
 // identical to engine.affordability_assess (4-indicator financial viability screen)
 const income=Math.max(f.income,1),net=income*0.78/12,prem=premiumJS(f.age,f.smoker,f.coverage,f.policy);
 const pm=prem/12,pti=prem/income,disp=net-f.expenses-pm,dpay=f.debt*0.025,dsr=dpay/net;
 const cap=f.age<40?25:f.age<50?20:f.age<60?15:10;
 const cmult=f.coverage/income;
 const ind=[],reasons=[];
 const add=(label,value,status,detail)=>{ind.push({label,value,status,detail});if(status==="fail")reasons.push(label+": "+detail);};
 add("Premium-to-income",(pti*100).toFixed(1)+"%",pti<=0.05?"pass":pti<=0.10?"strain":"fail",
  `annual premium ${fmt$(prem)} is ${(pti*100).toFixed(1)}% of gross income (benchmark ≤5%, strained to 10%)`);
 const floor=Math.max(0.05*net,150);
 add("Disposable income after premium",fmt$(disp)+"/mo",disp<0?"fail":disp<floor?"strain":"pass",
  `net ${fmt$(net)}/mo − expenses ${fmt$(f.expenses)}/mo − premium ${fmt$(pm)}/mo leaves ${fmt$(disp)}/mo (floor ${fmt$(floor)})`);
 add("Coverage-to-income multiple",cmult.toFixed(1)+"×",cmult<=cap?"pass":cmult<=cap*1.1?"strain":"fail",
  `total coverage sought is ${cmult.toFixed(1)}× income against an age-${f.age} cap of ${cap}×`);
 add("Debt-service ratio",(dsr*100).toFixed(0)+"%",dsr<=0.20?"pass":dsr<=0.35?"strain":"fail",
  `estimated debt payments ${fmt$(dpay)}/mo consume ${(dsr*100).toFixed(0)}% of net income (benchmark ≤20%)`);
 const sts=ind.map(i=>i.status);
 const verdict=sts.includes("fail")?"fail":sts.includes("strain")?"strain":"pass";
 if(verdict==="strain")reasons.push("Affordability indicators are within tolerance but strained: "+ind.filter(i=>i.status==="strain").map(i=>i.label).join("; "));
 return {verdict,label:{pass:"AFFORDABLE",strain:"STRAINED",fail:"NOT JUSTIFIED"}[verdict],
  premium:prem,premium_monthly:pm,pti,disposable:disp,cov_mult:cmult,cov_cap:cap,dsr,indicators:ind,reasons};
}
function decideJS(rule,ml,unique,afford){
 const comp=Math.round(0.5*rule+0.5*ml);const reasons=[];
 const affFail=afford&&afford.verdict==="fail";
 let verdict,decision,rate;
 // Score-driven bands (same rule as the portfolio): the composite score sets
 // the decision; disclosed circumstances and affordability are shown as flags.
 if(comp>=D_LINE){verdict="red";decision="DECLINE";rate="Declined — Risk Exceeds Appetite";
  reasons.push(`Composite risk score ${comp}/100 is at or above the ${D_LINE}-point decline line`);}
 else if(comp>=A_LINE){verdict="yellow";decision="MANUAL REVIEW";rate="Referred — Senior Underwriter Review";
  reasons.push(`Composite score ${comp} sits in the ${A_LINE}–${D_LINE-1} manual-review band`);}
 else{verdict="green";decision="APPROVE";rate=comp<=25?"Preferred Rate Class":"Standard Rate Class";
  reasons.push(`Composite score ${comp} is below the ${A_LINE}-point approval line`);}
 if(unique)reasons.push("Flag: applicant disclosed unique circumstances: "+unique);
 if(affFail){reasons.push("Flag: affordability screen refers to financial underwriting");afford.reasons.forEach(r=>reasons.push(r));}
 else if(afford&&afford.verdict==="strain")reasons.push("Affordability is strained but within tolerance");
 return {verdict,decision,rate,comp,reasons};
}
let pdfLoaded=false;
function scoreView(){
 pdfLoaded=false;
 return `<div class="case-head"><div><h2>Score a New Application</h2>
  <div class="case-meta"><span>Upload the application PDF — everything else is optional</span><span>scored live with the same engines as the portfolio</span></div></div></div>
 <div class="card" style="margin-top:18px"><h3>1 · Application PDF (required)</h3>
  <div class="drop-zone" id="dropZone" onclick="document.getElementById('pdfInput').click()">Click to upload the application form PDF — name, DOB, income, debt and coverage are extracted automatically. Scoring unlocks once a PDF is read.</div>
  <input type="file" id="pdfInput" accept="application/pdf" style="display:none">
 </div>
 <div class="card"><h3>2 · Optional — correct or add anything the PDF didn't capture</h3>
  <div class="note" style="margin:0 0 14px">Every field below is optional. Anything extracted from the PDF is filled in for you; anything left blank falls back to a standard assumption and is listed on the result.</div>
  <div class="form-grid">
   <div><label>Full name</label><input id="f_name" placeholder="from PDF"></div>
   <div><label>Sex</label><select id="f_sex"><option value="">Unspecified</option><option value="M">Male</option><option value="F">Female</option></select></div>
   <div><label>Age</label><input id="f_age" type="number" min="18" max="85" placeholder="from PDF (default 40)"></div>
   <div><label>Credit score</label><input id="f_credit" type="number" min="300" max="850" placeholder="default 715"></div>
   <div><label>Annual income (USD)</label><input id="f_income" type="number" placeholder="from PDF (default 60,000)"></div>
   <div><label>Total debt (USD)</label><input id="f_debt" type="number" placeholder="from PDF (default 20,000)"></div>
   <div><label>Coverage requested (USD)</label><input id="f_coverage" type="number" placeholder="from PDF (default 300,000)"></div>
   <div><label>Monthly expenses (USD)</label><input id="f_expenses" type="number" placeholder="default 55% of monthly income"></div>
   <div><label>Policy type</label><select id="f_policy"><option>Term Life - 20yr</option><option>Term Life - 30yr</option><option>Universal Life</option><option>Whole Life</option></select></div>
   <div><label>BMI</label><input id="f_bmi" type="number" step="0.1" placeholder="default 25"></div>
   <div><label>Systolic blood pressure</label><input id="f_sysbp" type="number" placeholder="default 120"></div>
   <div><label>Total cholesterol (mg/dL)</label><input id="f_chol" type="number" placeholder="default 200"></div>
   <div><label>Tobacco use</label><select id="f_smoker"><option>Non-smoker</option><option>Former smoker</option><option>Smoker</option></select></div>
   <div><label>Alcohol use</label><select id="f_alcohol"><option>None</option><option selected>Moderate</option><option>Heavy</option></select></div>
   <div><label>Existing conditions (comma-separated)</label><input id="f_conditions" placeholder="default None"></div>
   <div><label>Family history of serious illness</label><select id="f_family"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div><label>Driving violations (3 yr)</label><input id="f_violations" type="number" min="0" max="10" placeholder="default 0"></div>
   <div><label>Hazardous activities</label><select id="f_hazard" onchange="document.getElementById('hazardWrap').style.display=this.value==='1'?'block':'none'"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div class="fg-wide" id="hazardWrap" style="display:none"><label>If yes, describe the activity</label><input id="f_hazard_detail" placeholder="e.g. Skydiving, scuba diving, motorcycle racing"></div>
   <div><label>Unique circumstances to disclose?</label><select id="f_unique" onchange="document.getElementById('uniqueWrap').style.display=this.value==='1'?'block':'none'"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div class="fg-wide" id="uniqueWrap" style="display:none"><label>Tell us — a human underwriter will read this</label><textarea id="f_unique_text" rows="2" placeholder="e.g. Recent job change, caregiving gap, rebuilt finances after bankruptcy…"></textarea></div>
  </div>
  <h3 style="margin-top:22px">Section 6 — Personal Declarations <span style="font-weight:400;text-transform:none;letter-spacing:0">(per the term-life application; answer what applies)</span></h3>
  <div class="form-grid">
   <div><label>Insurance ever declined / modified / rated?</label><select id="f_priorDecline"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div><label>Careless/dangerous driving or suspension, 5 yr?</label><select id="f_dangerousDriving"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div><label>Foreign travel planned, next 12 months?</label><select id="f_foreignTravel"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div><label>Drug use or alcohol/drug counselling, 5 yr?</label><select id="f_drugUse"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div><label>Criminal offence, charged or convicted?</label><select id="f_criminal"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div><label>Bankruptcy declared or contemplated?</label><select id="f_bankruptcy"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div><label>Weight changed >10 lb in past 12 months?</label><select id="f_weightChange"><option value="0">No</option><option value="1">Yes</option></select></div>
   <div class="fg-wide"><label>Details for any “Yes” above (shown to the underwriter)</label><textarea id="f_decl_text" rows="2" placeholder="e.g. Licence suspended 2023, reinstated; bankruptcy discharged 2022…"></textarea></div>
  </div>
  <button class="score-btn" id="scoreBtn" onclick="scoreNow()" disabled style="opacity:.45;cursor:not-allowed">Upload the application PDF to score</button></div>
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
   // each field tries multiple label synonyms so forms from other carriers still auto-fill
   const grab=(labels,re,flags="i")=>{for(const label of labels){
    const m=text.match(new RegExp(label+"[\\s\\S]{0,60}?("+re+")",flags));if(m)return m[1];}return null;};
   // name value must match case-SENSITIVELY (no "i") or the [A-Z]/[a-z] token
   // classes stop distinguishing names from the next ALL-CAPS form label
   const name=grab(["FULL NAME","Full [Nn]ame","APPLICANT NAME","NAME OF APPLICANT","INSURED NAME","\\bNAME\\b"],"[A-Z][a-zA-Z'’-]*[a-z](?:\\s+[A-Z][a-zA-Z'’-]*[a-z])+","");
   if(name){document.getElementById('f_name').value=name;got.push('name');}
   const dob=grab(["DATE OF BIRTH","\\bDOB\\b","BIRTH DATE"],"\\d{4}-\\d{2}-\\d{2}")
    ||grab(["DATE OF BIRTH","\\bDOB\\b","BIRTH DATE"],"\\d{1,2}/\\d{1,2}/\\d{4}");
   if(dob){const age=Math.floor((Date.now()-new Date(dob))/31557600000);
    if(age>0&&age<110){document.getElementById('f_age').value=age;got.push('age (from DOB '+dob+')');}}
   const inc=grab(["DECLARED ANNUAL INCOME","ANNUAL INCOME","GROSS ANNUAL INCOME","ANNUALIZED GROSS INCOME","YEARLY INCOME","SALARY"],"[\\d,]{4,}");
   if(inc){document.getElementById('f_income').value=parseFloat(inc.replace(/,/g,''));got.push('income');}
   const debt=grab(["DECLARED TOTAL DEBT","TOTAL DEBT","EXISTING DEBT","OUTSTANDING DEBT","TOTAL LIABILITIES"],"[\\d,]{3,}");
   if(debt){document.getElementById('f_debt').value=parseFloat(debt.replace(/,/g,''));got.push('debt');}
   const cov=grab(["COVERAGE AMOUNT REQUESTED","COVERAGE AMOUNT","FACE AMOUNT","SUM ASSURED","BENEFIT AMOUNT"],"[\\d,]{4,}");
   if(cov){document.getElementById('f_coverage').value=parseFloat(cov.replace(/,/g,''));got.push('coverage');}
   const ht=grab(["HEIGHT / WEIGHT","HEIGHT"],"[\\d.]+\\s*cm\\s*/\\s*[\\d.]+\\s*kg");
   if(ht){const hm=ht.match(/([\d.]+)\s*cm\s*\/\s*([\d.]+)\s*kg/);
    if(hm){const bmi=parseFloat(hm[2])/Math.pow(parseFloat(hm[1])/100,2);
     if(bmi>10&&bmi<70){document.getElementById('f_bmi').value=bmi.toFixed(1);got.push('BMI (from height/weight)');}}}
   const bp=grab(["BLOOD PRESSURE","\\bBP\\b"],"\\d{2,3}/\\d{2,3}");
   if(bp){document.getElementById('f_sysbp').value=parseInt(bp);got.push('blood pressure');}
   const ch=grab(["TOTAL CHOLESTEROL","CHOLESTEROL"],"\\d{3}");
   if(ch){document.getElementById('f_chol').value=parseInt(ch);got.push('cholesterol');}
   const smokeYes=/TOBACCO[\s\S]{0,120}?YES|SMOKER\s*STATUS[\s\S]{0,40}?(CURRENT\s+)?SMOKER\b/i.test(text)&&!/NON-?SMOKER/i.test(text);
   if(smokeYes){document.getElementById('f_smoker').value='Smoker';got.push('tobacco (flagged — confirm)');}
   dz.className='drop-zone loaded';
   dz.textContent=got.length?('✓ '+file.name+' — extracted '+got.join(', ')+'. Adjust anything below if needed, then score.')
    :('✓ '+file.name+' read, but no known fields matched — fill in what you know below.');
   pdfLoaded=true;
   const b=document.getElementById('scoreBtn');
   b.disabled=false;b.style.opacity='1';b.style.cursor='pointer';b.textContent='Score Application';
  }catch(err){dz.textContent='Could not read PDF ('+err.message+') — please try another file. A PDF is required to score.';}
 });
}
function scoreNow(){
 if(!pdfLoaded){document.getElementById('dropZone').scrollIntoView({behavior:'smooth'});return;}
 const v=id=>document.getElementById(id).value;
 const defaulted=[];
 const num=(id,dflt,label)=>{const x=v(id);if(x===''||isNaN(+x)){defaulted.push(label+' = '+dflt);return dflt;}return +x;};
 const incomeIn=(v('f_income')===''||isNaN(+v('f_income')))?60000:+v('f_income');
 const f={name:v('f_name')||'New Applicant',
  age:num('f_age',40,'age'),credit:num('f_credit',715,'credit score'),income:num('f_income',60000,'income'),
  debt:num('f_debt',20000,'debt'),coverage:num('f_coverage',300000,'coverage'),bmi:num('f_bmi',25,'BMI'),
  sysbp:num('f_sysbp',120,'systolic BP'),chol:num('f_chol',200,'cholesterol'),
  expenses:num('f_expenses',Math.round(incomeIn/12*0.55),'monthly expenses'),policy:v('f_policy'),
  smoker:v('f_smoker'),alcohol:v('f_alcohol'),sex:v('f_sex'),
  conditions:v('f_conditions')||'None',family:+v('f_family'),violations:num('f_violations',0,'driving violations'),
  hazard:v('f_hazard')==='1',hazardDetail:v('f_hazard_detail'),
  priorDecline:v('f_priorDecline')==='1',dangerousDriving:v('f_dangerousDriving')==='1',
  foreignTravel:v('f_foreignTravel')==='1',drugUse:v('f_drugUse')==='1',
  criminal:v('f_criminal')==='1',bankruptcy:v('f_bankruptcy')==='1',weightChange:v('f_weightChange')==='1',
  declText:v('f_decl_text').trim(),
  unique:v('f_unique')==='1'?(v('f_unique_text').trim()||'Disclosed — details pending'):null};
 const [rule,factors]=ruleScoreJS(f);
 const prior=extPriorJS(f);
 const ml=mlScoreJS(f,prior);
 const af=affordJS(f);
 const d=decideJS(rule,ml,f.unique,af);
 const esc=s=>String(s).replace(/</g,'&lt;');
 const vbSub={green:"Clear-cut acceptable risk. This applicant should be approved — every signal is clean and the score is comfortably below the approval line.",
  yellow:"A human underwriter needs to review this application and the person as a whole before a decision is issued.",
  red:"This application should be declined — the risk clearly exceeds appetite at the disclosed values."};
 document.getElementById('scoreResult').innerHTML=`
  <div class="verdict-banner v-${d.verdict}"><div class="vb-word">${d.decision} — ${esc(f.name)}</div>
   <div class="vb-sub"><b>${d.rate}.</b> ${vbSub[d.verdict]} Financial viability: <b>${af.label}</b> — estimated premium ${fmt$(af.premium)}/yr (${(af.pti*100).toFixed(1)}% of income).</div></div>
  ${affordCard(af)}
  <div class="card"><h3>Live Composite Score</h3>
   <div class="gauge-wrap">${gauge(d.comp)}
    <div class="gauge-info">
     <div class="g-band cls-${VM[d.verdict][1]}">${VM[d.verdict][0]}</div>
     <div class="why-head">Why this decision</div>
     <ul class="why-list">${d.reasons.map(r=>`<li>${esc(r)}</li>`).join('')}</ul>
     <div class="sub-scores">
      <div class="sub-score"><div class="ss-l">Rule engine (50%)</div><div class="ss-v">${rule}</div><div class="bar-track"><div class="bar-fill" style="width:${rule}%;background:var(--acc)"></div></div></div>
      <div class="sub-score"><div class="ss-l">ML — logistic (50%)</div><div class="ss-v">${ml.toFixed(0)}</div><div class="bar-track"><div class="bar-fill" style="width:${ml}%;background:var(--acc)"></div></div></div>
      <div class="sub-score"><div class="ss-l">External-data prior (${(M.risk_models.prior_export||[]).length} real datasets)</div><div class="ss-v">${(prior*100).toFixed(0)}</div><div class="bar-track"><div class="bar-fill" style="width:${prior*100}%;background:var(--mut)"></div></div></div>
     </div></div></div></div>
  ${defaulted.length?`<div class="card"><div class="note" style="margin:0"><b>Standard assumptions used for blank fields:</b> ${defaulted.join(' · ')}. Fill them in above and re-score for a sharper read.</div></div>`:''}
  ${f.unique?`<div class="unique-banner"><b>UNIQUE CIRCUMSTANCES DISCLOSED</b><p style="margin:5px 0 0">“${esc(f.unique)}” — shown to the reviewing underwriter alongside the score.</p></div>`:''}
  ${f.hazard&&f.hazardDetail?`<div class="unique-banner"><b>HAZARDOUS ACTIVITY DETAIL</b><p style="margin:5px 0 0">“${esc(f.hazardDetail)}”</p></div>`:''}
  ${(()=>{const yes=[["priorDecline","prior insurance declined/modified/rated"],["dangerousDriving","careless/dangerous driving or licence suspension"],
    ["foreignTravel","foreign travel planned"],["drugUse","drug use or alcohol/drug counselling"],
    ["criminal","criminal offence"],["bankruptcy","bankruptcy declared or contemplated"],["weightChange","weight change >10 lb"]]
    .filter(([k])=>f[k]).map(([,l])=>l);
   return yes.length?`<div class="unique-banner"><b>SECTION 6 DECLARATIONS — ANSWERED YES</b>
    <p style="margin:5px 0 0">${yes.join(' · ')}${f.declText?` — “${esc(f.declText)}”`:''}</p></div>`:'';})()}
  <div class="card"><h3>Factor Breakdown (rule engine)</h3>
   ${factors.map(x=>`<div class="factor-row"><div><div class="factor-label">${esc(x[0])}</div><div class="factor-detail">${esc(x[1])}</div></div><div class="factor-pts">${x[2]>0?'+':''}${x[2]}</div></div>`).join('')}
   <div class="note">The ML half uses the trained logistic-regression coefficients exported from the pipeline (the browser cannot run gradient boosting; logistic is its auditable stand-in, AUC ${(M.risk_models.logistic_regression.auc*100).toFixed(1)}%), including the external-data prior learned from ${((M.external_learning||{}).total_rows||0).toLocaleString()} real records across ${(M.risk_models.prior_export||[]).length} public datasets. Portfolio cases are scored offline with the full dual engine.</div></div>`;
 document.getElementById('scoreResult').scrollIntoView({behavior:'smooth'});
}
render();
// Esc returns from a case file to the queue with its context intact (§3.3).
document.addEventListener('keydown',e=>{if(!CURRENT_ROLE||view!=='case')return;
 if(e.key==='Escape')goBack();
 else if(e.key==='ArrowRight'&&!e.target.matches('input,textarea,select'))nextCase();
 else if(e.key==='ArrowLeft'&&!e.target.matches('input,textarea,select'))prevCase();});
// keep SLA timers + priority ranking live (queue/case views only, so forms aren't disturbed)
setInterval(()=>{if(CURRENT_ROLE&&(view==='space'||view==='case'))render();},60000);
</script>
"""

APPROVE_LINE, DECLINE_LINE = 50, 90  # fallback; build() overrides from pipeline thresholds

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
    decl = c.get("decl") or {}
    decl_names = {"prior_decline": "a previously declined/rated insurance application",
                  "dangerous_driving": "careless or dangerous driving within five years",
                  "drug_use": "drug use or alcohol/drug counselling",
                  "criminal": "a criminal offence", "bankruptcy": "a declared bankruptcy",
                  "foreign_travel": "planned foreign travel", "weight_change": "a >10 lb weight change this year"}
    yes = [decl_names[k] for k, v in decl.items() if v and k in decl_names]
    if yes:
        life.append("answered Yes on the Section 6 declarations to " + ", ".join(yes))
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
    af = c.get("afford")
    if af:
        s.append(f"On financial viability, the estimated premium of {_money(af['premium'])}/yr "
                 f"is {af['pti']*100:.1f}% of income and the coverage sought is "
                 f"{af['cov_mult']:.1f}× income — the affordability screen reads {af['label']}."
                 + (f" {af['reasons'][0]}." if af["verdict"] == "fail" and af.get("reasons") else ""))
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
    import summaries
    with open(os.path.join(OUT, "portfolio.json")) as f:
        data = json.load(f)
    use_llm = bool(os.environ.get("ANTHROPIC_API_KEY"))
    llm_limit = int(os.environ.get("LLM_SUMMARY_LIMIT", 40))
    n_llm = 0
    for c in data["cases"]:
        text = None
        if use_llm and n_llm < llm_limit:
            text = summaries.llm_summary(c)
            if text:
                ok, bad = summaries.groundedness_check(text, c)
                if not ok:      # a summary citing untraceable numbers is worse than a template
                    text = None
                else:
                    n_llm += 1
        c["ai_summary"] = text or case_summary(c)
        c["summary_source"] = "llm" if text else "template"
        # §3.6 — neutralise the legacy "Notable" family-history value baked into
        # portfolio.json (engine.py is fixed at source; this cleans already-exported
        # data without a stateful pipeline rerun).
        for f in c.get("rule_factors", []):
            if f[1] == "Notable":
                f[1] = "Family history disclosed"
    if use_llm:
        print(f"LLM summaries: {n_llm}/{len(data['cases'])} generated (grounded), rest templated")
    html = TEMPLATE.replace("/*__DATA__*/", json.dumps(data))
    path = os.path.join(OUT, "underwriting_copilot_mvp.html")
    with open(path, "w") as f:
        f.write(html)
    print(f"dashboard written: {path} ({os.path.getsize(path)//1024} KB, {len(data['cases'])} cases embedded)")

if __name__ == "__main__":
    build()
