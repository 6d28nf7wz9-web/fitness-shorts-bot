import json
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image

from ffaudio import load_audio

SR = 16000
STATE_FPS = 30
OUT_FPS = 30
AVATAR_DIR = os.getenv("AVATAR_DIR", "avatar")
CACHE_DIR = "output/avatar_cache"
BOB = 6  # pixels of gentle up and down movement

# h = height of the presenter on the video, bottom = gap from the bottom edge
LAYOUTS = {
    "short": {"h": 370, "x": "W-w-32", "bottom": 1320},
    "long": {"h": 380, "x": "W-w-40", "bottom": 24},
}

NAMES = ["closed", "mid", "open", "wide", "round"]   # codes 0..4

# Tuning knobs for how the mouth reacts to the voice
SILENCE = 0.08      # below this loudness the mouth is closed
WIDE_RATIO = 0.30   # higher = fewer wide (ee, s) mouths
ROUND_CENTROID = 820  # lower = fewer round (oo) mouths
BIG_OPEN = 0.55     # loudness needed for the fully open mouth
FALLBACK = {"mid": "open", "wide": "open", "round": "mid", "blink": "closed"}


def video_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def load_states(height):
    """Resize every presenter picture once and cache it. Missing pictures fall back."""
    raw = {}
    for key in NAMES + ["blink"]:
        p = os.path.join(AVATAR_DIR, key + ".png")
        if os.path.exists(p):
            raw[key] = p
    if "closed" not in raw or "open" not in raw:
        raise SystemExit("avatar/closed.png and avatar/open.png are required")
    for key in ["mid", "wide", "round", "blink"]:
        k = key
        while k not in raw:
            k = FALLBACK[k]
        raw.setdefault(key, raw[k])
    os.makedirs(CACHE_DIR, exist_ok=True)
    base = Image.open(raw["closed"]).convert("RGBA")
    width = max(2, int(round(base.width * height / base.height / 2)) * 2)
    out, done = {}, {}
    for key, path in raw.items():
        stamp = int(os.path.getmtime(path))
        dest = f"{CACHE_DIR}/h{height}_{key}_{stamp}.png"
        if path not in done:
            if not os.path.exists(dest):
                Image.open(path).convert("RGBA").resize((width, height), Image.LANCZOS).save(dest)
            done[path] = os.path.abspath(dest)
        out[key] = done[path]
    return out


def analyze(samples):
    """Return one mouth code (0 closed, 1 mid, 2 open, 3 wide, 4 round) per frame."""
    hop = SR // STATE_FPS
    win = 640
    n = len(samples) // hop
    if n < 3:
        return np.zeros(max(n, 1), dtype=int)
    pad = np.pad(samples, (0, win + hop)).astype(np.float32)
    window = np.hanning(win).astype(np.float32)
    freqs = np.fft.rfftfreq(win, 1.0 / SR)
    voice = (freqs >= 200) & (freqs < 4000)
    high = (freqs >= 4000) & (freqs < 7500)
    f1_band = (freqs >= 200) & (freqs < 1000)
    f2_band = (freqs >= 1800) & (freqs < 3500)
    rms = np.zeros(n)
    cent = np.zeros(n)
    hi_ratio = np.zeros(n)
    zcr = np.zeros(n)
    r2 = np.zeros(n)
    for i in range(n):
        start = i * hop + hop // 2 - win // 2
        seg = np.zeros(win, dtype=np.float32)
        lo = max(start, 0)
        part = pad[lo: start + win]
        seg[lo - start: lo - start + len(part)] = part
        rms[i] = np.sqrt(np.mean(seg ** 2))
        zcr[i] = np.mean(np.abs(np.diff(np.sign(seg)))) / 2.0
        spec = np.abs(np.fft.rfft(seg * window)) ** 2
        total = spec[freqs >= 100].sum() + 1e-12
        v = spec[voice].sum() + 1e-12
        cent[i] = (freqs[voice] * spec[voice]).sum() / v
        hi_ratio[i] = spec[high].sum() / total
        r2[i] = spec[f2_band].sum() / (spec[f1_band].sum() + 1e-12)
    ref = max(float(np.percentile(rms, 95)), 1e-4)
    lvl = rms / ref

    codes = np.zeros(n, dtype=int)
    for i in range(n):
        L = lvl[i]
        if L < SILENCE:
            codes[i] = 0
        elif hi_ratio[i] > 0.30 or zcr[i] > 0.28:      # s, sh, f, t: teeth showing
            codes[i] = 3
        elif r2[i] > WIDE_RATIO:                       # ee, eh: wide lips
            codes[i] = 3
        elif cent[i] < ROUND_CENTROID and L > 0.15:     # oo, oh: rounded lips
            codes[i] = 4
        elif L > BIG_OPEN:                             # ah: wide open
            codes[i] = 2
        else:
            codes[i] = 1

    # short closures between syllables (m, b, p): a sharp dip between two loud parts
    for i in range(2, n - 2):
        if codes[i] != 0:
            before = lvl[max(0, i - 5): i].max()
            after = lvl[i + 1: i + 6].max()
            peak = min(before, after)
            if peak > 0.5 and lvl[i] < 0.30 * peak:
                codes[i] = 0

    # remove single-frame blips so the mouth does not flicker
    out = list(codes)
    i = 0
    while i < n:
        j = i
        while j < n and out[j] == out[i]:
            j += 1
        if j - i < 2 and i > 0:
            for k in range(i, j):
                out[k] = out[i - 1]
        i = j
    return np.array(out, dtype=int)


def frame_states(codes, can_blink):
    states = [NAMES[int(c)] for c in codes]
    n = len(states)
    if can_blink:
        i = random.randint(50, 100)
        while i < n:
            limit = min(i + 30, n)
            k = i
            while k < limit and states[k] != "closed":
                k += 1
            if k < limit:
                for j in range(k, min(k + 4, n)):
                    if states[j] == "closed":
                        states[j] = "blink"
            i += random.randint(70, 140)
    return states


def write_list(states, paths, list_path):
    dt = 1.0 / STATE_FPS
    lines, i, n = [], 0, len(states)
    while i < n:
        j = i
        while j < n and states[j] == states[i]:
            j += 1
        lines.append(f"file '{paths[states[i]]}'\nduration {(j - i) * dt:.4f}\n")
        i = j
    lines.append(f"file '{paths[states[-1]]}'\n")
    with open(list_path, "w", encoding="utf-8") as f:
        f.write("".join(lines))


def render(video, samples, layout):
    marker = video + ".avatar"
    if os.path.exists(marker):
        with open(marker) as f:
            if f.read().strip() == str(os.path.getmtime(video)):
                print("Presenter already added to", video, "(rebuild the video first to redo it)")
                return
    cfg = LAYOUTS[layout]
    dur = video_duration(video)
    need = int(dur * SR)
    if len(samples) < need:
        samples = np.concatenate([samples, np.zeros(need - len(samples), dtype=np.float32)])
    samples = samples[:need]

    paths = load_states(cfg["h"])
    codes = analyze(samples)
    states = frame_states(codes, True)
    total = max(len(states), 1)
    shares = ", ".join(f"{k} {states.count(k) * 100 // total}%" for k in NAMES + ["blink"])
    print("Mouth shapes used:", shares)

    os.makedirs(CACHE_DIR, exist_ok=True)
    list_path = f"{CACHE_DIR}/list_{os.getpid()}.txt"
    write_list(states, paths, list_path)

    tmp = video[:-4] + "_av.mp4"
    fc = (
        f"[1:v]fps={OUT_FPS},format=rgba[av];"
        f"[0:v][av]overlay=x={cfg['x']}:y='H-h-{cfg['bottom']}+{BOB}*sin(2*PI*t*0.9)'"
        f":eof_action=repeat:format=auto[v]"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", video, "-f", "concat", "-safe", "0", "-i", list_path,
        "-filter_complex", fc,
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart",
        "-t", f"{dur:.3f}", tmp,
    ]
    subprocess.run(cmd, check=True)
    os.replace(tmp, video)
    os.remove(list_path)
    with open(marker, "w") as f:
        f.write(str(os.path.getmtime(video)))


def add_avatar(video, audio_path, audio_start, duration, layout="short"):
    """Used by long_shorts.py for each Short cut from a long video."""
    if os.getenv("NO_AVATAR"):
        return
    audio = load_audio(audio_path)
    s = int(audio_start * SR)
    render(video, audio[s: s + int(duration * SR)], layout)


def voice_for(kind):
    if kind == "short":
        with open("output/audio_info.json", encoding="utf-8") as f:
            info = json.load(f)
        parts = []
        for item in info:
            a = load_audio(item["file"])
            need = int(round(item["seconds"] * SR))
            if len(a) < need:
                a = np.concatenate([a, np.zeros(need - len(a), dtype=np.float32)])
            parts.append(a[:need])
        return np.concatenate(parts), "output/final.mp4"
    with open("output/long/timeline.json", encoding="utf-8") as f:
        tl = json.load(f)
    a = load_audio(tl["recording"])
    s = int(tl["audio_start"] * SR)
    return a[s: s + int(tl["duration"] * SR)], "output/long/final_long.mp4"


def main():
    kind = sys.argv[1] if len(sys.argv) > 1 else "short"
    if kind not in LAYOUTS:
        raise SystemExit("Use: python avatar.py short   or   python avatar.py long")
    if os.getenv("NO_AVATAR"):
        print("NO_AVATAR is set, skipping the presenter")
        return
    samples, video = voice_for(kind)
    if not os.path.exists(video):
        raise SystemExit(f"{video} not found. Build the video first.")
    print(f"Adding the presenter to {video} ...")
    render(video, samples, kind)
    print("Done.")


if __name__ == "__main__":
    main()