import json
import os
import random
import re
import subprocess

from gen_script import DISCLAIMER
from yt import upload_video
from avatar import add_avatar

OUT_DIR = "output/long"
SHORT_DIR = f"{OUT_DIR}/shorts"
W, H, FPS = 1080, 1920, 30
FONT = "DejaVu Sans"
SHORTS_PER_LONG = int(os.getenv("SHORTS_PER_LONG", "2"))
MIN_LEN, MAX_LEN = 18.0, 58.0
MUSIC_VOLUME = 0.10
PRIVACY = os.getenv("UPLOAD_PRIVACY", "private")

MAX_TEXT_WIDTH = 840
BASE_SIZE = 92
MIN_SIZE = 50
CHAR_WIDTH = 0.80
MAX_CHARS = 16

HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT},{BASE_SIZE},&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,8,2,2,120,120,700,1
Style: Head,{FONT},62,&H00FFFFFF,&H000000FF,&H99000000,&H00000000,-1,0,0,0,100,100,0,0,3,18,0,8,100,100,230,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ass_time(t):
    cs = int(round(max(t, 0) * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def clean(text):
    return re.sub(r"[{}\\]", "", text)


def group_words(words):
    groups, cur = [], []
    for w in words:
        text = clean(w["w"]).upper()
        if not cur:
            cur = [(text, w)]
            continue
        chars = sum(len(t) + 1 for t, _ in cur) + len(text)
        if len(cur) < 2 and chars <= MAX_CHARS:
            cur.append((text, w))
        else:
            groups.append(cur)
            cur = [(text, w)]
    if cur:
        groups.append(cur)
    return groups


def fit_size(text):
    size = int(MAX_TEXT_WIDTH / (max(len(text), 1) * CHAR_WIDTH))
    return max(MIN_SIZE, min(BASE_SIZE, size))


def build_ass(words, sec, dur):
    pop = "{\\fscx85\\fscy85\\t(0,90,\\fscx100\\fscy100)}"
    yellow = "{\\c&H00FFFF&}"
    out = [HEADER]
    sec_words = [w for w in words if sec["start"] - 0.05 <= w["s"] < sec["end"]]
    groups = group_words(sec_words)
    for i, g in enumerate(groups):
        text = " ".join(t for t, _ in g)
        start = max(g[0][1]["s"] - sec["start"], 0)
        nxt = (groups[i + 1][0][1]["s"] - sec["start"]) if i + 1 < len(groups) else dur
        end = min(nxt, g[-1][1]["e"] - sec["start"] + 0.3, start + 1.6)
        end = max(end, start + 0.2)
        color = yellow if i % 3 == 2 else ""
        out.append(
            f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,"
            f"{pop}{color}{{\\fs{fit_size(text)}}}{text}"
        )
    out.append(
        f"Dialogue: 1,{ass_time(0)},{ass_time(dur)},Head,,0,0,0,,{clean(sec['heading']).upper()}"
    )
    return "\n".join(out) + "\n"


def pick_sections(tl, n):
    total = len(tl["sections"])

    def ok(i):
        s = tl["sections"][i - 1]
        return MIN_LEN <= s["end"] - s["start"] <= MAX_LEN

    cands = [i for i in range(2, total) if ok(i)]
    if not cands:
        cands = [i for i in range(1, total + 1) if ok(i)]
    if len(cands) <= n:
        return cands
    step = len(cands) / n
    return [cands[int(k * step)] for k in range(n)]


def render(tl, chunks, si, n, music):
    sec = tl["sections"][si - 1]
    dur = round(sec["end"] - sec["start"], 2)
    files = [c["file"] for c in chunks if c["section"] == si]
    if not files:
        raise RuntimeError(f"No clips found for section {si}")

    list_path = f"{SHORT_DIR}/list_{n}.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for p in files:
            f.write(f"file '{os.path.abspath(p)}'\n")
    ass_path = f"{SHORT_DIR}/caps_{n}.ass"
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(build_ass(tl["words"], sec, dur))

    out = f"{SHORT_DIR}/short_{n}.mp4"
    a_start = tl["audio_start"] + sec["start"]
    fade_start = max(dur - 1.2, 0)
    fc = ";".join([
        "[0:v]split[a][b]",
        f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:5,eq=brightness=0.08:saturation=0.92[bg]",
        "[b]crop='min(iw,ih)':'min(iw,ih)',scale=1080:1080[fg]",
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2-80,tpad=stop_mode=clone:stop_duration=2,ass={ass_path}[v]",
        f"[1:a]aresample=44100,aformat=channel_layouts=stereo,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100,apad=whole_dur={dur}[voice]",
        f"[2:a]atrim=0:{dur},asetpts=PTS-STARTPTS,aresample=44100,"
        f"aformat=channel_layouts=stereo,volume={MUSIC_VOLUME},"
        f"afade=t=in:d=0.5,afade=t=out:st={fade_start:.2f}:d=1.2[mus]",
        "[voice][mus]amix=inputs=2:duration=first:dropout_transition=0,"
        "volume=2,alimiter=limit=0.95[aout]",
    ])
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", list_path,
        "-ss", f"{a_start:.2f}", "-t", f"{dur}", "-i", tl["recording"],
        "-stream_loop", "-1", "-i", music,
        "-filter_complex", fc,
        "-map", "[v]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        "-t", f"{dur}", out,
    ]
    subprocess.run(cmd, check=True)
    return out, dur


def main():
    with open(f"{OUT_DIR}/timeline.json", encoding="utf-8") as f:
        tl = json.load(f)
    with open(f"{OUT_DIR}/chunks.json", encoding="utf-8") as f:
        chunks = json.load(f)
    with open(f"{OUT_DIR}/job.json", encoding="utf-8") as f:
        job = json.load(f)
    with open(job["queue_file"], encoding="utf-8") as f:
        queue = json.load(f)

    music_files = [
        f"music/{x}" for x in os.listdir("music")
        if x.lower().endswith((".mp3", ".wav", ".m4a"))
    ]
    if not music_files:
        raise SystemExit("No music files in the music/ folder")
    os.makedirs(SHORT_DIR, exist_ok=True)

    picks = pick_sections(tl, SHORTS_PER_LONG)
    print("Sections chosen for Shorts:", picks or "none (no section is 18-58 seconds)")

    tags = [str(h).lstrip("#") for h in queue.get("hashtags", [])][:9] + ["Shorts"]
    tag_line = " ".join("#" + t.replace(" ", "") for t in tags)
    link = ""
    if queue.get("youtube_id"):
        link = f"\n\nFull video: https://www.youtube.com/watch?v={queue['youtube_id']}"

    failed = 0
    for n, si in enumerate(picks, 1):
        sec = tl["sections"][si - 1]
        out, dur = render(tl, chunks, si, n, random.choice(music_files))
        add_avatar(out, tl["recording"], tl["audio_start"] + sec["start"], dur, "short")
        print(f"Rendered {out} ({dur:.0f}s): {sec['heading']}")
        if os.getenv("SKIP_UPLOAD", "").strip().lower() in {"1", "true", "yes"}:
            print("SKIP_UPLOAD is enabled: Short remains local.")
            continue
        description = (
            f"{sec['heading']}. Part of: {queue['title']}{link}\n\n{tag_line}\n\n"
            f"{DISCLAIMER}\n\nVideo clips and music: Pixabay."
        )
        try:
            vid = upload_video(out, sec["heading"], description, tags, "26", PRIVACY)
            print("Uploaded: https://www.youtube.com/watch?v=" + vid)
        except Exception as e:
            failed += 1
            print(f"Upload failed: {str(e)[:300]}")

    if picks and failed == len(picks):
        raise SystemExit("All Short uploads failed")



if __name__ == "__main__":
    main()
