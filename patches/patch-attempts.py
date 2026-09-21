#!/usr/bin/env python3
"""Admin: an attempt limit, after which the assessment pauses."""
import pathlib

p = pathlib.Path(__file__).parent.parent / "index.html"
s = p.read_text()
n = 0
def sub(old, new, count=1):
    global s, n
    assert old in s, f"NOT FOUND: {old[:110]}"
    s = s.replace(old, new, count); n += 1

# ── the control, next to the time limit ────────────────────────────────────
sub("""      <div class="form-group">
        <label>Time limit <small>— seconds for a whole attempt, blank for none</small></label>
        <input type="number" min="10" id="f_timer" placeholder="None">
        <div id="timerNote" style="font-size:13px;color:var(--faint);line-height:1.5"></div>
      </div>""",
"""      <div class="form-group">
        <label>Time limit <small>— seconds for a whole attempt, blank for none</small></label>
        <input type="number" min="10" id="f_timer" placeholder="None">
        <div id="timerNote" style="font-size:13px;color:var(--faint);line-height:1.5"></div>
      </div>
      <div class="form-group">
        <label>Attempts before a manager steps in <small>— blank for unlimited</small></label>
        <input type="number" min="1" max="10" id="f_maxTries" placeholder="3">
        <div id="triesNote" style="font-size:13px;color:var(--faint);line-height:1.5"></div>
      </div>""")

sub("""function freshT(){ return {id:uid(),name:'',widget:'mini-banner',videos:[blankVideo(1)],timer:'',
  certificate:false,perVideo:false,""",
"""function freshT(){ return {id:uid(),name:'',widget:'mini-banner',videos:[blankVideo(1)],timer:'',maxTries:3,
  certificate:false,perVideo:false,""")

sub("  if(t.timer==null) t.timer='';",
"""  if(t.timer==null) t.timer='';
  // Unlimited retries on a blocking training locks an FSE out of their job.
  if(t.maxTries===undefined) t.maxTries=3;""")

sub("  $('f_timer').value=T.timer||''; $('f_cert').checked=!!T.certificate;",
"""  $('f_timer').value=T.timer||''; $('f_cert').checked=!!T.certificate;
  $('f_maxTries').value=(T.maxTries===''||T.maxTries==null)?'':T.maxTries;
  const tries=+T.maxTries||0;
  $('triesNote').textContent = !tries
    ? 'Unlimited. On a mandatory training this means an FSE who cannot pass stays locked out of the app indefinitely.'
    : `After ${tries} failed attempt${tries===1?'':'s'} the retry stops, the home-screen gate lifts so they can work, and the training is flagged for coaching.`;""")

sub("$('f_cert').onchange=e=>{T.certificate=e.target.checked;renderT();};",
"""$('f_cert').onchange=e=>{T.certificate=e.target.checked;renderT();};
$('f_maxTries').oninput=e=>{T.maxTries=e.target.value===''?'':Math.max(1,+e.target.value);renderT();};""")

# ── say it in the summary and the library ──────────────────────────────────
sub("  if(T.certificate) bits.push('and earns a downloadable certificate');",
"""  if(T.certificate) bits.push('and earns a downloadable certificate');
  if(+T.maxTries) bits.push(`with a manager stepping in after ${T.maxTries} failed attempts`);""")

sub("""  if(t.certificate) parts.push('<span class="badge">🎓 certificate</span>');""",
"""  if(t.certificate) parts.push('<span class="badge">🎓 certificate</span>');
  if(+t.maxTries) parts.push(`<span class="badge grey">${t.maxTries} attempts</span>`);
  else parts.push('<span class="badge warn">unlimited attempts</span>');""")

# ── warn where it actually bites ───────────────────────────────────────────
sub("""  if(P.blocker && !P.hub)""",
"""  if(P.blocker && t && !(+t.maxTries))
    warnings.push('This training allows unlimited attempts and blocks the home screen — an FSE who cannot pass it has no way back into the app. Set an attempt limit on the training.');
  if(P.blocker && !P.hub)""")

p.write_text(s)
print(f"admin attempt limit: {n} replacements applied")
