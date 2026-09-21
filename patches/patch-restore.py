#!/usr/bin/env python3
"""Admin: attempt limit + automatic restore window."""
import pathlib

p = pathlib.Path(__file__).parent.parent / "index.html"
s = p.read_text()
n = 0
def sub(old, new, count=1):
    global s, n
    assert old in s, f"NOT FOUND: {old[:110]}"
    s = s.replace(old, new, count); n += 1

# ── the two settings, side by side ─────────────────────────────────────────
sub("""      <div class="form-group">
        <label>Attempts before a manager steps in <small>— blank for unlimited</small></label>
        <input type="number" min="1" max="10" id="f_maxTries" placeholder="3">
        <div id="triesNote" style="font-size:13px;color:var(--faint);line-height:1.5"></div>
      </div>""",
"""      <div class="form-group">
        <label>Attempts allowed <small>— blank for unlimited</small></label>
        <input type="number" min="1" max="10" id="f_maxTries" placeholder="3">
      </div>
      <div class="form-group">
        <label>Attempts come back after <small>— hours; blank means only a reset restores them</small></label>
        <input type="number" min="1" max="720" id="f_restore" placeholder="24">
      </div>
      <div class="form-group full">
        <div id="triesNote" class="slotnote" style="text-align:left"></div>
      </div>""")

sub("""function freshT(){ return {id:uid(),name:'',widget:'mini-banner',videos:[blankVideo(1)],timer:'',maxTries:3,""",
    """function freshT(){ return {id:uid(),name:'',widget:'mini-banner',videos:[blankVideo(1)],timer:'',maxTries:3,restoreHours:24,""")

sub("""  if(t.maxTries===undefined) t.maxTries=3;""",
"""  if(t.maxTries===undefined) t.maxTries=3;
  // Without a way back, an FSE out of attempts on a blocking training is stuck
  // until someone intervenes. A wait is the version that needs nobody.
  if(t.restoreHours===undefined) t.restoreHours=24;""")

sub("""  $('f_maxTries').value=(T.maxTries===''||T.maxTries==null)?'':T.maxTries;
  const tries=+T.maxTries||0;
  $('triesNote').textContent = !tries
    ? 'Unlimited. On a mandatory training this means an FSE who cannot pass stays locked out of the app indefinitely.'
    : `After ${tries} failed attempt${tries===1?'':'s'} the retry stops, the home-screen gate lifts so they can work, and the training is flagged for coaching.`;""",
"""  $('f_maxTries').value=(T.maxTries===''||T.maxTries==null)?'':T.maxTries;
  $('f_restore').value=(T.restoreHours===''||T.restoreHours==null)?'':T.restoreHours;
  const tries=+T.maxTries||0, back=+T.restoreHours||0;
  const hrs=h=>h%24===0?`${h/24} day${h/24===1?'':'s'}`:`${h} hour${h===1?'':'s'}`;
  $('triesNote').innerHTML = !tries
    ? '<b>Unlimited attempts.</b> On a mandatory training an FSE who cannot pass stays locked out of the app with no way forward. Set a limit unless you have a reason not to.'
    : back
      ? `After <b>${tries}</b> failed attempt${tries===1?'':'s'} the assessment pauses and the home-screen gate lifts, so the FSE can keep working. Attempts come back on their own <b>${hrs(back)}</b> later — nobody has to do anything.`
      : `After <b>${tries}</b> failed attempt${tries===1?'':'s'} the assessment pauses and the gate lifts. <b>Attempts do not come back on their own</b> — the FSE stays stuck on this training until you reset it below.`;""")

sub("$('f_maxTries').oninput=e=>{T.maxTries=e.target.value===''?'':Math.max(1,+e.target.value);renderT();};",
"""$('f_maxTries').oninput=e=>{T.maxTries=e.target.value===''?'':Math.max(1,+e.target.value);renderT();};
$('f_restore').oninput=e=>{T.restoreHours=e.target.value===''?'':Math.max(1,+e.target.value);renderT();};""")

sub("  if(+T.maxTries) bits.push(`with a manager stepping in after ${T.maxTries} failed attempts`);",
"""  if(+T.maxTries) bits.push(+T.restoreHours
    ? `pausing after ${T.maxTries} failed attempts and reopening ${+T.restoreHours>=24?`${Math.round(T.restoreHours/24)} day${Math.round(T.restoreHours/24)===1?'':'s'}`:`${T.restoreHours} hours`} later`
    : `stopping after ${T.maxTries} failed attempts until an admin resets it`);""")

sub("""  if(+t.maxTries) parts.push(`<span class="badge grey">${t.maxTries} attempts</span>`);
  else parts.push('<span class="badge warn">unlimited attempts</span>');""",
"""  if(+t.maxTries) parts.push(`<span class="badge grey">${t.maxTries} attempts${+t.restoreHours?` · back in ${t.restoreHours}h`:' · reset only'}</span>`);
  else parts.push('<span class="badge warn">unlimited attempts</span>');""")

sub("""  if(P.blocker && t && !(+t.maxTries))
    warnings.push('This training allows unlimited attempts and blocks the home screen — an FSE who cannot pass it has no way back into the app. Set an attempt limit on the training.');""",
"""  if(P.blocker && t && !(+t.maxTries))
    warnings.push('This training allows unlimited attempts and blocks the home screen — an FSE who cannot pass it has no way back into the app. Set an attempt limit on the training.');
  if(P.blocker && t && +t.maxTries && !(+t.restoreHours))
    warnings.push(`Attempts do not come back on their own, so an FSE who fails ${t.maxTries} times waits for an admin reset before they can finish this. Set a restore window unless that is intended.`);""")

p.write_text(s)
print(f"attempt limit + restore window: {n} replacements applied")
