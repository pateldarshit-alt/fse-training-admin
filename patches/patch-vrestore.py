#!/usr/bin/env python3
"""Viewer: attempts come back on a timer, or when an admin resets them."""
import pathlib

p = pathlib.Path(__file__).parent.parent / "viewer.html"
s = p.read_text()
n = 0
def sub(old, new, count=1):
    global s, n
    assert old in s, f"NOT FOUND: {old[:110]}"
    s = s.replace(old, new, count); n += 1

# ── one place decides whether attempts are available ───────────────────────
sub("const blockingTrainings = () => TRAININGS.filter(t => t.inHub && t.blocker && !tDone(t));",
"""// An admin reset is written here by the console. Nothing else reads or
// writes it, so the two surfaces stay honest about where the state lives.
const adminResets = () => { try{ return JSON.parse(localStorage.getItem('tv_attempt_resets'))||{}; }catch{ return {}; } };

// Attempts come back two ways: the configured wait elapses, or an admin reset
// lands after the lock. Both are checked on read, so nothing has to run on a
// schedule and a reset takes effect the next time the FSE opens the app.
function triesState(t){
  const p = prog(t.id + '-tries');
  if(!p.escalated) return {locked:false, tries:p.tries||0};
  const reset = adminResets()[t.id];
  if(reset && reset.at > (p.at||0)) return {locked:false, tries:0, restoredBy:'admin'};
  const wait = (+t.restoreHours||0) * 3600000;
  if(wait && p.at && Date.now() - p.at >= wait) return {locked:false, tries:0, restoredBy:'wait'};
  return {locked:true, tries:p.tries||0, at:p.at, readyAt: wait && p.at ? p.at + wait : null};
}
const escalated = t => triesState(t).locked;

// When someone is out of attempts the training stops gating the app. The point
// of the gate is to force attention, not to stop someone doing their job.
const blockingTrainings = () => TRAININGS.filter(t => t.inHub && t.blocker && !tDone(t) && !escalated(t));

// "Sat 14:36" reads better on a phone than a duration that keeps changing.
function retryWhen(t){
  const st = triesState(t);
  if(!st.locked) return '';
  if(!st.readyAt) return 'once an admin reopens it';
  const d = new Date(st.readyAt);
  const soon = st.readyAt - Date.now() < 86400000;
  return soon
    ? `at ${d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}`
    : `${d.toLocaleDateString([], {weekday:'short'})} ${d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}`;
}""")

# ── the result screen when that was the last attempt ───────────────────────
sub("""    const msg = passed
      ? (v.pass_message || 'Well done — you have cleared this assessment.')
      : (v.fail_message || 'You have not cleared it this time. Rewatch the content and try again.');""",
"""    const backIn = (+v.restore_hours||0);
    const backTxt = backIn ? (backIn%24===0 ? `${backIn/24} day${backIn/24===1?'':'s'}` : `${backIn} hour${backIn===1?'':'s'}`) : '';
    const msg = passed
      ? (v.pass_message || 'Well done — you have cleared this assessment.')
      : outOfTries
        ? (backTxt
            ? `That is all the attempts for now. You can try this again in ${backTxt} — nothing else is held up in the meantime.`
            : 'That is all the attempts for now. This will reopen once an admin reviews it — nothing else is held up in the meantime.')
        : (v.fail_message || 'You have not cleared it this time. Rewatch the content and try again.');""")

sub("""        <div style="font-size:17px;font-weight:800">${!scoreable?'Answers recorded':passed?'Assessment passed':'Assessment failed'}</div>""",
"""        <div style="font-size:17px;font-weight:800">${!scoreable?'Answers recorded':passed?'Assessment passed':outOfTries?'Attempts used up':'Assessment failed'}</div>""")

sub("""background:${passed?'#e6faf0':expired?'#fff4dc':'#fff5f5'};display:flex;align-items:center;justify-content:center;font-size:34px;margin-bottom:16px">${!scoreable?'✓':passed?'🎉':expired?'⏱':'📘'}</div>""",
"""background:${passed?'#e6faf0':outOfTries?'#eef4fb':expired?'#fff4dc':'#fff5f5'};display:flex;align-items:center;justify-content:center;font-size:34px;margin-bottom:16px">${!scoreable?'✓':passed?'🎉':outOfTries?'⏳':expired?'⏱':'📘'}</div>""")

sub("""        ${!passed?`<div style="font-size:11.5px;color:#8a5555;text-align:center;line-height:1.5;padding:0 4px 4px">
          ${(v.rewatch_ids||[]).length>1?'The videos have been reopened.':'The video has been reopened.'}
          Work through ${(v.rewatch_ids||[]).length>1?'them':'it'} again and the assessment will unlock.</div>`:''}
        <button data-p style="width:100%;padding:12px;border-radius:9px;border:none;background:#004299;color:#fff;font:inherit;font-size:13.5px;font-weight:800;cursor:pointer">${passed?'Done':'Back to the video'+((v.rewatch_ids||[]).length>1?'s':'')}</button>""",
"""        ${!passed&&!outOfTries?`<div style="font-size:11.5px;color:#8a5555;text-align:center;line-height:1.5;padding:0 4px 4px">
          ${(v.rewatch_ids||[]).length>1?'The videos have been reopened.':'The video has been reopened.'}
          Work through ${(v.rewatch_ids||[]).length>1?'them':'it'} again and the assessment will unlock.
          ${limit?`Attempt ${tries} of ${limit}.`:''}</div>`:''}
        ${outOfTries?`<div style="font-size:11.5px;color:#31507d;text-align:center;line-height:1.5;padding:0 4px 4px">
          You can carry on using the app — this is no longer holding you up.</div>`:''}
        <button data-p style="width:100%;padding:12px;border-radius:9px;border:none;background:#004299;color:#fff;font:inherit;font-size:13.5px;font-weight:800;cursor:pointer">${passed?'Done':outOfTries?'Back to my trainings':'Back to the video'+((v.rewatch_ids||[]).length>1?'s':'')}</button>""")

# ── the hub says when, not just that ───────────────────────────────────────
sub("""      function statusOf(t){
        const fin=prog(t.id+'-final');
        if(tDone(t)) return {t:`Assessment passed${t.final.enabled?` · ${fin.score}/${fin.total}`:''}`,bg:'#e6faf0',c:'#0a7a42'};""",
"""      function statusOf(t){
        const fin=prog(t.id+'-final');
        if(tDone(t)) return {t:`Assessment passed${t.final.enabled?` · ${fin.score}/${fin.total}`:''}`,bg:'#e6faf0',c:'#0a7a42'};
        if(escalated(t)) return {t:`Try again ${retryWhen(t)}`,bg:'#eef4fb',c:'#31507d'};""")

# ── no button that cannot do anything ──────────────────────────────────────
sub("""        const fin=prog(t.id+'-final'), locked=!allVids(t), step=nextStep(t);""",
"""        // Out of attempts: the content stays readable, but there is no step to
        // offer, so the sticky CTA is dropped rather than rendered inert.
        const fin=prog(t.id+'-final'), locked=!allVids(t);
        const step=(escalated(t)&&!tDone(t)) ? null : nextStep(t);""")

p.write_text(s)
print(f"viewer restore + reset: {n} replacements applied")
