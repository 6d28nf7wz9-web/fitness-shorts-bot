"""Optional Wan enhancement for a selected Coverr/Pixabay stock shot.

The stock clip remains the fallback and visual source. This feature is inert unless
both I2V_ENABLED=1 and WAN_STOCK_ASSIST=1 are explicitly set by the workflow owner.
At most one selected stock segment is animated per Short.
"""
import os
import subprocess
from pathlib import Path

from image_to_video import generate_video, is_enabled

_used_this_run = False


def try_animate_stock(raw_stock_path, scene, duration, destination):
    global _used_this_run
    if _used_this_run:
        return None
    if not is_enabled() or os.getenv("I2V_PROVIDER", "wan").strip().lower() != "wan":
        return None
    if os.getenv("WAN_STOCK_ASSIST", "0").strip().lower() not in ("1", "true", "yes", "on"):
        return None
    if not os.getenv("WAN_API_KEY", "").strip():
        print("  Wan stock assist skipped: WAN_API_KEY is not configured")
        return None

    _used_this_run = True
    still = Path("output/raw/wan_stock_reference.jpg")
    generated = Path("output/raw/wan_stock_assist.mp4")
    still.parent.mkdir(parents=True, exist_ok=True)
    still.unlink(missing_ok=True)
    generated.unlink(missing_ok=True)
    try:
        seek = max(0.0, min(float(duration) * 0.35, 1.5))
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", str(seek),
            "-i", str(raw_stock_path), "-frames:v", "1",
            "-vf", "scale=768:-2", "-q:v", "3", str(still),
        ], check=True)
        if not still.is_file() or still.stat().st_size < 1000:
            raise RuntimeError("Could not extract a reference frame from the stock clip")

        prompt = (
            "Animate this exact real-world fitness/nutrition stock-footage shot. "
            "Preserve the same people, objects, clothing, location and action. "
            "Add only subtle natural movement and a gentle cinematic camera move. "
            "Photorealistic live-action footage, natural anatomy and physics. "
            "No CGI, no 3D render, no anatomical overlays, no text, no logos, "
            "no new people or objects. Scene context: "
            + str(scene.get("narration") or scene.get("keyword") or "")[:900]
        )
        print("  Wan stock assist: animating one frame from the selected stock clip")
        generate_video(still, prompt, str(generated), provider="wan")
        if not generated.is_file() or generated.stat().st_size < 10_000:
            raise RuntimeError("Wan returned no valid video")
        return str(generated)
    except Exception as exc:
        print(f"  Wan stock assist failed; keeping original stock footage: {str(exc)[:220]}")
        generated.unlink(missing_ok=True)
        return None
    finally:
        still.unlink(missing_ok=True)
