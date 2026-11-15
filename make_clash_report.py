"""Generate a self-contained HTML clash report from the Navisworks addin bridge."""
import json, urllib.request, html, datetime, os, sys

# Usage: python make_clash_report.py "<clash test name>" [output.html]
if len(sys.argv) < 2:
    sys.exit('Usage: python make_clash_report.py "<clash test name>" [output.html]')
TEST = sys.argv[1]
BASE = "http://localhost:8765"
FT_TO_IN = 12.0
FT_TO_MM = 304.8

def post(path, payload):
    req = urllib.request.Request(BASE + path, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

data = post("/clash/results", {"name": TEST, "limit": 100000})
results = data.get("results", [])

CLEAR_TOKENS = ("HEC_Clearance", "Clearance_Access", "Clearance_Service")
def is_clearance(r):
    return any(t in (r["item1"], r["item2"]) for t in CLEAR_TOKENS)

for r in results:
    d_ft = r["distance"]
    r["pen_in"] = abs(d_ft) * FT_TO_IN
    r["pen_mm"] = abs(d_ft) * FT_TO_MM
    r["kind"] = "Clearance (soft)" if is_clearance(r) else "Hard"
    r["pair"] = f'{r["item1"]} ↔ {r["item2"]}'

total = len(results)
hard = [r for r in results if r["kind"] == "Hard"]
soft = [r for r in results if r["kind"] != "Hard"]

# status counts
status_ct, pair_ct = {}, {}
for r in results:
    status_ct[r["status"]] = status_ct.get(r["status"], 0) + 1
    pair_ct[r["pair"]] = pair_ct.get(r["pair"], 0) + 1
top_pairs = sorted(pair_ct.items(), key=lambda x: -x[1])[:8]
max_pen = max((r["pen_in"] for r in results), default=0)

rows_json = json.dumps(results)
gen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def chips(ct):
    order = ["New","Active","Reviewed","Approved","Resolved"]
    out = []
    for k in order:
        if k in ct: out.append(f'<span class="chip s-{k}">{k}: {ct[k]}</span>')
    for k,v in ct.items():
        if k not in order: out.append(f'<span class="chip">{html.escape(k)}: {v}</span>')
    return " ".join(out)

pair_rows = "".join(
    f"<tr><td>{html.escape(p)}</td><td class='num'>{c}</td>"
    f"<td><div class='bar' style='width:{c/top_pairs[0][1]*100:.0f}%'></div></td></tr>"
    for p,c in top_pairs)

HTML = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Clash Report — {html.escape(TEST)}</title>
<style>
 :root{{--bg:#0f1115;--card:#181b22;--line:#262b36;--txt:#e6e9ef;--mut:#9aa3b2;--accent:#4f9cff;
   --hard:#ff5c5c;--soft:#6b7280;--New:#ff5c5c;--Active:#ffb020;--Reviewed:#4f9cff;--Approved:#27c093;--Resolved:#27c093;}}
 *{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--txt);
   font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif;padding:28px;}}
 h1{{font-size:20px;margin:0 0 4px}} .sub{{color:var(--mut);margin-bottom:20px;font-size:13px}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:22px}}
 .kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
 .kpi .n{{font-size:26px;font-weight:700}} .kpi .l{{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.04em}}
 .kpi.hard .n{{color:var(--hard)}}
 .card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:22px}}
 .card h2{{font-size:14px;margin:0 0 12px;color:var(--mut);text-transform:uppercase;letter-spacing:.05em}}
 .chip{{display:inline-block;padding:3px 10px;border-radius:999px;background:#222734;font-size:12px;margin:2px 4px 2px 0}}
 .chip.s-New{{background:#3a1d1d;color:#ff8e8e}} .chip.s-Active{{background:#3a2f17;color:#ffce7a}}
 .chip.s-Reviewed{{background:#16304d;color:#8fc1ff}} .chip.s-Approved,.chip.s-Resolved{{background:#16382c;color:#73e0bb}}
 table{{width:100%;border-collapse:collapse}} th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}}
 th{{color:var(--mut);font-size:12px;cursor:pointer;user-select:none;position:sticky;top:0;background:var(--card)}}
 th:hover{{color:var(--txt)}} td.num{{text-align:right;font-variant-numeric:tabular-nums}}
 .bar{{height:8px;background:var(--accent);border-radius:4px}}
 .tag{{padding:2px 8px;border-radius:6px;font-size:12px;font-weight:600}}
 .tag.Hard{{background:#3a1d1d;color:#ff8e8e}} .tag.soft{{background:#23262e;color:var(--mut)}}
 .controls{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;align-items:center}}
 input,select{{background:#0d0f14;border:1px solid var(--line);color:var(--txt);padding:7px 10px;border-radius:8px;font-size:13px}}
 .st{{font-weight:600}} .st-New{{color:var(--New)}} .st-Active{{color:var(--Active)}} .st-Reviewed{{color:var(--Reviewed)}}
 .st-Approved,.st-Resolved{{color:var(--Approved)}}
 .pen{{font-variant-numeric:tabular-nums}} .wrap{{max-height:620px;overflow:auto;border:1px solid var(--line);border-radius:10px}}
 .foot{{color:var(--mut);font-size:12px;margin-top:18px}}
</style></head><body>
<h1>Clash Report &mdash; {html.escape(TEST)}</h1>
<div class="sub">Navisworks Manage 2027 &middot; Hard test, tol 1&nbsp;mm &middot; generated {gen} &middot; distance = penetration depth</div>

<div class="grid">
  <div class="kpi"><div class="n">{total}</div><div class="l">Total clashes</div></div>
  <div class="kpi hard"><div class="n">{len(hard)}</div><div class="l">Hard geometry</div></div>
  <div class="kpi"><div class="n">{len(soft)}</div><div class="l">Clearance (soft)</div></div>
  <div class="kpi"><div class="n">{max_pen:.2f}&Prime;</div><div class="l">Max penetration</div></div>
</div>

<div class="card"><h2>Status breakdown</h2>{chips(status_ct)}</div>

<div class="card"><h2>Top colliding pairs</h2>
  <table><thead><tr><th>Pair</th><th class="num">Count</th><th></th></tr></thead>
  <tbody>{pair_rows}</tbody></table>
</div>

<div class="card"><h2>All clashes</h2>
  <div class="controls">
    <input id="q" placeholder="Search item / clash name&hellip;" oninput="render()">
    <select id="fk" onchange="render()"><option value="">All kinds</option>
      <option value="Hard">Hard only</option><option value="Clearance (soft)">Clearance only</option></select>
    <select id="fs" onchange="render()"><option value="">All statuses</option></select>
    <span id="cnt" class="sub" style="margin:0"></span>
  </div>
  <div class="wrap"><table id="t">
    <thead><tr>
      <th onclick="sortBy('name')">Clash</th>
      <th onclick="sortBy('status')">Status</th>
      <th onclick="sortBy('kind')">Kind</th>
      <th onclick="sortBy('item1')">Item 1</th>
      <th onclick="sortBy('item2')">Item 2</th>
      <th class="num" onclick="sortBy('pen_in')">Pen (in)</th>
      <th class="num" onclick="sortBy('pen_mm')">Pen (mm)</th>
    </tr></thead><tbody id="tb"></tbody>
  </table></div>
</div>

<div class="foot">Soft = involves a clearance/maintenance envelope (HEC_Clearance, Clearance_Access/Service), not a physical conflict.
Hard = real geometry interference &mdash; prioritise these. &nbsp;Remember to <b>File &rarr; Save</b> the .nwf in Navisworks to persist results.</div>

<script>
const DATA = {rows_json};
let sortKey='pen_in', sortDir=-1;
const fs=document.getElementById('fs');
[...new Set(DATA.map(r=>r.status))].forEach(s=>{{const o=document.createElement('option');o.value=o.textContent=s;fs.appendChild(o)}});
function sortBy(k){{sortDir = sortKey===k? -sortDir : 1; sortKey=k; render();}}
function render(){{
  const q=document.getElementById('q').value.toLowerCase();
  const fk=document.getElementById('fk').value, sv=fs.value;
  let rows=DATA.filter(r=>(!fk||r.kind===fk)&&(!sv||r.status===sv)&&
     (!q||r.name.toLowerCase().includes(q)||r.item1.toLowerCase().includes(q)||r.item2.toLowerCase().includes(q)));
  rows.sort((a,b)=>{{const x=a[sortKey],y=b[sortKey];return (x>y?1:x<y?-1:0)*sortDir}});
  document.getElementById('tb').innerHTML = rows.map(r=>`<tr>
    <td>${{r.name}}</td><td class="st st-${{r.status}}">${{r.status}}</td>
    <td><span class="tag ${{r.kind==='Hard'?'Hard':'soft'}}">${{r.kind==='Hard'?'Hard':'Soft'}}</span></td>
    <td>${{r.item1}}</td><td>${{r.item2}}</td>
    <td class="num pen">${{r.pen_in.toFixed(2)}}</td><td class="num pen">${{r.pen_mm.toFixed(0)}}</td></tr>`).join('');
  document.getElementById('cnt').textContent = rows.length+' / '+DATA.length+' shown';
}}
render();
</script></body></html>"""

out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.expanduser("~"), "Downloads", "clash_report.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"WROTE {out}")
print(f"total={total} hard={len(hard)} soft={len(soft)} statuses={status_ct}")
