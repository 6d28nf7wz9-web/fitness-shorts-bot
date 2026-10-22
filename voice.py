import asyncio
import json
import os
import subprocess

import edge_tts

VOICE = os.getenv("TTS_VOICE", "en-US-AndrewNeural")
RATE = "+8%"  # slightly faster = more energetic
OUT_DIR = "output/audio"


def get_duration(path):
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


async def make_audio(text, path, retries=3):
    for attempt in range(1, retries + 1):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
            if os.path.getsize(path) > 1000:
                return
            print(f"[attempt {attempt}] audio file too small, retrying")
        except Exception as e:
            print(f"[attempt {attempt}] voice failed: {str(e)[:200]}")
        await asyncio.sleep(3)
    raise RuntimeError(f"Could not create audio for: {text[:40]}")


async def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)

    os.makedirs(OUT_DIR, exist_ok=True)
    info = []
    for i, scene in enumerate(script["scenes"], 1):
        path = f"{OUT_DIR}/scene_{i}.mp3"
        await make_audio(scene["narration"], path)
        seconds = round(get_duration(path), 2)
        info.append({"scene": i, "file": path, "seconds": seconds})
        print(f"Scene {i}: {seconds}s")

    total = round(sum(item["seconds"] for item in info), 1)
    with open("output/audio_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)

    print(f"\nVoice: {VOICE}")
    print(f"Total narration: {total}s")
    if total > 55:
        print("Warning: over 55 seconds. Shorts work best under 60.")
    print("Saved to output/audio_info.json")


asyncio.run(main())