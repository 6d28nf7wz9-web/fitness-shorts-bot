import json
import os
import subprocess

from clips import CLIPS_DIR, RAW_DIR, choose_clip, download, process

PART_SECONDS = float(os.getenv("PART_SECONDS", "2.6"))
MAX_PARTS = 4


def main():
    with open("output/script.json", encoding="utf-8") as f:
        script = json.load(f)
    with open("output/audio_info.json", encoding="utf-8") as f:
        audio = json.load(f)
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)

    used_ids, info = set(), []
    for i, scene in enumerate(script["scenes"], 1):
        seconds = audio[i - 1]["seconds"]
        keywords = [k.strip() for k in str(scene["keyword"]).split("|") if k.strip()]
        if not keywords:
            keywords = ["gym workout"]
        parts = max(1, min(MAX_PARTS, round(seconds / PART_SECONDS)))
        each = seconds / parts
        print(f"\nScene {i} ({seconds}s, {parts} cuts)")

        part_files, ids = [], []
        for p in range(parts):
            kw = keywords[p % len(keywords)]
            query, hit, url, portrait = choose_clip(kw, each, used_ids)
            used_ids.add(hit.get("id"))
            raw = f"{RAW_DIR}/s{i}_{p}.mp4"
            part = f"{CLIPS_DIR}/s{i}_{p}.mp4"
            download(url, raw)
            process(raw, part, each, portrait)
            os.remove(raw)
            part_files.append(part)
            ids.append(hit.get("id"))
            kind = "vertical" if portrait else "wide (blur-fit)"
            print(f"  cut {p + 1}: '{query}' -> {kind}, id {hit.get('id')}")

        out = f"{CLIPS_DIR}/scene_{i}.mp4"
        if len(part_files) == 1:
            os.replace(part_files[0], out)
        else:
            list_path = f"{CLIPS_DIR}/list_{i}.txt"
            with open(list_path, "w", encoding="utf-8") as f:
                for pf in part_files:
                    f.write(f"file '{os.path.abspath(pf)}'\n")
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                 "-i", list_path, "-c", "copy", out],
                check=True,
            )
            for pf in part_files:
                os.remove(pf)
            os.remove(list_path)
        info.append({"scene": i, "file": out, "seconds": seconds, "pixabay_ids": ids})

    with open("output/clips_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    print("\nSaved to output/clips_info.json")


main()