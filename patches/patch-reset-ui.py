#!/usr/bin/env python3
"""Admin: the reset action itself — everyone, or named ecodes."""
import pathlib

p = pathlib.Path(__file__).parent.parent / "index.html"
s = p.read_text()
n = 0
def sub(old, new, count=1):
    global s, n
    assert old in s, f"NOT FOUND: {old[:110]}"
    s = s.replace(old, new, count); n += 1

sub("""        <button class="btn btn-ghost btn-sm" data-ted="${t.id}">Edit</button>
        <button class="btn btn-ghost btn-sm" data-tdup="${t.id}" style="margin-left:5px">Duplicate</button>""",
"""        <button class="btn btn-ghost btn-sm" data-ted="${t.id}">Edit</button>
        <button class="btn btn-ghost btn-sm" data-treset="${t.id}" style="margin-left:5px" title="Give failed attempts back">↺ Reset attempts</button>
        <button class="btn btn-ghost btn-sm" data-tdup="${t.id}" style="margin-left:5px">Duplicate</button>""")

sub("""  $('tLib').querySelectorAll('[data-ted]').forEach(b=>b.onclick=()=>{""",
"""  $('tLib').querySelectorAll('[data-treset]').forEach(b=>b.onclick=()=>resetSheet(trainingById(b.dataset.treset)));
  $('tLib').querySelectorAll('[data-ted]').forEach(b=>b.onclick=()=>{""")

# ── the sheet ──────────────────────────────────────────────────────────────
sub("function drawTLib(){",
"""/* ── resetting attempts ───────────────────────────────────────────────────
   Written where the app can read it, so a reset here reaches the FSE without
   anyone else being involved. In the build this is an API call; the shape of
   what it records is the same either way.                                  */
const RESET_KEY = 'tv_attempt_resets';
function readResets(){ try{ return JSON.parse(localStorage.getItem(RESET_KEY))||{}; }catch{ return {}; } }
function writeReset(trainingId, scope, ecodes, reason){
  const all = readResets();
  all[trainingId] = {at: Date.now(), scope, ecodes: ecodes||[], reason: reason||'', by: 'admin'};
  try{ localStorage.setItem(RESET_KEY, JSON.stringify(all)); }catch{}
  return all[trainingId];
}

function resetSheet(t){
  if(!t) return;
  const wrap=document.createElement('div');
  wrap.className='sheetwrap';
  wrap.innerHTML=`
    <div class="sheetbg" data-close></div>
    <div class="sheet">
      <h3 style="margin:0 0 4px;font-size:18px">Reset attempts</h3>
      <p style="margin:0 0 16px;font-size:14px;color:var(--faint);line-height:1.55">
        Gives failed attempts back on <b>${esc(t.name)}</b> so the assessment can be taken again.
        Anyone who has already passed is untouched.</p>

      <label class="toggle-row"><input type="radio" name="rscope" value="all" checked>
        <span>Everyone on this training<small>Use when the content or the questions were the problem — a low pass rate is usually the paper, not the people.</small></span></label>
      <label class="toggle-row"><input type="radio" name="rscope" value="ecodes">
        <span>Specific ecodes<small>One per line, or comma separated.</small></span></label>

      <div id="rEcodeBox" hidden style="margin:-4px 0 14px 26px">
        <textarea id="rEcodes" rows="4" placeholder="E-48213&#10;E-51907"
          style="width:100%;border:1px solid var(--line);border-radius:8px;padding:9px 11px;font:inherit;font-size:14px;
          resize:vertical;background:var(--card);color:var(--ink)"></textarea>
      </div>

      <div class="form-group" style="margin-bottom:16px">
        <label>Why <small>— recorded against the reset</small></label>
        <input type="text" id="rReason" placeholder="e.g. Q3 was ambiguous, reworded on 11 Sep">
      </div>

      <div class="slotnote" id="rPreview" style="text-align:left;margin-bottom:16px"></div>

      <div style="display:flex;gap:9px;justify-content:flex-end">
        <button class="btn btn-ghost" type="button" data-close>Cancel</button>
        <button class="btn btn-primary" type="button" id="rGo">Reset attempts</button>
      </div>
    </div>`;
  document.body.appendChild(wrap);

  const ecodesOf=()=> $('rEcodes').value.split(/[\\n,]/).map(x=>x.trim()).filter(Boolean);
  const preview=()=>{
    const scope=wrap.querySelector('[name=rscope]:checked').value;
    const list=ecodesOf();
    $('rEcodeBox').hidden = scope!=='ecodes';
    $('rPreview').innerHTML = scope==='all'
      ? `Every FSE who has failed <b>${esc(t.name)}</b> gets their attempts back${+t.maxTries?` — ${t.maxTries} again`:''}. Those who passed keep their result.`
      : list.length
        ? `<b>${list.length}</b> ecode${list.length===1?'':'s'} will have their attempts restored on this training.`
        : '<span style="color:var(--amber-fg)">Add at least one ecode.</span>';
  };
  wrap.querySelectorAll('[name=rscope]').forEach(r=>r.onchange=preview);
  $('rEcodes').oninput=preview;
  preview();

  wrap.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>wrap.remove());
  $('rGo').onclick=()=>{
    const scope=wrap.querySelector('[name=rscope]:checked').value;
    const list=ecodesOf();
    if(scope==='ecodes'&&!list.length) return toast('Add at least one ecode.');
    const r=writeReset(t.id, scope, list, $('rReason').value.trim());
    wrap.remove();
    toast(scope==='all'
      ? `Attempts reset for everyone on “${t.name}”`
      : `Attempts reset for ${list.length} ecode${list.length===1?'':'s'} on “${t.name}”`);
    drawTLib();
  };
}

function drawTLib(){""")

# show that a reset is in force
sub("""  if(+t.maxTries) parts.push(`<span class="badge grey">${t.maxTries} attempts${+t.restoreHours?` · back in ${t.restoreHours}h`:' · reset only'}</span>`);""",
"""  if(+t.maxTries) parts.push(`<span class="badge grey">${t.maxTries} attempts${+t.restoreHours?` · back in ${t.restoreHours}h`:' · reset only'}</span>`);
  const rst=readResets()[t.id];
  if(rst) parts.push(`<span class="badge">↺ reset ${new Date(rst.at).toLocaleDateString([], {day:'numeric',month:'short'})}${rst.scope==='ecodes'?` · ${rst.ecodes.length} ecodes`:' · everyone'}</span>`);""")

# ── styles for the sheet ───────────────────────────────────────────────────
sub("  .ctbox{",
"""  .sheetwrap{position:fixed;inset:0;z-index:200;display:flex;align-items:center;justify-content:center;padding:24px}
  .sheetbg{position:absolute;inset:0;background:rgba(12,18,32,.45)}
  .sheet{position:relative;background:var(--card);border-radius:14px;padding:24px;width:100%;max-width:560px;
    max-height:90vh;overflow-y:auto;box-shadow:0 20px 50px rgba(0,0,0,.3)}
  .ctbox{""")

p.write_text(s)
print(f"reset action: {n} replacements applied")
