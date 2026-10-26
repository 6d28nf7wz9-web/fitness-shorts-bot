import json
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image

from ffaudio import load_audio

SR = 16000
STATE_FPS = 25
OUT_FPS = 30
AVATAR_DIR = os.getenv("AVATAR_DIR", "avatar")
CACHE_DIR = "output/avatar_cache"
BOB = 5  # pixels of gentle up and down movement

LAYOUTS = {
    "short": {"h": 520, "x": "(W-w)/2", "bottom": 170},
    "long": {"h": 500, "x": "W-w-40", "bottom": 30},
}


def video_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def load_states(height):
    files = {"closed": "closed.png", "mid": "mid.png", "open": "open.png", "blink": "blink.png"}
    raw = {k: os.path.join(AVATAR_DIR, v) for k, v in files.items()
           if os.path.exists(os.path.join(AVATAR_DIR, v))}
    if "closed" not in raw or "open" not in raw:
        raise SystemExit("avatar/closed.png and avatar/open.png are required. Run: python make_avatar.py")
    raw.setdefault("mid", raw["open"])
    os.makedirs(CACHE_DIR, exist_ok=True)
    base = Image.open(raw["closed"]).convert("RGBA")
    width = max(2, int(round(base.width * height / base.height / 2)) * 2)
    out = {}
    for key, path in raw.items():
        im = Image.open(path).convert("RGBA").resize((width, height), Image.LANCZOS)
        dest = f"{CACHE_DIR}/h{height}_{key}.png"
        im.save(dest)
        out[key] = os.path.abspath(dest)
    return out


def mouth_levels(samples):
    hop = SR // STATE_FPS
    n = len(samples) // hop
    if n < 1:
        return np.zeros(1, dtype=int)
    frames = samples[: n * hop].reshape(n, hop)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    ref = max(float(np.percentile(rms, 95)), 1e-4)
    x = rms / ref
    levels = np.zeros(n, dtype=int)
    levels[x > 0.20] = 1
    levels[x > 0.50] = 2
    smooth = levels.copy()
    for i in range(n):
        window = sorted(levels[max(0, i - 1): i + 2])
        smooth[i] = window[len(window) // 2]
    return smooth


def frame_states(levels, can_blink):
    names = ["closed", "mid", "open"]
    states = [names[int(v)] for v in levels]
    n = len(states)
    if can_blink:
        i = random.randint(40, 90)
        while i < n:
            limit = min(i + 25, n)
            k = i
            while k < limit and states[k] != "closed":
                k += 1
            if k < limit:
                for j in range(k, min(k + 4, n)):
                    if states[j] == "closed":
                        states[j] = "blink"
            i += random.randint(60, 120)
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
    states = frame_states(mouth_levels(samples), "blink" in paths)
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