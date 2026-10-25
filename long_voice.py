import asyncio
import json
import os
import subprocess

import edge_tts

VOICE = os.getenv("TTS_VOICE", "en-US-AndrewNeural")
RATE = os.getenv("TTS_RATE", "+4%")
OUT = "output/long/ai_voice.mp3"


def get_id():
    vid = os.getenv("LONG_ID")
    if vid:
        return vid
    with open("output/long_id.txt") as f:
        return f.read().strip()


def duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


async def make_audio(text, retries=3):
    for attempt in range(1, retries + 1):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(OUT)
            if os.path.getsize(OUT) > 10000:
                return
            print(f"[attempt {attempt}] audio too small, retrying")
        except Exception as e:
            print(f"[attempt {attempt}] voice failed: {str(e)[:200]}")
        await asyncio.sleep(5)
    raise RuntimeError("Could not create the voiceover")


def main():
    vid = get_id()
    with open(f"queue/{vid}.json", encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs("output/long", exist_ok=True)
    text = " ".join(s["narration"].strip() for s in data["sections"])
    print(f"Voicing {vid}: {len(text.split())} words with {VOICE}")
    asyncio.run(make_audio(text))
    secs = duration(OUT)
    print(f"Voiceover: {int(secs // 60)}:{int(secs % 60):02d}  ->  {OUT}")


main()