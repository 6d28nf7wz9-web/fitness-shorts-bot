import difflib
import glob
import json
import os
import re

from faster_whisper import WhisperModel

from ffaudio import load_audio

QUEUE_DIR = "queue"
REC_DIR = "recordings"
OUT_DIR = "output/long"
MODEL_SIZE = os.getenv("WHISPER_MODEL", "base.en")
LANGUAGE = os.getenv("WHISPER_LANG", "en")
AUDIO_EXTS = (".m4a", ".mp3", ".wav", ".aac", ".mp4", ".mov", ".ogg", ".opus", ".flac", ".caf")


def norm(word):
    return re.sub(r"[^a-z0-9']", "", word.lower())


def load_queue():
    items = []
    for path in sorted(glob.glob(f"{QUEUE_DIR}/L*.json")):
        with open(path, encoding="utf-8") as f:
            items.append((path, json.load(f)))
    return items


def find_recording(video_id):
    for path in glob.glob(f"{REC_DIR}/*"):
        stem, ext = os.path.splitext(os.path.basename(path))
        if stem.lower() == video_id.lower() and ext.lower() in AUDIO_EXTS:
            return path
    return None


def find_job():
    """Pick a queue item that has a recording and is not built yet.
    LONG_ID forces a specific item. LONG_REC overrides the recording file (for tests)."""
    wanted = os.getenv("LONG_ID")
    override = os.getenv("LONG_REC")
    for path, data in load_queue():
        if wanted and data["id"] != wanted:
            continue
        if not wanted and data.get("status") != "waiting_for_recording":
            continue
        rec = override or find_recording(data["id"])
        if rec and os.path.exists(rec):
            return path, data, rec
    return None


def transcribe(path):
    print(f"Loading Whisper model '{MODEL_SIZE}' (first run downloads it)...")
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print("Transcribing...")
    segments, info = model.transcribe(
        load_audio(path), language=LANGUAGE, word_timestamps=True, vad_filter=True, beam_size=5
    )
    words = []
    for seg in segments:
        for w in seg.words or []:
            text = w.word.strip()
            if text:
                words.append({"w": text, "s": round(w.start, 3), "e": round(w.end, 3)})
    return words, info.duration


def map_index(b, anchors, n_script, n_spoken):
    """Map a script word position to a spoken word position using matched anchors."""
    prev, nxt = (0, 0), (n_script, n_spoken)
    for a in anchors:
        if a[0] <= b:
            prev = a
        else:
            nxt = a
            break
    if nxt[0] == prev[0]:
        return prev[1]
    return int(round(prev[1] + (b - prev[0]) * (nxt[1] - prev[1]) / (nxt[0] - prev[0])))


def align(data, words):
    script, boundaries = [], []
    for sec in data["sections"]:
        boundaries.append(len(script))
        for x in sec["narration"].split():
            script.append(norm(x) or f"#s{len(script)}")
    spoken = [norm(w["w"]) or f"#t{j}" for j, w in enumerate(words)]

    matcher = difflib.SequenceMatcher(None, script, spoken, autojunk=False)
    anchors = []
    for a, b, size in matcher.get_matching_blocks():
        for k in range(size):
            anchors.append((a + k, b + k))
    coverage = len(anchors) / max(len(script), 1)

    indexes = []
    for b in boundaries:
        idx = map_index(b, anchors, len(script), len(spoken))
        indexes.append(min(max(idx, 0), len(words) - 1))
    return indexes, coverage


def mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    job_file = f"{OUT_DIR}/job.json"
    if os.path.exists(job_file):
        os.remove(job_file)

    job = find_job()
    if not job:
        print("Nothing to build: no queued script has a recording yet.")
        return
    qpath, data, rec = job
    print(f"Building {data['id']}: {data['title']}")
    print(f"Recording: {rec}")

    words, audio_len = transcribe(rec)
    if len(words) < 50:
        raise SystemExit("Whisper found almost no speech. Check the recording.")

    indexes, coverage = align(data, words)

    t0 = max(words[0]["s"] - 0.3, 0.0)
    end_abs = min(words[-1]["e"] + 0.8, audio_len)
    n = len(data["sections"])

    starts = []
    for k in range(n):
        if k == 0:
            s = t0
        else:
            s = words[indexes[k]]["s"] - 0.2
            s = max(s, starts[-1] + 1.0)
        s = min(s, end_abs - (n - k) * 1.0)
        starts.append(s)
    ends = starts[1:] + [end_abs]

    sections = []
    for sec, s, e in zip(data["sections"], starts, ends):
        sections.append({
            "heading": sec["heading"],
            "keywords": sec["keywords"],
            "start": round(s - t0, 2),
            "end": round(e - t0, 2),
        })

    timeline = {
        "id": data["id"],
        "title": data["title"],
        "recording": rec,
        "audio_start": round(t0, 2),
        "duration": round(end_abs - t0, 2),
        "sections": sections,
        "words": [
            {"w": w["w"], "s": round(w["s"] - t0, 3), "e": round(w["e"] - t0, 3)}
            for w in words
        ],
    }
    with open(f"{OUT_DIR}/timeline.json", "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False)
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump({"id": data["id"], "queue_file": qpath, "recording": rec}, f)

    print(f"\nSpoken words: {len(words)}")
    print(f"Match with script: {coverage:.0%}")
    print(f"Video length: {mmss(timeline['duration'])}\n")
    for i, s in enumerate(sections, 1):
        print(f"Section {i}: {mmss(s['start'])}-{mmss(s['end'])} ({s['end'] - s['start']:.0f}s)  {s['heading']}")
    if coverage < 0.5:
        print("\nWarning: the recording differs a lot from the script, so section timing may be off.")


main()