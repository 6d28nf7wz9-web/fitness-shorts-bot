import json
import os
import random
import re
import subprocess

W, H = 1080, 1920
ASS_FILE = "output/captions.ass"
FINAL = "output/final.mp4"
MUSIC_VOLUME = 0.12
FONT = "DejaVu Sans"

HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{FONT},96,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,8,2,2,60,60,560,1

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
    return re.sub(r"[{}\\]", "", text).upper()


def chunk_words(text):
    words = text.replace("\n", " ").split()
    chunks, current = [], []
    for w in words:
        current.append(w)
        if len(current) == 2 or len(w) > 8:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


def build_captions(script, audio):
    lines = [HEADER]
    pop = "{\\fscx85\\fscy85\\t(0,90,\\fscx100\\fscy100)}"
    yellow = "{\\c&H00FFFF&}"
    scene_start = 0.0
    k = 0
    for scene, a in zip(script["scenes"], audio):
        duration = a["seconds"]
        chunks = chunk_words(clean(scene["narration"]))
        weights = [len(c) + 2 for c in chunks]
        total_w = sum(weights)
        t = scene_start
        for c, w in zip(chunks, weights):
            d = duration * w / total_w
            color = yellow if k % 3 == 2 else ""
            lines.append(
                f"Dialogue: 0,{ass_time(t)},{ass_time(t + d)},Cap,,0,0,0,,{pop}{color}{c}"
            )
            t += d
            k += 1
        scene_start += duration
    return "\n".join(lines) + "\n"


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)
    with open("output/audio_info.json", encoding="utf-8") as f:
        audio = json.load(f)

    n = len(audio)
    secs = [a["seconds"] for a in audio]
    total = round(sum(secs), 2)

    music_files = [
        f"music/{name}" for name in os.listdir("music")
        if name.lower().endswith((".mp3", ".wav", ".m4a"))
    ]
    if not music_files:
        raise SystemExit("No music files found in the music/ folder")
    music = random.choice(music_files)
    print("Music:", music)

    with open(ASS_FILE, "w", encoding="utf-8") as f:
        f.write(build_captions(script, audio))

    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for i in range(1, n + 1):
        cmd += ["-i", f"output/clips/scene_{i}.mp4"]
    for a in audio:
        cmd += ["-i", a["file"]]
    cmd += ["-stream_loop", "-1", "-i", music]

    parts = []
    parts.append("".join(f"[{i}:v]" for i in range(n)) + f"concat=n={n}:v=1:a=0[vc]")
    parts.append(f"[vc]ass={ASS_FILE}[v]")

    for i in range(n):
        parts.append(
            f"[{n + i}:a]aresample=44100,aformat=channel_layouts=stereo,"
            f"apad=whole_dur={secs[i]},atrim=0:{secs[i]},asetpts=PTS-STARTPTS[a{i}]"
        )
    parts.append("".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[voice]")

    fade_start = max(total - 1.2, 0)
    parts.append(
        f"[{2 * n}:a]atrim=0:{total},asetpts=PTS-STARTPTS,aresample=44100,"
        f"aformat=channel_layouts=stereo,volume={MUSIC_VOLUME},"
        f"afade=t=in:d=0.5,afade=t=out:st={fade_start}:d=1.2[mus]"
    )
    parts.append(
        "[voice][mus]amix=inputs=2:duration=first:dropout_transition=0,"
        "volume=2,alimiter=limit=0.95[aout]"
    )

    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "[v]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-t", str(total),
        FINAL,
    ]

    print("Rendering video (1-2 minutes)...")
    subprocess.run(cmd, check=True)

    size_mb = os.path.getsize(FINAL) / 1e6
    print(f"\nDone: {FINAL}  ({total}s, {size_mb:.1f} MB)")
    if total > 58:
        print("Warning: longer than 58 seconds. Shorts must be under 60.")


main()