import asyncio
import os
import shutil
from pathlib import Path

import yaml
from moviepy import VideoFileClip
from pipelines.script2video_pipeline import Script2VideoPipeline


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "configs" / "fitfuel_eval.yaml"
SCRIPT_PATH = ROOT / "fitfuel_test_script.txt"
OUTPUT_DIR = ROOT / "artifacts"
WORK_DIR = ROOT / ".working_dir" / "fitfuel_eval"


def prepare_config():
    config = yaml.safe_load((ROOT / "configs" / "script2video.yaml").read_text(encoding="utf-8"))
    config["chat_model"]["init_args"].update({
        "model": "gemini-3.5-flash-lite",
        "model_provider": "openai",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": os.environ["GEMINI_API_KEY"],
    })
    config["image_generator"]["init_args"]["api_key"] = os.environ["GOOGLE_API_KEY"]
    config["video_generator"]["init_args"]["api_key"] = os.environ["GOOGLE_API_KEY"]
    config["image_selection"]["num_candidates"] = 1
    config["working_dir"] = str(WORK_DIR)
    CONFIG_PATH.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


async def main():
    prepare_config()
    script = SCRIPT_PATH.read_text(encoding="utf-8").strip()
    requirement = """
Create a short, coherent FitFuel fitness-science explainer with NO MORE THAN 3 shots.
Visual identity: premium cinematic 3D anatomical fitness explainer, realistic adult human anatomy,
clearly visible muscle fibers and muscle groups only when relevant, physically plausible proportions,
clean studio lighting, deep neutral background with restrained red accents.
Narration-to-visual matching is mandatory: protein and muscle repair must be shown directly;
then show a clear, realistic protein-food example (grilled chicken, tofu, or eggs);
finish with a human muscle-recovery / muscle-preservation visual.
Keep the same adult athletic human subject and consistent anatomical design across shots.
No unrelated gym montage, no text, no labels, no logos, no watermark, no subtitles.
Compose the main subject centrally with safe margins for a vertical 9:16 social video.
"""
    pipeline = Script2VideoPipeline.init_from_config(str(CONFIG_PATH))
    result = await pipeline(
        script=script,
        user_requirement=requirement,
        style="Cinematic 3D anatomical fitness explainer",
    )
    output = Path(result)
    if not output.is_file():
        raise FileNotFoundError(f"ViMax returned no final MP4 at: {output}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT_DIR / "FitFuel_ViMax_preview.mp4"
    shutil.copy2(output, destination)
    print(f"FITFUEL_PREVIEW={destination}")
    print(f"FITFUEL_PREVIEW_BYTES={destination.stat().st_size}")
    with VideoFileClip(str(destination)) as clip:
        print(f"FITFUEL_PREVIEW_SIZE={clip.size[0]}x{clip.size[1]}")
        print(f"FITFUEL_PREVIEW_DURATION={clip.duration:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
