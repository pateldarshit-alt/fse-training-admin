#!/usr/bin/env python3
"""Viewer: count attempts; pause the assessment instead of locking someone out."""
import pathlib, re, json

p = pathlib.Path(__file__).parent.parent / "viewer.html"
s = p.read_text()
n = 0
def sub(old, new, count=1):
    global s, n
    assert old in s, f"NOT FOUND: {old[:110]}"
    s = s.replace(old, new, count); n += 1

# ── data ───────────────────────────────────────────────────────────────────
m = re.search(r'^const TRAININGS = (\[.*\]);$', s, re.M)
T = json.loads(m.group(1))
for t in T:
    t['maxTries'] = 3
    t['restoreHours'] = 24
s = s[:m.start()] + 'const TRAININGS = ' + json.dumps(T, ensure_ascii=False) + ';' + s[m.end():]
n += 1

sub("const prog = id => getMap()[id] || { watched:false, attempted:false, passed:false, score:0, total:0 };",
    "const prog = id => getMap()[id] || { watched:false, attempted:false, passed:false, score:0, total:0, tries:0, escalated:false };")

# ── count the attempt, and decide whether this was the last one ────────────
sub("""    save(v.id,{attempted:true,score:gained,total:possible,passed});""",
"""    // Attempts are counted against the training, so per-video checks and the
    // closing assessment share one budget rather than each having their own.
    const triesKey = (v.agg_training ? v.agg_training.id : (v.training_id || v.id)) + '-tries';
    const priorTries = prog(triesKey).tries || 0;
    const tries = passed ? priorTries : priorTries + 1;
    const limit = +v.max_tries || 0;
    const outOfTries = !passed && limit > 0 && tries >= limit;
    save(triesKey, {tries, escalated: outOfTries, at: outOfTries ? Date.now() : 0});
    save(v.id,{attempted:true,score:gained,total:possible,passed,tries});""")

# ── out of attempts: do not reopen the content ─────────────────────────────
sub("""    if(!passed){
      (v.rewatch_ids || []).forEach(id => save(id, {watched:false, pos:0, answered:false}));
      if(v.agg_training) aggClear(v.agg_training);
    }""",
"""    // Reopening the videos is how we make a retry cost something. Once there
    // is no retry left, doing it would just be punishment.
    if(!passed && !outOfTries){
      (v.rewatch_ids || []).forEach(id => save(id, {watched:false, pos:0, answered:false}));
      if(v.agg_training) aggClear(v.agg_training);
    }""")

# ── pass the limit through every call site ─────────────────────────────────
for old, new in [
  ("""                  pass_score:isAggregate(t)?t.final.pass:v.pass,mandatory:t.mandatory,""",
   """                  pass_score:isAggregate(t)?t.final.pass:v.pass,mandatory:t.mandatory,
                  max_tries:t.maxTries,restore_hours:t.restoreHours,training_id:t.id,"""),
  ("""                      pass_score:t.final.pass,mandatory:t.mandatory,""",
   """                      pass_score:t.final.pass,mandatory:t.mandatory,
                      max_tries:t.maxTries,restore_hours:t.restoreHours,training_id:t.id,"""),
  ("""            {id:v.id,title:v.title,questions:v.questions,pass_score:t.final.pass,total_score:'',""",
   """            {id:v.id,title:v.title,questions:v.questions,pass_score:t.final.pass,total_score:'',
             max_tries:t.maxTries,restore_hours:t.restoreHours,training_id:t.id,"""),
  ("""            {id:t.id+'-final',title:t.name,questions:t.final.questions,pass_score:t.final.pass,""",
   """            {id:t.id+'-final',title:t.name,questions:t.final.questions,pass_score:t.final.pass,
             max_tries:t.maxTries,restore_hours:t.restoreHours,training_id:t.id,"""),
]:
    sub(old, new)

p.write_text(s)
print(f"viewer attempts: {n} replacements applied")
