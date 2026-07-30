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
.stat .sv{font-family:'Space Grotesk',sans-serif;font-size:30px;font-weight:700}.stat .sl{font-size:11.5px;color:var(--mut);margin-top:2px;line-height:1.45}
/* The metric's NAME carries equal weight to its value — number answers "how much",
   the bold lead answers "of what"; only the explanation is quiet. */
.stat .sl b{display:block;font-family:'Poppins',sans-serif;font-size:22px;font-weight:700;color:var(--ink);line-height:1.14;letter-spacing:-.012em;margin:0 0 5px;text-wrap:balance}
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
/* case-wide conflict alert (shown on every tab so the underwriter can't miss it) */
.conflict-alert{border:2px solid var(--bad);background:var(--bad-soft);border-radius:14px;padding:14px 18px;margin-bottom:16px}
.conflict-alert.warn{border-color:var(--warn);background:var(--warn-soft)}
.conflict-alert .ca-head{font-family:'Poppins',sans-serif;font-weight:700;font-size:14px;color:var(--bad);margin-bottom:6px}
.conflict-alert.warn .ca-head{color:var(--warn)}
.conflict-line{padding:9px 0;border-top:1px solid rgba(242,88,91,.22)}
.conflict-line:first-of-type{border-top:none}
.conf-tag{font-family:'JetBrains Mono',monospace;font-size:10px;font-weight:600;letter-spacing:.4px;color:var(--bad)}
.conflict-line.minor .conf-tag{color:var(--warn)}
.conf-desc{font-size:13px;margin-top:3px;color:var(--ink)}
.conf-vals{font-size:12.5px;margin-top:6px;color:var(--mut);display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.conf-bad{color:var(--bad);background:var(--bad-soft);padding:2px 8px;border-radius:6px;font-family:'JetBrains Mono',monospace;font-weight:600}
/* red-highlighted fields on the Application / Extraction tabs */
.field.field-conflict{background:var(--bad-soft);border-radius:8px;padding-left:8px;margin-left:-8px;border-bottom-color:transparent}
.field-conflict .val{color:var(--bad);font-weight:700}
.fc-badge{color:var(--bad);font-family:'JetBrains Mono',monospace;font-size:8px;letter-spacing:.4px;margin-left:6px}
tr.row-conflict td{background:var(--bad-soft);color:var(--bad);font-weight:700}
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
.banner-x{position:absolute;top:12px;right:14px;background:transparent;border:none;color:var(--warn);font-size:17px;font-weight:700;cursor:pointer;line-height:1;padding:5px 9px;border-radius:8px}
.banner-x:hover{background:rgba(0,0,0,.08)}
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
#app{max-width:1880px;width:calc(100% - 40px);margin:18px auto;min-height:calc(100vh - 36px);background:#0A0A0C !important;border:none !important;border-radius:30px !important;overflow:hidden;box-shadow:0 30px 90px rgba(0,0,0,.55)}
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
/* ---- sign-in whoosh: the wordmark flies through the camera into the workbench ---- */
#whoosh{position:fixed;inset:0;z-index:2050;display:flex;align-items:center;justify-content:center;background:var(--bg);perspective:1000px;overflow:hidden;pointer-events:none;animation:whooshFade 1.7s cubic-bezier(.65,0,.35,1) forwards}
#whoosh .wz{transform-style:preserve-3d;text-align:center;animation:whooshZoom 1.7s cubic-bezier(.5,0,.15,1) forwards}
#whoosh .w-mark,#landing .w-mark{font:800 clamp(34px,6vw,64px) 'Poppins',sans-serif;letter-spacing:-.5px;color:var(--ink)}
#whoosh .w-mark b,#landing .w-mark b{color:var(--acc)}
#whoosh .w-sub,#landing .w-sub{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:3px;color:var(--mut);margin-top:12px}
#whoosh .w-ring{position:absolute;left:50%;top:50%;width:340px;height:340px;margin:-170px 0 0 -170px;border:1.5px solid var(--acc);border-radius:50%;animation:whooshRing 1.7s cubic-bezier(.5,0,.15,1) forwards}
@keyframes whooshZoom{0%{opacity:0;transform:translateZ(-420px) rotateX(16deg)}25%{opacity:1;transform:translateZ(-60px) rotateX(4deg)}48%{opacity:1;transform:translateZ(0) rotateX(0deg)}100%{opacity:0;transform:translateZ(860px) rotateX(-8deg)}}
@keyframes whooshRing{0%{transform:scale(.15);opacity:0}40%{opacity:.35}100%{transform:scale(3.6);opacity:0}}
@keyframes whooshFade{0%,74%{opacity:1}100%{opacity:0}}
#app.app-reveal{animation:appReveal .95s .85s cubic-bezier(.22,1,.36,1) backwards}
@keyframes appReveal{0%{opacity:0;transform:scale(.986) translateY(10px)}100%{opacity:1;transform:none}}
/* ---- role switch: a quick 3D seat-change, distinct from the first-entry whoosh ---- */
#roleswap{position:fixed;inset:0;z-index:2050;display:flex;align-items:center;justify-content:center;pointer-events:none;perspective:1100px;animation:rsScrim .95s ease forwards}
@keyframes rsScrim{0%{background:rgba(24,24,50,0)}30%{background:rgba(24,24,50,.30)}70%{background:rgba(24,24,50,.30)}100%{background:rgba(24,24,50,0)}}
#roleswap .rs-chip{display:flex;align-items:center;gap:13px;padding:16px 26px;border-radius:16px;background:var(--card);border:1px solid var(--line);box-shadow:0 24px 70px rgba(20,20,40,.35);animation:rsChip .95s cubic-bezier(.22,1,.36,1) forwards}
@keyframes rsChip{0%{opacity:0;transform:rotateY(75deg) translateX(110px) scale(.88)}28%{opacity:1;transform:none}72%{opacity:1;transform:none}100%{opacity:0;transform:rotateY(-75deg) translateX(-110px) scale(.88)}}
#roleswap .rs-av{width:42px;height:42px;border-radius:50%;background:var(--acc);color:#fff;display:flex;align-items:center;justify-content:center;font:700 16px 'Poppins',sans-serif;flex:none}
#roleswap .rs-name{font:700 16px 'Poppins',sans-serif;color:var(--ink)}
#roleswap .rs-role{font:500 12px 'Poppins',sans-serif;color:var(--mut)}
#app.role-turn{animation:roleTurn .8s .25s cubic-bezier(.22,1,.36,1) backwards}
@keyframes roleTurn{0%{opacity:.35;transform:translateX(30px) scale(.992)}100%{opacity:1;transform:none}}
@media (prefers-reduced-motion: reduce){#roleswap{display:none}#app.role-turn{animation:none}}
.login-card{animation:loginIn .6s cubic-bezier(.22,1,.36,1) both}
@keyframes loginIn{0%{opacity:0;transform:translateY(14px) scale(.985)}100%{opacity:1;transform:none}}
@media (prefers-reduced-motion: reduce){#whoosh{display:none}#app.app-reveal,.login-card{animation:none}}
.cap-cut td{text-align:center;font:600 10.5px 'JetBrains Mono',monospace;color:var(--warn);padding:10px 6px;border-top:2px dashed var(--warn) !important;border-bottom:2px dashed var(--warn);letter-spacing:.5px}
/* ---- executive rail: book-at-a-glance instead of a case list ---- */
.exec-rail{padding:6px 4px}
/* Numbers carry the panel: value big on top, label a quiet caption beneath.
   Size encodes importance — operating income largest, ratios next, context last. */
.exec-rail .er-row{padding:11px 8px 10px;border-bottom:1px solid var(--line)}
.exec-rail .er-row b{display:block;font:700 19px 'JetBrains Mono',monospace;color:var(--ink);letter-spacing:-.02em;line-height:1.05;white-space:nowrap}
.exec-rail .er-row span{display:block;font:600 9.5px 'JetBrains Mono',monospace;letter-spacing:.7px;text-transform:uppercase;color:var(--mut);margin-top:4px}
.exec-rail .er-hero b{font-size:31px}
.exec-rail .er-big b{font-size:24px}
.exec-rail .er-note{font:500 11px 'Poppins',sans-serif;color:var(--mut);padding:12px 8px 0;line-height:1.5}
/* ---- landing scene: orbiting case artifacts around the wordmark, before sign-in ---- */
#landing{position:fixed;inset:0;z-index:1600;background:var(--bg);display:flex;align-items:center;justify-content:center;overflow:hidden;font-family:'Poppins',sans-serif;perspective:1200px}
#landing::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 50% 42%,rgba(106,103,247,0) 32%,rgba(106,103,247,.14) 64%,rgba(106,103,247,.36) 100%);pointer-events:none}
#landing .ld-glow{position:absolute;border-radius:50%;filter:blur(90px);opacity:.28;animation:ldDrift 16s ease-in-out infinite alternate}
#landing .ld-glow.g1{width:560px;height:560px;left:-120px;top:-120px;background:var(--acc)}
#landing .ld-glow.g2{width:460px;height:460px;right:-100px;bottom:-100px;background:var(--acc);animation-duration:21s}
#landing .ld-glow.g3{width:640px;height:320px;left:50%;margin-left:-320px;bottom:-160px;background:var(--acc);opacity:.18;animation-duration:26s}
@keyframes ldDrift{0%{transform:translate(0,0) scale(1)}100%{transform:translate(70px,45px) scale(1.16)}}
#landing .ld-scene{position:absolute;inset:0;transform-style:preserve-3d;transition:transform .3s ease-out;will-change:transform}
#landing .ld-rings i{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);border:1.5px solid var(--acc);border-radius:50%;opacity:.22}
#landing .ld-rings i:nth-child(1){width:430px;height:430px}
#landing .ld-rings i:nth-child(2){width:660px;height:660px;opacity:.14}
#landing .ld-rings i:nth-child(3){width:900px;height:900px;opacity:.09}
#landing .ld-orbits{position:absolute;left:50%;top:50%;z-index:1}
#landing .ld-orb{position:absolute;left:0;top:0;padding:7px 12px;border-radius:10px;border:1px solid rgba(106,103,247,.38);background:var(--card);color:var(--mut);font:600 11px 'JetBrains Mono',monospace;letter-spacing:.4px;white-space:nowrap;box-shadow:0 8px 24px rgba(106,103,247,.16);animation:ldOrbit var(--t) linear infinite}
/* radar sweep: the copilot scanning the book — a slow beam over the ring field */
#landing .ld-sweep{position:absolute;left:50%;top:50%;width:240vmax;height:240vmax;margin:-120vmax 0 0 -120vmax;border-radius:50%;pointer-events:none;background:conic-gradient(from 0deg,rgba(106,103,247,0) 0deg,rgba(106,103,247,.10) 46deg,rgba(106,103,247,.26) 58deg,rgba(106,103,247,0) 72deg,rgba(106,103,247,0) 360deg);animation:ldSpin 22s linear infinite}
@keyframes ldSpin{to{transform:rotate(360deg)}}
#landing .ld-orb.far{opacity:.55;filter:blur(.4px);font-size:10px}
@keyframes ldOrbit{0%{transform:translate(-50%,-50%) rotate(var(--a)) translateX(var(--r)) rotate(calc(-1*var(--a)))}100%{transform:translate(-50%,-50%) rotate(calc(var(--a) + 360deg)) translateX(var(--r)) rotate(calc(-1*var(--a) - 360deg))}}
#landing .ld-center{position:relative;text-align:center;z-index:3;animation:ldIn 1.1s cubic-bezier(.22,1,.36,1) both}
@keyframes ldIn{0%{opacity:0;transform:translateY(20px) scale(.965)}100%{opacity:1;transform:none}}
#landing .ld-tag{font:500 13px 'Poppins',sans-serif;color:var(--mut);margin-top:16px}
#landing .ld-btn{margin-top:26px;padding:13px 42px;border-radius:999px;border:none;background:var(--acc);color:#fff;font:600 15px 'Poppins',sans-serif;cursor:pointer;box-shadow:0 10px 30px rgba(106,103,247,.4);transition:transform .2s;animation:ldPulse 2.6s ease-in-out infinite}
#landing .ld-btn:hover{transform:translateY(-2px)}
@keyframes ldPulse{0%,100%{box-shadow:0 10px 30px rgba(106,103,247,.4)}50%{box-shadow:0 10px 46px rgba(106,103,247,.8),0 0 0 9px rgba(106,103,247,.13)}}
#landing.out{animation:ldOut .9s cubic-bezier(.5,0,.15,1) forwards;pointer-events:none}
@keyframes ldOut{0%{opacity:1}100%{opacity:0}}
#landing.out .ld-center{animation:ldCenterOut .9s cubic-bezier(.5,0,.15,1) forwards}
@keyframes ldCenterOut{0%{opacity:1;transform:none}100%{opacity:0;transform:scale(5.5)}}
@media (prefers-reduced-motion: reduce){#landing .ld-orb,#landing .ld-glow,#landing .ld-center,#landing .ld-sweep,#landing .ld-btn{animation:none}#landing .ld-scene{transform:none !important}}
/* interactive tutorial */
#tourBtn{position:fixed;top:14px;right:66px;z-index:2000;height:40px;padding:0 16px;border-radius:999px;border:none;background:var(--acc);color:#fff;font:600 12.5px 'Poppins',sans-serif;cursor:pointer;box-shadow:0 6px 18px rgba(87,84,240,.4);display:flex;align-items:center;gap:6px}
#tourBtn:hover{filter:brightness(1.07)}
#tourPanel{position:fixed;bottom:20px;right:20px;z-index:2100;width:372px;max-width:calc(100vw - 40px);background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:0 22px 60px rgba(0,0,0,.45);padding:18px 20px;display:none;font-family:'Poppins',sans-serif}
#tourPanel.on{display:block}
.tour-step{font-family:'JetBrains Mono',monospace;font-size:9.5px;letter-spacing:.6px;text-transform:uppercase;color:var(--acc)}
.tour-title{font-size:16px;font-weight:700;color:var(--ink);margin:4px 0 9px;line-height:1.25}
.tour-do{background:var(--acc-soft);border-radius:10px;padding:9px 12px;font-size:12.5px;color:var(--ink);margin-bottom:9px;line-height:1.5}
.tour-do b{color:var(--acc)}
.tour-learn{font-size:12.5px;color:var(--mut);line-height:1.6}
.tour-actions{display:flex;gap:8px;align-items:center;margin-top:14px}
.tour-actions .sp{flex:1}
.tour-btn{font:600 12px 'Poppins',sans-serif;border:none;border-radius:999px;padding:8px 15px;cursor:pointer;background:#26262E;color:#fff}
.tour-btn.prim{background:var(--acc)}
/* tertiary text button: symmetric padding so the label stays centred even if a
   theme rule gives it a background */
.tour-btn.ghost{background:transparent;color:var(--mut);padding:8px 12px}
.tour-btn.doit{background:var(--ok);color:#fff;margin-top:11px}
.tour-btn:disabled{opacity:.4;cursor:default}
.tour-prog{height:4px;background:var(--line);border-radius:999px;overflow:hidden;margin-top:13px}
.tour-prog>div{height:100%;background:var(--acc);border-radius:999px;transition:width .2s}
:root[data-theme="light"] .tour-btn{background:#EAECF2;color:var(--ink)}
:root[data-theme="light"] .tour-btn.prim{background:var(--acc);color:#fff}
:root[data-theme="light"] .tour-btn.doit{background:var(--ok);color:#fff}
/* the ghost button must stay text-only in light mode too — the generic light
   .tour-btn rule outranks .tour-btn.ghost on specificity */
:root[data-theme="light"] .tour-btn.ghost{background:transparent;color:var(--mut)}
:root[data-theme="light"] #tourPanel{box-shadow:0 22px 60px rgba(30,32,60,.22)}
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
/* ---------- sign-in shell: brand panel + form (7/30 redesign) ---------- */
.login-shell{display:grid;grid-template-columns:380px 420px;max-width:94vw;border-radius:24px;overflow:hidden;box-shadow:0 32px 90px rgba(18,18,55,.38);background:var(--card)}
.login-shell .login-card{border-radius:0 !important;box-shadow:none !important;border:none !important;width:auto;max-width:none;padding:34px 36px 30px}
.login-brand{position:relative;overflow:hidden;background:linear-gradient(155deg,#504DC9,#28276E 52%,#131230);padding:38px 34px 30px;display:flex}
.lb-body{position:relative;z-index:2;display:flex;flex-direction:column;gap:14px}
.lb-h{font-family:'Poppins',sans-serif;font-size:23px;font-weight:700;line-height:1.32;color:#fff;margin:2px 0 0}
.lb-h em{font-style:normal;color:#C8C6FF}
.lb-mono{font:600 9.5px 'JetBrains Mono',monospace;letter-spacing:1.1px;color:#A5A3EA}
.lb-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:2px}
.lb-chips span{border:1px solid rgba(255,255,255,.30);color:#EBEAFF;border-radius:999px;padding:5px 11px;font:600 9.5px 'JetBrains Mono',monospace;letter-spacing:.5px;backdrop-filter:blur(2px)}
.lb-foot{margin-top:auto;padding-top:26px;font:500 10.5px 'Poppins',sans-serif;color:#8B89CF;line-height:1.55}
.lb-rings{position:absolute;right:-130px;bottom:-150px;width:380px;height:380px;z-index:1;pointer-events:none}
.lb-rings i{position:absolute;inset:0;border:1px solid rgba(255,255,255,.13);border-radius:50%}
.lb-rings i:nth-child(2){inset:52px}.lb-rings i:nth-child(3){inset:110px;border-color:rgba(255,255,255,.20)}
.lb-sweep{position:absolute;inset:-40%;z-index:0;pointer-events:none;opacity:.5;background:conic-gradient(from 0deg,transparent 0deg,rgba(150,148,255,.16) 40deg,transparent 90deg);animation:lbSpin 26s linear infinite}
@keyframes lbSpin{to{transform:rotate(360deg)}}
.role-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:0 0 20px}
.role-chip{text-align:left;border:1px solid var(--line);background:transparent;border-radius:12px;padding:8px 12px;cursor:pointer;font-family:'Poppins',sans-serif;transition:border-color .12s,background .12s}
.role-chip b{display:block;font-size:12px;font-weight:700;color:var(--ink);line-height:1.3}
.role-chip span{font:600 8.5px 'JetBrains Mono',monospace;letter-spacing:.5px;text-transform:uppercase;color:var(--mut)}
.role-chip:hover{border-color:var(--acc)}
.role-chip.sel{border-color:var(--acc);background:var(--acc-soft)}
.role-chip.sel b{color:var(--acc)}
@media (max-width:880px){.login-shell{grid-template-columns:1fr;max-width:460px}.login-brand{padding:26px 30px 22px}.lb-h{font-size:18px}.lb-foot{padding-top:14px}.lb-rings{display:none}}
@media (prefers-reduced-motion:reduce){.lb-sweep{animation:none}}
/* ---------- sign-in ambience: living aurora ----------
   Four saturated colour fields in constant orbit — never still, never the
   same frame twice. Each blob runs its own loop duration so the composite
   pattern doesn't repeat. Pure CSS, GPU-cheap (transform only). */
.login-shell{position:relative;z-index:2}
.lg-geo{position:absolute;inset:0;z-index:0;pointer-events:none;overflow:hidden}
.au-blob{position:absolute;border-radius:50%;filter:blur(70px);will-change:transform}
.au-blob.a1{width:56vw;height:56vw;left:-14%;top:-24%;background:radial-gradient(circle,#7B78FF 0%,rgba(123,120,255,0) 65%);opacity:.85;animation:auA 17s ease-in-out infinite}
.au-blob.a2{width:48vw;height:48vw;right:-16%;top:-10%;background:radial-gradient(circle,#B39BFF 0%,rgba(179,155,255,0) 65%);opacity:.7;animation:auB 23s ease-in-out infinite}
.au-blob.a3{width:52vw;height:52vw;left:-10%;bottom:-28%;background:radial-gradient(circle,#4E4BD9 0%,rgba(78,75,217,0) 65%);opacity:.8;animation:auC 20s ease-in-out infinite}
.au-blob.a4{width:40vw;height:40vw;right:-8%;bottom:-18%;background:radial-gradient(circle,#8F6BFF 0%,rgba(143,107,255,0) 65%);opacity:.75;animation:auD 14s ease-in-out infinite}
@keyframes auA{0%{transform:translate(0,0) scale(1)}25%{transform:translate(16vw,10vh) scale(1.15)}50%{transform:translate(28vw,-4vh) scale(.95)}75%{transform:translate(10vw,14vh) scale(1.1)}100%{transform:translate(0,0) scale(1)}}
@keyframes auB{0%{transform:translate(0,0) scale(1)}30%{transform:translate(-18vw,16vh) scale(1.12)}60%{transform:translate(-6vw,30vh) scale(.92)}100%{transform:translate(0,0) scale(1)}}
@keyframes auC{0%{transform:translate(0,0) scale(1)}33%{transform:translate(22vw,-14vh) scale(1.08)}66%{transform:translate(6vw,-26vh) scale(1.18)}100%{transform:translate(0,0) scale(1)}}
@keyframes auD{0%{transform:translate(0,0) scale(1)}40%{transform:translate(-20vw,-12vh) scale(1.14)}70%{transform:translate(-30vw,4vh) scale(.9)}100%{transform:translate(0,0) scale(1)}}
.au-sheen{position:absolute;left:50%;top:50%;width:160vmax;height:160vmax;transform:translate(-50%,-50%);
 background:conic-gradient(from 0deg,transparent 0deg,rgba(255,255,255,.10) 55deg,transparent 110deg,rgba(255,255,255,.06) 220deg,transparent 300deg);
 animation:auSheen 28s linear infinite;mix-blend-mode:overlay}
@keyframes auSheen{to{transform:translate(-50%,-50%) rotate(360deg)}}
:root[data-theme="light"] .au-blob{opacity:.72}
:root[data-theme="light"] .au-blob.a1{opacity:.8}
:root[data-theme="light"] .au-blob.a3{opacity:.75}
@media (prefers-reduced-motion:reduce){.au-blob,.au-sheen{animation:none}}
/* ---------- UW Guide — embedded knowledge assistant ---------- */
#uwgBtn{position:fixed;right:20px;bottom:20px;z-index:960;display:none;align-items:center;gap:6px;font:600 12.5px 'Poppins',sans-serif;color:#fff;background:var(--acc);border:none;border-radius:999px;padding:11px 18px;cursor:pointer;box-shadow:0 8px 24px rgba(106,103,247,.38)}
#uwgBtn:hover{filter:brightness(1.08)}
#uwgPanel{position:fixed;right:20px;bottom:74px;z-index:961;width:372px;max-width:calc(100vw - 32px);height:min(540px,calc(100vh - 110px));display:none;flex-direction:column;background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:0 24px 60px rgba(10,10,25,.45);overflow:hidden}
#uwgPanel.on{display:flex}
.uwg-head{display:flex;justify-content:space-between;align-items:center;padding:13px 15px;border-bottom:1px solid var(--line);background:var(--acc-soft)}
.uwg-head b{font:700 14px 'Space Grotesk',sans-serif;color:var(--ink)}
.uwg-sub{font:600 9px 'JetBrains Mono',monospace;letter-spacing:.6px;text-transform:uppercase;color:var(--mut);margin-top:2px}
.uwg-x{cursor:pointer;color:var(--mut);font-size:14px;padding:4px 6px}
.uwg-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}
.uwg-m{max-width:90%;padding:9px 12px;border-radius:12px;font:500 12.5px 'Poppins',sans-serif;line-height:1.55;color:var(--ink)}
.uwg-m.bot{background:var(--acc-soft);border-bottom-left-radius:4px;align-self:flex-start}
.uwg-m.me{background:var(--acc);color:#fff;border-bottom-right-radius:4px;align-self:flex-end}
.uwg-m .mono{font-size:11.5px}
.uwg-chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 12px 10px}
.uwg-chip{font:600 10px 'JetBrains Mono',monospace;color:var(--acc);background:transparent;border:1px solid var(--acc);border-radius:999px;padding:5px 10px;cursor:pointer}
.uwg-chip:hover{background:var(--acc-soft)}
.uwg-input{display:flex;gap:8px;padding:10px 12px;border-top:1px solid var(--line)}
.uwg-input input{flex:1;background:rgba(128,128,128,.10);border:1px solid var(--line);border-radius:10px;padding:9px 12px;font:500 12.5px 'Poppins',sans-serif;color:var(--ink);outline:none}
.uwg-input input:focus{border-color:var(--acc)}
.uwg-input button{background:var(--acc);color:#fff;border:none;border-radius:10px;padding:0 15px;font-size:15px;cursor:pointer}
:root[data-theme="light"] #uwgPanel{box-shadow:0 24px 60px rgba(30,32,60,.22)}
@media (max-width:640px){#uwgPanel{right:8px;left:8px;width:auto}}
</style>
<button id="themeToggle" onclick="toggleTheme()" title="Toggle light / dark mode" aria-label="Toggle light or dark mode">🌙</button>
<button id="tourBtn" onclick="tourStart()" title="Interactive tutorial — learn every feature">🎓 Tutorial</button>
<div id="tourPanel"></div>
<div id="landing">
 <div class="ld-glow g1"></div><div class="ld-glow g2"></div><div class="ld-glow g3"></div>
 <div class="ld-scene">
 <div class="ld-sweep"></div>
 <div class="ld-rings"><i></i><i></i><i></i></div>
 <div class="ld-orbits">
  <span class="ld-orb" style="--r:305px;--t:34s;--a:15deg">RISK 24</span>
  <span class="ld-orb" style="--r:305px;--t:34s;--a:105deg">DOB ✓ VERIFIED</span>
  <span class="ld-orb" style="--r:305px;--t:34s;--a:195deg">STP 77%</span>
  <span class="ld-orb" style="--r:305px;--t:34s;--a:285deg">6-CHECK SCREEN</span>
  <span class="ld-orb far" style="--r:455px;--t:52s;--a:0deg">APS ORDERED</span>
  <span class="ld-orb far" style="--r:455px;--t:52s;--a:72deg">COTININE −</span>
  <span class="ld-orb far" style="--r:455px;--t:52s;--a:144deg">AUC 0.92</span>
  <span class="ld-orb far" style="--r:455px;--t:52s;--a:216deg">$487k /YR</span>
  <span class="ld-orb far" style="--r:455px;--t:52s;--a:288deg">ACORD 103</span>
 </div>
 </div>
 <div class="ld-center">
  <div class="w-mark">Underwriting <b>Copilot</b></div>
  <div class="w-sub">EXTRACTION · CONFLICT SCREEN · RISK SCORE · DECISION</div>
  <div class="ld-tag">Every application read, screened, scored and routed — a human on every borderline call.</div>
  <button class="ld-btn" onclick="landingGo()">Login →</button>
 </div>
</div>
<div id="login">
 <div class="lg-geo" aria-hidden="true">
  <div class="au-blob a1"></div>
  <div class="au-blob a2"></div>
  <div class="au-blob a3"></div>
  <div class="au-blob a4"></div>
  <div class="au-sheen"></div>
 </div>
 <div class="login-shell">
  <div class="login-brand">
   <div class="lb-sweep"></div>
   <div class="lb-rings"><i></i><i></i><i></i></div>
   <div class="lb-body">
    <div class="brandmark" style="color:#BDBBFF">◆ UNDERWRITING COPILOT</div>
    <h2 class="lb-h">Every application read, screened, scored — <em>and routed to the right human.</em></h2>
    <div class="lb-mono">EXTRACTION · CONFLICT SCREEN · RISK SCORE · DECISION</div>
    <div class="lb-chips"><span>STP 83%</span><span>6-CHECK SCREEN</span><span>28·ln WEIGHTS</span><span>$47 / APP</span></div>
    <div class="lb-foot">Synthetic book · 200 applications · no real applicants — sign-in is an honest role selector, not authentication.</div>
   </div>
  </div>
  <div class="login-card">
   <h1>Sign in to the workbench</h1>
   <p class="sub">One product, six seats — the role you pick decides what you see. Choose a persona, or type the credentials.</p>
   <div class="role-grid">
    <button class="role-chip" onclick="loginFill('mrivera','senior',this)"><b>Marcus Rivera</b><span>Senior underwriter</span></button>
    <button class="role-chip" onclick="loginFill('ewong','review',this)"><b>Erin Wong</b><span>Mid-tier underwriter</span></button>
    <button class="role-chip" onclick="loginFill('dpark','analyst',this)"><b>Dana Park</b><span>New analyst</span></button>
    <button class="role-chip" onclick="loginFill('nsethi','oversight',this)"><b>Nadia Sethi</b><span>Manager</span></button>
    <button class="role-chip" onclick="loginFill('mvale','executive',this)"><b>Marcus Vale</b><span>Executive · CUO</span></button>
    <button class="role-chip" onclick="loginFill('panand','admin',this)"><b>Priya Anand</b><span>Operations admin</span></button>
   </div>
   <label>Username</label>
   <input id="loginUser" placeholder="username" autocomplete="off" oninput="loginErr('')" onkeydown="if(event.key==='Enter')doLogin()">
   <label>Password</label>
   <input id="loginPass" type="password" placeholder="password" onkeydown="if(event.key==='Enter')doLogin()">
   <div id="loginError" class="login-error"></div>
   <button class="login-btn" id="loginBtn" onclick="doLogin()">Sign in →</button>
  </div>
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
<button id="uwgBtn" onclick="uwgToggle()" title="UW Guide — underwriting knowledge assistant">💬 UW Guide</button>
<div id="uwgPanel" role="dialog" aria-label="UW Guide knowledge assistant">
 <div class="uwg-head"><div><b>UW Guide</b><div class="uwg-sub">Knowledge assistant · guidelines · product rules · process</div></div><span class="uwg-x" onclick="uwgToggle()" title="Close">✕</span></div>
 <div class="uwg-msgs" id="uwgMsgs"></div>
 <div class="uwg-chips" id="uwgChips"></div>
 <div class="uwg-input"><input id="uwgIn" placeholder="Ask about guidelines, rules, or a case ID…" onkeydown="if(event.key==='Enter')uwgSend()"><button onclick="uwgSend()" aria-label="Send">→</button></div>
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
// Light is the default; dark only when the user explicitly chose it before.
(function(){var t='light';try{if(localStorage.getItem('uw_theme')==='dark')t='dark';}catch(e){}
 if(t==='light')document.documentElement.setAttribute('data-theme','light');applyThemeIcon();})();
/* ---------- interactive tutorial (learn every feature hands-on) ---------- */
let tourIdx=0;
function tourLogin(u,p){if(typeof CURRENT_ROLE!=='undefined'&&CURRENT_ROLE)signOut();
 document.getElementById('loginUser').value=u;document.getElementById('loginPass').value=p;doLogin();}
function tourOpenConflictCase(){const c=CASES.find(x=>(x.conflicts||[]).some(k=>k.type==='dob_mismatch'))||CASES.find(x=>(x.conflicts||[]).length);if(c)sel(c.id);}
function tourShowTab(n){selTab(n);const el=document.querySelector('.tabs');if(el)el.scrollIntoView({block:'start'});}
const TUTORIAL_STEPS=[
 {title:`The Underwriting Copilot`,
  learn:`An AI-assisted life-insurance underwriting workbench. It scores every application <b>0–100</b>: the clean ones (0–50) are auto-approved, the risky ones (90–100) are auto-declined, and the 51–89 middle band goes to a human underwriter. First, why this exists — then one case, end to end.`},
 {title:`Where underwriting sits — and where it hurts`,
  learn:`In the insurance value chain — <b>distribution → new business intake → underwriting → policy issue → claims</b> — underwriting is the bottleneck. Underwriters typically spend <b>~40% of their time</b> gathering and re-keying data instead of judging risk; fully underwritten life runs <b>3–8 weeks of turnaround</b>; a single APS costs ~$350 and weeks of waiting; incomplete (“NIGO”) applications loop back to agents; and two underwriters can rate the same file differently. Slow TAT loses applicants, and manual cost makes small policies unwritable. <i>(Industry-typical figures, cited as context.)</i>`},
 {title:`What an AI-enabled platform changes`,
  learn:`The copilot reads the full packet in seconds, runs a <b>6-check cross-document conflict screen</b>, scores risk on <b>evidence-anchored weights</b>, and routes only the genuinely ambiguous middle band to a human. Clean cases decide in <b>seconds instead of weeks</b>; underwriter attention concentrates where judgement matters; every decision carries an audit trail. For the insurer: ~$47 vs ~$162 per application, and a TAT measured in minutes for the straight-through book.`},
 {title:`One case, end to end`,
  do:`Signing in as the junior underwriter.`,
  learn:`Before the other personas, follow <b>one journey</b> the way a real desk runs it: intake → junior desk → escalation by authority → senior review → evidence → decision, with SLA clocks running the whole way. Starting at the bottom: Dana Park, new analyst.`,
  action:{label:`Sign in as the junior analyst`,fn:()=>tourLogin('dpark','analyst')}},
 {title:`The junior desk — authority-limited`,
  do:`Dana's queue: only the cases within a new analyst's authority.`,
  learn:`Routing follows <b>authority, not availability</b>: a new analyst holds clean cases up to <b>$250k</b>. Each row already shows the SLA clock (8-hour line), outstanding requirements, and an AI recommendation. If a file is incomplete, <b>Request information</b> sends it back (NIGO) and parks the clock — a manual intervention, logged.`},
 {title:`Escalation — the case moves up`,
  do:`Signing in as the senior underwriter.`,
  learn:`High coverage (<b>$750k+</b>) or a major document conflict escalates <b>automatically at intake</b> — a junior never holds a case beyond their authority, so escalation is a routing rule, not a favour. The flagged case we're following sits on the senior desk: Marcus Rivera.`,
  action:{label:`Sign in as the senior underwriter`,fn:()=>tourLogin('mrivera','senior')}},
 {title:`The Review Queue`,
  do:`The main table is the underwriter's queue.`,
  learn:`Only the 51–89 cases that need a human land here. It's ranked by <b>coverage + time-in-queue</b> — not risk score, so the model never decides who gets looked at first. The SLA chips keep turnaround honest: amber from 6 hours, breach at 8. Each row carries an actionable <b>AI recommendation</b> on the right.`},
 {title:`A case the system flagged`,
  do:`Opening a case flagged for a conflict.`,
  learn:`This applicant has a <b>date-of-birth mismatch</b> across documents. The amber alert at the top flags it as a <b>data discrepancy — verify</b>: likely a data-entry mistake, not fraud, so the system routes it to a human instead of auto-declining. The two mismatched dates are named right under the applicant's name — nobody has to hunt for the problem.`,
  action:{label:`Open a flagged case`,fn:()=>tourOpenConflictCase()}},
 {title:`Application tab — read-only`,
  do:`The Application tab.`,
  learn:`The full application, <b>read-only for every role</b> — it's evidence, not a working document. The conflicting field (Date of Birth) is highlighted red so the discrepancy shows in context.`,
  action:{label:`Show the Application tab`,fn:()=>{tourShowTab(1);}}},
 {title:`Documents — the source packet`,
  do:`The Documents tab — each document opens inline.`,
  learn:`Every parsed document in the packet, viewable in place. Below it: the <b>Requirements grid</b> (which evidence this age/amount needs) and "Request more information".`,
  action:{label:`Show the Documents tab`,fn:()=>{tourShowTab(2);}}},
 {title:`Ordering more evidence (with AI pre-check)`,
  do:`The "Request more information" panel, at the bottom of Documents.`,
  learn:`Underwriters order evidence — APS, labs, MVR, pharmacy, MIB — with a <b>mandatory reason</b>. An AI pre-check flags duplicate or non-indicated orders <i>before</i> they cost ~$350 and weeks. Requests land in the admin's queue.`},
 {title:`Extraction & Conflicts`,
  do:`The Extraction & Conflicts tab.`,
  learn:`Every extracted value across the 5 documents, with the <b>conflicting rows highlighted red</b>, and the 6-check conflict screen explaining each discrepancy.`,
  action:{label:`Show the Extraction tab`,fn:()=>{tourShowTab(3);}}},
 {title:`Risk Score`,
  do:`The Risk Score tab.`,
  learn:`The composite-score gauge, the rule-engine vs ML sub-scores (a 50/50 blend), and the full factor breakdown. The generic "how scoring works" explainer lives <b>once</b> on the manager's Model Card — not repeated on every case.`,
  action:{label:`Show the Risk Score tab`,fn:()=>{tourShowTab(4);}}},
 {title:`Decision + audit trail`,
  do:`The Decision tab.`,
  learn:`The system decision and rationale, the affordability screen, the case desk where the underwriter <b>approves or declines</b> (with a required reason) or requests info — and the full <b>audit trail</b> of everything that happened on the case. That completes the journey: intake → junior desk → escalation → senior review → evidence → decision, inside SLA. Now the other personas.`,
  action:{label:`Show the Decision tab`,fn:()=>{tourShowTab(5);}}},
 {title:`Auto-Approved — ranked for capacity`,
  do:`The Auto-Approved space.`,
  learn:`Straight-through approvals, ranked <b>best candidate first</b> by expected underwriting margin — because a real book has a capacity constraint, and if you can only accept N cases this month, these are the N to take. The dashed line marks where the monthly appetite runs out. The <b>"Bulk approve all"</b> button batch-records them under one rationale, each case still written to the audit trail individually.`,
  action:{label:`Go to Auto-Approved`,fn:()=>{if(CURRENT_ROLE!=='underwriter')tourLogin('mrivera','senior');goSpace('auto_approved');}}},
 {title:`The Manager`,
  do:`Switching roles: signing in as the manager.`,
  learn:`Nadia Sethi, manager. She gets an oversight dashboard, a <b>"Decided cases"</b> list, and can <b>reopen or override</b> any underwriter's decision — with a logged reason. Only the manager has this power.`,
  action:{label:`Sign in as the manager`,fn:()=>tourLogin('nsethi','oversight')}},
 {title:`The Model Card (regulator-facing)`,
  do:`Portfolio & Model Card, from the left nav.`,
  learn:`The score formula & bands, feature importance, calibration, <b>fairness by group</b>, and the evidence-anchored weights (<span class="mono">28 × ln(mortality multiple)</span>). This is what makes the model defensible in a regulatory exam.`,
  action:{label:`Open the Model Card`,fn:()=>{if(CURRENT_ROLE!=='manager')tourLogin('nsethi','oversight');goOverview();}}},
 {title:`The Executive view`,
  do:`Switching roles: signing in as the Chief Underwriting Officer.`,
  learn:`Marcus Vale, CUO. A <b>money-only</b> view — coverage accepted vs declined, and a full <b>portfolio P&L</b>: expected claims payout against the approved premium, SG&A, the cost to underwrite, down to <b>operating income</b> and the combined ratio. Plus the cost-per-application economics that make small-premium policies viable. No individual cases, and no other role sees this.`,
  action:{label:`Sign in as the executive`,fn:()=>tourLogin('mvale','executive')}},
 {title:`The Operations Admin`,
  do:`Switching roles: signing in as operations admin.`,
  learn:`Priya Anand, ops. The full <b>decision feed</b> — every recorded decision, attributed and timestamped, <b>exportable to CSV/JSON</b> for compliance — plus the outstanding evidence requests raised by underwriters.`,
  action:{label:`Sign in as the admin`,fn:()=>tourLogin('panand','admin')}},
 {title:`That's the whole product 🎉`,
  learn:`Every application read, screened, scored, and routed — with a human on every borderline call and an audit trail behind every decision. This tour can be re-launched anytime from the <b>🎓 Tutorial</b> button.`}
];
function tourStart(){const ld=document.getElementById('landing');if(ld)ld.remove();
 tourIdx=0;const p=document.getElementById('tourPanel');if(p)p.classList.add('on');tourRender();}
function tourExit(){const p=document.getElementById('tourPanel');if(p)p.classList.remove('on');}
function tourGo(d){tourIdx=Math.max(0,Math.min(TUTORIAL_STEPS.length-1,tourIdx+d));tourRender();}
function tourAct(){const s=TUTORIAL_STEPS[tourIdx];if(s&&s.action&&s.action.fn){s.action.fn();document.getElementById('tourPanel').classList.add('on');}}
function tourRender(){
 const s=TUTORIAL_STEPS[tourIdx];const p=document.getElementById('tourPanel');if(!p||!s)return;
 const last=tourIdx===TUTORIAL_STEPS.length-1;
 p.innerHTML=`<div class="tour-step">Step ${tourIdx+1} of ${TUTORIAL_STEPS.length} · Guided tour</div>
  <div class="tour-title">${s.title}</div>
  ${s.do?`<div class="tour-do"><b>On screen:</b> ${s.do}</div>`:''}
  <div class="tour-learn">${s.learn}</div>
  ${s.action?`<button class="tour-btn doit" onclick="tourAct()">▶ ${s.action.label}</button>`:''}
  <div class="tour-prog"><div style="width:${(tourIdx+1)/TUTORIAL_STEPS.length*100}%"></div></div>
  <div class="tour-actions">
   <button class="tour-btn ghost" onclick="tourExit()">Exit tour</button><span class="sp"></span>
   <button class="tour-btn" onclick="tourGo(-1)" ${tourIdx===0?'disabled':''}>‹ Back</button>
   <button class="tour-btn prim" onclick="${last?'tourExit()':'tourGo(1)'}">${last?'Finish ✓':'Next ›'}</button></div>`;
}
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
// Material misrepresentation = evidence contradicts a sworn answer (fraud → decline).
// A DOB mismatch is a data-entry discrepancy, not fraud (7/24 carrier feedback):
// it forces a manual verification pass, never an auto-decline.
const MISREP=new Set(['smoker_nondisclosure']);
const DATA_FLAG=new Set(['dob_mismatch']);
function recomputeVerdicts(){
 CASES.forEach(c=>{
  const comp=c.risk_score,conf=c.conflicts||[];
  const majors=conf.filter(k=>k.severity==='major');
  const misrep=majors.filter(k=>MISREP.has(k.type));
  const disc=majors.filter(k=>DATA_FLAG.has(k.type));
  const reasons=[];let verdict,decision,rate;
  // Score-driven bands: the composite score alone sets the decision. Material
  // misrepresentation is the one hard override (fraud → decline regardless of
  // score); a data discrepancy (DOB mismatch) forces manual review — a human
  // verifies the data-entry mistake, whatever the score. Other conflicts,
  // affordability and disclosed circumstances are surfaced as flags for the
  // reviewer but no longer change the band.
  if(misrep.length){verdict='red';decision='DECLINE';rate='Declined — Material Misrepresentation';
    reasons.push('Application materially contradicts medical/identity evidence: '+misrep.map(k=>k.type.replace(/_/g,' ')).join('; '));}
  else if(comp>=D_LINE){verdict='red';decision='DECLINE';rate='Declined — Risk Exceeds Appetite';
    reasons.push(`Composite risk score ${comp}/100 is at or above the ${D_LINE}-point decline line`);}
  else if(disc.length){verdict='yellow';decision='MANUAL REVIEW';rate='Referred — Data Discrepancy (Verify)';
    reasons.push(`Data discrepancy — the date of birth on the application does not match the paramedical/ID. Likely a data-entry mistake, not fraud: verify before proceeding. Composite score ${comp} would otherwise ${comp<A_LINE?'auto-approve':'refer on score'}.`);}
  else if(comp>=A_LINE){verdict='yellow';decision='MANUAL REVIEW';rate='Referred — Senior Underwriter Review';
    reasons.push(`Composite score ${comp} sits in the ${A_LINE}–${D_LINE-1} manual-review band`);}
  else{verdict='green';decision='APPROVE';rate=comp<=25?'Preferred Rate Class':'Standard Rate Class';
    reasons.push(`Composite score ${comp} is below the ${A_LINE}-point approval line`);}
  if(verdict!=='red'){   // informational flags — do not change the band
    const flagMajors=majors.filter(k=>!DATA_FLAG.has(k.type));   // discrepancies already lead the reasons
    if(flagMajors.length)reasons.push(`Flag: ${flagMajors.length} major data conflict(s) for the reviewer — `+flagMajors.map(k=>k.type.replace(/_/g,' ')).join('; '));
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
/* ---------- landing ambience: the real book streams past, the scene tilts with the cursor ---------- */
(function(){
 const ld=document.getElementById('landing');if(!ld)return;
 try{if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;}catch(e){}
 const sc=ld.querySelector('.ld-scene');
 ld.addEventListener('mousemove',e=>{if(!sc||!document.getElementById('landing'))return;
  const r=ld.getBoundingClientRect();
  const ty=((e.clientX-r.left)/r.width-.5)*-9, tx=((e.clientY-r.top)/r.height-.5)*7;
  sc.style.transform='rotateY('+ty.toFixed(2)+'deg) rotateX('+tx.toFixed(2)+'deg)';});
})();
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
function loginFill(u,p,btn){
 // persona quick-pick: fills the credentials, keeps the deliberate Sign in click
 document.getElementById('loginUser').value=u;document.getElementById('loginPass').value=p;loginErr('');
 document.querySelectorAll('.role-chip').forEach(x=>x.classList.remove('sel'));
 if(btn)btn.classList.add('sel');
 const b=document.getElementById('loginBtn');if(b)b.focus();
}
function doLogin(){
 const _ld=document.getElementById('landing');if(_ld)_ld.remove();   // tour / direct logins skip the landing
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
 render();
 const _uwg=document.getElementById('uwgBtn');if(_uwg)_uwg.style.display='flex';
 if(hasEnteredApp)roleSwapPlay();else{hasEnteredApp=true;whooshPlay();}}
let hasEnteredApp=false;   // first entry gets the brand whoosh; later logins get the seat-change
function roleSwapPlay(){
 try{if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;}catch(e){}
 const old=document.getElementById('roleswap');if(old)old.remove();
 const initials=(CURRENT_USER||'').split(' ').map(w=>w[0]||'').join('').slice(0,2).toUpperCase();
 const roleEl=document.querySelector('#roleBadge .rb-role');
 const roleLabel=roleEl?roleEl.textContent:'';
 const d=document.createElement('div');d.id='roleswap';
 d.innerHTML='<div class="rs-chip"><div class="rs-av">'+initials+'</div><div><div class="rs-name">'+CURRENT_USER+'</div><div class="rs-role">'+roleLabel+'</div></div></div>';
 document.body.appendChild(d);
 const app=document.getElementById('app');
 if(app){app.classList.remove('app-reveal','role-turn');void app.offsetWidth;app.classList.add('role-turn');}
 setTimeout(()=>{d.remove();},1000);
}
function whooshPlay(){
 // 3D brand transition from sign-in into the workbench. Decorative only:
 // pointer-events none, skipped entirely under prefers-reduced-motion.
 try{if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;}catch(e){}
 const old=document.getElementById('whoosh');if(old)old.remove();
 const d=document.createElement('div');d.id='whoosh';
 d.innerHTML='<div class="w-ring"></div><div class="wz"><div class="w-mark">Underwriting <b>Copilot</b></div><div class="w-sub">EXTRACTION · CONFLICT SCREEN · RISK SCORE · DECISION</div></div>';
 document.body.appendChild(d);
 const app=document.getElementById('app');
 if(app){app.classList.remove('app-reveal');void app.offsetWidth;app.classList.add('app-reveal');}
 setTimeout(()=>{d.remove();},1750);
}
function landingGo(){
 // Landing → sign-in: the center zooms through the camera, echoing the whoosh.
 const ld=document.getElementById('landing');if(!ld)return;
 try{if(matchMedia('(prefers-reduced-motion: reduce)').matches){ld.remove();return;}}catch(e){}
 ld.classList.add('out');
 const card=document.querySelector('.login-card');
 if(card){card.style.animation='none';void card.offsetWidth;card.style.animation='';}
 setTimeout(()=>{ld.remove();},950);
}
function applyRole(){
 // nav (buildNav) shows the oversight links only for managers
 const badge=document.getElementById('roleBadge');
 const sub=CURRENT_ROLE==='underwriter'?((UWS[CURRENT_TIER]||{}).label||'Underwriter')
   :CURRENT_ROLE==='executive'?'Chief Underwriting Officer'
   :CURRENT_ROLE==='admin'?'Operations Administrator':'Manager';
 badge.innerHTML=`<div><div class="rb-name">${CURRENT_USER}</div><div class="rb-role">${sub}</div></div><span class="signout" onclick="signOut()">Sign out</span>`;}
function signOut(){CURRENT_ROLE=null;CURRENT_USER="";CURRENT_UID="";
 document.getElementById('loginUser').value='';document.getElementById('loginPass').value='';loginErr('');
 const _b=document.getElementById('uwgBtn'),_p=document.getElementById('uwgPanel');
 if(_b)_b.style.display='none';if(_p)_p.classList.remove('on');
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
function conflictDetail(c,k){
 // the specific mismatched values behind a conflict, pulled from the extraction
 const e=c.extraction||{};
 switch(k.type){
  case 'dob_mismatch': return {field:'Date of birth',a:['Application form',e.form_dob],b:['Paramedical / ID',e.paramed_dob]};
  case 'smoker_nondisclosure': return {field:'Tobacco use',a:['Declared on form',e.form_tobacco_yes?'Smoker':'Non-smoker'],b:['Lab cotinine',e.cotinine]};
  case 'income_mismatch': return {field:'Annual income',a:['Declared',fmt$(e.form_income)],b:['Payslip',fmt$(e.payslip_income)]};
  case 'tax_income_mismatch': return {field:'Annual income',a:['Declared',fmt$(e.form_income)],b:['Tax slip',fmt$(e.tax_income)]};
  case 'debt_understated': return {field:'Existing debt',a:['Declared',fmt$(e.form_debt)],b:['Credit bureau',fmt$(e.bureau_debt)]};
 }
 return null;
}
function conflictAlertHTML(c){
 // A case-wide red alert shown at the top of the case file (visible on every
 // tab) so the underwriter sees exactly what's wrong without hunting for it.
 const conf=c.conflicts||[];if(!conf.length)return '';
 // Data discrepancies (DOB mismatch) render amber "verify" — a data-entry issue,
 // visually distinct from the red fraud treatment (7/24 carrier feedback).
 const anyRed=conf.some(k=>k.severity==='major'&&!DATA_FLAG.has(k.type));
 const rows=conf.map(k=>{const d=conflictDetail(c,k);const misrep=MISREP.has(k.type);const disc=DATA_FLAG.has(k.type);
   const vals=d?`<div class="conf-vals"><b>${d.field}:</b> ${d.a[0]} <span class="conf-bad">${d.a[1]??'—'}</span> <span style="opacity:.6">vs</span> ${d.b[0]} <span class="conf-bad">${d.b[1]??'—'}</span></div>`:'';
   return `<div class="conflict-line ${k.severity==='minor'?'minor':''}">
     <span class="conf-tag"${disc?' style="color:var(--warn)"':''}>${k.severity.toUpperCase()} · ${k.type.replace(/_/g,' ').toUpperCase()}${misrep?' · MATERIAL MISREPRESENTATION':disc?' · DATA DISCREPANCY — VERIFY':''}</span>
     <div class="conf-desc">${k.description}${disc?' Likely a data-entry mistake — verify with the applicant/ID before proceeding.':''}</div>${vals}</div>`;}).join('');
 const majors=conf.filter(k=>k.severity==='major').length;
 return `<div class="conflict-alert ${anyRed?'':'warn'}">
   <div class="ca-head">⚠ ${conf.length} data conflict${conf.length>1?'s':''} flagged${majors?` · ${majors} major — resolve before deciding`:''}</div>${rows}</div>`;
}
function conflictFieldLabels(c){
 // Application-tab field labels a conflict touches → highlighted red
 const s=new Set();(c.conflicts||[]).forEach(k=>{
  if(k.type==='dob_mismatch')s.add('Date of Birth');
  if(k.type==='smoker_nondisclosure'){s.add('Smoker Status (last 12 months)');s.add('Tobacco / cotinine-verified (8-1)');}
  if(k.type==='income_mismatch'||k.type==='tax_income_mismatch')s.add('Annual Net Earned Income');
  if(k.type==='debt_understated')s.add('Existing Debt');});
 return s;
}
function conflictRowLabels(c){
 // Extraction-tab row labels a conflict touches → highlighted red
 const s=new Set();(c.conflicts||[]).forEach(k=>{
  if(k.type==='dob_mismatch'){s.add('DOB (form)');s.add('DOB (paramed / ID)');}
  if(k.type==='smoker_nondisclosure'){s.add('Tobacco (form 4a)');s.add('Cotinine (lab)');}
  if(k.type==='income_mismatch'){s.add('Declared income (form)');s.add('Income (payslip, annualized)');}
  if(k.type==='tax_income_mismatch'){s.add('Declared income (form)');s.add('Income (tax slip, 2025)');}
  if(k.type==='debt_understated'){s.add('Declared debt (form)');s.add('Debt (credit bureau)');}});
 return s;
}
function topDriversHTML(c){
 // Top drivers at the top of the case file (§4.2). If the case was declined,
 // LEAD with why (misrepresentation / score) so the reason is right below the
 // name, not buried in the Decision tab. Then the rule-engine contributors.
 if(!c.rule_factors)return '';
 const drivers=c.rule_factors.filter(f=>f[2]>0).sort((a,b)=>b[2]-a[2]).slice(0,3);
 const clean=c.rule_factors.filter(f=>f[2]===0).slice(0,3);
 let lead='';
 if(c.verdict==='red'){
  const misrep=(c.conflicts||[]).filter(k=>MISREP.has(k.type));
  const why=misrep.length
   ?['⚠ Declined — material misrepresentation',misrep.map(k=>k.type.replace(/_/g,' ')+' — '+k.description).join('; ')]
   :['⚠ Declined — risk exceeds appetite','Composite score '+c.risk_score+' is at or above the '+D_LINE+'-point decline line'];
  lead=`<div class="factor-row" style="background:var(--bad-soft);border-radius:10px;padding:10px 12px;margin-bottom:8px"><div><div class="factor-label" style="color:var(--bad)">${why[0]}</div><div class="factor-detail">${why[1]}</div></div><div class="factor-pts" style="color:var(--bad)">DECLINE</div></div>`;
 } else {
  const disc=(c.conflicts||[]).filter(k=>DATA_FLAG.has(k.type));
  const majors=(c.conflicts||[]).filter(k=>k.severity==='major'&&!DATA_FLAG.has(k.type));
  if(disc.length)lead=`<div class="factor-row" style="background:var(--warn-soft);border-radius:10px;padding:10px 12px;margin-bottom:8px"><div><div class="factor-label" style="color:var(--warn)">⚑ Data discrepancy — verify before proceeding</div><div class="factor-detail">The date of birth on the application does not match the paramedical/ID — likely a data-entry mistake, not fraud. Both fields are highlighted on the Application and Extraction tabs.</div></div><div class="factor-pts" style="color:var(--warn)">VERIFY</div></div>`;
  else if(majors.length)lead=`<div class="factor-row" style="background:var(--warn-soft);border-radius:10px;padding:10px 12px;margin-bottom:8px"><div><div class="factor-label" style="color:var(--warn)">⚑ ${majors.length} major data conflict(s) flagged</div><div class="factor-detail">${majors.map(k=>k.type.replace(/_/g,' ')).join('; ')} — see the alert above and the Extraction tab</div></div><div class="factor-pts" style="color:var(--warn)">FLAG</div></div>`;
 }
 const dr=drivers.map((f,i)=>`<div class="factor-row"><div><div class="factor-label">${i+1}. ${f[0]}</div><div class="factor-detail">${f[1]}</div></div><div class="factor-pts" style="color:var(--warn)">+${f[2]}</div></div>`).join('');
 const off=clean.length?`<div class="note" style="margin-top:10px"><b>Offsetting / clean signals:</b> ${clean.map(f=>f[0].toLowerCase()+' ('+f[1]+')').join(' · ')}</div>`:'';
 return `<div class="card"><h3>Top drivers of this ${c.verdict==='red'?'decision':'score'}</h3>${lead}${drivers.length?dr:'<div class="note" style="margin:0">No positive risk contributors — every rule factor is clean.</div>'}${off}
  <div class="note">${c.verdict==='red'?'The decision reason leads; below are the largest rule-engine contributors to the score.':'The three largest positive contributors to the composite score, straight from the documented rule-engine factor weights.'} Full breakdown on the Risk Score tab.</div></div>`;
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
function wfReopen(id){const st=wfGet(id);const wasBy=st.decision?st.decision.by:'';st.decision=null;st.status='in_review';
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:'Reopened for review'+((CURRENT_ROLE==='manager'||CURRENT_ROLE==='admin')&&wasBy?' by '+(CURRENT_ROLE==='manager'?'manager':'operations')+' (was decided by '+wasBy+')':'')});wfSave(id,st);
 const ov=getOverrides();delete ov[id];localStorage.setItem('uw_overrides',JSON.stringify(ov));
 if(CURRENT_ROLE==='underwriter')space='review';render();}
function wfManagerOverride(id,kind){
 // Manager or operations admin: change a recorded decision after the fact.
 // Ops corrects decisions recorded in error (wrong case, typo, missed evidence
 // landing) — same audit discipline, distinct tag so the trail shows who acted.
 if(CURRENT_ROLE!=='manager'&&CURRENT_ROLE!=='admin'){alert('Only a manager or operations admin can change a recorded decision.');return;}
 const tag=CURRENT_ROLE==='admin'?'OPS AMENDMENT':'MANAGER OVERRIDE';
 const labels={approve:'APPROVED',decline:'DECLINED'};
 const st=wfGet(id);const prevDecision=st.decision?st.decision.action:'(none)';const prevBy=st.decision?st.decision.by:'';
 const rationale=(prompt(tag.charAt(0)+tag.slice(1).toLowerCase()+' → '+labels[kind]+'. Reason (required — supersedes the '+prevDecision+' decision'+(prevBy?' by '+prevBy:'')+'):')||'').trim();
 if(!rationale){alert('A rationale is required to change a recorded decision.');return;}
 st.status=kind==='approve'?'approved':'declined';
 st.decision={action:labels[kind],by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),rationale:rationale,managerOverride:CURRENT_ROLE==='manager',opsAmendment:CURRENT_ROLE==='admin',supersedes:prevDecision};
 st.history.push({by:CURRENT_USER,role:CURRENT_ROLE,at:nowStr(),action:tag+' → '+labels[kind]+' (superseded '+prevDecision+(prevBy?' by '+prevBy:'')+') — “'+rationale+'”'});
 wfSave(id,st);
 const ov=getOverrides();ov[id]={decision:labels[kind],label:kind==='decline'?1:0,reason:rationale,at:st.decision.at};
 localStorage.setItem('uw_overrides',JSON.stringify(ov));
 render();}
/* dismissable review-queue banner */
function bannerClosed(){try{return localStorage.getItem('uw_queue_banner_closed')==='1';}catch(e){return false;}}
function closeQueueBanner(){try{localStorage.setItem('uw_queue_banner_closed','1');}catch(e){}render();}
/* ---------- case spaces: manual-review queue vs auto-decisioned record ---------- */
const SPACES=[
 ["review","Review Queue","▣","Cases the system flagged for a human. These are the only cases you action."],
 ["completed","Completed","✓","Manual-review cases you've approved or declined."],
 ["auto_approved","Auto-Approved","⤴","Straight-through approvals — ranked best candidate first by expected underwriting margin."],
 ["auto_declined","Auto-Declined","⤵","Straight-through declines — decided automatically, kept as a record."]];
const SPACE_LABEL=Object.fromEntries(SPACES.map(s=>[s[0],s[1]]));
let space='review';
function bucketOf(c){const st=wfGet(c.id);
 if(c.verdict==='yellow'||st.pulled)return st.decision?'completed':'review';
 return c.verdict==='green'?'auto_approved':'auto_declined';}
function spaceCases(sp){return CASES.filter(c=>bucketOf(c)===sp);}
function acceptMargin(c){
 // Expected annual underwriting margin per accepted case: premium less SG&A
 // less expected claims payout (same evidence-anchored model as the exec P&L).
 // This is the "how good a candidate is this?" number a capacity-constrained
 // book ranks its acceptances by.
 return (c.premium||0)*(1-SGA_RATE)-expectedAnnualClaim(c);
}
function currentList(){let l=spaceCases(space);
 if(space==='review'){
  if(CURRENT_ROLE==='underwriter'&&queueScope==='mine')l=l.filter(c=>wfGet(c.id).assigneeUid===CURRENT_UID);
  l=l.slice().sort((a,b)=>priorityScore(b)-priorityScore(a));   // most important first
 }
 if(space==='auto_approved'){  // best candidate first — margin, then the cleaner score
  l=l.slice().sort((a,b)=>(acceptMargin(b)-acceptMargin(a))||(a.risk_score-b.risk_score));
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
  const isMgr=CURRENT_ROLE==='manager',isOps=CURRENT_ROLE==='admin';
  const verb=isOps?'Amend':'Override';
  const mgrControls=((isMgr||isOps)&&resolved)?`
   <div class="desk-actions" style="margin-top:14px">
     <button class="ai-btn" style="background:var(--warn)" onclick="wfReopen('${c.id}')">↺ Reopen for review</button>
     <button class="ai-btn" style="background:var(--ok)" onclick="wfManagerOverride('${c.id}','approve')">${verb} → Approve</button>
     <button class="ai-btn" style="background:var(--bad)" onclick="wfManagerOverride('${c.id}','decline')">${verb} → Decline</button></div>
   <div class="note"><b>${isOps?'Operations authority':'Manager authority'}:</b> reopen this case to send it back to the underwriter, or ${isOps?'amend':'override'} the recorded decision directly. Both are logged to the audit trail with your name and what they superseded.</div>`:'';
  const roleNote=(isMgr||isOps)
   ?(resolved?'':`<div class="note">${isMgr?'Manager':'Operations'} view — this case is still with the underwriter. Reopen / ${isOps?'amend':'override'} becomes available once a decision is recorded.</div>`)
   :'<div class="note">Read-only view.</div>';
  controls=`<div class="desk-row"><span class="desk-l">Status</span><span class="status-chip wf-${st.status}">${WF_LABEL[st.status]}</span></div>
   <div class="desk-row"><span class="desk-l">Owner</span><span>${owner}</span></div>
   ${mgrControls}${roleNote}`;
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
function sel(id){if(view!=='case'){prev={view,space};caseNav=currentList().map(x=>x.id);}activeId=id;view="case";const c=CASES.find(x=>x.id===id);activeTab=(c&&(bucketOf(c)==='review'||wfGet(c.id).decision))?5:4;render();}
function selInNav(id){activeId=id;const c=CASES.find(x=>x.id===id);activeTab=(c&&(bucketOf(c)==='review'||wfGet(c.id).decision))?5:4;render();}
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
 if(CURRENT_ROLE==='executive'){execRail();return;}
 document.getElementById('searchBox').style.display='';
 document.querySelector('.pagination').style.display='';
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
function execRail(){
 // The CUO never opens a case — the rail carries the book at a glance, not a case list.
 document.getElementById('listTitle').textContent='Book at a glance';
 document.getElementById('queueCount').textContent='live';
 document.getElementById('searchBox').style.display='none';
 document.querySelector('.pagination').style.display='none';
 const appr=CASES.filter(c=>finalOf(c)==='approve'),decl=CASES.filter(c=>finalOf(c)==='decline');
 const pend=CASES.length-appr.length-decl.length;
 const covAppr=appr.reduce((s,c)=>s+(c.coverage||0),0);
 const premAppr=appr.reduce((s,c)=>s+(c.premium||0),0);
 const expClaims=appr.reduce((s,c)=>s+expectedAnnualClaim(c),0);
 const referredN=CASES.filter(c=>c.verdict==='yellow').length;
 const opsCost=CASES.length*COST_AUTO+referredN*COST_HUMAN;
 const opInc=premAppr*(1-SGA_RATE)-expClaims-opsCost;
 const combined=premAppr?((expClaims+premAppr*SGA_RATE+opsCost)/premAppr*100):0;
 const appetitePct=covAppr/APPETITE_MONTHLY*100;
 const stp=(M.decisioning.straight_through_rate*100);
 const row=(l,v,col,cls)=>`<div class="er-row${cls?' '+cls:''}"><b${col?` style="color:${col}"`:''}>${v}</b><span>${l}</span></div>`;
 document.getElementById('caseList').innerHTML=`<div class="exec-rail">
  ${row('Operating income',(opInc>=0?'':'−')+fmtMoneyK(Math.abs(opInc))+'/yr',opInc>=0?'var(--ok)':'var(--bad)','er-hero')}
  ${row('Combined ratio',combined.toFixed(0)+'%',combined<100?'var(--ok)':'var(--bad)','er-big')}
  ${row('Coverage accepted',fmtBigMoney(covAppr),'','er-big')}
  ${row('Approved premium',fmtMoneyK(premAppr)+'/yr')}
  ${row('Appetite used',appetitePct.toFixed(0)+'%',appetitePct>100?'var(--warn)':'')}
  ${row('Straight-through',stp.toFixed(0)+'%')}
  ${row('Approved · pending · declined',appr.length+' · '+pend+' · '+decl.length)}
  <div class="er-note">Portfolio-only view — the executive holds no individual cases. These figures update live as decisions are recorded.</div></div>`;
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
 }else if(space==='auto_approved'){
  // Ranked acceptance order for a capacity-constrained book (7/26 request):
  // best candidate first by expected margin, with the appetite cutoff drawn in.
  let cum=0,cut=-1;
  list.forEach((c,i)=>{cum+=(c.coverage||0);if(cut<0&&cum>APPETITE_MONTHLY)cut=i;});
  head=`<tr><th>Rank</th><th>Applicant</th><th>Case ID</th><th>Risk score</th><th>Coverage</th><th>Premium /yr</th><th>Expected margin /yr</th><th>Margin</th><th>Status</th></tr>`;
  rows=list.slice(0,300).map((c,i)=>{const st=wfGet(c.id);
    const m=acceptMargin(c);const mp=c.premium?m/c.premium*100:0;
    const over=cut>=0&&i>=cut;
    const divider=(cut>=0&&i===cut)?`<tr class="cap-cut"><td colspan="9">MONTHLY APPETITE ${fmtBigMoney(APPETITE_MONTHLY)} REACHED — CASES BELOW QUEUE FOR NEXT MONTH'S CAPACITY</td></tr>`:'';
    return divider+`<tr onclick="sel('${c.id}')" style="cursor:pointer${over?';opacity:.55':''}">
      <td class="rank-num">${i+1}</td>
      <td><b>${c.name}</b><div style="font-size:11px;color:var(--mut)">${c.policy}</div></td>
      <td><span class="mono" style="font-weight:700;font-size:13px;white-space:nowrap">${c.id}</span></td>
      <td><span class="score-chip sc-ok">${c.risk_score}</span></td>
      <td class="mono" style="white-space:nowrap">${fmt$(c.coverage)}</td>
      <td class="mono" style="white-space:nowrap">${fmt$(c.premium)}</td>
      <td class="mono" style="white-space:nowrap;font-weight:600;color:${m>=0?'var(--ok)':'var(--bad)'}">${m>=0?'':'−'}${fmt$(Math.abs(m))}</td>
      <td><span class="pri-chip" style="background:${mp>=35?'var(--ok)':mp>=15?'var(--warn)':'var(--bad)'}">${mp.toFixed(0)}%</span></td>
      <td>${over?'<span class="pri-chip" style="background:var(--warn)">NEXT MONTH</span>':`<span class="status-chip wf-${st.status}">${WF_LABEL[st.status]}</span>`}</td></tr>`;}).join('');
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
 const banner=(isRev&&!bannerClosed())?`<div class="verdict-banner v-yellow" style="margin-top:16px;position:relative"><button class="banner-x" onclick="closeQueueBanner()" title="Dismiss">✕</button><div class="vb-word">${list.length} case(s) ranked by coverage &amp; time in queue${breaches?` · ${breaches} over the 8h SLA`:''}</div><div class="vb-sub">Work top-down — most important first. These are the only cases needing a human; auto-approvals and auto-declines are filed separately. Anything over 8 hours in the queue is flagged red.</div></div>`:'';
 // Bulk approve/decline (§4.4) — batch-affirm straight-through decisions into
 // the recorded decision trail, top-right of the auto-decisioned spaces.
 const canBulk=CURRENT_ROLE==='underwriter'&&(space==='auto_approved'||space==='auto_declined')&&list.length;
 const bulkBtn=canBulk?`<button class="ai-btn" style="background:${space==='auto_approved'?'var(--ok)':'var(--bad)'}" onclick="bulkDecide('${space}')">${space==='auto_approved'?'✓ Bulk approve all':'✕ Bulk decline all'} (${list.length})</button>`:'';
 const rankBanner=(space==='auto_approved'&&list.length)?`<div class="verdict-banner v-green" style="margin-top:16px"><div class="vb-word">Ranked best candidate first — for a capacity-constrained book</div><div class="vb-sub">A real book can only take on so much cover per period. These straight-through approvals are ordered by <b>expected annual underwriting margin</b> (premium − expected claims payout − SG&amp;A, the same evidence-anchored model as the executive P&amp;L), lower risk score breaking ties. If capacity only allows N acceptances this month, take them from the top; the dashed line marks where cumulative coverage reaches the monthly appetite.</div></div>`:'';
 return `<div class="case-head"><div><h2>${meta[1]}</h2>
    <div class="case-meta"><span>${list.length} case(s)</span><span>${meta[3]}</span></div>${toggle}</div>${bulkBtn}</div>
   ${banner}${rankBanner}
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
  ${conflictAlertHTML(c)}
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
function scoreExplainerHTML(){
 // The generic "how scoring works" reference — shown ONCE on the model card,
 // not repeated on every case file (underwriters don't need it per application).
 return `<div class="card explain"><h3>How the composite score works</h3>
   <p><b>Formula:</b> Risk Score = 50% × Rule Engine score + 50% × ML probability. The rule engine is fully auditable — every point traces to a documented factor weight. The ML component is a gradient-boosting model trained on ${M.risk_models.n_train.toLocaleString()} records (AUC ${(M.risk_models.gradient_boosting.auc*100).toFixed(1)}% on ${M.risk_models.n_test.toLocaleString()} held-out cases), which captures factor interactions the rules miss. Blending them means one bad model can never single-handedly approve a risky case.</p>
   <p><b>The traffic light:</b> the composite score alone sets the band. Below ${A_LINE} the case is <b style="color:var(--ok)">GREEN — APPROVE</b>, clear-cut and auto-approved. From ${A_LINE} to ${D_LINE-1} it is <b style="color:var(--warn)">YELLOW — MANUAL REVIEW</b>: a human underwriter looks at the application and the person as a whole. At ${D_LINE} or above — or when the application materially misrepresents the medical/identity evidence — it is <b style="color:var(--bad)">RED — DECLINE</b>. A <b>data discrepancy</b> (e.g. a date of birth that differs between documents) is treated as a data-entry issue, not fraud: it routes the case to manual review with an amber <b>verify</b> flag, never an auto-decline. Other conflicts, affordability and disclosed circumstances are surfaced as flags for the reviewer, but they no longer change the band.</p>
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
   <div class="override-note"><span class="on-ic">⚠</span><div><b>Score-driven bands:</b> the composite score sets the decision. Material misrepresentation is the one hard override — it declines regardless of score. A data discrepancy (DOB mismatch) instead forces a manual-review <b>verify</b> step — a data-entry issue, not fraud. Other flags (conflicts, affordability, disclosed circumstances) are shown to the reviewer without changing the band.</div></div></div>`;
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
  <div class="stat"><div class="sv">${(M.extraction.field_level_accuracy*100).toFixed(1)}%</div><div class="sl"><b>Extraction accuracy</b> — field level vs ground truth</div></div>
  <div class="stat"><div class="sv">${(M.conflict_screening.detection_recall*100).toFixed(0)}%</div><div class="sl"><b>Conflict recall</b> — injected-conflict detection (${M.conflict_screening.tp}/${M.conflict_screening.tp+M.conflict_screening.fn} caught, ${M.conflict_screening.fp} false alarms)</div></div>
  <div class="stat"><div class="sv">${(gb.auc*100).toFixed(1)}%</div><div class="sl"><b>Gradient Boosting AUC</b> — on ${M.risk_models.n_test.toLocaleString()} held-out records</div></div>
  <div class="stat"><div class="sv">${(lr.auc*100).toFixed(1)}%</div><div class="sl"><b>Logistic Regression AUC</b> — auditable baseline</div></div>
  <div class="stat"><div class="sv">${(M.decisioning.straight_through_rate*100).toFixed(1)}%</div><div class="sl"><b>Straight-through rate</b> — decided with no human touch</div></div>
  <div class="stat"><div class="sv">${M.risk_models.n_train.toLocaleString()}</div><div class="sl"><b>Training records</b> — test: ${M.risk_models.n_test.toLocaleString()}, base risk rate ${(M.risk_models.positive_rate*100).toFixed(0)}%</div></div>
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
 ${scoreExplainerHTML()}
 <div class="card" style="margin-top:16px"><h3>Composite Risk Score Distribution</h3>
  ${Object.entries(tc).map(([t,n],i)=>`<div class="hist-bar-row"><div class="hist-label">${t}</div>
   <div class="hist-track"><div class="hist-fill" style="width:${n/mx*100}%;background:${cols[i]}"></div></div><div class="hist-count">${n}</div></div>`).join('')}
  <div class="note">Score-driven bands: below ${A_LINE} → green auto-approve. ${A_LINE}–${D_LINE-1} → yellow manual review. At or above ${D_LINE}, or material misrepresentation → red decline. A DOB data discrepancy → manual review with a verify flag (data-entry issue, not fraud). Other conflicts, affordability and disclosed circumstances are shown as flags but no longer change the band.</div></div>
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
  <div class="case-meta"><span>${n} cases in queue</span><span>${M.n_applicants.toLocaleString()} scored pipeline-wide</span><span>evaluated ${M.generated_at}</span></div></div>
  <div><button class="ai-btn" style="background:var(--acc)" onclick="exportBenchmark()" title="Every application with the system's score, flags, routing and time-to-decision beside any recorded human decision — the artifact for benchmarking a pilot batch against human underwriters.">⬇ Pilot benchmark CSV</button></div></div>
 <div class="grid3" style="margin-top:18px">
  <div class="stat" style="border-top:4px solid var(--ok)"><div class="sv" style="color:var(--ok)">${G.length}</div><div class="sl"><b>APPROVED</b> · ${pct(G)} of queue · no human touch needed</div></div>
  <div class="stat" style="border-top:4px solid var(--warn)"><div class="sv" style="color:var(--warn)">${Y.length}</div><div class="sl"><b>MANUAL REVIEW</b> · ${pct(Y)} · awaiting an underwriter</div></div>
  <div class="stat" style="border-top:4px solid var(--bad)"><div class="sv" style="color:var(--bad)">${R.length}</div><div class="sl"><b>DECLINED</b> · ${pct(R)} · ${majors.length} tied to major conflicts</div></div>
 </div>
 <div class="grid3" style="margin-top:14px">
  <div class="stat"><div class="sv">${(M.decisioning.straight_through_rate*100).toFixed(0)}%</div><div class="sl"><b>Straight-through rate</b> — decided with zero human minutes</div></div>
  <div class="stat"><div class="sv">${fmtM(covAll)}</div><div class="sl"><b>Coverage requested</b> · <span style="color:var(--ok)">${fmtM(covG)} auto-approved</span> · <span style="color:var(--warn)">${fmtM(covY)} pending</span> · <span style="color:var(--bad)">${fmtM(covR)} declined</span></div></div>
  <div class="stat"><div class="sv">${avg(CASES,c=>c.risk_score).toFixed(0)}</div><div class="sl"><b>Avg composite risk</b> — green ${avg(G,c=>c.risk_score).toFixed(0)} · yellow ${avg(Y,c=>c.risk_score).toFixed(0)} · red ${avg(R,c=>c.risk_score).toFixed(0)}</div></div>
  <div class="stat"><div class="sv">${conflicts.length}</div><div class="sl"><b>Conflict cases</b> — cross-document (${majors.length} major) — recall ${(M.conflict_screening.detection_recall*100).toFixed(0)}%, ${M.conflict_screening.fp} false alarms</div></div>
  <div class="stat"><div class="sv">${uniques.length}</div><div class="sl"><b>Unique disclosures</b> — every one routed to a human</div></div>
  <div class="stat"><div class="sv">${ovList.length}</div><div class="sl"><b>Overrides recorded</b> — in this browser${(M.decisioning.n_overrides_learned||0)>0?` · ${M.decisioning.n_overrides_learned} already trained on`:''} — export from the Model Card</div></div>
  ${M.affordability?`<div class="stat" style="border-top:4px solid var(--warn)"><div class="sv">${CASES.filter(c=>c.afford&&c.afford.verdict==='fail').length}</div><div class="sl"><b>NOT FINANCIALLY JUSTIFIED</b> · coverage or premium out of line with income — referred to financial underwriting (${(M.affordability.not_justified_rate*100).toFixed(0)}% pipeline-wide)</div></div>`:''}
 </div>
 <div class="card" style="margin-top:16px"><h3>Review Queue — largest exposure first (where senior time should go)</h3>
  <table class="xt"><tr><th>Case</th><th>Applicant</th><th>Coverage</th><th>Risk</th><th>Why it's here</th></tr>
   ${queue.map(c=>`<tr style="cursor:pointer" onclick="sel('${c.id}')"><td class="mono">${c.id}</td><td><b>${c.name}</b>, ${c.age} · ${c.occupation}</td>
    <td class="mono">${fmt$(c.coverage)}</td><td><span class="score-chip sc-warn" style="color:var(--warn);background:var(--warn-soft)">${c.risk_score}</span></td>
    <td style="font-size:12px;color:var(--mut)">${ov[c.id]?'<b style="color:var(--acc)">OVERRIDDEN → '+ov[c.id].decision+'</b>':(c.reasons[0]||'')}</td></tr>`).join('')}</table>
  <div class="note">Click any row to open the full case file. ${Y.length-queue.length>0?`${Y.length-queue.length} more manual-review cases in the queue at left.`:''}</div></div>
 ${(()=>{const dec=allDecisions();return `<div class="card"><h3>Decided cases — reopen or override</h3>
  ${dec.length?`<table class="xt"><tr><th>Case</th><th>Applicant</th><th>AI rec</th><th>Underwriter decision</th><th>By</th><th></th></tr>
   ${dec.map(d=>{const flip=d.model&&((d.model==='APPROVE'&&d.action==='DECLINED')||(d.model==='DECLINE'&&d.action==='APPROVED'));
     return `<tr style="cursor:pointer" onclick="sel('${d.id}')"><td class="mono">${d.id}</td><td><b>${d.name}</b></td>
     <td style="font-size:12px;color:var(--mut)">${d.model}</td>
     <td><span class="status-chip ${d.action==='APPROVED'?'wf-approved':'wf-declined'}">${d.action}</span>${flip?' <span class="pri-chip" style="background:var(--warn)">vs AI</span>':''}</td>
     <td style="font-size:12px">${d.by||'—'}</td>
     <td style="text-align:right"><button class="ai-btn" onclick="event.stopPropagation();sel('${d.id}')">Open</button></td></tr>`;}).join('')}</table>
   <div class="note">Open any decided case to <b>reopen</b> it (send back to the underwriter) or <b>override</b> the decision. Manager-only — every action is logged to the audit trail.</div>`
  :'<div class="note" style="margin:0">No underwriter decisions recorded yet this session. Once an underwriter approves or declines a case, it appears here for you to reopen or override.</div>'}</div>`;})()}
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
/* ---- portfolio economics (7/26 carrier feedback) ----
   "Premium in the door" is only half the P&L: show the expected payout against
   that premium, SG&A and the cost to underwrite, down to operating income.
   Assumptions are illustrative, named, and labeled as such in the UI. */
const SGA_RATE=0.12;               // SG&A + acquisition as a share of premium (illustrative loading)
const COST_AUTO=12;                // per-application system cost: compute, parsing, data pulls
const COST_HUMAN=150;              // fully-loaded underwriter touch per referred case
const MORT_A=0.00005,MORT_B=0.088; // Gompertz base annual mortality ≈ unisex period life table
const SELECT_FACTOR=0.45;          // select-period discount: newly underwritten lives run well
                                   // below ultimate mortality (SOA select & ultimate tables)
function expectedAnnualClaim(c){
 // Expected annual claims cost = coverage × q(age) × relative-mortality multiple × select factor.
 // Rule-engine weights are round(28·ln(real mortality multiple)) (derive_weights.py),
 // so exp(rule_score/28) recovers the combined evidence-anchored multiple; capped
 // at 12× (and q at 5%/yr) to stay conservative on the synthetic book.
 const q=MORT_A*Math.exp(MORT_B*(c.age||45));
 const mult=Math.min(Math.exp((c.rule_score||0)/28),12);
 return (c.coverage||0)*Math.min(q*mult*SELECT_FACTOR,0.05);
}
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
/* ---- configurable executive reporting (7/28 feedback) ----
   The dashboard is composable per stakeholder: any block can be shown or
   hidden, and the choice persists in this browser. Different stakeholder
   groups keep different views of the same live numbers. */
const EXEC_SECTIONS=[
 ['headline','Headline exposure tiles'],['pnl','Portfolio economics (P&L)'],
 ['cost','Cost to underwrite'],['growth','Approval · appetite · STP tiles'],
 ['yoy','YoY risk underwritten'],['ops','Operational tiles'],
 ['mix','Decision mix'],['appetite','Risk appetite levers']];
let execCfgOpen=false;
function execCfg(){try{return JSON.parse(localStorage.getItem('uw_exec_cfg')||'{}');}catch(e){return {};}}
function execShown(k){return execCfg()[k]!==false;}
function execCfgToggle(k){const s=execCfg();s[k]=!(s[k]!==false);localStorage.setItem('uw_exec_cfg',JSON.stringify(s));render();}
function execCfgPanel(){execCfgOpen=!execCfgOpen;render();}
function executiveView(){
 // A money view, not a queue (§5.1). Built from the whole book + recorded decisions.
 const n=CASES.length;
 const appr=CASES.filter(c=>finalOf(c)==='approve'),decl=CASES.filter(c=>finalOf(c)==='decline'),pend=CASES.filter(c=>finalOf(c)==='pending');
 const sum=(a,f)=>a.reduce((s,c)=>s+(f(c)||0),0);
 const covAppr=sum(appr,c=>c.coverage),covDecl=sum(decl,c=>c.coverage),covPend=sum(pend,c=>c.coverage),covAll=covAppr+covDecl+covPend;
 const premAppr=sum(appr,c=>c.premium||0);
 // portfolio economics (7/26 feedback): payout vs premium, costs, operating income
 const expClaims=sum(appr,expectedAnnualClaim);
 const sga=premAppr*SGA_RATE;
 const referredN=CASES.filter(c=>c.verdict==='yellow').length;
 const opsCost=n*COST_AUTO+referredN*COST_HUMAN;
 const opInc=premAppr-expClaims-sga-opsCost;
 const lossRatio=premAppr?expClaims/premAppr*100:0;
 const expenseRatio=premAppr?(sga+opsCost)/premAppr*100:0;
 const combined=lossRatio+expenseRatio;
 const costPerAppCopilot=n?opsCost/n:0;
 const costPerAppManual=COST_HUMAN+COST_AUTO;
 const uwSavings=costPerAppManual*n-opsCost;
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
 const moNames=['January','February','March','April','May','June','July','August','September','October','November','December'];
 const _now=new Date();const moName=moNames[_now.getMonth()];const yr=_now.getFullYear();
 const underwritten2025=covAppr*0.82;   // illustrative prior-year same-month figure (no dated cohort in synthetic data)
 const yoyAmt=underwritten2025>0?(covAppr/underwritten2025-1)*100:0;
 const tile=(v,l,accent)=>`<div class="stat"${accent?` style="border-top:4px solid ${accent}"`:''}><div class="sv">${v}</div><div class="sl">${l}</div></div>`;
 return `<div class="case-head"><div><h2>Executive Overview</h2>
   <div class="case-meta"><span>Chief Underwriting Officer</span><span>Executive-only view</span><span>evaluated ${M.generated_at}</span></div></div>
   <button class="ai-btn" style="background:var(--acc)" onclick="execCfgPanel()">⚙ Customize view</button></div>
  ${execCfgOpen?`<div class="card" style="margin-top:14px"><h3>Customize this report</h3>
   <div class="legend-row">${EXEC_SECTIONS.map(([k,l])=>`<label class="legend-chip" style="cursor:pointer;gap:7px"><input type="checkbox" ${execShown(k)?'checked':''} onchange="execCfgToggle('${k}')">${l}</label>`).join('')}</div>
   <div class="note">Add or remove reporting blocks to fit the audience — the choice persists in this browser, and every block reads the same live numbers. Different stakeholder groups keep different views of one book.</div></div>`:''}
  ${execShown('headline')?`<div class="grid3" style="margin-top:18px">
   ${tile(fmtBigMoney(covAppr),'<b>Total coverage accepted</b> — exposure taken on to the book','var(--ok)')}
   ${tile(fmtBigMoney(covDecl),'<b>Total coverage declined</b> — risk turned away','var(--bad)')}
   ${tile(fmtMoneyK(premAppr)+'/yr','<b>Approved premium</b> — annualised, the revenue side','var(--acc)')}
  </div>`:''}
  ${execShown('pnl')?`<div class="card" style="margin-top:16px"><h3>Portfolio economics — what the book keeps, not just what it writes</h3>
   ${[['Approved premium (annualised)',premAppr,'+'],
      ['Expected claims payout against that premium',-expClaims,'−'],
      ['SG&A + acquisition ('+(SGA_RATE*100).toFixed(0)+'% of premium)',-sga,'−'],
      ['Cost to underwrite the book ('+n+' applications processed)',-opsCost,'−']]
     .map(r=>`<div style="display:flex;justify-content:space-between;align-items:baseline;padding:7px 2px;border-bottom:1px solid var(--line,rgba(128,128,128,.15))">
       <span>${r[2]==='+'?'':'− '}${r[0]}</span><span class="mono" style="font-weight:600;color:${r[1]>=0?'var(--ok)':'var(--bad)'}">${r[1]>=0?'':'−'}${fmtMoneyK(Math.abs(r[1]))}</span></div>`).join('')}
   <div style="display:flex;justify-content:space-between;align-items:baseline;padding:10px 2px 2px">
     <span><b>Expected operating income</b> — premium after payout, SG&A and underwriting cost</span>
     <span class="mono" style="font-size:20px;font-weight:700;color:${opInc>=0?'var(--ok)':'var(--bad)'}">${opInc>=0?'':'−'}${fmtMoneyK(Math.abs(opInc))}/yr</span></div>
   <div class="grid3" style="margin-top:12px">
    ${tile(lossRatio.toFixed(0)+'%','<b>Loss ratio</b> — expected payout ÷ approved premium',lossRatio<70?'var(--ok)':'var(--bad)')}
    ${tile(expenseRatio.toFixed(0)+'%','<b>Expense ratio</b> — SG&A + underwriting ops ÷ premium')}
    ${tile(combined.toFixed(0)+'%','<b>Combined ratio</b> — under 100% means the book earns an underwriting profit',combined<100?'var(--ok)':'var(--bad)')}
   </div>
   <div class="note">Expected payout is an illustrative actuarial model on the synthetic book: Gompertz base mortality by age × each case's rule-engine relative-mortality multiple (the published weights are 28·ln(multiple), so exp(score/28) recovers it). SG&A and cost figures are named, illustrative assumptions — swap in carrier actuals during a pilot to make this the real class-profile P&L.</div></div>`:''}
  ${execShown('cost')?`<div class="card"><h3>Cost to underwrite — the economics of automation</h3>
   <div class="grid3">
    ${tile('$'+costPerAppCopilot.toFixed(0),'<b>Per application with the copilot</b> — only '+referredN+' of '+n+' cases need an underwriter’s time','var(--ok)')}
    ${tile('$'+costPerAppManual.toFixed(0),'<b>Per application, all-manual baseline</b> — every case gets a full human review','var(--bad)')}
    ${tile(fmtMoneyK(uwSavings),'<b>Saved across this book</b> — underwriting cost avoided on '+n+' applications','var(--acc)')}
   </div>
   <div class="note">This is what makes small-premium policies economically viable: a term policy writing a few hundred dollars a year cannot carry a $${costPerAppManual.toFixed(0)} manual underwriting cost, but it can carry $${costPerAppCopilot.toFixed(0)}. Straight-through processing pays for the low end of the market, and human attention concentrates on the ${referredN} cases that genuinely need it.</div></div>`:''}
  ${execShown('growth')?`<div class="grid3" style="margin-top:14px">
   ${tile(apprRate.toFixed(0)+'%','<b>YoY approval rate</b> — '+yr+' vs. '+priorApprRate.toFixed(0)+'% in '+(yr-1)+' (illustrative)','var(--acc)')}
   ${tile(appetitePct.toFixed(0)+'%','<b>% of monthly appetite</b> — accepted cover vs the '+fmtBigMoney(APPETITE_MONTHLY)+' target','var(--warn)')}
   ${tile(stp.toFixed(0)+'%','<b>Straight-through rate</b> — decided with no human touch')}
  </div>`:''}
  ${execShown('yoy')?`<div class="card" style="margin-top:16px"><h3>Total amount of risk underwritten — ${moName} ${yr-1} vs ${moName} ${yr}</h3>
   <div style="display:flex;gap:26px;flex-wrap:wrap;align-items:flex-end">
    <div><div class="hs-lab">${moName} ${yr-1} <span style="opacity:.7">(illustrative)</span></div><div class="sv" style="color:var(--mut)">${fmtBigMoney(underwritten2025)}</div></div>
    <div style="font-size:24px;color:var(--mut);padding-bottom:6px">→</div>
    <div><div class="hs-lab">${moName} ${yr} (actual)</div><div class="sv" style="color:var(--ok)">${fmtBigMoney(covAppr)}</div></div>
    <div style="margin-left:8px"><div class="hs-lab">Year-over-year</div><div class="sv" style="color:${yoyAmt>=0?'var(--ok)':'var(--bad)'}">${yoyAmt>=0?'+':''}${yoyAmt.toFixed(0)}%</div></div>
   </div>
   <div class="note">Total amount of risk underwritten (approved cover), this month against the same month last year — the executive's headline movement, held by no other role. The ${yr-1} figure is an illustrative baseline pending a real historical book; ${yr} is live.</div></div>`:''}
  ${execShown('ops')?`<div class="grid3" style="margin-top:14px">
   ${tile(fmtBigMoney(avgCover),'<b>Avg cover / policy</b> — across the approved book')}
   ${tile(fmtAge(avgCycle),'<b>Avg time in queue</b> — proxy for cycle time')}
   ${tile(overrideRate.toFixed(0)+'%','<b>Override rate</b> — human decisions against the model lean ('+nOv+' of '+decidedManual+')')}
   ${tile(appr.length+' / '+pend.length+' / '+decl.length,'<b>Decision counts</b> — approved · referred-pending · declined')}
   ${tile(fmtBigMoney(covAll),'<b>Coverage requested</b> — total across the book')}
  </div>`:''}
  ${execShown('mix')?`<div class="card" style="margin-top:16px"><h3>Decision mix — cover per bucket</h3>
   <div class="mix-bar">
    <div class="mix-seg" style="width:${pctG}%;background:var(--ok)">${pctG>7?fmtBigMoney(covAppr):''}</div>
    <div class="mix-seg" style="width:${pctP}%;background:var(--warn)">${pctP>7?fmtBigMoney(covPend):''}</div>
    <div class="mix-seg" style="width:${pctR}%;background:var(--bad)">${pctR>7?fmtBigMoney(covDecl):''}</div></div>
   <div class="legend-row" style="margin-top:10px">
    <div class="legend-chip cls-ok"><span class="swatch" style="background:var(--ok)"></span>Approved · ${appr.length} · ${fmtBigMoney(covAppr)}</div>
    <div class="legend-chip cls-warn"><span class="swatch" style="background:var(--warn)"></span>Referred / pending · ${pend.length} · ${fmtBigMoney(covPend)}</div>
    <div class="legend-chip cls-bad"><span class="swatch" style="background:var(--bad)"></span>Declined · ${decl.length} · ${fmtBigMoney(covDecl)}</div></div></div>`:''}
  ${execShown('appetite')?`<div class="card"><h3>Risk appetite — the levers you own</h3>
   <div class="note" style="margin:0 0 10px">Approved cover this book is <b>${fmtBigMoney(covAppr)}</b> against a monthly appetite target of <b>${fmtBigMoney(APPETITE_MONTHLY)}</b> — <b style="color:${appetitePct>=100?'var(--bad)':'var(--ok)'}">${appetitePct.toFixed(0)}%</b> of appetite. ${appetitePct<80?'The book is running below appetite — the acceptance lines could be loosened.':appetitePct>100?'The book is over appetite — tighten the acceptance lines.':'The book is tracking to appetite.'}</div>
   <div class="gauge-line"><div class="fill" style="width:${appetitePct}%;background:${appetitePct>=100?'var(--bad)':'var(--ok)'}"></div></div>
   <div class="appetite" style="margin-top:14px">
    <div class="lever"><b>Approval line — score < ${A_LINE}</b><div class="note" style="margin:6px 0 0">Below this, cases auto-approve. Lowering it tightens the book; raising it takes on more volume and exposure.</div></div>
    <div class="lever"><b>Decline line — score ≥ ${D_LINE}</b><div class="note" style="margin:6px 0 0">At or above this, cases auto-decline. These two lines are configuration, versioned, and owned by underwriting leadership — not baked into the model.</div></div></div></div>`:''}
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
   const flipKind=d.action==='APPROVED'?'decline':'approve';
   return `<div class="feed-row"><span class="feed-when">${d.at}</span>
    <span class="feed-what"><b>${d.action}</b> — <span class="mono" style="cursor:pointer;color:var(--acc)" onclick="sel('${d.id}')">${d.id}</span> ${d.name}, ${fmt$(d.coverage)} ${badge}<div style="color:var(--mut);font-size:12px;margin-top:2px">AI: ${d.model} · “${d.rationale||''}”</div>
     <div style="margin-top:6px"><button class="ai-btn" style="background:var(--mut)" onclick="wfReopen('${d.id}')">↺ Reopen</button> <button class="ai-btn" style="background:${flipKind==='approve'?'var(--ok)':'var(--bad)'}" onclick="wfManagerOverride('${d.id}','${flipKind}')">Amend → ${flipKind==='approve'?'Approve':'Decline'}</button></div></span>
    <span class="feed-who">${d.by||''}</span></div>`;}).join(''):'<div class="note" style="margin:0">No decisions recorded yet. Underwriter decisions land here in real time.</div>';
 const evList=ev.length?ev.map(e=>`<div class="feed-row"><span class="feed-when">${e.at}</span>
    <span class="feed-what"><span class="status-chip wf-info_requested">${e.status}</span> <span class="mono" style="cursor:pointer;color:var(--acc)" onclick="sel('${e.caseId}')">${e.caseId}</span> ${e.name} — ${e.labels}<div style="color:var(--mut);font-size:12px;margin-top:2px">“${e.rationale}”${e.flags&&e.flags.length?` · <span style="color:var(--warn)">${e.flags.length} pre-check flag(s) acknowledged</span>`:''}</div></span>
    <span class="feed-who">${e.by||''}</span></div>`).join(''):'<div class="note" style="margin:0">No outstanding evidence requests.</div>';
 // Operations control (7/26): the admin desk is more than a decision feed —
 // SLA watch, evidence chasing, and workload balance are ops-owned levers.
 const reviewCases=CASES.filter(c=>c.verdict==='yellow'&&!wfGet(c.id).decision);
 const slaBreaches=reviewCases.filter(c=>ageHours(c)>=8);
 const oldest=reviewCases.slice().sort((a,b)=>ageHours(b)-ageHours(a))[0];
 const deskLoad={};reviewCases.forEach(c=>{const t=wfGet(c.id).tier||'unassigned';deskLoad[t]=(deskLoad[t]||0)+1;});
 const deskChips=Object.entries(deskLoad).map(([t,k])=>`<span class="pri-chip" style="background:var(--acc)">${(UWS[t]||{}).label||t} · ${k}</span>`).join(' ');
 const evOpen=ev.filter(e=>e.status==='info_requested'||!e.status).length;
 return `<div class="case-head"><div><h2>Decision Feed</h2>
   <div class="case-meta"><span>Operations administrator</span><span>${dec.length} recorded decision(s)</span><span>${ev.length} evidence request(s)</span></div></div></div>
  <div class="grid3" style="margin-top:18px">
   ${tile(nApproved,'<b>Approved</b> — decisions recorded this session','var(--ok)')}
   ${tile(nInfo,'<b>Info / evidence requested</b> — awaiting third parties','var(--warn)')}
   ${tile(nDeclined,'<b>Declined</b> — decisions recorded this session','var(--bad)')}
  </div>
  <div class="card" style="margin-top:16px"><h3>Operations control — the desk beyond the feed</h3>
   <div class="grid3">
    ${tile(slaBreaches.length,'<b>SLA breaches</b> — review cases over the 8-hour line, chase the assigned desk',slaBreaches.length?'var(--bad)':'var(--ok)')}
    ${tile(evOpen,'<b>Evidence being chased</b> — open third-party requests (APS, labs, MVR)','var(--warn)')}
    ${tile(oldest?fmtAge(ageHours(oldest)):'—','<b>Oldest case in queue</b>'+(oldest?' — <span class="mono">'+oldest.id+'</span> '+oldest.name:''))}
   </div>
   <div style="margin-top:12px"><b style="font-size:13px">Workload by desk</b> &nbsp;${deskChips||'<span class="note">no referred cases assigned</span>'}</div>
   <div class="note" style="margin-top:10px">Ops owns the flow, not the risk call: watching SLAs, chasing evidence vendors, rebalancing desks when one underwriter backs up, and keeping the audit package export-ready below.</div></div>
  <div class="card" style="margin-top:16px"><div class="ai-head"><h3 style="margin:0">Decision trail — every recorded decision, newest first</h3>
    <div><button class="ai-btn" onclick="exportDecisions('csv')">⬇ CSV</button> <button class="ai-btn" style="background:var(--acc)" onclick="exportDecisions('json')">⬇ JSON</button></div></div>
   ${feed}
   <div class="note">This is the regulator-ready package — attributed, timestamped, and linked to each case, with the model recommendation beside the human decision. Export as CSV or JSON for compliance. <b>Reopen</b> sends a case back to the underwriter; <b>Amend</b> corrects a decision recorded in error — both are logged as OPS AMENDMENT with your name and what they superseded.</div></div>
  <div class="card"><h3>Outstanding evidence requests</h3>${evList}
   <div class="note">Raised by underwriters from the case file (§4.3). Each carries the requesting underwriter, a mandatory rationale, and any pre-check flags they proceeded over — so operations can chase the right provider.</div></div>
  <div class="card"><h3>Integration coverage — where the platform sits in the estate</h3>
   ${(()=>{const chip=(n,d,s)=>`<div class="doc-row"><div class="dot ${s==='demo'?'':'miss'}"></div><div class="dname">${n}<div style="font-size:11px;color:var(--mut);font-weight:500">${d}</div></div><div class="dstatus" style="color:${s==='demo'?'var(--ok)':'var(--acc)'}">${s==='demo'?'Simulated in demo':'Pilot connector'}</div></div>`;
     return `<div style="display:grid;grid-template-columns:1fr 1fr;gap:0 22px">
      <div><b style="font-size:13px">Internal systems</b>
       ${chip('New Business Platform','application packet intake — the demo ingests the ACORD-style packet directly','demo')}
       ${chip('Agent / Producer Portal','NIGO return loop + status callbacks — “Request information” models the return leg','demo')}
       ${chip('Notification Services','decision + SLA-breach events — surfaced in-app today, webhook out in pilot','demo')}
       ${chip('CRM','applicant record sync, decision write-back','plan')}
       ${chip('Claims','decision + rating context handed to claims at FNOL','plan')}</div>
      <div><b style="font-size:13px">External systems</b>
       ${chip('Risk-assessment data providers','NHANES / NCHS mortality evidence already anchors the rule weights','demo')}
       ${chip('Medical &amp; health APIs','Rx history, MIB, lab networks — replaces simulated evidence ordering','plan')}
       ${chip('Address verification services','identity + address validation at intake','plan')}
       ${chip('Third-Party Administrators (TPA)','delegated case exchange for TPA-serviced blocks','plan')}</div></div>`;})()}
   <div class="note">The engine is deliberately <b>document-intake-only</b> — no external repository is assumed at decision time (there is no shared cross-insurer claims/health repository in the target markets). Every connector lands behind the same extraction layer, so integrations add evidence without changing the scoring contract.</div></div>`;
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
function exportBenchmark(){
 // Pilot benchmark artifact: every application with the system's score, flags and
 // routing beside any recorded human decision — formatted so a carrier's tech team
 // can replay a batch of its own applications through the copilot and benchmark
 // score, fraud flags and time-to-decision against what its underwriters decided.
 const hdr='case_id,applicant,age,policy,coverage,annual_premium,composite_score,rule_score,ml_score,band,system_decision,rate_class,fraud_flags,data_flags,affordability,routing,assigned_desk,time_to_decision,human_decision,decided_by,agreement\n';
 const rows=CASES.map(c=>{
  const st=wfGet(c.id);const dec=st.decision;
  const conf=c.conflicts||[];
  const fraud=conf.filter(k=>MISREP.has(k.type)).map(k=>k.type).join('; ');
  const flags=conf.filter(k=>!MISREP.has(k.type)).map(k=>k.type).join('; ');
  const auto=c.verdict!=='yellow';
  const agree=dec?(((c.decision==='APPROVE'&&dec.action==='APPROVED')||(c.decision==='DECLINE'&&dec.action==='DECLINED'))?'AGREED':c.decision==='MANUAL REVIEW'?'HUMAN CALL':'OVERRIDE'):'';
  return [c.id,'"'+c.name+'"',c.age,'"'+c.policy+'"',c.coverage,c.premium,c.risk_score,c.rule_score,Math.round(c.ml_score),c.verdict,c.decision,'"'+c.rate_class+'"','"'+fraud+'"','"'+flags+'"',(c.afford&&c.afford.verdict)||'',auto?'straight-through':'referred',c.assigned_desk||'',auto?'instant (auto)':fmtAge(ageHours(c))+' in queue',dec?dec.action:'',dec?dec.by:'',agree].join(',');
 }).join('\n');
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([hdr+rows],{type:'text/csv'}));a.download='pilot_benchmark.csv';a.click();
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
  const cl=conflictFieldLabels(c);   // fields a cross-document conflict touches → highlighted red
  const sec=(title,fields)=>`<div class="card"><h3>${title}</h3><div class="grid2">
   ${fields.map(f=>{const bad=cl.has(f[0]);
     return `<div class="field${bad?' field-conflict':''}"><label>${f[0]}${bad?' <span class="fc-badge">⚠ CONFLICT</span>':''}</label><div class="val">${f[1]}</div></div>`;}).join('')}</div></div>`;
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
  const rl=conflictRowLabels(c);   // the specific extracted rows in conflict → highlighted red
  return `<div class="card"><h3>Extracted Fields (5 documents)</h3><table class="xt"><tr><th>Field</th><th>Value</th></tr>
   ${rows.map(r=>{const bad=rl.has(r[0]);return `<tr class="${bad?'row-conflict':''}"><td>${r[0]}${bad?' ⚠':''}</td><td class="mono">${r[1]??'—'}</td></tr>`;}).join('')}</table>
   ${rl.size?'<div class="note">Rows highlighted red are the values in conflict across documents — see the alert at the top of the case and the conflict screen below.</div>':''}</div>
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
/* ---------- UW Guide — embedded knowledge assistant (Knowledge Bot feedback) ----------
   Fully offline by design: a curated knowledge base over the platform’s own
   guidelines, product rules and process, plus live lookups into the current
   book. It answers from the same constants the engine runs on (A_LINE, the
   requirements grid, the routing tiers), so the bot can never drift from the
   product. No external calls — it ships inside the single file. */
const UWG_KB=[
 {k:['band','threshold','line','cutoff','0-50','51','89','90','score range','how is a case decided'],
  a:()=>`Scores run <b>0–100</b>. Under <b>${A_LINE}</b> auto-approves, <b>${D_LINE}+</b> auto-declines, and the <b>${A_LINE}–${D_LINE-1}</b> middle band goes to a human underwriter. The two lines are configuration owned by underwriting leadership — tightening or loosening the book is a config change, not a retrain.`},
 {k:['conflict','6-check','conflict screen','mismatch','discrepan','cross-document'],
  a:()=>`The <b>6-check conflict screen</b> compares every packet across documents: income vs payslip, income vs tax slip, income vs bank deposits, declared debt vs bureau, DOB across form and paramedical, and declared tobacco vs the cotinine lab. Majors force manual review; smoker non-disclosure alone is treated as material misrepresentation.`},
 {k:['dob','date of birth','verify','data entry'],
  a:()=>`A <b>DOB mismatch is a data discrepancy, not fraud</b> — most are transcription errors. Policy: it forces <b>manual review</b> with an amber “verify” flag (never an auto-decline, never a silent approve). The underwriter confirms identity against the source documents, then decides.`},
 {k:['smoker','cotinine','tobacco','nondisclosure','misrepresentation','fraud'],
  a:()=>`Declaring non-smoker with a <b>positive cotinine lab</b> is material misrepresentation — evidence contradicting a sworn answer — and auto-declines whatever the score. A declared smoker with a positive lab is consistent: rated as a smoker, no flag. This is the only conflict treated as fraud on its own.`},
 {k:['afford','financial underwriting','justif','premium burden','income multiple'],
  a:()=>`The <b>affordability screen</b> checks the premium against income and the coverage amount against an income multiple by age. A failing case is never declined on affordability alone — it routes to <b>financial underwriting review</b>, because the fix is usually a smaller face amount, not a rejection.`},
 {k:['requirement','aps','labs','evidence','paramed','ekg','cognitive','mvr','mib','grid','order'],
  a:()=>`Requirements come from the <b>age × amount grid</b>: 50+ or $250k+ needs a paramed exam and blood profile; $1M+ or 66+ adds an APS; 50+ at $1M+ adds an EKG; 61+ at $1M+ adds a cognitive assessment. Ordering more evidence needs a <b>written rationale</b>, and an AI pre-check flags duplicate or non-indicated orders before they cost money (an APS runs ~$350 and takes weeks).`},
 {k:['routing','desk','assign','authority','junior','analyst','senior','escalat','tier','mid-tier'],
  a:()=>`Referred cases route by <b>authority, not availability</b>: a new analyst gets clean cases up to $250k; mid-tier takes $250k+; anything at $750k+ or carrying a major conflict goes straight to the <b>senior desk</b>. A junior underwriter never holds a case beyond their authority — escalation is automatic at intake.`},
 {k:['sla','tat','turnaround','time in queue','priority','cycle time','oldest'],
  a:()=>`Every referred case carries a clock: the review SLA is <b>8 hours</b>, with a warning state from 6. Queue order is <b>coverage + time-in-queue</b> — deliberately not the risk score, so the model never decides who gets looked at first. Straight-through cases decide in seconds, which is what moves the book’s TAT.`},
 {k:['weight','evidence-anchored','nhanes','mortality','28','calibrat','prudential','why these points'],
  a:()=>`Rule weights are <b>round(28 × ln(relative mortality))</b>, derived from NHANES + NCHS linked-mortality data and cross-validated against real Prudential applicants — not hand-picked numbers. That’s why a current smoker is +24: cotinine-confirmed smokers run ~2.37× mortality, and 28·ln(2.37) ≈ 24.`},
 {k:['model','composite','auc','logistic','gradient','ml score','how is the score'],
  a:()=>`The composite is a <b>50/50 blend</b>: the evidence-anchored rule engine and a trained ML model. The pipeline trains logistic regression and gradient boosting; the browser re-scores with the exported logistic coefficients (auditable, ships as numbers). Model quality, calibration and fairness by group live on the manager’s <b>Model Card</b>.`},
 {k:['stp','straight-through','cost per app','automation','viab','small premium','economics of'],
  a:()=>`Straight-through processing decides the clean and the clearly declinable with no human touch — only the middle band costs underwriter time. That takes the cost per application from ~$162 all-manual to ~$47, which is what makes small-premium term policies economically writable.`},
 {k:['operating income','p&l','claims payout','sg&a','combined ratio','loss ratio','gompertz','select period','expected claims'],
  a:()=>`The executive P&L: approved premium − expected claims (Gompertz mortality by age × each case’s rule-engine mortality multiple × a select-period factor) − SG&A (12% illustrative) − cost to underwrite = <b>operating income</b>. Under 100% combined ratio, the book earns an underwriting profit. Assumptions are named and swap for carrier actuals in a pilot.`},
 {k:['override','amend','reopen','change a decision','change decision','who can change','undo'],
  a:()=>`Three levels: an <b>underwriter</b> can reopen their own decided case; a <b>manager</b> can reopen or override any recorded decision (logged as MANAGER OVERRIDE); an <b>operations admin</b> can reopen or amend decisions recorded in error (logged as OPS AMENDMENT). Every change requires a written reason and records what it superseded.`},
 {k:['export','csv','json','benchmark','memo','regulator','compliance','audit trail','audit'],
  a:()=>`Exports: the admin’s <b>decision trail</b> (CSV/JSON, attributed and timestamped), the manager’s <b>pilot benchmark CSV</b> (every case with scores, flags and routing beside any human decision), and a per-case <b>decision memo</b>. Every case action lands in its audit trail automatically.`},
 {k:['product','term','whole life','policy type','rate class','premium calc'],
  a:()=>`The book carries term (10/20/30-yr), whole life and universal life. Premiums scale with age, smoker status, face amount and product. Rate classes follow the decision: approved cases price standard-or-better; referred cases can come back rated (Table B–D) after review.`},
 {k:['manager and the admin','manager vs','admin vs','manager or the admin','what does the manager do','what does the admin do','role difference','difference between the roles','manager and admin'],
  a:()=>`Different jobs. The <b>manager</b> owns the <b>risk call</b>: portfolio oversight, the regulator-facing Model Card, and the authority to reopen or override any recorded decision. The <b>operations admin</b> owns the <b>flow</b>: the decision feed, chasing evidence vendors, SLA watch, workload balance across desks, compliance exports, and correcting decisions recorded in error. Neither underwrites; the manager judges risk, ops keeps cases moving.`},
 {k:['role','login','persona','who sees','which view'],
  a:()=>`Each role sees a different product: <b>underwriters</b> get the review queue and case desk, the <b>manager</b> gets oversight + the Model Card, the <b>executive</b> gets the money view only, and the <b>operations admin</b> gets the decision feed, evidence chasing and SLA watch. Sign-in is the role selector.`},
 {k:['appetite','capacity','monthly target','lever','45m','how much can we write'],
  a:()=>`The monthly appetite is <b>$45M of accepted cover</b> — a config lever, not a model output. The Auto-Approved space ranks candidates by expected underwriting margin so a capacity-constrained book accepts the best N first; the dashed line marks where appetite runs out. The executive owns the approve/decline lines that throttle it.`},
 {k:['integration','crm','api','tpa','connector','agent portal','claims system','address verification','notification','send email','emails','notify','callback','webhook'],
  a:()=>`The demo is <b>document-intake-only</b> by design. The pilot integration surface: internal — CRM, new-business platform, agent portal, notification services, claims; external — medical/health data APIs, address verification, TPAs and risk-data providers. Each lands behind the same extraction layer, so connectors add evidence without changing the engine.`},
 {k:['nigo','incomplete','not in good order','info request','missing information'],
  a:()=>`<b>NIGO</b> (“not in good order”) — incomplete or malformed applications — is the biggest single source of cycle-time loss. Underwriters send a case back with <b>Request information</b>, which stamps it Info Requested, logs what’s missing, and parks the SLA clock on the applicant’s side.`},
 {k:['refer','why manual','yellow','middle band','human review'],
  a:()=>`A case is referred when the system can’t safely decide alone: a mid-band score (${A_LINE}–${D_LINE-1}), a document conflict, a failed affordability screen, or disclosed unique circumstances. Open any referred case and ask me <i>“why is this case here?”</i> — I’ll read its actual drivers.`},
 {k:['how do i approve','how do i record','how do i decline','record a decision','where do i decide','how do i action','add a note','leave a note','leave a comment','annotate','case note'],
  a:()=>`Open a case from the queue, go to the <b>Decision</b> tab, and use Approve or Decline on the case desk — a written rationale is required, and it writes to the audit trail and moves the case to Completed. <b>Request information</b> parks it as NIGO instead, and <b>+ Note</b> adds a comment without changing state. Auto-decided cases can be pulled into manual review from their space if you want to touch one.`},
 {k:['paramed','what is an aps','what does aps','what is aps','attending physician','what is mib','what is mvr','glossary','what does that mean','stand for','acronym','abbreviation','jargon'],
  a:()=>`Quick glossary: <b>APS</b> — Attending Physician Statement, records from the applicant's doctor (~$350, weeks; the slowest requirement). <b>Paramed</b> — a nurse-run exam: height, weight, blood pressure, blood draw. <b>MIB</b> — the industry's prior-application database. <b>MVR</b> — motor vehicle record. <b>NIGO</b> — "not in good order", an incomplete application. <b>STP</b> — straight-through processing, decided with no human touch. <b>Cotinine</b> — the lab marker that confirms tobacco use. <b>A&A grid</b> — the age × amount table that decides which requirements apply.`},
 {k:['who are the underwriters','who is on the team','team members','which underwriters','who works here','staff'],
  a:()=>`Three underwriting desks by experience — <b>${UWS.senior.name}</b> (senior, $750k+ and hard conflicts), <b>${UWS.mid.name}</b> (mid-tier, $250k+), <b>${UWS.analyst.name}</b> (new analyst, clean cases to $250k) — plus a manager for oversight and overrides, a Chief Underwriting Officer for the money view, and an operations administrator for flow and compliance. All fictional personas on synthetic data.`},
 {k:['demo login','credentials','what are the logins','username','how do i sign in','sign in as','test account'],
  a:()=>`Six demo accounts, shown on the sign-in card: <span class="mono">mrivera / senior</span>, <span class="mono">ewong / review</span>, <span class="mono">dpark / analyst</span>, <span class="mono">nsethi / oversight</span> (manager), <span class="mono">mvale / executive</span> (CUO), <span class="mono">panand / admin</span> (operations). It is a role selector rather than real authentication — each role reveals a different product.`},
 {k:['what should i show','demo tips','how do i present','order to demo','best way to show','walkthrough order','pitch this'],
  a:()=>`Land the problem before the product. Suggested order: (1) the <b>🎓 Tutorial</b> intro — value chain, ~40% of underwriter time on data gathering, 3–8 week turnaround; (2) <b>one case end to end</b> as a junior analyst, escalating to senior — that is the story people remember; (3) a <b>flagged case</b>, so the 6-check screen shows a real discrepancy with both values; (4) <b>Auto-Approved ranked by margin</b> for the capacity argument; (5) the <b>Executive P&L</b> — the $47 vs $162 per application is the line that sells automation; (6) the <b>Model Card</b> if anyone asks how it is defensible. Ask me anything mid-demo — I read from the live book, so nothing goes stale.`},
 {k:['roadmap','what is next','future','coming soon','not built yet','next step','what would you add','improve'],
  a:()=>`Honest roadmap. Nearest-term: <b>table ratings</b> (the composite already implies a mortality multiple, so rated offers replace binary refer/decline), <b>NIGO intake triage</b>, and <b>requirement/vendor SLA tracking</b> — the biggest real cycle-time levers. Then: workforce and queue balancing, user/access administration with separation-of-duties, a formal reconsideration path, and pilot connectors (CRM, new business, agent portal, notifications, claims). Deliberately excluded: image-based fraud detection and any dependency on external claims or health repositories, since the target markets have none to rely on.`},
 {k:['extraction accurate','how accurate','ocr','reads the document','confidence','misread','low confidence','parse fail','garbled'],
  a:()=>`Extraction runs at <b>${(M.extraction.field_level_accuracy*100).toFixed(1)}% field-level accuracy</b> against ground truth on this book, and the conflict screen catches <b>${(M.conflict_screening.detection_recall*100).toFixed(0)}%</b> of injected discrepancies with ${M.conflict_screening.fp} false alarms. The design point that matters: extraction never decides anything alone — every parsed field is shown beside its source document so an underwriter can check it, and a disagreement between documents refers the case rather than resolving it silently. A low-confidence or unparseable field is a human's problem to look at, which is the correct failure mode.`},
 {k:['handwriting','handwritten','scanned badly','retinal','biometric','image fraud','image-based','image based','photo','picture','selfie','face','damage assessment'],
  a:()=>`Explicit non-goals, and worth stating in a pitch. <b>Image-based fraud detection</b> (comparing photos, assessing damage) is a different problem domain — the validated capability here is document-level inconsistency detection, which is where life underwriting misrepresentation actually shows up. <b>Handwritten OCR</b> and <b>biometric or retinal checks</b> are research items, not build items. The scope discipline is deliberate: document intake only, no external data at decision time.`},
 {k:['language','malay','bahasa','translate','multilingual','non-english','indonesian document'],
  a:()=>`English-only in this build — the extraction schema, the UI and I all assume English documents. For Malaysia or Indonesia a pilot would need multilingual extraction (Bahasa Malaysia and Bahasa Indonesia, plus mixed-language forms, which are common) and localised UI labels. The scoring engine itself is language-agnostic: it consumes extracted fields, not text, so the work is in the reader and the interface rather than the risk logic.`},
 {k:['why does this exist','why does this project','project exist','why this exists','why was this built','who built this','purpose of the project','background','the story','why build','origin'],
  a:()=>`It is a prototype built to answer one question: can a small carrier make <b>low-premium life policies economically writable</b>? Manual underwriting costs roughly $160 an application, which a policy earning a few hundred dollars a year cannot carry — so the thesis is straight-through processing for the clean majority and concentrated human judgement on the ${CASES.filter(c=>c.verdict==='yellow').length} cases that need it. Everything here runs on <b>synthetic data</b>, with no real insurer and no real applicants, and the honest-limits framing is part of the deliverable rather than a footnote.`},
 {k:['retention','reinsur','treaty','ceding','cede','jumbo','facultative','automatic binding'],
  a:()=>`Not modelled in this prototype, and worth saying plainly. A real carrier holds risk up to a <b>retention limit</b> and reinsures the excess — automatically under a treaty up to a binding limit, facultatively above it, with jumbo limits on total in-force cover. This demo underwrites the risk decision only; the ${fmtBigMoney(APPETITE_MONTHLY)} monthly appetite is the sole capacity lever in it. Retention, treaty terms and cession routing would be pilot configuration on top of the same engine.`},
 {k:['postpone','postponement','defer the case','hold the case','revisit later','not now'],
  a:()=>`Not a separate state in this build — the recorded dispositions are approve, decline, and referred-with-evidence-outstanding. In practice a postpone is modelled as <b>Request information</b>: the case moves to Info Requested with a written reason, the SLA clock parks on the applicant's side, and it comes back when the evidence lands. A true "postpone 6 months" status (pending recent surgery, for example) is a pilot addition.`},
 {k:['table rating','substandard','rated offer','counteroffer','counter offer','loading','modal premium','rate up','offer terms'],
  a:()=>`The demo's outcomes are approve at <b>Preferred</b> or <b>Standard</b>, refer, or decline — it does not yet issue table ratings. A production build slots naturally here: the composite already implies a mortality multiple (weights are <span class="mono">28 × ln(multiple)</span>, so <span class="mono">exp(score/28)</span> recovers it), which maps to Table A–H loadings instead of a binary refer/decline. That is the highest-value next step for the pricing side, because most referred cases are insurable at a price rather than uninsurable.`},
 {k:['reconsider','reconsideration','re-apply','reapply','appeal a decline','after a decline','second chance','contest the decision'],
  a:()=>`Yes. A declined case is a record, not a locked door: any auto-decision can be <b>pulled into manual review</b> from its space, and a recorded decision can be reopened by the underwriter who made it, overridden by a manager, or amended by operations if it was recorded in error. Every reopen is logged with who did it and what it superseded. Carrier practice is usually to invite reconsideration when new evidence arrives (a repeat lab, a specialist letter) — that arrives here as an evidence request on the reopened case.`},
 {k:['lab result valid','how long are lab','evidence valid','stale','expire','expiry','age of evidence','out of date'],
  a:()=>`Not enforced in the demo — every packet is treated as current. Carrier norms: routine labs and paramed exams are good for <b>6–12 months</b>, an APS typically 12 months, MVR and Rx pulls a few months, and anything older is re-ordered. Worth adding as a rule alongside the requirements grid, since re-ordering stale evidence is a real cost and a real cycle-time hit.`},
 {k:['occupation','pilot','miner','job risk','dangerous job','occupational','commercial pilot','military','fire fighter','firefighter'],
  a:()=>`Occupation is captured on every case and shown on the file, but the rule engine does <b>not</b> currently score it — the weighted factors are age, tobacco, build, conditions, family history, financial signals, hazardous activities, driving, alcohol and the Section 6 declarations. So a commercial pilot scores on their health and finances here, while a real carrier would add an aviation or occupational loading (or an exclusion rider). It surfaces indirectly: an unusual occupation often arrives with disclosed circumstances, which forces a human look.`},
 {k:['juvenile','child','minor applicant','under 18','kids policy'],
  a:()=>`Out of scope for this book — the synthetic applicants are adults (age ${Math.min.apply(null,CASES.map(c=>c.age))}–${Math.max.apply(null,CASES.map(c=>c.age))}), and juvenile underwriting is a different discipline: no financial underwriting on the child, parental insurable-interest checks, sibling-equity limits, and much lighter medical requirements. The engine would need its own requirement grid and weight table for it.`},
 {k:['simplified','full underwriting','accelerated','fluidless','no exam','guaranteed issue','underwriting path','which path'],
  a:()=>`One path in the demo: every application gets the full document packet, the 6-check screen and a composite score, and the age × amount grid decides what extra evidence is needed. That is effectively <b>accelerated underwriting</b> — clean cases clear with no human and no new exams, which is exactly what the ${(M.decisioning.straight_through_rate*100).toFixed(0)}% straight-through rate measures. Simplified issue (a few questions, no labs) and guaranteed issue would be separate products with their own grids, not variations of this decision logic.`},
 {k:['blood pressure','hypertension reading','systolic','cholesterol level','what reading','build chart','height weight table','bmi threshold'],
  a:()=>`Individual clinical cut-offs are not published as thresholds in this build — blood pressure and cholesterol are captured on the paramedical and shown on the file, while the scored factors are <b>BMI band</b>, declared conditions (hypertension included), tobacco, age and the rest of the weight table. So a reading contributes through its diagnosis rather than through a hard cut-off. A production build would carry the carrier's own build chart and BP/lipid tables; the derivation script (<span class="mono">derive_weights.py</span>) is where those would be anchored to mortality data rather than picked by hand.`},
 {k:['foreign','residency','overseas','travel plan','visa','expat','abroad','non-resident'],
  a:()=>`<b>Foreign travel planned</b> is a Section 6 declaration and is captured per case; answering yes contributes points and shows on the file as a disclosure. Residency and destination-specific rules (war-zone exclusions, country risk classes, non-resident eligibility) are not modelled — and deliberately so, since the design assumes <b>no external data source</b>: there is no shared cross-insurer or travel-risk repository in the target markets, so any such rule would have to arrive as carrier configuration.`},
 {k:['replacement','replacing','churn','1035','surrender','existing policy','switch policies'],
  a:()=>`Captured: every case carries <b>existing cover in force</b> and a <b>replacing</b> flag, and both are visible on the file. Replacement matters twice — the total in-force amount drives the requirements grid and the affordability screen, and replacing a policy raises a suitability question (is the applicant better off?) that regulators care about. The demo surfaces the facts; the suitability review would be a pilot rule with its own disclosure form.`},
 {k:['family member','own family','relative','conflict of interest','separation of duties','my own case','friend'],
  a:()=>`Right instinct, and it is a known gap: role separation exists (only a manager can override, only ops can amend) but the demo does <b>not</b> block an underwriter from working a case involving someone they know, because the synthetic book has no relationship data to check against. Real practice is a declared conflict-of-interest register plus an automatic reassignment rule on name/address/policy-number matches. It is listed in the operations roadmap as a separation-of-duties check.`},
 {k:['who can see','access log','who opened','audit who','viewed the case','track access','surveillance'],
  a:()=>`Every <b>action</b> is attributed — claims, notes, status changes, evidence requests, decisions and overrides all land in the case audit trail with a name, role and timestamp, and export to CSV or JSON. What is not tracked in this build is passive <b>viewing</b>: opening a case leaves no record. Real carriers log reads too, for privacy audits. Also worth being honest about: sign-in here is a demo role selector, not authentication, so attribution is only as trustworthy as the person picking the role.`},
 {k:['retention of records','how long are records','archive','retain','record keeping','data retention','purge'],
  a:()=>`Nothing is purged in the demo — the decision trail persists in your browser until you clear site data, and there is no scheduled retention. Insurance retention is typically measured in <b>years after the policy ends</b> (jurisdiction-specific, commonly 7–10), covering the application, the evidence, and the decision rationale. A pilot needs a retention schedule and a defensible deletion process; the export formats are already the right shape for an archive.`},
 {k:['does the model learn','learn from my override','training loop','feedback loop','my override','improve over time','retrain on'],
  a:()=>`Yes, deliberately. Every recorded decision writes to an <b>override store</b> alongside the case, and the pipeline folds those human calls back into the training pool on its next run — so the underwriters' judgement becomes training signal rather than being thrown away. The manager's view reports the override rate and how many overrides have already been trained on, and the Model Card carries the export. The guardrail: the rule half stays evidence-anchored, so learning from humans can shift the ML half without quietly rewriting the published mortality weights.`},
 {k:['how often is the model retrained','retrain','cadence','drift','monitor the model','model refresh','champion challenger'],
  a:()=>`In this prototype, retraining happens on every pipeline run — it appends the batch to the training pool and refits, which is why AUC, thresholds and the straight-through rate drift slightly run to run (currently AUC ${(M.risk_models.gradient_boosting.auc*100).toFixed(1)}% on ${(M.risk_models.n_train||0).toLocaleString()} records). A production cadence would be scheduled rather than per-batch — monthly or quarterly, with champion/challenger comparison, calibration and fairness checks before promotion, and drift monitoring in between. The decision <b>lines stay fixed</b> across retrains, so a model refresh cannot silently change the book's risk appetite.`},
 {k:['explain a decline','tell the agent','adverse action','explain to the customer','justify the decision','why was it declined to','communicate the decision'],
  a:()=>`Every decision comes with the material to explain it: the <b>rate class and reason</b>, the ranked rule factors with their points, any document conflicts with both conflicting values, the affordability result, and a downloadable <b>decision memo</b> from the case desk. Because the rule half is published (<span class="mono">28 × ln(mortality multiple)</span>), a decline can be explained factor by factor rather than as "the model said no" — which is what makes it defensible to an agent, an applicant, and a regulator. Formal adverse-action notice wording is a carrier/jurisdiction template, not something the demo generates.`},
 {k:['appeal','appeals process','complain','dispute','ombudsman','applicant rights'],
  a:()=>`No formal applicant-facing appeals workflow in the demo. What exists is the internal equivalent: a declined case can be pulled into manual review, reopened, overridden by a manager or amended by ops, all with written reasons, and the decision memo gives the applicant's agent something concrete to argue with. A production appeals process would add an intake channel, a service-level clock, and a reviewer who did not make the original call — that last part matters, and the role model here already supports it.`},
 {k:['regulation','regulatory','compliance requirement','which laws','gdpr','pdpa','solvency','ojk','bnm','regulator expects'],
  a:()=>`This is a synthetic prototype, so it is not certified against any regime — but it is built for the questions regulators actually ask: <b>explainability</b> (published weights, factor-level reasons), <b>human oversight</b> (every borderline case goes to a person, and the model advises rather than decides), <b>auditability</b> (attributed, timestamped, exportable trail), <b>fairness measurement</b> (Model Card reports by group), and <b>data minimisation</b> (document-intake only, no external profiling). In the target markets that maps to insurance-authority conduct rules plus the local data-protection act; the specifics belong in a pilot's compliance review, not in a demo's claims.`},
 {k:['two underwriters at once','same case at once','simultaneous','collision','locking','concurrent','claim the case','take over'],
  a:()=>`Cases are <b>assigned</b> rather than locked. Each referred case routes to one desk by authority, shows its owner, and another underwriter can explicitly <b>Take over</b> — which is logged as a reassignment in the audit trail. Since state lives in your browser in this demo, there is no server-side lock; a live build would add optimistic locking so two people cannot record conflicting decisions on the same case.`},
 {k:['hand over','handover','hand it','give it to','pass it to','someone else','reassign','transfer the case','vacation','out of office','cover for me','absence','my backlog'],
  a:()=>`Per-case today: open a case and use <b>Take over</b> to move ownership, which logs the reassignment. Bulk handover of a whole desk is not built — and it is exactly what the operations roadmap calls workforce and queue balancing: reassigning a backed-up desk, forecasting capacity, and covering absence. The admin's <b>Workload by desk</b> panel already shows where the load sits, which is the input that decision needs.`},
 {k:['bulk decline','decline all','batch decline','mass decline'],
  a:()=>`No — and that asymmetry is intentional. <b>Bulk approve</b> exists for the auto-approved space because those cases already cleared the screen and the score, so the batch action confirms a decision the system already made. A decline is adverse: it needs a case-by-case rationale you would have to defend one applicant at a time. Auto-declines are recorded automatically with their reason, and any of them can be pulled into manual review individually.`},
 {k:['filter','sort the queue','reorder','sort by','search by','find cases where','narrow the list','group by'],
  a:()=>`The rail search matches <b>applicant name or case ID</b>, and the four spaces separate the queue from the auto-decisioned record. Ordering is deliberate rather than user-sortable: the review queue is fixed to <b>coverage + time-in-queue</b> so the model's opinion never decides who gets looked at first, and Auto-Approved is fixed to expected margin for capacity. Ad-hoc filtering (by policy, employer, desk, score band) is not in the UI — but ask me instead: I can answer "how many whole-life cases", "which desk is busiest", "cases with coverage over 900k".`},
 {k:['decision memo','memo contents','what is in the memo','download the memo','case summary document'],
  a:()=>`The decision memo is the case's shareable record: applicant and policy details, the composite score with its rule and ML halves, the ranked risk factors, any document conflicts, the affordability result, the system's recommendation, the human decision with its written rationale, and the attributed timestamped audit trail. It downloads from the case desk once a decision is recorded — that is the artifact an agent, a reinsurer or an auditor asks for.`},
 {k:['print','pdf a case','export the case','share the case','hard copy'],
  a:()=>`Use the <b>decision memo</b> download for a shareable record of one case, or the admin's CSV/JSON exports for the whole trail. There is no dedicated print stylesheet, so browser print will work but will not be pretty — worth adding for the underwriters who still put a file in front of a chief medical officer.`},
 {k:['tablet','mobile','phone','ipad','responsive','small screen','laptop screen'],
  a:()=>`It is one self-contained page with a responsive layout, so it opens and works on a tablet or laptop — the chat panel and cards reflow, and there is nothing to install. It is designed for a <b>desk</b> though: the queue, the case tabs and the executive tables assume width, so a phone will feel cramped. Since everything is in one file with no server, a tablet works offline just as well as online.`},
 {k:['offline','no internet','without a server','airplane','local file','self contained'],
  a:()=>`Yes — that is a design constraint, not an accident. The whole app is a <b>single self-contained HTML file</b>: the book, the model coefficients, the scoring engine and this assistant all ship inside it, with no external requests at runtime. Open it from a file on a laptop with no network and every feature works, including scoring a new application and this conversation. State saves to your browser.`},
 {k:['api','integrate with','webhook','rest','sdk','programmatic','headless','batch scoring'],
  a:()=>`Two surfaces exist. A <b>FastAPI service</b> in the repo serves the portfolio and accepts decisions (<span class="mono">GET /portfolio</span>, <span class="mono">POST /cases/{id}/decision</span>, SQLite-backed) for a live deployment; the deployed demo runs without it, snapshot-only. For batch work, the manager's <b>Pilot benchmark CSV</b> is the intended artifact: run a batch of real applications through the engine and get scores, flags, routing and time-to-decision beside your underwriters' own decisions. Anything richer — CRM sync, agent-portal callbacks — is pilot connector work behind the same extraction layer.`},
 {k:['add a user','new user','provision','user admin','manage users','permissions','new role','access control'],
  a:()=>`Not in the demo: the six accounts are fixed in the source and sign-in is an honest <b>role selector</b>, not authentication. Real user administration — provisioning, role changes, authority limits per underwriter, separation-of-duties checks, deprovisioning — is an operations responsibility and sits on the roadmap. The role model itself is the part worth reviewing now: which authority each role holds, and what each one can and cannot change.`},
 {k:['data residency','where does data live','hosting','cloud','on premise','sovereignty','malaysia','indonesia','servers'],
  a:()=>`In the demo, nowhere but your browser — the page is static and stores state locally, so no application data leaves the machine. For a pilot, residency is a deployment choice rather than a rewrite: the scoring engine is a Python service plus a static front end, so it can run in-country or on-premise to satisfy local data-protection requirements. The design deliberately avoids external data dependencies at decision time, which keeps that choice open.`},
 {k:['session timeout','log me out','stay signed in','auto logout','idle','security of login','password','authentication','real login','is the login','sign-in real','sign in real','\bauth\b'],
  a:()=>`No timeout, and no real authentication — the demo's sign-in is a role selector, so treat it as a stage prop rather than a security control. Sign out clears the session in this tab; state persists in the browser until site data is cleared. Real auth, SSO, idle timeout and access logging are pilot requirements, not demo features.`},
 {k:['are you an ai','are you a bot','are you human','are you chatgpt','what are you','llm','who are you'],
  a:()=>`I am an assistant built into this page — not a language model calling out to a server. Everything I answer comes from the platform's own rulebook and the live book in front of you, which is why I ship inside a single offline file and why my numbers always match the screen. The trade-off is honest: I know this product deeply and nothing else, so I will tell you when something is outside the build instead of guessing. A pilot could swap my retrieval layer for a hosted model without changing this panel.`},
 {k:['trust your numbers','why should i trust','how do i know you are right','are you accurate','make things up','hallucinat','verify what you say'],
  a:()=>`Check me — everything I quote is on screen. Case answers read the same fields the case file shows; portfolio figures use the same computation as the Executive Overview; rankings use the same ordering as the spaces; rule points come from the published weight table. I compute rather than recall, so I cannot drift from the app. Two honest limits: the book is <b>synthetic data</b>, so no figure here describes a real person or a real carrier's results, and the P&L rests on named illustrative assumptions (SG&A 12%, select-period factor) that a pilot would replace with your actuals.`},
 {k:['what can you not','what cant you','your limits','limitations','out of scope for you','what dont you know'],
  a:()=>`Straight answer. I <b>cannot</b>: change data or record decisions for you (ask me what to do, then do it in the case desk); read anything outside this book, since there are no external data calls by design; price a policy or issue table ratings, which this build does not do; or speak to reinsurance, juvenile, or occupational-loading rules that are not modelled. I also cannot promise a legal or actuarial opinion — the book is synthetic and the economics rest on labelled assumptions. Everything else about this platform, its rules, its cases and its numbers, ask away.`},
 {k:['hire another underwriter','more underwriters','headcount','capacity planning','staffing','throughput per underwriter','how many can one'],
  a:()=>{const y=CASES.filter(c=>c.verdict==='yellow').length;
   return `Do the arithmetic on the current book: <b>${y} of ${CASES.length}</b> applications need a human (${(100-M.decisioning.straight_through_rate*100).toFixed(0)}%), at roughly $${COST_HUMAN} of fully-loaded underwriter time each. Another underwriter adds review capacity but does nothing for the ${(M.decisioning.straight_through_rate*100).toFixed(0)}% that never reaches a desk — so the cheaper lever is usually the <b>approval line</b> (configuration, and I can model moving it: ask "if I raise the approval line to 60, how many more auto-approve?"). Hire for the referred band when volume grows; automate to keep that band from growing with it.`;}},
 {k:['model is unavailable','model goes down','if the model fails','system down','fallback','outage','manual mode'],
  a:()=>`The business does not stop. The two halves fail differently: the <b>rule engine</b> is a deterministic weight table that always scores, and the <b>ML half</b> is exported coefficients evaluated in the page, so there is no live service to be down — the demo has no runtime dependency at all. If a pilot's model service were unavailable, the safe posture is to route everything to <b>manual review</b> rather than fall back to the rule half alone: underwriting continues at manual cost and manual speed, which is the pre-automation baseline, and nothing gets auto-decided on half the evidence.`},
 {k:['score a','what would a','hypothetical','test an applicant','try a case','new application','price out','run a scenario for'],
  a:()=>`Use the <b>Score a new application</b> form (on the Portfolio & Model Card page) — enter age, tobacco, build, conditions and the financials and it runs the same engine in your browser: composite score, both halves, the factor breakdown and the band. I cannot score an applicant from a sentence, because a real score needs the full field set the form asks for, and inventing the missing fields would give you a confident wrong number. Tell me the profile you want to test and I will tell you which fields drive it.`},
 {k:['reviewed first','identical score','same score','tiebreak','tie-break','a tie','who goes first','queue order','order of the queue','ordering','decides who gets','review order','which gets looked at'],
  a:()=>`Score doesn’t decide it at all — two applicants with identical scores are ordered exactly like everyone else. Queue priority is <b>60% coverage + 40% time-in-queue</b>: bigger exposure and older cases rise, and the risk score is <b>deliberately excluded</b> from the ordering so the model never chooses who gets human attention first. If both coverage and age match too, the tie is immaterial — both cases carry the same SLA clock and both get reviewed.`},
 {k:['disagree','disagreement','two underwriters','conflicting opinion','who wins','tie break','second opinion'],
  a:()=>`Two kinds of disagreement. <b>Model disagreement</b> — when the rule engine and the ML model diverge sharply on the same file — is itself a referral trigger: the case goes to a human rather than being auto-decided. <b>Human disagreement</b> resolves by authority: the case belongs to whoever holds it, and only a <b>manager</b> can override a recorded decision (logged as MANAGER OVERRIDE, with a written reason and what it superseded). Operations can amend a decision recorded in error, but that is a correction, not a risk opinion.`},
 {k:['rule engine vs','rule half','ml half','difference between the rule','rules vs the model','why two models','why both'],
  a:()=>`They answer different questions. The <b>rule engine</b> is transparent and evidence-anchored: each factor carries published points (<span class="mono">28 × ln(relative mortality)</span>) you can read off the case, so any score can be explained line by line. The <b>ML model</b> catches interactions no rule table encodes, trained on ${(M.risk_models.n_train||0).toLocaleString()} records (AUC ${(M.risk_models.gradient_boosting.auc*100).toFixed(1)}%). The composite is a <b>50/50 blend</b> — the rules keep it defensible, the model keeps it accurate, and a sharp divergence between them refers the case to a human.`},
 {k:['single factor','one factor','enough to decline','automatically decline','auto decline someone','one condition','by itself'],
  a:()=>`No single medical or lifestyle factor declines an application on its own. Every factor contributes <b>points</b> to a 0–100 composite, and only the composite crosses a line — so a high BMI, a condition, or heavy alcohol use raises the score but is judged in the whole-person context. The one exception is <b>material misrepresentation</b>: a declared non-smoker with a positive cotinine lab auto-declines regardless of score, because the evidence contradicts a sworn answer.`},
 {k:['how long does','turnaround','how much does an','how expensive','vendor time','what does an aps cost','evidence cost'],
  a:()=>`Typical evidence turnaround and cost: <b>APS ~$350, weeks</b> (the slowest and priciest) · paramed exam ~$150, days–weeks · EKG ~$180, days–weeks · labs ~$120, days · cognitive ~$90, days · MVR ~$12, hours–days · Rx history ~$15, hours–days · MIB ~$8, hours. That spread is why the AI pre-check flags a non-indicated or duplicate order <i>before</i> dispatch — an unnecessary APS costs both the money and the weeks.`},
 {k:['bias','biased','fair','discriminat','protected','age bias','unfair'],
  a:()=>`Three defences. <b>Inputs</b>: the rule weights are derived from published mortality evidence (NHANES + NCHS linked mortality), not from historical accept/decline decisions, so past human bias is not learned as signal. <b>Measurement</b>: the Model Card reports <b>fairness by age band and group</b> alongside calibration, so drift is visible rather than assumed away. <b>Process</b>: no protected characteristic is a rule factor, every borderline case gets a human, and every decision carries a written reason in an audit trail a regulator can read.`},
 {k:['who owns','who changes','who signs off','who decides the line','change the threshold','approval line owner','governance of'],
  a:()=>`The acceptance lines (<b>approve under ${A_LINE}</b>, <b>decline at ${D_LINE}</b>) and the ${fmtBigMoney(APPETITE_MONTHLY)} monthly appetite are <b>configuration owned by underwriting leadership</b> — the Chief Underwriting Officer's levers, versioned, not baked into the model. Tightening or loosening the book is a config change with an owner, not a retrain. Individual case authority sits with the desks; decision changes sit with the manager; ops owns the flow.`},
 {k:['what can you do','what do you know','help me','your capabilities','what can i ask','how do i use you','show me everything','everything you can','list what you'],
  a:()=>`Ask me anything about this platform or the book. I answer: <b>rules</b> (decision bands, conflict screen, affordability, requirements grid, routing, SLAs, weights) · <b>live numbers</b> (“what is my loss ratio right now?”, “how much are we earning a month?”) · <b>any applicant</b> by name or case ID, including single fields (“${CASES[0].name}’s credit score”, “does it match across the documents?”) · <b>rankings</b> (auto-approved by margin, auto-declined by risk, who to review first) · and <b>the app itself</b> (roles, exports, spaces, overrides, where things live).`},
 {k:['what is this app','what is this platform','what does this do','what is underwriting copilot','about this system','what am i looking at'],
  a:()=>`<b>Underwriting Copilot</b> — an AI-assisted life-insurance underwriting workbench. It reads a five-document application packet, runs a 6-check cross-document conflict screen, scores risk 0–100 on evidence-anchored weights plus a trained model, and routes only the ambiguous middle band to a human. It runs on a <b>synthetic book of ${CASES.length} applications</b> — a prototype, not a live carrier system — and the whole thing is one self-contained file that works offline.`},
 {k:['spaces','review queue','completed','left rail','sidebar','navigation','case list','case spaces'],
  a:()=>`The left rail holds four case spaces: <b>Review Queue</b> (the ${CASES.filter(c=>c.verdict==='yellow').length} cases needing a human, ranked by coverage + time), <b>Completed</b> (what you have decided), <b>Auto-Approved</b> (${CASES.filter(c=>c.verdict==='green').length} straight-through approvals, ranked by expected margin) and <b>Auto-Declined</b> (${CASES.filter(c=>c.verdict==='red').length}, kept as a record). The executive sees a live book-at-a-glance panel there instead — no case list.`},
 {k:['keyboard','shortcut','esc','arrow key','navigate cases','next case'],
  a:()=>`Inside a case file: <b>Esc</b> returns to the queue with your scroll position intact, and <b>←/→</b> walk to the previous or next case in the list you opened it from. The search box filters by applicant name or case ID.`},
 {k:['theme','dark mode','light mode','colour','color scheme','toggle'],
  a:()=>`The ☀️/🌙 button top-right switches light and dark; the app opens in <b>light mode</b> and remembers your choice in this browser.`},
 {k:['tour','tutorial','walkthrough','guided','demo flow','how do i demo'],
  a:()=>`The <b>🎓 Tutorial</b> button runs a guided tour: it opens with the insurance value chain and the pain it addresses, then follows <b>one case end to end</b> — junior desk, escalation by authority, senior review, evidence, decision — before touring the manager, executive and operations personas. It drives the real app as it goes.`},
 {k:['bulk','approve all','batch','all at once'],
  a:()=>`The Auto-Approved space has <b>Bulk approve all</b> — it records the batch under one rationale, but writes each case to its own audit trail individually, so the record stays per-case.`},
 {k:['saved','stored','database','persist','local storage','where is the data','lose my work','real data','refresh','reload','close the browser','start over','reset the demo'],
  a:()=>`Everything runs <b>in your browser</b>: decisions, notes, assignments and evidence requests are stored in this browser only (localStorage), and the book itself is <b>synthetic data</b> — no real applicants, no server, no network calls. Clearing site data resets the demo to a clean book.`},
 {k:['model card','fairness','calibration','feature importance','regulator','governance','bias'],
  a:()=>`The <b>Portfolio & Model Card</b> (manager nav) is the regulator-facing page: score formula and bands, feature importance, calibration, <b>fairness by age band and group</b>, dataset provenance, and the evidence-anchored weight table. It exists so the model is defensible in an exam, not just accurate.`},
 {k:['pdf','original document','view document','open the packet','attachment'],
  a:()=>`Cases marked <b>· PDF</b> carry original scanned documents you can open inline from the Documents tab; every case also shows the parsed field-level extraction beside the source, so you can check what the reader pulled against the page.`},
 {k:['earning','earn','revenue','profit','making','money a month','per month','how much money','we making','am i making'],
  a:()=>{const appr=CASES.filter(c=>finalOf(c)==='approve');
   const prem=appr.reduce((s,c)=>s+(c.premium||0),0);
   const claims=appr.reduce((s,c)=>s+expectedAnnualClaim(c),0);
   const refN=CASES.filter(c=>c.verdict==='yellow').length;
   const ops=CASES.length*COST_AUTO+refN*COST_HUMAN;
   const opInc=prem*(1-SGA_RATE)-claims-ops;
   return `The approved book writes <b>${fmtMoneyK(prem)}/yr</b> of premium — about <b>${fmtMoneyK(prem/12)} a month</b>. After expected claims (${fmtMoneyK(claims)}/yr), SG&A (12%) and the cost to underwrite, expected operating income is <b>${fmtMoneyK(opInc)}/yr ≈ ${fmtMoneyK(opInc/12)}/month</b>. These are live numbers — they move as decisions are recorded — and the full P&L sits on the Executive Overview.`;}},
 {k:['how many case','how many application','book size','total cases','how big is the book','case count'],
  a:()=>{const a=CASES.filter(c=>finalOf(c)==='approve').length,d=CASES.filter(c=>finalOf(c)==='decline').length;const p=CASES.length-a-d;
   return `The book holds <b>${CASES.length} applications</b>: <b>${a}</b> approved, <b>${p}</b> referred / pending, <b>${d}</b> declined. ${CASES.filter(c=>c.verdict==='yellow').length} needed a human; the rest decided straight-through.`;}},
 {k:['coverage accepted','exposure','how much cover','risk on the book','underwritten'],
  a:()=>{const appr=CASES.filter(c=>finalOf(c)==='approve');
   const cov=appr.reduce((s,c)=>s+(c.coverage||0),0);
   return `The book has accepted <b>${fmtBigMoney(cov)}</b> of coverage across ${appr.length} approved policies — ${(cov/APPETITE_MONTHLY*100).toFixed(0)}% of the ${fmtBigMoney(APPETITE_MONTHLY)} monthly appetite. Average approved policy: ${fmtBigMoney(appr.length?cov/appr.length:0)}.`;}}
];
function uwgMetricAnswer(q){
 // A question about a specific metric gets the EXACT live number first —
 // the one-line computation after it, never a definition of the term.
 const appr=CASES.filter(c=>finalOf(c)==='approve');
 const prem=appr.reduce((s,c)=>s+(c.premium||0),0);
 const claims=appr.reduce((s,c)=>s+expectedAnnualClaim(c),0);
 const sga=prem*SGA_RATE;
 const refN=CASES.filter(c=>c.verdict==='yellow').length;
 const ops=CASES.length*COST_AUTO+refN*COST_HUMAN;
 const opInc=prem-claims-sga-ops;
 const loss=prem?claims/prem*100:0, exp=prem?(sga+ops)/prem*100:0, comb=loss+exp;
 const cov=appr.reduce((s,c)=>s+(c.coverage||0),0);
 const MM=[
  [/loss ratio/,()=>`<b>${loss.toFixed(1)}%</b> — expected claims ${fmtMoneyK(claims)}/yr ÷ approved premium ${fmtMoneyK(prem)}/yr.`],
  [/expense ratio/,()=>`<b>${exp.toFixed(1)}%</b> — (SG&A ${fmtMoneyK(sga)} + underwriting cost ${fmtMoneyK(ops)}) ÷ premium ${fmtMoneyK(prem)}/yr.`],
  [/combined ratio/,()=>`<b>${comb.toFixed(1)}%</b> — loss ${loss.toFixed(1)}% + expense ${exp.toFixed(1)}%.`],
  [/operating income|bottom line/,()=>`<b>${fmtMoneyK(opInc)}/yr</b> (≈${fmtMoneyK(opInc/12)}/month) — premium ${fmtMoneyK(prem)} − claims ${fmtMoneyK(claims)} − SG&A ${fmtMoneyK(sga)} − underwriting cost ${fmtMoneyK(ops)}.`],
  [/making money|profitable|in the black|break.?even|before or after the cost|money before|money after/,()=>{
    const before=prem-claims-sga, after=before-ops;
    return `Both, in this book — but the honest cut is <b>after</b>. Before underwriting cost: <b>${fmtMoneyK(before)}/yr</b> (premium ${fmtMoneyK(prem)} − claims ${fmtMoneyK(claims)} − SG&A ${fmtMoneyK(sga)}). After the ${fmtMoneyK(ops)} cost to underwrite: <b>${after>=0?'':'−'}${fmtMoneyK(Math.abs(after))}/yr</b> operating income. Underwriting cost is ${(ops/prem*100).toFixed(1)}% of premium, so automation is what keeps the after-number close to the before-number.`;}],
  [/straight.?through|\bstp\b/,()=>`<b>${(M.decisioning.straight_through_rate*100).toFixed(1)}%</b> decided with no human touch.`],
  [/appetite/,()=>`<b>${(cov/APPETITE_MONTHLY*100).toFixed(0)}%</b> of the ${fmtBigMoney(APPETITE_MONTHLY)} monthly appetite — ${fmtBigMoney(cov)} accepted.`],
  [/approved premium|premium (of|on|across) the book/,()=>`<b>${fmtMoneyK(prem)}/yr</b> (≈${fmtMoneyK(prem/12)}/month) across ${appr.length} approved policies.`],
  [/expected claims|claims payout/,()=>`<b>${fmtMoneyK(claims)}/yr</b> of expected claims against ${fmtMoneyK(prem)}/yr of premium (loss ratio ${loss.toFixed(1)}%).`],
  [/average (approved )?cover|avg cover/,()=>`<b>${fmtBigMoney(appr.length?cov/appr.length:0)}</b> average approved cover across ${appr.length} policies.`]];
 for(const [re,fn] of MM)if(re.test(q))return fn()+' <i>Live from the current book.</i>';
 return null;
}
function uwgRankAnswer(kind){
 // Ranked reads of the auto-decisioned book — the same ordering the
 // Auto-Approved space uses (expected margin), worst-first for declines.
 if(kind==='approve'){
  const l=CASES.filter(c=>c.verdict==='green').sort((a,b)=>(acceptMargin(b)-acceptMargin(a))||(a.risk_score-b.risk_score)).slice(0,5);
  return `<b>Auto-approved, ranked best candidate first</b> (by expected annual underwriting margin — premium − expected claims − SG&A):<br>${l.map((c,i)=>`${i+1}. <span class="mono">${c.id}</span> ${c.name} — ${fmtMoneyK(acceptMargin(c))}/yr margin, score ${c.risk_score}, ${fmt$(c.coverage)}`).join('<br>')}<br>The full ranked list, with the appetite cutoff, lives in the <b>Auto-Approved</b> space.`;
 }
 const l=CASES.filter(c=>c.verdict==='red').sort((a,b)=>b.risk_score-a.risk_score).slice(0,5);
 return `<b>Auto-declined, ranked highest risk first</b>:<br>${l.map((c,i)=>`${i+1}. <span class="mono">${c.id}</span> ${c.name} — score ${c.risk_score}${(c.reasons||[])[0]?', '+c.reasons[0].toLowerCase():''}`).join('<br>')}<br>Every one is filed with its rationale in the <b>Auto-Declined</b> space — and any can be pulled back into manual review.`;
}
/* ---- book-level analytics: counts, averages, superlatives, existence ----
   "How many cases breached SLA?", "which case has the highest coverage?",
   "what is the average risk score?" — computed live over the current book,
   because an underwriter asks the book questions, not just case questions. */
function uwgSubset(q){
 // A subset has two independent parts: a SCOPE (which pile of cases) and
 // ATTRIBUTES (what is true of them). "Smokers in the queue" is one of each,
 // so they intersect rather than the first one winning.
 const undecidedY=CASES.filter(c=>c.verdict==='yellow'&&!wfGet(c.id).decision);
 const SCOPE=[
  [/my desk|my queue|my cases|assigned to me|on my plate|\bmine\b/,'open on your desk',()=>undecidedY.filter(c=>CURRENT_ROLE!=='underwriter'||wfGet(c.id).assigneeUid===CURRENT_UID)],
  [/which desk|what desk|whose desk|which underwriter|who holds|which team/,'in manual review (the only cases on a desk)',()=>undecidedY],
  [/review queue|in (the )?queue|manual review|referred|need a human|pending|undecided|awaiting|not decided/,'in manual review',()=>undecidedY],
  [/auto.?declin|\bdeclined\b|rejected|decline pile/,'auto-declined',()=>CASES.filter(c=>c.verdict==='red')],
  [/auto.?approv|\bapproved\b|straight.?through/,'auto-approved',()=>CASES.filter(c=>c.verdict==='green')]];
 const ATTR=[
  [/\bsla\b|breach|over the 8|past due|overdue/,'past the 8-hour SLA',()=>CASES.filter(c=>c.verdict==='yellow'&&!wfGet(c.id).decision&&ageHours(c)>=8)],
  [/conflict|mismatch|discrepan|flagged/,'with document conflicts',()=>CASES.filter(c=>(c.conflicts||[]).length)],
  [/non.?disclos|misrepresent|undeclared smok|hid(ing|den)? (their |the )?(smoking|tobacco)|lied about|lying about|positive cotinine|cotinine .{0,24}(but|no|non|without)|no smoker flag|didn.?t declare|failed to declare/,'with smoker non-disclosure (declared non-smoker, cotinine positive — material misrepresentation)',()=>CASES.filter(c=>(c.conflicts||[]).some(k=>k.type==='smoker_nondisclosure'))],
  [/smoker|tobacco|cotinine/,'smokers',()=>CASES.filter(c=>/smok/i.test(c.smoker||'')&&!/non/i.test(c.smoker||''))],
  [/afford/,'failing the affordability screen',()=>CASES.filter(c=>c.afford&&c.afford.verdict==='fail')],
  [/unique|disclos|section 6/,'with unique circumstances disclosed',()=>CASES.filter(c=>c.unique)],
  [/pdf|scanned|original doc/,'with original PDFs attached',()=>CASES.filter(c=>c.has_docs)],
  [/condition|medical|diabet|hypertens/,'with declared medical conditions',()=>CASES.filter(c=>c.conditions&&c.conditions!=='None')],
  [/hazard|skydiv|dangerous activit/,'with hazardous activities',()=>CASES.filter(c=>c.hazard&&c.hazard!=='None')]];
 let scope=null;
 for(const [re,label,fn] of SCOPE)if(re.test(q)){scope={label,fn};break;}
 const attrs=[];
 for(const [re,label,fn] of ATTR)if(re.test(q))attrs.push({label,fn});
 if(!scope&&!attrs.length)return null;
 const keep=[];
 if(attrs.length){
  // multiple attributes intersect only on an explicit conjunction
  if(attrs.length>1&&/\bboth\b|as well as|and also|at the same time/.test(q))keep.push(...attrs);
  else keep.push(attrs[0]);
 }
 let list=CASES.slice();
 keep.forEach(a=>{const ids=new Set(a.fn().map(c=>c.id));list=list.filter(c=>ids.has(c.id));});
 if(scope){const ids=new Set(scope.fn().map(c=>c.id));list=list.filter(c=>ids.has(c.id));}
 const attrLabel=keep.map(a=>a.label).join(' AND ');
 const label=[attrLabel,scope?scope.label:''].filter(Boolean).join(' ')||'in the book';
 return {label,list};
}
function uwgMetricOf(q){
 // `worse` gives each metric a direction, so "the worst credit score" means the
 // LOWEST while "the worst risk score" means the highest. `sum` marks the
 // metrics it is meaningful to total.
 if(/\bgap\b|diverg|disagree|difference between|rule .{0,12}(vs|versus|and) .{0,6}ml|ml .{0,12}(vs|versus|and) .{0,6}rule|split between/.test(q)&&/rule|ml|model|score/.test(q))
  return {label:'rule-vs-ML gap',get:c=>Math.abs((c.rule_score||0)-(c.ml_score||0)),fmt:v=>Math.round(v)+' pts',worse:'high',gap:1};
 if(/years? old|yrs old|aged \d|\bage of\b/.test(q))return {label:'age',get:c=>c.age||0,fmt:v=>Math.round(v)+' years',worse:'high'};
 if(/coverage|cover\b|face amount|exposure/.test(q))return {label:'coverage',get:c=>c.coverage||0,fmt:v=>fmt$(v),worse:'high',sum:1};
 if(/premium/.test(q))return {label:'premium',get:c=>c.premium||0,fmt:v=>fmt$(v)+'/yr',worse:'low',sum:1};
 if(/expected claim|claims cost|payout/.test(q))return {label:'expected annual claims',get:c=>expectedAnnualClaim(c),fmt:v=>fmt$(v)+'/yr',worse:'high',sum:1};
 if(/\bage\b|oldest|youngest/.test(q))return {label:'age',get:c=>c.age||0,fmt:v=>Math.round(v)+' years',worse:'high'};
 if(/credit/.test(q))return {label:'credit score',get:c=>c.credit||0,fmt:v=>Math.round(v),worse:'low'};
 if(/\bbmi\b/.test(q))return {label:'BMI',get:c=>c.bmi||0,fmt:v=>v.toFixed(1),worse:'high'};
 if(/income|salary/.test(q))return {label:'income',get:c=>c.income||0,fmt:v=>fmt$(v),worse:'low',sum:1};
 if(/score|risk/.test(q))return {label:'risk score',get:c=>c.risk_score||0,fmt:v=>Math.round(v),worse:'high'};
 if(/queue|waiting|\bsla\b|time in|how long/.test(q))return {label:'time in queue',get:c=>ageHours(c),fmt:v=>fmtAge(v),worse:'high'};
 return null;
}
function uwgAggregateAnswer(q){
 const wantsCount=/how many|number of|count of|how much of the book/.test(q);
 const wantsPct=/what (percent|percentage|share)|percentage of|what pc/.test(q);
 const wantsAvg=/average|mean |typical/.test(q);
 const wantsMax=/highest|largest|biggest|most |top |maximum|longest|oldest|worst|riskiest|most risky/.test(q);
 const wantsMin=/lowest|smallest|least|minimum|shortest|youngest|cheapest|best score|safest|least risky/.test(q);
 const wantsAny=/^(is|are|does|do|has|have|did) (there|any|anyone|anybody)|\bany case|\banyone (who|with|over|under|lied|hid|declared)/.test(q);
 // "how much premium is sitting in the queue" — a total, not a count. Excludes
 // price questions ("how much does an APS cost"), which belong to the rulebook.
 const wantsSum=/how much|\btotal\b|combined|sum of|aggregate|worth of|how many dollars/.test(q)
   &&!/how much (does|do|would|did|will) (an?|it|the|that|this)\b/.test(q);
 if(!(wantsCount||wantsPct||wantsAvg||wantsMax||wantsMin||wantsAny||wantsSum))return null;
 const sub=uwgSubset(q);
 let met=uwgMetricOf(q);
 // a question about a gap/difference must resolve to the gap metric or not at all —
 // substituting "risk score" here is how a confidently wrong answer happens
 if(/\bgap\b|diverg|difference between|delta between|spread between/.test(q)&&(!met||!met.gap))return null;
 if(!met&&(wantsMax||wantsMin)&&/largest|biggest|smallest|most expensive|cheapest/.test(q))met=uwgMetricOf('coverage');
 if(!met&&(wantsMax||wantsMin)&&/worst|best|riskiest|safest/.test(q))met=uwgMetricOf('risk score');
 if(!sub&&!met)return null;   // no subject and no metric: not an analytics question
 // a numeric qualifier: "over 60", "above $700k", "score under 40"
 let list=sub?sub.list:CASES.slice(),label=sub?sub.label:'in the book';
 const num=q.match(/(over|above|more than|greater than|under|below|less than|at least)\s*\$?\s*([\d.,]+)\s*(k|m|million|thousand)?/);
 if(num){
  let v=parseFloat(num[2].replace(/,/g,''));const u=(num[3]||'').toLowerCase();
  const money=/\$/.test(q)||!!u;
  if(u==='k'||u==='thousand')v*=1000;if(u==='m'||u==='million')v*=1e6;
  // a bare small number is an age or a score, never a dollar amount
  let fm=met;
  if(!money&&v<=130){
   fm=(/score|risk/.test(q)&&!/credit/.test(q))?uwgMetricOf('risk score')
     :/credit/.test(q)?uwgMetricOf('credit')
     :/\bbmi\b/.test(q)?uwgMetricOf('bmi')
     :(!met||met.sum||met.label==='age')?uwgMetricOf('years old'):met;
  }
  if(fm){
   const up=/over|above|more than|greater than|at least/.test(num[1]);
   list=list.filter(c=>up?fm.get(c)>=v:fm.get(c)<=v);
   label=`${label==='in the book'?'':label+' '}with ${fm.label} ${up?'over':'under'} ${fm.fmt(v)}`;
   if(!met)met=fm;
  }
 }
 const ex=l=>l.slice(0,3).map(c=>`<span class="mono">${c.id}</span> ${c.name}`).join(', ');
 if(wantsSum&&!met&&/money|dollar|value|tied up|worth|exposure|capital/.test(q))met=uwgMetricOf('coverage');
 if(wantsSum&&met&&met.sum){
  if(!list.length)return `Nothing ${label} to total.`;
  const tot=list.reduce((s,c)=>s+met.get(c),0);
  const bookTot=CASES.reduce((s,c)=>s+met.get(c),0);
  const biggest=list.slice().sort((a,b)=>met.get(b)-met.get(a))[0];
  return `<b>${met.fmt(tot)}</b> of ${met.label} across <b>${list.length}</b> case(s) ${label} — ${bookTot?(tot/bookTot*100).toFixed(0):0}% of the book's ${met.fmt(bookTot)}. Largest single: <span class="mono">${biggest.id}</span> ${biggest.name} at ${met.fmt(met.get(biggest))}.`;
 }
 if(wantsMax||wantsMin){
  if(!met)return null;
  // "worst"/"best" follow the metric's own direction
  let hi=wantsMax;
  if(/\bworst\b|riskiest/.test(q))hi=met.worse!=='low';
  else if(/\bbest\b|safest|healthiest|strongest/.test(q))hi=met.worse==='low';
  const sorted=list.slice().sort((a,b)=>hi?met.get(b)-met.get(a):met.get(a)-met.get(b));
  const wantsMaxL=hi;
  const top=sorted.slice(0,3);if(!top.length)return `No cases ${label}.`;
  uwgLastCase=top[0];
  return `${wantsMaxL?'Highest':'Lowest'} <b>${met.label}</b> ${label==='in the book'?'in the book':label}:<br>${top.map((c,i)=>{const st=wfGet(c.id);
    return `${i+1}. <span class="mono">${c.id}</span> ${c.name} — <b>${met.fmt(met.get(c))}</b>${met.gap?` (rule ${c.rule_score} / ML ${Math.round(c.ml_score)})`:met.label!=='risk score'?`, score ${c.risk_score}`:''}, ${c.decision.toLowerCase()}${(c.verdict==='yellow'&&st.assignee)?` · ${st.assignee} (${(UWS[st.tier]||{}).label||''} desk)`:''}`;}).join('<br>')}${met.gap?`<br>A wide split matters: strong rule/ML disagreement is itself a referral trigger — neither half is trusted alone when they can’t agree.`:''}`;
 }
 if(wantsAvg){
  if(!met)return null;
  if(!list.length)return `No cases ${label} to average.`;
  const avg=list.reduce((s,c)=>s+met.get(c),0)/list.length;
  return `Average <b>${met.label}</b> ${label==='in the book'?'across the book':label} is <b>${met.fmt(avg)}</b> over ${list.length} case(s).`;
 }
 // count / percentage / existence
 const pct=(list.length/CASES.length*100).toFixed(0);
 if(wantsAny)return list.length?`Yes — <b>${list.length}</b> case(s) ${label}: ${ex(list)}${list.length>3?`, and ${list.length-3} more`:''}.`:`No — nothing ${label} in the current book.`;
 return `<b>${list.length}</b> of ${CASES.length} case(s) ${label} — <b>${pct}%</b> of the book.${list.length?` For example ${ex(list)}.`:''}`;
}
function uwgGroupAnswer(q){
 // "which policy type approves most?", "workload by desk", "exposure by state"
 if(/riskiest|worst case|highest|lowest|oldest case|which case|largest|biggest|most expensive/.test(q))return null;   // that is a case question
 const grp=/by (policy|product|type)|policy type|which product|whole life|term life|universal/.test(q)?'policy'
  :/desk|analyst|senior|mid.?tier|workload|who is busiest|team load/.test(q)?'desk'
  :/state|region|geograph|where.*exposure|by city/.test(q)?'state':null;
 if(!grp)return null;
 if(grp==='desk'){
  const y=CASES.filter(c=>c.verdict==='yellow'&&!wfGet(c.id).decision);
  const d={};y.forEach(c=>{const t=wfGet(c.id).tier||'unassigned';(d[t]=d[t]||[]).push(c);});
  const rows=Object.entries(d).sort((a,b)=>b[1].length-a[1].length).map(([t,l])=>{
   const avg=l.reduce((s,c)=>s+ageHours(c),0)/l.length;
   const br=l.filter(c=>ageHours(c)>=8).length;
   return `<b>${(UWS[t]||{}).label||t}</b>${(UWS[t]||{}).name?` (${UWS[t].name})`:''} — ${l.length} open, avg ${fmtAge(avg)} in queue, ${br} over SLA`;});
  return `Workload across the desks right now:<br>${rows.join('<br>')}<br>Routing is by authority, not availability — a case lands on the desk allowed to hold it, so an uneven split is expected.`;
 }
 if(grp==='policy'){
  const g={};CASES.forEach(c=>{(g[c.policy]=g[c.policy]||[]).push(c);});
  const rows=Object.entries(g).map(([p,l])=>{
   const ap=l.filter(c=>c.verdict==='green').length,rf=l.filter(c=>c.verdict==='yellow').length,dc=l.filter(c=>c.verdict==='red').length;
   const cov=l.reduce((s,c)=>s+(c.coverage||0),0);
   return {p,n:l.length,ap,rf,dc,rate:ap/l.length*100,cov};})
   .sort((a,b)=>b.rate-a.rate);
  return `By policy type — approval rate, mix and exposure:<br>${rows.map(r=>`<b>${r.p}</b> — ${r.n} cases (${(r.n/CASES.length*100).toFixed(0)}% of book), <b>${r.rate.toFixed(0)}% auto-approved</b>, ${r.rf} referred, ${r.dc} declined, ${fmtBigMoney(r.cov)} requested`).join('<br>')}`;
 }
 const g={};CASES.forEach(c=>{const k=c.state||'—';(g[k]=g[k]||[]).push(c);});
 const rows=Object.entries(g).map(([st,l])=>({st,n:l.length,cov:l.filter(c=>finalOf(c)==='approve').reduce((s,c)=>s+(c.coverage||0),0)}))
  .sort((a,b)=>b.cov-a.cov).slice(0,6);
 return `Accepted exposure by state (top ${rows.length}):<br>${rows.map(r=>`<b>${r.st}</b> — ${fmtBigMoney(r.cov)} accepted across ${r.n} application(s)`).join('<br>')}<br>Concentration is worth watching: a single-state catastrophe correlates claims that the score treats as independent.`;
}
function uwgWhatIfAnswer(q){
 // Threshold and claims scenarios, recomputed live rather than described.
 const line=q.match(/(approval|approve|accept)[^\d]{0,24}(\d{2})|(\d{2})[^\d]{0,14}(approval|approve) line/);
 if(line&&/raise|lower|move|change|set|if (i|we)/.test(q)){
  const v=parseInt(line[2]||line[3],10);
  if(v>=10&&v<=95){
   const now=CASES.filter(c=>c.verdict==='green').length;
   const then=CASES.filter(c=>c.risk_score<v&&!(c.conflicts||[]).some(k=>k.severity==='major')).length;
   const d=then-now;
   const newCov=CASES.filter(c=>c.risk_score<v&&!(c.conflicts||[]).some(k=>k.severity==='major')).reduce((s,c)=>s+(c.coverage||0),0);
   // and what that does to the money, since the line is the executive's lever
   const clean=c=>!(c.conflicts||[]).some(k=>k.severity==='major');
   const setFor=L=>CASES.filter(c=>c.risk_score<L&&clean(c));
   const pnl=L=>{const a=setFor(L);const prem=a.reduce((s,c)=>s+(c.premium||0),0);
    const cl=a.reduce((s,c)=>s+expectedAnnualClaim(c),0);
    const ref=CASES.filter(c=>c.risk_score>=L&&c.risk_score<D_LINE).length;
    const ops=CASES.length*COST_AUTO+ref*COST_HUMAN;
    return {prem:prem,op:prem-cl-prem*SGA_RATE-ops,comb:prem?((cl+prem*SGA_RATE+ops)/prem*100):0};};
   const b=pnl(A_LINE),n2=pnl(v);
   return `Moving the approval line from <b>${A_LINE}</b> to <b>${v}</b>:<br>• Auto-approvals go from <b>${now}</b> to <b>${then}</b> (<b>${d>=0?'+':''}${d}</b> cases, ${(then/CASES.length*100).toFixed(0)}% straight-through), accepted cover about <b>${fmtBigMoney(newCov)}</b> against the ${fmtBigMoney(APPETITE_MONTHLY)} appetite.<br>• Approved premium <b>${fmtMoneyK(b.prem)} → ${fmtMoneyK(n2.prem)}</b>/yr.<br>• Expected operating income <b>${fmtMoneyK(b.op)} → ${n2.op>=0?'':'−'}${fmtMoneyK(Math.abs(n2.op))}</b>/yr, combined ratio <b>${b.comb.toFixed(0)}% → ${n2.comb.toFixed(0)}%</b>.<br>${d>0?`The trade is throughput for scrutiny: ${d} more case(s) clear with no human look, and the extra premium arrives with the extra mortality attached.`:`Tighter book: ${Math.abs(d)} case(s) that used to clear now need underwriter time, which costs $${COST_HUMAN} each but buys a look at the risk.`} The line is configuration, so this is a decision, not a model change.`;
  }
 }
 const worse=q.match(/claims?[^\d]{0,24}(\d{1,3})\s*%|(\d{1,3})\s*%[^.]{0,24}(worse|higher|more claims)/);
 if(worse&&/claim|loss|mortality/.test(q)){
  const pct=parseInt(worse[1]||worse[2],10);
  const appr=CASES.filter(c=>finalOf(c)==='approve');
  const prem=appr.reduce((s,c)=>s+(c.premium||0),0);
  const base=appr.reduce((s,c)=>s+expectedAnnualClaim(c),0);
  const refN=CASES.filter(c=>c.verdict==='yellow').length;
  const ops=CASES.length*COST_AUTO+refN*COST_HUMAN;
  const cl=base*(1+pct/100);
  const op=prem-cl-prem*SGA_RATE-ops;
  const comb=(cl+prem*SGA_RATE+ops)/prem*100;
  return `If claims run <b>${pct}% worse</b> than modelled (${fmtMoneyK(base)} → ${fmtMoneyK(cl)}/yr): operating income moves from <b>${fmtMoneyK(prem-base-prem*SGA_RATE-ops)}</b> to <b>${op>=0?'':'−'}${fmtMoneyK(Math.abs(op))}/yr</b>, and the combined ratio goes to <b>${comb.toFixed(0)}%</b> — ${comb<100?'still an underwriting profit':'an underwriting loss'}. The lever is the approval line, which is configuration.`;
 }
 return null;
}
function uwgBriefingAnswer(){
 // "anything I should worry about today?" — the shift briefing.
 const mine=CASES.filter(c=>c.verdict==='yellow'&&!wfGet(c.id).decision&&(CURRENT_ROLE!=='underwriter'||wfGet(c.id).assigneeUid===CURRENT_UID));
 const br=mine.filter(c=>ageHours(c)>=8).sort((a,b)=>ageHours(b)-ageHours(a));
 const conf=mine.filter(c=>(c.conflicts||[]).length);
 const big=mine.slice().sort((a,b)=>(b.coverage||0)-(a.coverage||0))[0];
 const appr=CASES.filter(c=>finalOf(c)==='approve');
 const pct=appr.reduce((s,c)=>s+(c.coverage||0),0)/APPETITE_MONTHLY*100;
 const L=[`<b>${mine.length}</b> case(s) open${CURRENT_ROLE==='underwriter'?' on your desk':''}.`];
 if(br.length)L.push(`⚠ <b>${br.length} past the 8-hour SLA</b> — oldest is <span class="mono">${br[0].id}</span> ${br[0].name} at ${fmtAge(ageHours(br[0]))}.`);
 else L.push(`✓ Nothing past the 8-hour SLA.`);
 if(conf.length)L.push(`⚠ <b>${conf.length} carrying document conflicts</b> — resolve those before scoring anything else: ${conf.slice(0,2).map(c=>`<span class="mono">${c.id}</span>`).join(', ')}.`);
 if(big)L.push(`Largest exposure waiting: <span class="mono">${big.id}</span> ${big.name}, ${fmt$(big.coverage)}.`);
 L.push(`Book is at <b>${pct.toFixed(0)}%</b> of the ${fmtBigMoney(APPETITE_MONTHLY)} monthly appetite.`);
 return L.join('<br>');
}
function uwgProfileAnswer(q){
 // A judgement question about a profile rather than a case: "is a 21-year-old
 // asking for $1M a red flag?" Answer with what the engine would actually do,
 // then ground it in comparable cases from the live book.
 const ageM=q.match(/(\d{2})\s*[-\s]?\s*(?:year|yr)s?\s*[-\s]?\s*old|\bage[d]?\s+(\d{2})\b/);
 const amtM=q.match(/\$\s*([\d.,]+)\s*(m|million|k|thousand)?|\b([\d.]+)\s*(m|million|k)\b/);
 if(!ageM||!amtM)return null;
 if(!/red flag|concern|worry|unusual|suspicious|normal|\bok\b|okay|fine\b|acceptable|problem|should i|would you|risky|reasonable/.test(q))return null;
 const age=parseInt(ageM[1]||ageM[2],10);
 let amt=parseFloat((amtM[1]||amtM[3]||'0').replace(/,/g,''));
 const u=(amtM[2]||amtM[4]||'').toLowerCase();
 if(u==='m'||u==='million')amt*=1e6;else if(u==='k'||u==='thousand')amt*=1000;
 if(!age||!amt||amt<1000)return null;
 const req=requirementsFor({age:age,coverage:amt});
 const peers=CASES.filter(c=>Math.abs((c.age||0)-age)<=6&&(c.coverage||0)>=amt*0.7);
 const ref=peers.filter(c=>c.verdict==='yellow').length,dec=peers.filter(c=>c.verdict==='red').length;
 const scores=peers.map(c=>c.risk_score).sort((a,b)=>a-b);
 const affordPeers=peers.filter(c=>c.afford&&c.afford.verdict!=='pass').length;
 const L=[];
 L.push(`<b>Not on age or amount alone.</b> Nothing in the decision logic declines a combination of age and face amount — age contributes points (younger is fewer, so a ${age}-year-old sits near the bottom of the mortality table) and the amount drives requirements, not the band.`);
 L.push(`What ${fmt$(amt)} at ${age} <i>does</i> trigger: ${req.length?`the age × amount grid requires <b>${req.join(', ')}</b>`:'no extra evidence under the grid'}, and the <b>affordability screen</b> — which is where this profile usually gets caught. ${fmt$(amt)} of cover implies an income multiple a ${age}-year-old rarely supports, and a failing screen refers the case to <b>financial underwriting</b> rather than declining it, because the fix is normally a smaller face amount.`);
 if(peers.length)L.push(`In this book, <b>${peers.length}</b> comparable applicant(s) (age ${age-6}–${age+6}, ${fmt$(amt*0.7)}+ of cover): scores run <b>${scores[0]}–${scores[scores.length-1]}</b>, ${ref} referred, ${dec} declined${affordPeers?`, and ${affordPeers} tripped the affordability screen`:''}.`);
 else L.push(`This book has no comparable applicant at that age and amount, so there is no precedent to read off.`);
 L.push(`The judgement a desk actually applies: <b>insurable interest</b> and <b>suitability</b> — why this amount, who benefits, is it replacing something — none of which the score can see. That is exactly the kind of case the middle band exists to put in front of a human.`);
 return L.join('<br>');
}
let UWG_FACTORS=null;
function uwgFactorTable(){
 // The real weight table, read off the book's own scored factors.
 if(UWG_FACTORS)return UWG_FACTORS;
 const m={};
 CASES.forEach(c=>(c.rule_factors||[]).forEach(f=>{
  if(!f||f[2]==null||f[2]<=0)return;
  const k=(f[0]+'|'+f[1]).toLowerCase();
  if(!m[k])m[k]={label:f[0],detail:String(f[1]),pts:f[2],n:0};
  m[k].n++;}));
 UWG_FACTORS=Object.values(m);
 return UWG_FACTORS;
}
function uwgFactorAnswer(q){
 // "how many points does heavy alcohol cost?", "does a criminal record matter?"
 if(/(lose|drop|shed|cut) .{0,16}points?|points? .{0,20}(lose|drop|shed)|from referred to approved|clear the line/.test(q))return null;  // that is line arithmetic, not a weight lookup
 if(!/\bpoints?\b|weigh|weight of|red flag|does .{0,20}matter|affect the score|hurt the score|count against|penal|worse than|more serious/.test(q))return null;
 const terms=q.replace(/[^a-z0-9\s]/g,' ').split(/\s+/).filter(w=>w.length>=3&&!UWG_STOP.has(w));
 if(!terms.length)return null;
 const scored=uwgFactorTable().map(f=>{
  const hay=(f.label+' '+f.detail).toLowerCase();
  let sc=0;terms.forEach(w=>{if(hay.indexOf(w)>=0)sc+=w.length;});
  return {f,sc};}).filter(x=>x.sc>=3).sort((a,b)=>b.sc-a.sc||b.f.pts-a.f.pts);
 if(!scored.length)return null;
 // an explicit comparison ("X vs Y", "more points than") gets a verdict
 if(/more .{0,14}than|less .{0,14}than|worse than|versus|\bvs\b|compared to|bigger than|heavier than|or a\b/.test(q)){
  const seen=new Set(),picks=[];
  scored.forEach(x=>{if(picks.length<2&&!seen.has(x.f.label+x.f.detail)){seen.add(x.f.label+x.f.detail);picks.push(x.f);}});
  if(picks.length===2){
   const [a,b]=picks;const hi=a.pts>=b.pts?a:b,lo=a.pts>=b.pts?b:a;
   return a.pts===b.pts
    ? `They carry the <b>same</b> weight: <b>${a.label} — ${a.detail}</b> and <b>${b.label} — ${b.detail}</b> are both <b>+${a.pts}</b> point(s). Both are mortality-anchored (<span class="mono">round(28 × ln(relative mortality))</span>), so equal points means the evidence puts them at the same relative mortality.`
    : `<b>${hi.label} — ${hi.detail}</b> costs more: <b>+${hi.pts}</b> point(s) against <b>+${lo.pts}</b> for <b>${lo.label} — ${lo.detail}</b> — a ${hi.pts-lo.pts}-point difference. Points are <span class="mono">round(28 × ln(relative mortality))</span>, so that gap is the mortality evidence, not a judgement about which is morally worse. Against the ${A_LINE}-point approval line, ${hi.pts} point(s) is ${(hi.pts/A_LINE*100).toFixed(0)}% of the way to a referral on its own.`;
  }
 }
 const top=scored.slice(0,4).map(x=>x.f);
 return `From the live weight table (points are <span class="mono">round(28 × ln(relative mortality))</span>, so they are mortality evidence, not opinion):<br>${top.map(f=>`<b>${f.label} — ${f.detail}</b>: <b>+${f.pts}</b> point(s), seen on ${f.n} case(s) in this book`).join('<br>')}<br>For scale, the approval line is <b>${A_LINE}</b> and the decline line <b>${D_LINE}</b> — so ${top[0].pts} point(s) is ${(top[0].pts/A_LINE*100).toFixed(0)}% of the way to a referral on its own. No single factor decides; they accumulate into the composite.`;
}
function uwgSharedAnswer(q){
 // "are any two applicants in the same city / with the same employer?"
 if(!/same (city|town|state|employer|company|name|surname)|any two|duplicate|\bshare\b.{0,14}(employer|city|address|name|surname|company|town)|more than one .{0,18}(in|from)/.test(q))return null;
 const key=/employer|company/.test(q)?['employer',c=>c.employer]
  :/state|region/.test(q)?['state',c=>c.state]
  :/surname|last name/.test(q)?['surname',c=>(c.name||'').split(' ').pop()]
  :/\bname\b/.test(q)?['full name',c=>c.name]
  :['city',c=>c.city];
 const g={};CASES.forEach(c=>{const k=key[1](c)||'—';if(/^(self.?employed|unemployed|retired|none|n\/a|—)$/i.test(String(k)))return;(g[k]=g[k]||[]).push(c);});
 const dups=Object.entries(g).filter(([,l])=>l.length>1).sort((a,b)=>b[1].length-a[1].length);
 if(!dups.length)return `No — every applicant has a distinct ${key[0]} in this book.`;
 return `Yes — <b>${dups.length}</b> ${key[0]}(s) appear more than once. Top overlaps:<br>${dups.slice(0,5).map(([k,l])=>`<b>${k}</b> — ${l.length} applicants (${l.slice(0,3).map(c=>`<span class="mono">${c.id}</span> ${c.name}`).join(', ')}${l.length>3?', …':''})`).join('<br>')}<br>Worth knowing why it matters: shared address, employer or surname is how a real desk spots <b>aggregation risk</b> (several policies on one life or household) and possible non-disclosure — neither of which the per-case score can see.`;
}
function uwgLineGapAnswer(q){
 // "how many points would a 45-year-old need to lose to move from referred to
 // approved" — arithmetic against the line, not a weight-table dump.
 if(!/points? .{0,32}(lose|shed|drop|cut|need)|need to (lose|drop|shed)|(move|go|get) from referred to approved|from referred to approved|clear the (approval )?line|get (under|below) the (approval )?line|to become auto.?approved/.test(q))return null;
 const explain=`A referred case auto-approves under <b>${A_LINE}</b>, so the points to lose are simply <b>score − ${A_LINE-1}</b>.`;
 const ageM=q.match(/(\d{2})\s*[-\s]?(?:year|yr)s?[-\s]?old|\bage[d]?\s+(\d{2})\b/);
 if(ageM){
  const age=parseInt(ageM[1]||ageM[2],10);
  const peers=CASES.filter(c=>c.verdict==='yellow'&&Math.abs((c.age||0)-age)<=2);
  const ageF=uwgFactorTable().find(f=>/applicant age/i.test(f.label)&&new RegExp('\\b'+age+' ').test(f.detail+' '));
  const rows=peers.slice(0,4).map(c=>`<span class="mono">${c.id}</span> ${c.name} (age ${c.age}) — score ${c.risk_score}, needs <b>${Math.max(1,c.risk_score-(A_LINE-1))}</b> point(s)`);
  return `${explain} It depends where the case sits in the ${A_LINE}–${D_LINE-1} band — anywhere from <b>1</b> to <b>${D_LINE-A_LINE}</b> point(s).${ageF?` Note the age factor itself: being ${age} contributes <b>+${ageF.pts}</b>, and that can’t be “lost”.`:''}${rows.length?`<br>Referred cases at ~${age} in this book:<br>${rows.join('<br>')}`:`<br>No referred case at ~${age} in this book right now.`}<br>Points come off by resolving what put them on: clearing a document conflict, evidence that removes a factor, or a corrected extraction — the score follows the facts.`;
 }
 if(uwgLastCase&&uwgLastCase.verdict==='yellow')
  return `${explain} <b>${uwgLastCase.name}</b> (<span class="mono">${uwgLastCase.id}</span>) scores <b>${uwgLastCase.risk_score}</b>, so it needs <b>${uwgLastCase.risk_score-(A_LINE-1)}</b> point(s) to clear the line.`;
 return `${explain} Referred cases sit ${A_LINE}–${D_LINE-1}, so between <b>1</b> and <b>${D_LINE-A_LINE}</b> point(s) depending on the case — give me a case ID, a name or an age and I’ll do the arithmetic.`;
}
function uwgOwnerAnswer(q){
 // "which underwriter is sitting on the most coverage?" — group the open queue
 // BY PERSON and sum, rather than listing cases.
 if(!/which (underwriter|uw\b|analyst|person|desk holder)|who ((is |'s )?(sitting on|holding|holds|has|carries|owns)) the most|busiest underwriter|most loaded/.test(q))return null;
 const met=uwgMetricOf(q)||uwgMetricOf('coverage');
 const open=CASES.filter(c=>c.verdict==='yellow'&&!wfGet(c.id).decision);
 const g={};open.forEach(c=>{const st=wfGet(c.id);const k=st.assignee||'Unassigned';
  (g[k]=g[k]||{n:0,v:0,tier:st.tier}).n++;g[k].v+=met.get(c);});
 const rows=Object.entries(g).sort((a,b)=>b[1].v-a[1].v);
 if(!rows.length)return 'The review queue is empty — no underwriter is holding open cases right now.';
 const fmtv=v=>met.label==='time in queue'?fmtAge(v):met.sum?fmt$(v):String(Math.round(v));
 const [name,top]=rows[0];
 return `<b>${name}</b>${top.tier?` (${(UWS[top.tier]||{}).label} desk)`:''} — <b>${fmtv(top.v)}</b> of ${met.label} across ${top.n} open case(s).<br>${rows.map(([n,x])=>`${n} — ${fmtv(x.v)} · ${x.n} case(s)`).join('<br>')}<br>Open referred cases only — decided and straight-through cases sit on no one’s desk.`;
}
function uwgAgreementAnswer(q){
 // "what fraction of referred cases agree with the model?" — computed from the
 // decisions actually recorded, never answered with model-card prose.
 if(!/agree(ing)? with the model|agreement rate|fraction .{0,48}agree|(what|how) (share|percent|fraction).{0,48}(agree|overr)|how often .{0,40}(agree|disagree|overr)|override rate|match the model|side with the model|end up agreeing|humans? (vs|versus) (the )?model/.test(q))return null;
 const dec=allDecisions();
 const leaned=dec.filter(d=>d.model==='APPROVE'||d.model==='DECLINE');
 const humanCall=dec.length-leaned.length;
 if(!dec.length)return `No human decisions are recorded in this browser yet, so there is nothing to measure — the agreement column starts filling the moment an underwriter decides a case (it is also a column in the decision-trail export and the pilot benchmark CSV). Pipeline-side, ${(M.decisioning.n_overrides_learned||0)} recorded override(s) have already been folded back into training.`;
 const agree=leaned.filter(d=>(d.model==='APPROVE'&&d.action==='APPROVED')||(d.model==='DECLINE'&&d.action==='DECLINED')).length;
 return `Of <b>${dec.length}</b> recorded decision(s): <b>${leaned.length}</b> had a model lean, and <b>${agree}</b> agreed — <b>${leaned.length?(agree/leaned.length*100).toFixed(0):0}%</b> agreement, ${leaned.length-agree} override(s).${humanCall?` The other ${humanCall} were mid-band referrals where the model deliberately takes no side — those are human calls by design, not agreements or disagreements.`:''} Every pair is in the decision trail with the model lean beside the human action.`;
}
function uwgAuditAnswer(q){
 // "show me every case the admin has amended" — read the records, not the rules.
 if(!/(show|list|which|what|every|any) .{0,30}(amend|overrid|overrode|reopen|changed decision)|amended cases|has (the )?(admin|manager|ops) (amended|overridden|changed)|amendments (made|recorded)/.test(q))return null;
 const wantOps=/admin|ops|operations/.test(q),wantMgr=/manager/.test(q);
 const wb=wfAll(),out=[];
 CASES.forEach(c=>{const st=wb[c.id];if(!st)return;
  if(st.decision&&(st.decision.opsAmendment||st.decision.managerOverride)){
   const kind=st.decision.opsAmendment?'OPS AMENDMENT':'MANAGER OVERRIDE';
   if((wantOps&&!st.decision.opsAmendment)||(wantMgr&&!st.decision.managerOverride))return;
   out.push(`<span class="mono">${c.id}</span> ${c.name} — <b>${kind}</b> → ${st.decision.action} by ${st.decision.by}, ${st.decision.at} (superseded ${st.decision.supersedes||'—'}) — “${st.decision.rationale}”`);}
  else if((st.history||[]).some(h=>/Reopened for review by (operations|manager)/.test(h.action))&&/reopen/.test(q)){
   const h=(st.history||[]).filter(h2=>/Reopened for review/.test(h2.action)).pop();
   out.push(`<span class="mono">${c.id}</span> ${c.name} — <b>REOPENED</b> by ${h.by}, ${h.at}`);}});
 if(!out.length)return `None yet — no ${wantOps?'ops amendments':wantMgr?'manager overrides':'amendments or overrides'} are recorded in this browser. When one happens it is logged with who acted, what it superseded and the written reason, and it will show up here and in the decision-trail export.`;
 return `<b>${out.length}</b> changed decision(s) on record:<br>${out.join('<br>')}`;
}
function uwgCounterfactualAnswer(c,q){
 // "if Farah Iyer quit smoking, would her case auto-approve?" — actually do the
 // arithmetic: remove the factor's points, reblend, compare to the line.
 if(!/\bif\b|would (it|she|he|they|her case|his case|the case)|without (the )?/.test(q))return null;
 if(!/quit|stopp?ed|gave up|no longer|without|dropped|lost|wasn.?t|weren.?t|didn.?t have|removed|cleared up/.test(q))return null;
 const MAP=[[/smok|tobacco|cigarette/, /tobacco|smok/i],[/alcohol|drink/, /alcohol/i],[/bmi|weight|obes/, /bmi|build|weight/i],
  [/diabet|condition|hypertens|illness/, /condition|diabet|hypertens/i],[/credit/, /credit/i],[/driv|violation/, /driving|violation/i],
  [/hazard|skydiv/, /hazard/i],[/bankrupt/, /bankrupt/i],[/debt|dti/, /debt/i]];
 let factRe=null;for(const [qre,fre] of MAP)if(qre.test(q)){factRe=fre;break;}
 if(!factRe){if(/\bage\b|younger|older/.test(q))return `Age is the one factor no applicant can change — I can model quitting smoking, clearing a condition, or improving credit, but not being younger.`;return null;}
 const hits=(c.rule_factors||[]).filter(f=>f[2]>0&&(factRe.test(String(f[0]))||factRe.test(String(f[1]))));
 const pts=hits.reduce((s2,f)=>s2+f[2],0);
 if(!pts)return `<b>${c.name}</b> (<span class="mono">${c.id}</span>): that factor isn’t costing any points — the rule engine scored it 0 on this case (score ${c.risk_score}: rule ${c.rule_score} / ML ${Math.round(c.ml_score)}), so removing it changes nothing.`;
 const newRule=Math.max(0,(c.rule_score||0)-pts);
 const newComp=Math.round((newRule+(c.ml_score||0))/2);
 const now=c.risk_score;
 const verdict=newComp<A_LINE?`clears the <b>${A_LINE}</b>-point line — it would <b>auto-approve</b>`:newComp<D_LINE?`still sits in the ${A_LINE}–${D_LINE-1} band — <b>still referred</b>, ${newComp-(A_LINE-1)} point(s) short`:`still at or above the ${D_LINE} decline line`;
 return `<b>${c.name}</b> (<span class="mono">${c.id}</span>): ${hits.map(f=>`${f[0]} (${f[1]}) is <b>+${f[2]}</b>`).join(', ')}. Remove ${pts} point(s) and the rule half goes ${c.rule_score} → <b>${newRule}</b>, blending to a composite of about <b>${newComp}</b> (from ${now}) — which ${verdict}. One honest caveat: the ML half also learned from this factor, so the true new score would likely be a little lower still — this estimate is conservative. And the change must be evidenced (a clean cotinine on retest), not just declared.`;
}
function uwgQueueAnswer(){
 // "Who should I review first?" — the queue’s own priority order, live.
 const pend=CASES.filter(c=>c.verdict==='yellow'&&!wfGet(c.id).decision);
 let mine=pend,scopeNote='';
 if(CURRENT_ROLE==='underwriter'){const m=pend.filter(c=>wfGet(c.id).assigneeUid===CURRENT_UID);if(m.length){mine=m;scopeNote=' in your queue';}}
 if(!mine.length)return 'The review queue is empty — nothing is waiting on a human right now.';
 const l=mine.slice().sort((a,b)=>priorityScore(b)-priorityScore(a)).slice(0,5);
 return `<b>Work top-down${scopeNote}</b> — ranked by coverage + time-in-queue (never by risk score):<br>${l.map((c,i)=>{const h=ageHours(c);return `${i+1}. <span class="mono">${c.id}</span> ${c.name} — ${fmt$(c.coverage)}, ${fmtAge(h)} in queue${h>=8?' · <b style="color:var(--bad)">SLA BREACH</b>':''}, priority ${priorityScore(c)}/100`;}).join('<br>')}${mine.length>5?`<br>(${mine.length-5} more behind them.)`:''}`;
}
function uwgFieldAnswer(c,q){
 // A specific field of a specific applicant — answer just that, from the packet.
 const e=c.extraction||{};
 const st=wfGet(c.id);
 const F=[
  [/case id|which id|the id\b/, ()=>`case ID <b><span class="mono">${c.id}</span></b>`],
  [/why (is|are|was|were) (it|this|that|he|she|they)? ?so (high|low|risky)|why so (high|low)|what.s driving it|why such a/, ()=>{
    const f=(c.rule_factors||[]).filter(x=>x[2]>0).sort((a,b)=>b[2]-a[2]).slice(0,4);
    return `score <b>${c.risk_score}</b> because — ${f.length?f.map(x=>`${x[0]} ${x[1]} <b>+${x[2]}</b>`).join(', '):'no rule factors fired; the ML half carries it'}${(c.conflicts||[]).length?`, plus ${c.conflicts.length} document conflict(s)`:''}`;}],
  [/who decided|who approved|who declined|decided by|who signed|who made the (call|decision)|has anyone decided|been decided/, ()=>{
    if(st.decision)return `decided <b>${st.decision.action}</b> by ${st.decision.by} (${st.decision.role}) at ${st.decision.at} — “${st.decision.rationale}”${st.decision.managerOverride?' [manager override]':''}${st.decision.opsAmendment?' [ops amendment]':''}`;
    if(c.verdict==='yellow')return `<b>not decided yet</b> — open with ${st.assignee||'no one'}${st.tier?` (${(UWS[st.tier]||{}).label} desk)`:''}, ${fmtAge(ageHours(c))} in queue`;
    return `no human decision on record — the system decided <b>${c.decision}</b> straight-through`;}],
  [/what would it take|how (could|do) (i|we) approve|to get (it|this) approved|path to approval|make it approvable/, ()=>{
    const gap=c.risk_score-(A_LINE-1);
    const out=reqOutstandingList(c);
    const bits=[];
    if(c.risk_score>=A_LINE)bits.push(`the score needs to fall <b>${gap} point(s)</b> to clear the ${A_LINE}-point line`);
    if((c.conflicts||[]).length)bits.push(`resolve ${c.conflicts.length} document conflict(s) (${c.conflicts.map(k=>k.type.replace(/_/g,' ')).join(', ')})`);
    if(out.length)bits.push(`complete outstanding evidence: <b>${out.join(', ')}</b>`);
    if(c.afford&&c.afford.verdict!=='pass')bits.push(`clear affordability (currently ${c.afford.label}) — usually by reducing the face amount`);
    if(c.unique)bits.push('a whole-person judgement on the disclosed circumstances');
    return bits.length?`to approve: ${bits.join('; ')}. Nothing here is automatic — an underwriter can approve it now with a written rationale, since the score advises rather than decides`:`nothing is blocking it — you can approve now with a rationale`;}],
  [/reopen|can i change (it|this)|amend it|undo (it|this)|take it back/, ()=>{
    if(!st.decision)return `nothing to reopen — no decision is recorded yet`;
    const who=CURRENT_ROLE==='manager'?'You can reopen or override it directly':CURRENT_ROLE==='admin'?'You can reopen it or amend the decision (logged as OPS AMENDMENT)':st.decision.by===CURRENT_USER?'You recorded it, so you can reopen it from the case desk':'Only a manager (or operations, to correct an error) can change another underwriter’s recorded decision';
    return `it is recorded as <b>${st.decision.action}</b> by ${st.decision.by}. ${who} — every change needs a written reason and keeps what it superseded`;}],
  // "does it match across the documents?" — run the whole 6-check screen out loud
  // Consistency verdict is concise: one line when clean, and only the failing
  // rows (with both values) when not. The third element claims the "all docs"
  // words so the document-list intent doesn't fire on the same breath.
  [/match(es|ed|ing)? across|consistent|consistency|same across|agree|tally|cross.?document|(all|the) (documents|docs)( submitted| agree| match)?|line up|verif/, ()=>{
    const k=c.conflicts||[];
    if(!k.length)return `yes — all six cross-document checks pass: DOB, income (form vs payslip, tax slip, bank deposits), debt vs bureau, and tobacco vs the cotinine lab all agree`;
    return `<b>${k.length} of the 6 cross-document checks fail</b>:<br>${k.map(x=>{const d=conflictDetail(c,x);
      return d?`⚠ ${d.field}: ${d.a[0]} <b>${d.a[1]??'—'}</b> vs ${d.b[0]} <b>${d.b[1]??'—'}</b> (${x.severity})`:`⚠ ${x.type.replace(/_/g,' ')} (${x.severity})`;}).join('<br>')}`;},
   /(all |the )?(docs|documents|paperwork|packet)( submitted)?/g],
  // "what is your AI recommendation for X" — spelling-tolerant on recommendation
  [/rec+o?m+|suggest|next step|advi[cs]e|what should i do|your take|your call/, ()=>{
    const r=caseRecommendation(c);
    return `the recommendation is <b>${r[0]}</b> — ${r[1]}. System call ${c.decision} at score ${c.risk_score} (${c.rate_class})${c.verdict==='yellow'?'. The call is yours; this is a suggested next step, not a decision':''}`;}],
  [/how long|in (the )?queue|waiting|queue time|\bsla\b/, ()=>{
    if(c.verdict!=='yellow')return `decided <b>straight-through, instantly</b> — no queue time (${c.decision.toLowerCase()})`;
    const h=ageHours(c);return `in the review queue for <b>${fmtAge(h)}</b>${h>=8?' — <b>over the 8-hour SLA</b>, flagged for chase':h>=6?' — inside SLA but past the 6-hour warning line':' — well inside the 8-hour SLA'}`;}],
  [/document|packet|paperwork|\bfile\b|\bdocs\b/, ()=>{
    const out=reqOutstandingList(c);
    return `the packet holds <b>5 parsed documents</b> — application form, payslip, paramedical exam, bank statement, tax slip${c.has_docs?' (PDF originals attached)':''}${out.length?`. Still outstanding by the age × amount grid: <b>${out.join(', ')}</b>`:'. No further evidence outstanding'}`;}],
  [/weight|height|bmi/, ()=>`height ${c.height} cm, weight <b>${c.weight} kg</b> (BMI ${c.bmi}), from the paramedical exam`],
  [/\bage\b|date of birth|\bdob\b|born/, ()=>`born ${c.dob} — age <b>${c.age}</b>`],
  // specific-before-generic: "debt to income" must not fall into plain income,
  // and "what is driving the score" must not fall into driving violations
  [/debt.to.income|\bdti\b/, ()=>`debt-to-income ratio <b>${c.dti!=null?(c.dti*100).toFixed(0)+'%':'—'}</b> — ${fmt$(c.debt)} of debt against ${fmt$(c.income)} of income`],
  [/\bdrivers?\b|factor|breakdown|driving .*score|score .*driv|why.* (high|low) score/, ()=>{
    const f=(c.rule_factors||[]).filter(x=>x[2]>0).sort((a,b)=>b[2]-a[2]).slice(0,4);
    return f.length?`top rule-engine drivers — ${f.map(x=>`${x[0]} (${x[1]}) <b>+${x[2]}</b>`).join(', ')}`:`no rule-engine risk factors fired — a clean file`;}],
  [/income|salary|earn/, ()=>`annual income <b>${fmt$(c.income)}</b> (${c.occupation||'—'}${c.employer?', '+c.employer:''})`],
  [/coverage|cover\b|face amount|sum assured/, ()=>`requesting <b>${fmt$(c.coverage)}</b> of cover — ${c.policy}`],
  [/premium/, ()=>`annual premium <b>${fmt$(c.premium)}</b> on ${fmt$(c.coverage)} of ${c.policy}`],
  // credit before the generic score matcher — "credit score" is its own field
  [/credit/, ()=>`credit score <b>${c.credit!=null?c.credit:'—'}</b>${c.credit!=null?` (${c.credit>=740?'excellent':c.credit>=670?'good':c.credit>=580?'fair':'poor'})`:''}`],
  [/debt.to.income|\bdti\b/, ()=>`debt-to-income ratio <b>${c.dti!=null?(c.dti*100).toFixed(0)+'%':'—'}</b> — ${fmt$(c.debt)} of debt against ${fmt$(c.income)} of income`],
  [/\bdebt\b|owe|liabilit/, ()=>`existing debt <b>${fmt$(c.debt)}</b> (DTI ${c.dti!=null?(c.dti*100).toFixed(0)+'%':'—'})`],
  [/net worth|assets/, ()=>`net worth <b>${fmt$(c.net_worth)}</b>`],
  [/bank|savings|balance|deposit/, ()=>`average bank balance <b>${fmt$(c.bank)}</b>${(c.extraction||{}).bank_deposit_monthly?`, monthly deposits ${fmt$(c.extraction.bank_deposit_monthly)}`:''}`],
  [/expense|outflow|spending/, ()=>`monthly outflows <b>${fmt$(c.expenses)}</b>`],
  [/family history|famil/, ()=>`family history <b>${c.family?'disclosed':'none disclosed'}</b>`],
  [/driving|violation|\bmvr\b|traffic/, ()=>`<b>${c.violations||0}</b> driving violation(s) in the last three years${(c.decl||{}).dangerous_driving?' · dangerous driving declared in the last five years':''}`],
  [/alcohol|drink/, ()=>`alcohol use <b>${c.alcohol||'None'}</b>`],
  [/hazard|dangerous activit|hobb|sport|skydiv|div(ing|e)\b/, ()=>`hazardous activities: <b>${c.hazard&&c.hazard!=='None'?c.hazard:'none declared'}</b>`],
  [/unique|circumstance|disclos|section 6|declaration/, ()=>{
    const d=c.decl||{};const yes=[['prior_decline','a prior application declined'],['dangerous_driving','dangerous driving'],['drug_counselling','drug or alcohol counselling'],['criminal','a criminal offence'],['bankruptcy','bankruptcy'],['foreign_travel','foreign travel planned'],['weight_change','a weight change over 10 lb']].filter(([k])=>d[k]).map(([,l])=>l);
    return `${c.unique?`unique circumstances: <b>${c.unique}</b>. `:''}${yes.length?`Section 6 answered YES to: <b>${yes.join(', ')}</b>`:(c.unique?'No Section 6 declarations':'nothing disclosed — no unique circumstances, no Section 6 declarations')}`;}],
  [/in line with|proportion|multiple of income|relative to .{0,12}income|sensible|reasonable|justif|too much cover|over.?insured|support that much/, ()=>{
    const mult=c.income?(c.coverage||0)/c.income:0;const pp=c.income?(c.premium||0)/c.income*100:0;
    return `${fmt$(c.coverage)} of cover on ${fmt$(c.income)} of income is a <b>${mult.toFixed(1)}× income multiple</b>, with the premium at <b>${pp.toFixed(1)}%</b> of income — affordability screen says <b>${((c.afford||{}).label)||'—'}</b>${(c.afford||{}).verdict!=='pass'?', so it refers to financial underwriting rather than declining':''}`;}],
  [/afford|financially justif/, ()=>`affordability <b>${((c.afford||{}).label)||'—'}</b>${(c.afford||{}).verdict==='fail'?' — referred to financial underwriting':''}`],
  [/conflict|flag|mismatch|discrepan/, ()=>{const k=c.conflicts||[];
    return k.length?`<b>${k.length}</b> conflict(s): ${k.map(x=>x.type.replace(/_/g,' ')+' ('+x.severity+')').join(', ')}`:`<b>no document conflicts</b> — the packet is internally consistent`;}],
  [/driver|factor|what.s driving|why.* (high|low) score|breakdown/, ()=>{
    const f=(c.rule_factors||[]).filter(x=>x[2]>0).sort((a,b)=>b[2]-a[2]).slice(0,4);
    return f.length?`top rule-engine drivers — ${f.map(x=>`${x[0]} (${x[1]}) <b>+${x[2]}</b>`).join(', ')}`:`no rule-engine risk factors fired — a clean file`;}],
  [/assign|underwriter|desk|who owns|who has/, ()=>{
    if(c.verdict!=='yellow')return `not assigned to a desk — decided straight-through (${c.decision.toLowerCase()})`;
    return `assigned to <b>${st.assignee||'unassigned'}</b>${st.tier?` (${(UWS[st.tier]||{}).label} desk)`:''}, status ${WF_LABEL[st.status]||st.status}`;}],
  [/rate class|rating|which class/, ()=>`rate class <b>${c.rate_class}</b>`],
  [/polic(y|ies)|product|term|whole life/, ()=>`<b>${c.policy}</b> — ${fmt$(c.coverage)} of cover at ${fmt$(c.premium)}/yr`],
  [/where do(es)?.*(live|reside|based)|which city|what city|\bcity\b|home address|lives? in/, ()=>`based in <b>${c.city||'—'}${c.state?', '+c.state:''}</b>`],
  [/sex|gender|male|female/, ()=>`<b>${c.sex==='M'?'Male':'Female'}</b>, age ${c.age}`],
  [/existing (cover|polic)|already (has|have)|replac/, ()=>`existing cover in force <b>${fmt$(c.existing_cov||0)}</b>${c.replacing?' — this application <b>replaces</b> an existing policy':''}`],
  [/years employ|how long.*(work|employ)|tenure/, ()=>`<b>${c.years_emp!=null?c.years_emp+' years':'—'}</b> with ${c.employer||'the current employer'} (${c.emp_status||'—'})`],
  [/score|risk\b/, ()=>`composite risk score <b>${c.risk_score}</b> (rule ${c.rule_score} / ML ${Math.round(c.ml_score)}) — ${c.decision}`],
  [/smok|tobacco|cotinine/, ()=>`declared <b>${c.smoker}</b>${e.cotinine?`, cotinine lab ${e.cotinine}`:''}`],
  [/blood pressure|\bbp\b/, ()=>`blood pressure <b>${c.bp}</b>`],
  [/cholesterol|chol\b/, ()=>`total cholesterol <b>${c.chol} mg/dL</b>`],
  [/condition|medical|health|diagnos/, ()=>`declared conditions: <b>${c.conditions||'None'}</b>`],
  [/occupation|job|employ/, ()=>`<b>${c.occupation||'—'}</b>${c.employer?` at ${c.employer}`:''}${c.emp_status?` (${c.emp_status})`:''}`],
  // "the decision" must not swallow "the decision bands" (a rulebook question)
  [/verdict|outcome|final decision|decision (on|for|is)\b|(his|her|their|this) decision|the decision(?! ?band)|approved or declined/, ()=>`<b>${c.decision}</b> — ${c.rate_class}`]];
 // A question can carry several asks at once ("age and DOB, and does it match
 // across the documents?"). Resolve EVERY intent present, most specific first,
 // consuming the words each one claims so a generic pattern cannot re-answer
 // ground a precise one already covered.
 // Consume most-specific first so a broad pattern can't steal a precise ask,
 // but ANSWER in the order the user asked — "age and dob and does it match"
 // leads with the age, not with whichever pattern happens to be longest.
 const scored=F.map(f=>{const m=q.match(f[0]);return {f,len:m?m[0].length:0};})
   .filter(x=>x.len>0).sort((a,b)=>b.len-a.len);
 let rem=q,hits=[];
 scored.forEach(s=>{
  const m=rem.match(s.f[0]);if(!m)return;                 // a longer intent already took these words
  rem=rem.replace(s.f[0],' '.repeat(m[0].length));
  if(s.f[2])rem=rem.replace(s.f[2],x=>' '.repeat(x.length));   // words this answer subsumes
  hits.push({pos:m.index,text:s.f[1]()});});
 hits.sort((a,b)=>a.pos-b.pos);
 hits=hits.slice(0,5);   // consume longest-first, but keep the asks the user made first
 if(hits.length===1)return `<b>${c.name}</b> (<span class="mono">${c.id}</span>): ${hits[0].text}.`;
 if(hits.length>1)return `<b>${c.name}</b> (<span class="mono">${c.id}</span>):<br>${hits.map(h=>'• '+h.text).join('<br>')}`;
 return null;
}
/* Applicant matching is typo-tolerant: people type “almedia” for “Almeida”
   and half a name far more often than a clean full match. Tokens are scored
   exact / near-miss (edit distance 1–2), and a tie asks rather than guesses. */
const UWG_STOP=new Set(['is','of','to','me','my','it','do','on','in','at','by','we','us','an','or','if','so','no','be','as','am','he','its','any','all','has','was','you','your','a','i','what','whats','which','the','and','for','with','about','tell','show','give','how','why','who','whom','does','did','his','her','hers','their','they','them','this','that','been','has','have','was','were','are','file','files','case','cases','document','documents','docs','packet','queue','score','weight','height','income','premium','coverage','decision','status','long','much','many','from','into','right','now','our','your','ours','yours','review','reviewed','need','needs','there','then','also','please','info','information']);
function uwgKeyHit(q,k){
 const qn=q.replace(/['’]/g,'');   // "can't" and "cant" are the same question
 if(k.indexOf(' ')>=0)return qn.indexOf(k)>=0;
 return new RegExp('\\b'+k.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).test(qn);
}
function uwgLev(a,b){
 // Damerau (OSA): a swapped pair — "asiha" for "aisha" — is ONE error, the
 // single most common typo shape in a hand-typed name.
 const m=a.length,n=b.length;if(Math.abs(m-n)>2)return 9;
 let prev2=null,prev=Array.from({length:n+1},(_,i)=>i),cur=new Array(n+1);
 for(let i=1;i<=m;i++){cur[0]=i;
  for(let j=1;j<=n;j++){
   cur[j]=Math.min(prev[j]+1,cur[j-1]+1,prev[j-1]+(a[i-1]===b[j-1]?0:1));
   if(prev2&&i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])cur[j]=Math.min(cur[j],prev2[j-2]+1);
  }
  prev2=prev.slice();const t=prev;prev=cur;cur=t;}
 return prev[n];
}
function uwgTokenScore(nameTok,qTok){
 if(nameTok===qTok)return 3;                       // exact
 if(nameTok.length<4||qTok.length<4)return 0;      // short tokens are too collision-prone
 const d=uwgLev(nameTok,qTok);
 if(d===1)return 2.5;                              // one typo
 if(d===2&&nameTok.length>=6)return 1.5;           // transposition in a long surname
 return 0;
}
function uwgNameMatches(q){
 const qTok=q.replace(/[^a-z\s]/g,' ').split(/\s+/).filter(t=>t.length>=2&&!UWG_STOP.has(t));
 if(!qTok.length)return {list:[],score:0,allScored:[]};
 let best=0,scored=[];
 CASES.forEach(c=>{
  let s=0,top=0;const toks=new Set();
  c.name.toLowerCase().split(/\s+/).forEach(nt=>{
   let b=0,bq=null;qTok.forEach(qt=>{const v=uwgTokenScore(nt,qt);if(v>b){b=v;bq=qt;}});
   s+=b;if(b>0)toks.add(bq);if(b>top)top=b;});
  // credible only on an exact/near-exact token, or a long surname near-miss
  if(top>=2.5||(top>=1.5&&s>=1.5)){scored.push([c,s,toks]);if(s>best)best=s;}});
 scored.sort((a,b)=>b[1]-a[1]);
 // allScored keeps every credible match with the query tokens it consumed —
 // a two-person question resolves each person from here, not just the best tie
 return {list:scored.filter(x=>x[1]===best).map(x=>x[0]),score:best,allScored:scored};
}
function uwgFindByName(q){const m=uwgNameMatches(q);return m.list.length===1?m.list[0]:null;}
function uwgAmbiguous(list){
 const shown=list.slice(0,5);
 return `${list.length} applicants share that name — which one?<br>${shown.map(c=>`<span class="mono">${c.id}</span> ${c.name} — ${fmt$(c.coverage)}, ${c.decision.toLowerCase()}`).join('<br>')}${list.length>shown.length?`<br>…and ${list.length-shown.length} more.`:''}<br>Reply with just the number (“${shown[0].id.slice(4)}”), a full name, or “the first one” — I’ll pick up your original question from there.`;
}
function uwgCompareAnswer(list){
 // Two or three applicants side by side — the underwriter's actual comparison
 // fields, one row each, no prose.
 const l=list.slice(0,3);
 uwgLastCase=l[0];
 const row=(label,fn)=>`<b>${label}</b> — ${l.map(c=>fn(c)).join(' · ')}`;
 return `<b>${l.map(c=>`${c.name} (<span class="mono">${c.id}</span>)`).join(' vs ')}</b><br>${[
  row('Age',c=>c.age),
  row('Cover',c=>`${fmt$(c.coverage)} ${c.policy}`),
  row('Premium',c=>fmt$(c.premium)+'/yr'),
  row('Income',c=>fmt$(c.income)),
  row('Risk',c=>`${c.risk_score} (rule ${c.rule_score} / ML ${Math.round(c.ml_score)})`),
  row('Decision',c=>c.decision),
  row('Conflicts',c=>(c.conflicts||[]).length?(c.conflicts||[]).map(x=>x.type.replace(/_/g,' ')).join(', '):'none'),
  row('Affordability',c=>((c.afford||{}).label)||'—'),
  row('Why',c=>(c.reasons&&c.reasons[0])||'clean file — no flags'),
  row('Next step',c=>caseRecommendation(c)[0])
 ].join('<br>')}`;
}
function uwgCaseAnswer(c){
 const st=wfGet(c.id);
 const conf=(c.conflicts||[]).map(k=>`${k.type.replace(/_/g,' ')} (${k.severity})`).join(', ');
 const rec=caseRecommendation(c);
 const why=(c.reasons||[]).slice(0,3).join(' · ');
 const lines=[`<b>${c.id}</b> — ${c.name}, ${c.age}, ${c.policy}, ${fmt$(c.coverage)} of cover.`,
  `System call: <b>${c.decision}</b> (score ${c.risk_score}: rule ${c.rule_score} / ML ${Math.round(c.ml_score)}) — ${c.rate_class}.`];
 if(why)lines.push(`Drivers: ${why}.`);
 if(conf)lines.push(`Conflicts: ${conf}.`);
 if(c.afford&&c.afford.verdict)lines.push(`Affordability: <b>${c.afford.verdict.toUpperCase()}</b>.`);
 if(c.verdict==='yellow')lines.push(`Routed to the <b>${(UWS[st.tier]||{}).label||'review'}</b> desk${st.assignee?` (${st.assignee})`:''}. Suggested next step: <b>${rec[0]}</b> — ${rec[1]}.`);
 if(st.decision)lines.push(`Human decision on record: <b>${st.decision.action}</b> by ${st.decision.by}, ${st.decision.at}.`);
 return lines.join('<br>');
}
let uwgBooted=false,uwgLastCase=null;   // last case discussed — resolves pronoun follow-ups
let uwgPending=null;                    // an unanswered "which one?" ask: {list, q}
function uwgToggle(){
 const p=document.getElementById('uwgPanel');const on=!p.classList.contains('on');
 p.classList.toggle('on',on);
 if(on&&!uwgBooted){uwgBooted=true;
  uwgMsg('Hi — I’m the <b>UW Guide</b>. Ask me about underwriting guidelines, product rules, risk-scoring, or process. I can also look up any applicant by name or case ID (“what is '+CASES[0].name+'’s weight?”) and rank the auto-approved or auto-declined book.','bot');}
 if(on){uwgChipsRender();const i=document.getElementById('uwgIn');if(i)i.focus();}
}
function uwgMsg(html,who){
 const m=document.getElementById('uwgMsgs');const d=document.createElement('div');
 d.className='uwg-m '+who;d.innerHTML=html;m.appendChild(d);m.scrollTop=m.scrollHeight;
}
function uwgChipsRender(){
 const chips=(view==='case'&&activeId)?['Why is this case here?','What evidence does it need?','Who can change a decision?']
  :['What are the decision bands?','Rank the auto-approved candidates','Rank the auto-declined cases','Who can change a decision?'];
 document.getElementById('uwgChips').innerHTML=chips.map(c=>`<button class="uwg-chip" onclick="uwgAsk('${c.replace(/'/g,'&#39;')}')">${c}</button>`).join('');
}
function uwgAsk(q){const i=document.getElementById('uwgIn');if(i)i.value=q;uwgSend();}
function uwgSend(){
 const i=document.getElementById('uwgIn');const q=(i.value||'').trim();if(!q)return;
 i.value='';uwgMsg(q.replace(/</g,'&lt;'),'me');
 setTimeout(()=>{uwgMsg(uwgAnswer(q),'bot');uwgChipsRender();},220);
}
let uwgHistory=[],uwgLastAnswer='';
function uwgAnswer(qRaw){
 const prevQ=uwgHistory.length?uwgHistory[uwgHistory.length-1]:null,prevA=uwgLastAnswer;
 const a=uwgAnswerCore(qRaw,prevQ,prevA);
 uwgHistory.push(qRaw);uwgLastAnswer=a;
 return a;
}
function uwgKbBest(q){
 let best=null,bestN=0;
 UWG_KB.forEach(e=>{let n=0;e.k.forEach(k=>{if(uwgKeyHit(q,k))n+=k.indexOf(' ')>=0?k.length+4:k.length;});if(n>bestN){bestN=n;best=e;}});
 return {entry:best,score:bestN};
}
function uwgWithFollowOn(ans,q){
 // "who owns the riskiest case AND can I hand it to someone else" — two asks
 // aimed at two different subsystems; answer both rather than dropping one.
 if(!/\band\b|also|plus|as well/.test(q))return ans;
 const kb=uwgKbBest(q);
 if(kb.entry&&kb.score>=14)return ans+'<br><br>'+kb.entry.a();
 return ans;
}
function uwgAnswerCore(qRaw,prevQ,prevA){
 const q=qRaw.toLowerCase();
 // When the last turn asked "which one?", this turn's job is to finish the
 // ORIGINAL question — so the chosen case is answered with the intent the
 // user started with, not dumped as a generic case read.
 const pending=uwgPending;uwgPending=null;
 const withIntent=(c)=>{uwgLastCase=c;
  return uwgCounterfactualAnswer(c,q)||uwgFieldAnswer(c,q)||(pending?uwgFieldAnswer(c,pending.q):null)||uwgCaseAnswer(c);};
 const idm=qRaw.toUpperCase().match(/APP-\d+/);
 if(idm){const c=CASES.find(x=>x.id===idm[0]);
  if(!c)return `I can’t find <span class="mono">${idm[0]}</span> in the current book.`;
  return withIntent(c);}
 // a bare case number — "1049" — is how people answer a disambiguation ask
 const bare=q.match(/\b(\d{3,4})\b/);
 if(bare){const c=CASES.find(x=>x.id==='APP-'+bare[1]);if(c)return withIntent(c);}
 // or they pick from the shortlist by ordinal, name, or decision word —
 // and "both" / "all of them" means compare the shortlist, not pick one
 if(pending){
  if(/\bboth\b|all of them|the two|all \d|compare/.test(q))return uwgCompareAnswer(pending.list);
  let c=null;
  [['first',0],['1st',0],['second',1],['2nd',1],['third',2],['3rd',2],['fourth',3],['4th',3],['last',pending.list.length-1]]
   .some(([w,i])=>{if(new RegExp('\\b'+w+'\\b').test(q)&&pending.list[i]){c=pending.list[i];return true;}return false;});
  if(!c){const m=pending.list.filter(x=>x.name.toLowerCase().split(/\s+/).some(t=>t.length>=3&&q.includes(t)));if(m.length===1)c=m[0];}
  if(!c){const m=pending.list.filter(x=>q.includes(x.decision.toLowerCase())||q.includes(x.verdict));if(m.length===1)c=m[0];}
  if(c)return withIntent(c);
  uwgPending=pending;   // not an answer to the ask — keep it alive one more turn
 }
 // conversational repair first — these are about the conversation, not the book
 if(/what did i (just )?ask|my last question|what was my question|repeat my question|what have i asked/.test(q))
  return prevQ?`You asked: “${prevQ.replace(/</g,'&lt;')}”${uwgHistory.length>1?` (before that: “${uwgHistory[uwgHistory.length-2].replace(/</g,'&lt;')}”)`:''}`
   :`Nothing yet — this is your first question.`;
 if(/short version|shorter|tl;?dr|in one line|one sentence|briefly|too long|summar(ise|ize) (that|it)|condense/.test(q)){
  if(!prevA)return `Ask me something first and I will give you the short version of it.`;
  const flat=prevA.replace(/<br>/g,' ').replace(/<[^>]+>/g,'').trim();
  const first=(flat.match(/^[^.!?]{10,220}[.!?]/)||[flat.slice(0,200)])[0];
  return `Short version: ${first}`;
 }
 if(/doesn.?t sound right|does not sound right|are you sure|you sure\?|that.?s wrong|thats wrong|check it|double.?check|verify that|prove it|says who/.test(q)){
  const src=uwgLastCase?`For ${uwgLastCase.name} (<span class="mono">${uwgLastCase.id}</span>), open the case file — the Extraction, Risk Score and Decision tabs show the same values I quoted.`:'';
  return `Fair — check me rather than trust me. Every figure I give is computed live from this book at the moment you ask: case answers read the same fields the case file shows, portfolio numbers use the same computation as the Executive Overview, and rule points come from the published weight table. ${src} If a number still looks wrong, tell me which one and I will show you the arithmetic behind it. Two standing caveats: the book is <b>synthetic</b>, and the P&L rests on named illustrative assumptions rather than carrier actuals.`;
 }
 // scenarios, judgement calls, group-bys and the shift briefing before case lookups
 const wi=uwgWhatIfAnswer(q);if(wi)return wi;
 const pr=uwgProfileAnswer(q);if(pr)return uwgWithFollowOn(pr,q);
 const sh=uwgSharedAnswer(q);if(sh)return sh;
 const own=uwgOwnerAnswer(q);if(own)return own;
 const agr=uwgAgreementAnswer(q);if(agr)return agr;
 const aud=uwgAuditAnswer(q);if(aud)return aud;
 const lg=uwgLineGapAnswer(q);if(lg)return lg;
 const fa=uwgFactorAnswer(q);if(fa)return fa;
 if(/worry about|anything i should know|brief me|briefing|summar(y|ise|ize) my (day|shift|queue)|how is my day|what.s on my plate/.test(q))return uwgBriefingAnswer();
 const grp=uwgGroupAnswer(q);if(grp)return uwgWithFollowOn(grp,q);
 // book-level analytics before anything case-specific: "how many…", "which
 // case has the highest…", "what is the average…", "is there any case with…"
 const agg=uwgAggregateAnswer(q);
 if(agg)return uwgWithFollowOn(agg,q);
 // "who should I review first?" — the live queue order
 if(/review first|first in (the )?queue|(start|begin) with|next case|prioriti[sz]|what should i (review|work|do)|who should i/.test(q))
  return uwgQueueAnswer();
 // "tell me about specific cases" — show what a case lookup can do, with real examples
 if(/specific case|about (a |the |some )?cases|which cases|examples? of (a )?case|show me (a|some) case/.test(q)){
  const ex=CASES.filter(c=>c.verdict==='yellow').slice(0,3);
  return `Absolutely — ask by case ID or applicant name: ${ex.map(c=>`<span class="mono">${c.id}</span> (${c.name})`).join(', ')}… I can read a case’s full story (“why is ${ex[0].name} referred?”), one field (“what is ${ex[0].name}’s weight?”), its documents (“what documents are in ${ex[0].name}’s file?”), or its queue time (“how long has ${ex[0].name} been in queue?”).`;}
 // ranked reads of the auto-decisioned book
 const wantsRank=/rank|top |best|worst|order|ideal|first/.test(q);
 const hitAppr=/auto[- ]?approv|approved (case|list|book|ones)|accept/.test(q);
 const hitDecl=/auto[- ]?declin|declined (case|list|book|ones)|reject/.test(q);
 if(wantsRank&&(hitAppr||hitDecl)){
  const parts=[];if(hitAppr)parts.push(uwgRankAnswer('approve'));if(hitDecl)parts.push(uwgRankAnswer('decline'));
  return parts.join('<br><br>');}
 // applicant by name — field question or full case read. A confident name match
 // wins outright; a fuzzy one waits behind the metric resolver so “loss ratio”
 // can never be mistaken for a surname.
 const nm=uwgNameMatches(q);
 // naming two people (or asking to compare) is a comparison, not an ambiguity.
 // One case per PERSON mentioned: walk credible matches best-first and take a
 // case only when it matched a query token no earlier pick covered — so
 // "arjun novak vs asiha mensah" yields one Novak and one Mensah, never two
 // Novaks. If the tokens can't split (compare the two Whitfields), take the tie.
 if(nm.allScored.length>=2&&/compar|versus|\bvs\b|difference|side.by.side|between|against|why was one|which one is (better|riskier|safer)/.test(q)){
  const picked=[],covered=new Set();
  for(const [cc,,toks] of nm.allScored){
   if(picked.length>=3)break;
   if(!picked.length||[...toks].some(t=>!covered.has(t))){picked.push(cc);toks.forEach(t=>covered.add(t));}
  }
  const cmp=picked.length>=2?picked:nm.list.slice(0,3);
  if(cmp.length>=2)return uwgCompareAnswer(cmp);
 }
 const nameReply=()=>{if(nm.list.length>1){uwgPending={list:nm.list,q:q};return uwgAmbiguous(nm.list);}
  const c=nm.list[0];uwgLastCase=c;return uwgCounterfactualAnswer(c,q)||uwgFieldAnswer(c,q)||uwgCaseAnswer(c);};
 if(nm.score>=3)return nameReply();
 // a named metric → the exact live number, before any explanatory entry
 const metric=uwgMetricAnswer(q);
 if(metric)return metric;
 // (fuzzy name fallback moved below the rulebook — a weak name guess must
 // not outrank a real answer)
 // Conversation memory: once we have been talking about someone, an unqualified
 // follow-up stays with them — "and his credit score?", "how long in queue?",
 // "does it match across documents?" — no need to repeat the name. The case on
 // screen serves the same role when no one has been named yet.
 const ctx=uwgLastCase||((view==='case'&&activeId)?CASES.find(x=>x.id===activeId):null);
 // Only an actual follow-up inherits the context — a pronoun, a continuation
 // opener, or a terse fragment. A full general question still goes to the
 // rulebook, so "what are the decision bands?" never becomes a case lookup.
 const isFollowUp=/^(and|also|what about|how about|then|ok|okay)\b/.test(q)
   ||/\b(he|she|his|her|hers|him|they|them|their|theirs|it|its|this person|that person|this applicant|this case|current case)\b/.test(q)
   ||q.split(/\s+/).filter(Boolean).length<=4;
 if(ctx&&isFollowUp){
  const f=uwgFieldAnswer(ctx,q);
  if(f){uwgLastCase=ctx;return f;}
  if(/\b(he|she|his|her|hers|they|them|their|theirs|this person|that person|this applicant|this case|current case|about (him|her|them|it))\b/.test(q)){uwgLastCase=ctx;return uwgCaseAnswer(ctx);}}
 // score by how much of the question a topic actually accounts for — longer and
 // multi-word keys beat incidental short ones, so “affordability screen” lands on
 // affordability rather than on any entry that happens to mention a screen.
 const kb=uwgKbBest(q);let best=kb.entry,bestN=kb.score;
 if(best)return best.a();
 if(nm.list.length)return nameReply();   // no rulebook hit: try the loose name match
 // Honest refusal beats a confident guess. Say plainly that the question
 // wasn’t understood, surface the nearest topics as clues, and never dress
 // a keyword accident up as an answer.
 const near=[];
 UWG_KB.forEach(e=>{let n=0;e.k.forEach(k=>{if(uwgKeyHit(q,k))n+=k.length;});if(n>0)near.push([n,e.k[0]]);});
 near.sort((a,b)=>b[0]-a[0]);
 const hints=near.slice(0,3).map(x=>'“'+x[1]+'”').join(', ');
 return `I didn’t understand that well enough to answer reliably — and I’d rather tell you so than guess wrong.${hints?` The nearest topics I know: ${hints}.`:''} What works well: a case ID or applicant name (with a specific field), a metric (“loss ratio right now”), a book question (“how many cases…”, “total premium in the queue”), a ranking, a what-if (“approval line to 60”), or a rulebook topic. Rephrase and I’ll take another run at it.`;
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
