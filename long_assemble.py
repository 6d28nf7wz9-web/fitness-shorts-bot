import json
import os
import random
import re
import subprocess

OUT_DIR = "output/long"
ASS_FILE = f"{OUT_DIR}/captions.ass"
FINAL = f"{OUT_DIR}/final_long.mp4"
W, H = 1920, 1080
FONT = "DejaVu Sans"
MUSIC_VOLUME = 0.07

HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT},52,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,2,2,100,520,70,1
Style: Title,{FONT},60,&H00FFFFFF,&H000000FF,&H99000000,&H00000000,-1,0,0,0,100,100,0,0,3,16,0,7,90,90,80,1

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


def mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def make_lines(words, max_chars=38, max_gap=0.6, max_words=7):
    lines, cur = [], []
    for w in words:
        if cur:
            gap = w["s"] - cur[-1]["e"]
            length = sum(len(x["w"]) + 1 for x in cur) + len(w["w"])
            ends = cur[-1]["w"][-1] in ".?!"
            if gap > max_gap or length > max_chars or ends or len(cur) >= max_words:
                lines.append(cur)
                cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def build_ass(tl):
    out = [HEADER]
    lines = make_lines(tl["words"])
    for i, line in enumerate(lines):
        start = line[0]["s"]
        end = line[-1]["e"]
        nxt = lines[i + 1][0]["s"] if i + 1 < len(lines) else end + 0.5
        end = max(min(nxt, end + 0.25), start + 0.4)
        text = clean(" ".join(w["w"] for w in line))
        size = min(52, int(1250 / (max(len(text), 1) * 0.62)))
        out.append(
            f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Cap,,0,0,0,,{{\\fs{size}}}{text}"
        )
    for sec in tl["sections"]:
        end = min(sec["start"] + 4.5, sec["end"])
        out.append(
            f"Dialogue: 1,{ass_time(sec['start'])},{ass_time(end)},Title,,0,0,0,,"
            f"{{\\fad(300,300)}}{clean(sec['heading'])}"
        )
    return "\n".join(out) + "\n"


def build_chapters(tl):
    chapters = []
    for s in tl["sections"]:
        if not chapters or s["start"] - chapters[-1][0] >= 10:
            chapters.append((s["start"], s["heading"]))
    if len(chapters) > 1 and tl["duration"] - chapters[-1][0] < 10:
        chapters.pop()
    if len(chapters) < 3:
        return ""
    chapters[0] = (0.0, chapters[0][1])
    return "\n".join(f"{mmss(t)} {h}" for t, h in chapters)


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
        f"music/{n}" for n in os.listdir("music")
        if n.lower().endswith((".mp3", ".wav", ".m4a"))
    ]
    if not music_files:
        raise SystemExit("No music files in the music/ folder")
    music = random.choice(music_files)
    print("Music:", music)

    with open(ASS_FILE, "w", encoding="utf-8") as f:
        f.write(build_ass(tl))

    list_path = f"{OUT_DIR}/concat.txt"
    with open(list_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(f"file '{os.path.abspath(c['file'])}'\n")

    dur = tl["duration"]
    t0 = tl["audio_start"]
    fade_start = max(dur - 2.0, 0)
    fc = ";".join([
        f"[0:v]tpad=stop_mode=clone:stop_duration=3,ass={ASS_FILE}[v]",
        f"[1:a]atrim=start={t0},asetpts=PTS-STARTPTS,aresample=44100,"
        f"aformat=channel_layouts=stereo,highpass=f=80,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100,apad=whole_dur={dur}[voice]",
        f"[2:a]atrim=0:{dur},asetpts=PTS-STARTPTS,aresample=44100,"
        f"aformat=channel_layouts=stereo,volume={MUSIC_VOLUME},"
        f"afade=t=in:d=1,afade=t=out:st={fade_start}:d=2[mus]",
        "[voice][mus]amix=inputs=2:duration=first:dropout_transition=0,"
        "volume=2,alimiter=limit=0.95[aout]",
    ])
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", list_path,
        "-i", tl["recording"],
        "-stream_loop", "-1", "-i", music,
        "-filter_complex", fc,
        "-map", "[v]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-t", f"{dur}",
        FINAL,
    ]
    print(f"Rendering {mmss(dur)} of 1080p video (a few minutes)...")
    subprocess.run(cmd, check=True)

    chapters = build_chapters(tl)
    parts = queue["description"].split("\n\n")
    if chapters:
        parts.insert(1, "Chapters:\n" + chapters)
    meta = {
        "id": tl["id"],
        "title": queue["title"],
        "description": "\n\n".join(parts),
        "tags": [str(h).lstrip("#") for h in queue.get("hashtags", [])][:10],
    }
    with open(f"{OUT_DIR}/meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    size = os.path.getsize(FINAL) / 1e6
    print(f"\nDone: {FINAL}  ({mmss(dur)}, {size:.0f} MB)")
    print("Chapters:\n" + (chapters or "(none, too few long sections)"))


main()