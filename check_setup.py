import datetime as dt
import glob
import itertools
import json
import os
import py_compile
import re
import subprocess
import sys
from collections import Counter, defaultdict

from topics import THRESHOLD, all_used, similarity, too_similar

WF_DIR = ".github/workflows"
UNITS_PER_UPLOAD = 1600
DAILY_QUOTA = 10000

SCRIPTS = [
    "gen_script.py", "voice.py", "clips_fast.py", "assemble.py", "upload.py",
    "long_script.py", "long_voice.py", "long_transcribe.py", "long_clips.py",
    "long_assemble.py", "long_upload.py", "long_shorts.py", "avatar.py", "yt.py",
    "ffaudio.py", "topics.py",
]
PACKAGES = [
    "google-genai", "edge-tts", "requests", "google-api-python-client",
    "google-auth-oauthlib", "faster-whisper",
]
EXPECTED = {
    "daily.yml": ["gen_script.py", "voice.py", "clips_fast.py", "assemble.py", "upload.py"],
    "long_ai.yml": [
        "long_script.py", "long_voice.py", "long_transcribe.py", "long_clips.py",
        "long_assemble.py", "avatar.py", "long_upload.py", "long_shorts.py",
    ],
}
SECRETS = ["GEMINI_API_KEY", "PIXABAY_API_KEY", "YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"]
CRON_RE = re.compile(r"""^\s*-\s*cron:\s*["']([^"']+)["']""", re.M)

counts = Counter()


def say(level, msg):
    counts[level] += 1
    tags = {"OK": "[ OK ]", "WARN": "[WARN]", "FAIL": "[FAIL]", "INFO": "[info]"}
    print(f"{tags[level]} {msg}")


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def load_list(path):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return [str(x) for x in data] if isinstance(data, list) else None
    except FileNotFoundError:
        return []
    except Exception:
        return None


def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return 1, "", str(e)


def tz(name):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        return None


def parse_field(field, lo, hi):
    if field == "*":
        return set(range(lo, hi + 1))
    vals = set()
    for part in field.split(","):
        if part.startswith("*/"):
            vals.update(range(lo, hi + 1, int(part[2:])))
        elif "-" in part:
            a, b = part.split("-")
            vals.update(range(int(a), int(b) + 1))
        else:
            vals.add(int(part))
    return vals


def cron_times(cron, start, days=7):
    try:
        m, h, dom, mon, dow = cron.split()
        if dom != "*" or mon != "*":
            return []
        mins, hrs = parse_field(m, 0, 59), parse_field(h, 0, 23)
        dows = {d % 7 for d in parse_field(dow, 0, 7)}
    except Exception:
        return []
    out = []
    for d in range(days + 1):
        day = (start + dt.timedelta(days=d)).date()
        if (day.weekday() + 1) % 7 not in dows:
            continue
        for hh in sorted(hrs):
            for mm in sorted(mins):
                t = dt.datetime(day.year, day.month, day.day, hh, mm, tzinfo=dt.timezone.utc)
                if start < t <= start + dt.timedelta(days=days):
                    out.append(t)
    return out


def check_files():
    print("\n== 1. Files and code ==")
    bad = False
    for name in SCRIPTS:
        if not os.path.exists(name):
            say("FAIL", f"missing file: {name}")
            bad = True
            continue
        try:
            py_compile.compile(name, doraise=True)
        except py_compile.PyCompileError as e:
            say("FAIL", f"{name} has a syntax error: {str(e)[:200]}")
            bad = True
    if not bad:
        say("OK", f"all {len(SCRIPTS)} scripts exist and compile")

    reqs = (read("requirements.txt") or "").lower()
    missing = [p for p in PACKAGES if p not in reqs]
    if missing:
        say("FAIL", "requirements.txt is missing: " + ", ".join(missing))
    else:
        say("OK", "requirements.txt lists every package")

    tracks = []
    if os.path.isdir("music"):
        tracks = [n for n in os.listdir("music") if n.lower().endswith((".mp3", ".wav", ".m4a"))]
    if tracks:
        say("OK", f"{len(tracks)} music tracks in music/")
    else:
        say("FAIL", "no music tracks in music/")

    for name in ("used_topics.json", "used_long_topics.json"):
        data = load_list(name)
        if data is None:
            say("FAIL", f"{name} is not a valid JSON list")
        else:
            say("OK", f"{name}: {len(data)} topics recorded")

    for name in ("gen_script.py", "long_script.py"):
        if "too_similar" in (read(name) or ""):
            say("OK", f"{name} blocks similar topics")
        else:
            say("WARN", f"{name} only blocks exact repeats. Run the patch commands from Step 3.")


def check_workflows():
    print("\n== 2. Workflows and schedule ==")
    schedules = {}
    files = sorted(glob.glob(f"{WF_DIR}/*.yml") + glob.glob(f"{WF_DIR}/*.yaml"))
    for fname, scripts in EXPECTED.items():
        text = read(f"{WF_DIR}/{fname}")
        if text is None:
            say("FAIL", f"{fname} is missing")
            continue
        crons = CRON_RE.findall(text)
        expected_crons = {"daily.yml": 3, "long_ai.yml": 1}.get(fname, 1)
        if len(crons) == expected_crons:
            say("OK", f"{fname}: {len(crons)} schedule(s) ({'; '.join(crons)} UTC)")
        else:
            say("FAIL", f"{fname}: expected {expected_crons} schedule(s), found {len(crons)}")
        if "workflow_dispatch" not in text:
            say("WARN", f"{fname}: no manual 'Run workflow' button")
        pos, ok = -1, True
        for s in scripts:
            idx = text.find(f"python {s}")
            if idx == -1:
                say("FAIL", f"{fname}: step 'python {s}' is missing")
                ok = False
                break
            if idx < pos:
                say("FAIL", f"{fname}: 'python {s}' runs out of order")
                ok = False
                break
            pos = idx
        if ok:
            say("OK", f"{fname}: all {len(scripts)} steps present and in order")
        if "git push" in text and "git pull --rebase" not in text:
            say("WARN", f"{fname}: pushes without 'git pull --rebase', which can fail when two workflows push")
        schedules[fname] = crons

    for path in files:
        fname = os.path.basename(path)
        if fname in EXPECTED:
            continue
        text = read(path) or ""
        if CRON_RE.search(text):
            say("WARN", f"{fname} also has a schedule and will run by itself. Remove it if you don't want extra scripts or Issues.")
        else:
            say("INFO", f"{fname}: no schedule (manual or event-triggered only)")

    per_long = 2
    m = re.search(r'SHORTS_PER_LONG:\s*"?(\d+)"?', read(f"{WF_DIR}/long_ai.yml") or "")
    if m:
        per_long = int(m.group(1))
    return schedules, per_long


def upload_plan(schedules, per_long):
    print("\n== 3. Upload plan for the next 7 days ==")
    now = dt.datetime.now(dt.timezone.utc)
    pac, cairo = tz("America/Los_Angeles"), tz("Africa/Cairo")
    per_day = defaultdict(Counter)
    runs = []
    for fname, crons in schedules.items():
        for c in crons:
            for t in cron_times(c, now, 7):
                day = (t.astimezone(pac) if pac else t).date()
                if fname == "daily.yml":
                    per_day[day]["short"] += 1
                else:
                    per_day[day]["long"] += 1
                    per_day[day]["cut"] += per_long
                runs.append((t, fname))
    if not runs:
        say("FAIL", "no scheduled runs found for the next 7 days")
        return
    print("Next scheduled runs:")
    for t, fname in sorted(runs)[:6]:
        local = f" = {t.astimezone(cairo):%H:%M} Cairo" if cairo else ""
        print(f"  {fname:12} {t:%a %d %b %H:%M} UTC{local}")
    print("Uploads per quota day (the YouTube quota resets at midnight Pacific time):")
    worst = 0
    for day in sorted(per_day):
        c = per_day[day]
        total = c["short"] + c["long"] + c["cut"]
        units = total * UNITS_PER_UPLOAD
        worst = max(worst, units)
        print(f"  {day}: {c['short']} Short + {c['long']} long + {c['cut']} cut Shorts = {total} uploads ({units:,} units)")
    if worst > DAILY_QUOTA:
        say("FAIL", f"a day needs {worst:,} units, above the {DAILY_QUOTA:,} limit")
    elif worst > 8000:
        say("WARN", f"busiest day uses {worst:,} of {DAILY_QUOTA:,} units, with little room for test uploads")
    else:
        say("OK", f"busiest day uses {worst:,} of {DAILY_QUOTA:,} units")
    full_days = [d for d in per_day if per_day[d]["short"] and per_day[d]["long"]]
    say("INFO", f"{len(full_days)} of {len(per_day)} days include both the Short and the long video")


def check_secrets():
    print("\n== 4. Keys and secrets ==")
    missing = [k for k in SECRETS[:4] if not os.getenv(k)]
    if missing:
        say("WARN", "not loaded in this Codespace: " + ", ".join(missing) + " (restart it if you added them recently)")
    else:
        say("OK", "the 4 Codespace secrets are loaded")
    if os.path.exists("token.json"):
        say("OK", "token.json (YouTube login) exists in this Codespace")
    else:
        say("WARN", "token.json not found here (fine if you only run in the cloud)")
    code, out, _ = run(["gh", "secret", "list"])
    if code != 0:
        say("INFO", "can't read GitHub's Actions secrets from here. Check Settings > Secrets and variables > Actions for: " + ", ".join(SECRETS))
        return
    names = {line.split()[0] for line in out.splitlines() if line.strip()}
    gone = [s for s in SECRETS if s not in names]
    if gone:
        say("FAIL", "missing in GitHub Actions secrets: " + ", ".join(gone))
    else:
        say("OK", "all 5 Actions secrets exist in GitHub")


def check_runs():
    print("\n== 5. What GitHub actually ran ==")
    code, out, _ = run(["gh", "run", "list", "--limit", "100", "--json",
                        "workflowName,event,conclusion,status,createdAt"])
    runs = None
    if code == 0:
        try:
            runs = json.loads(out)
        except Exception:
            runs = None
    if runs is None:
        say("INFO", "can't read run history from here. Open the Actions tab and look for runs labeled 'Scheduled'.")
        return
    for wf in ("Daily Short", "AI Long Video"):
        mine = [r for r in runs if r.get("workflowName") == wf]
        if not mine:
            say("INFO", f"{wf}: no runs yet")
            continue
        sched = [r for r in mine if r.get("event") == "schedule"]
        if sched:
            days = len({r["createdAt"][:10] for r in sched})
            say("OK", f"{wf}: {len(sched)} runs started by the schedule on {days} different days")
        else:
            say("WARN", f"{wf}: {len(mine)} runs so far, none started by the schedule yet")
        recent = sorted(mine, key=lambda r: r["createdAt"], reverse=True)[:5]
        last = ", ".join(
            f"{r['createdAt'][5:10]} {r.get('event')}:{r.get('conclusion') or r.get('status')}"
            for r in recent
        )
        say("INFO", f"{wf} latest: {last}")
        fails = [r for r in mine if r.get("conclusion") == "failure"]
        if recent[0].get("conclusion") == "failure":
            say("FAIL", f"{wf}: the latest run failed. Open it in the Actions tab.")
        elif fails:
            say("WARN", f"{wf}: {len(fails)} failed runs in the history")


def check_topics():
    print("\n== 6. Repeated subjects ==")
    shorts = load_list("used_topics.json") or []
    longs = load_list("used_long_topics.json") or []
    labeled = [("Short", t) for t in shorts] + [("Long", t) for t in longs]
    if not labeled:
        say("INFO", "no topics recorded yet")
        return
    norm = Counter(t.strip().lower() for _, t in labeled)
    exact = [t for t, n in norm.items() if n > 1]
    if exact:
        for t in exact:
            say("FAIL", f"exact repeat: {t}")
    else:
        say("OK", f"no exact repeats among {len(labeled)} topics")

    pairs = []
    for (la, a), (lb, b) in itertools.combinations(labeled, 2):
        if a.strip().lower() == b.strip().lower():
            continue
        s = similarity(a, b)
        if s >= THRESHOLD:
            pairs.append((s, la, a, lb, b))
    pairs.sort(reverse=True)
    if pairs:
        say("WARN", f"{len(pairs)} pairs of very similar topics (score {THRESHOLD} or more):")
        for s, la, a, lb, b in pairs[:8]:
            print(f"        {s:.2f}  [{la}] {a}   <->   [{lb}] {b}")
    else:
        say("OK", "no near-repeats among Short and long topics together")

    headings, titles = Counter(), Counter()
    for p in sorted(glob.glob("queue/L*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            continue
        titles[d.get("title", "").strip().lower()] += 1
        for s in d.get("sections", []):
            headings[s.get("heading", "").strip().lower()] += 1
        if d.get("topic") and d["topic"] not in longs:
            say("WARN", f"{os.path.basename(p)}: topic not found in used_long_topics.json")
    dup_titles = [t for t, n in titles.items() if t and n > 1]
    dup_heads = [h for h, n in headings.items() if h and n > 1]
    if dup_titles:
        say("FAIL", "repeated long video titles: " + "; ".join(dup_titles[:5]))
    else:
        say("OK", "no repeated long video titles")
    if dup_heads:
        say("INFO", "section headings used more than once (these become Short titles): " + "; ".join(dup_heads[:6]))

    last = labeled[-1][1]
    guard_works = too_similar(last, all_used()) and not too_similar("zebra giraffe migration patterns", all_used())
    if guard_works:
        say("OK", "the repeat guard works: it rejects a used topic and accepts a new one")
    else:
        say("WARN", "the repeat guard gave an unexpected answer in its self-test")


def main():
    print("Daily posting check")
    print("=" * 40)
    check_files()
    schedules, per_long = check_workflows()
    upload_plan(schedules, per_long)
    check_secrets()
    check_runs()
    check_topics()
    print("\n== Summary ==")
    print(f"{counts['OK']} ok, {counts['WARN']} warnings, {counts['FAIL']} failures")
    if counts["FAIL"]:
        print("Fix the [FAIL] lines first, then run this again.")
        sys.exit(1)
    print("Config looks good. Real proof is section 5 showing scheduled runs on several different days.")


main()