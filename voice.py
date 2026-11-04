
import asyncio
import json
import os
import subprocess

import edge_tts

VOICE = os.getenv("TTS_VOICE", "en-US-AndrewNeural")
FALLBACK_VOICE = os.getenv("TTS_FALLBACK_VOICE", "en-US-GuyNeural")

RATE = "+8%"
OUT_DIR = "output/audio"

MAX_RETRIES = 3
RETRY_DELAY = 5
REQUEST_TIMEOUT = 45


def get_duration(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    duration = float(result.stdout.strip())

    if duration <= 0:
        raise RuntimeError("Invalid audio duration")

    return duration


async def try_voice(text, path, voice):
    temp_path = path + ".tmp.mp3"

    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=RATE,
        )

        await asyncio.wait_for(
            communicate.save(temp_path),
            timeout=REQUEST_TIMEOUT,
        )

        if not os.path.exists(temp_path):
            raise RuntimeError("No audio file was created")

        if os.path.getsize(temp_path) < 1000:
            raise RuntimeError("Audio file is too small")

        # Validate the MP3 file and its duration
        get_duration(temp_path)

        # Replace the final file only after validation
        os.replace(temp_path, path)

        return True

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


async def make_audio(text, path):
    voices = [VOICE]

    if FALLBACK_VOICE != VOICE:
        voices.append(FALLBACK_VOICE)

    last_error = None

    for voice in voices:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(
                    f"Trying voice {voice} "
                    f"(attempt {attempt}/{MAX_RETRIES})"
                )

                await try_voice(text, path, voice)

                print(f"Audio created successfully using {voice}")
                return voice

            except Exception as e:
                last_error = e

                print(
                    f"[{voice} - attempt {attempt}] "
                    f"Failed: {str(e)[:200]}"
                )

                if attempt < MAX_RETRIES:
                    delay = RETRY_DELAY * attempt
                    print(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)

    raise RuntimeError(
        f"Could not create audio for: {text[:40]}. "
        f"Last error: {last_error}"
    )


async def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)

    os.makedirs(OUT_DIR, exist_ok=True)

    info = []

    for i, scene in enumerate(script["scenes"], 1):
        narration = scene.get("narration", "").strip()

        if not narration:
            raise RuntimeError(f"Scene {i} has empty narration")

        path = f"{OUT_DIR}/scene_{i}.mp3"

        used_voice = await make_audio(narration, path)

        seconds = round(get_duration(path), 2)

        info.append({
            "scene": i,
            "file": path,
            "seconds": seconds,
            "voice": used_voice,
        })

        print(f"Scene {i}: {seconds}s")

    total = round(sum(item["seconds"] for item in info), 1)

    with open("output/audio_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)

    print("\nVoice generation completed!")
    print(f"Primary voice: {VOICE}")
    print(f"Fallback voice: {FALLBACK_VOICE}")
    print(f"Total narration: {total}s")

    if total > 55:
        print("Warning: over 55 seconds. Shorts work best under 60.")

    print("Saved to output/audio_info.json")


if __name__ == "__main__":
    asyncio.run(main())