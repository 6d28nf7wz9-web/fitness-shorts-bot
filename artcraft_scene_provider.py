"""Optional ArtCraft video-generation fallback for unmatched B-roll.

ArtCraft is an additive source, never a replacement for verified free stock.
Generation is disabled unless ARTCRAFT_ENABLED=1, an API key is configured,
and ARTCRAFT_MAX_GENERATIONS is explicitly set above zero. This prevents
surprise paid generation and keeps Pixabay/Coverr as the default path.
"""
import json
import math
import os
import subprocess
import time
import uuid
from pathlib import Path

import requests

BASE_URL = os.getenv("ARTCRAFT_BASE_URL", "https://api.storyteller.ai").rstrip("/")
TERMINAL_FAILURES = {
    "complete_failure", "dead", "cancelled_by_user", "cancelled_by_system",
}
PENDING_STATES = {"pending", "started", "attempt_failed"}


def is_enabled():
    """Require explicit opt-in, credentials, and a non-zero per-run budget."""
    return (
        os.getenv("ARTCRAFT_ENABLED", "0").lower() in {"1", "true", "yes"}
        and bool(os.getenv("ARTCRAFT_API_KEY", "").strip())
        and int(os.getenv("ARTCRAFT_MAX_GENERATIONS", "0")) > 0
    )


def _prompt(scene, sentence_context):
    title = str(scene.get("visual_title") or "").strip()
    subtitle = str(scene.get("visual_subtitle") or "").strip()
    narration = str(sentence_context or scene.get("narration") or "").strip()
    topic = " | ".join(part for part in (title, subtitle, narration) if part)
    return (
        "Create a photorealistic, scientifically plausible fitness education "
        "B-roll shot for this exact spoken beat: " + topic + ". "
        "Show only visuals that directly illustrate this idea. Vertical 9:16 "
        "composition, clean premium documentary lighting, clear subject, "
        "natural human anatomy and realistic movement. No text, captions, "
        "logos, watermarks, UI, labels, diagrams, or unrelated scenery. "
        "One coherent continuous shot with restrained camera motion."
    )


def _request_headers():
    return {
        "Authorization": f"Bearer {os.environ['ARTCRAFT_API_KEY'].strip()}",
        "Content-Type": "application/json",
    }


def _submit(scene, sentence_context, seconds):
    duration = max(5, min(10, int(math.ceil(float(seconds)))))
    payload = {
        "model": os.getenv("ARTCRAFT_VIDEO_MODEL", "seedance_2p0"),
        "prompt": _prompt(scene, sentence_context),
        "duration_seconds": duration,
        "aspect_ratio": "tall_nine_by_sixteen",
        "resolution": os.getenv("ARTCRAFT_VIDEO_RESOLUTION", "seven_twenty_p"),
        "generate_audio": False,
        "idempotency_token": str(uuid.uuid4()),
    }
    response = requests.post(
        f"{BASE_URL}/v1/omni_api/generate/video",
        headers=_request_headers(), json=payload, timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    token = data.get("inference_job_token")
    if not data.get("success") or not token:
        raise RuntimeError(f"ArtCraft did not return a job token: {data}")
    return token


def _wait_for_result(token):
    max_wait = int(os.getenv("ARTCRAFT_MAX_WAIT_SECONDS", "240"))
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        response = requests.get(
            f"{BASE_URL}/v1/omni_api/job_status/job/{token}",
            headers=_request_headers(), timeout=30,
        )
        response.raise_for_status()
        state = response.json().get("state") or {}
        status_info = state.get("status") or {}
        status = status_info.get("status")
        print(
            f"  ArtCraft job {token}: {status} "
            f"({status_info.get('progress_percentage', 0)}%)"
        )
        if status == "complete_success":
            url = ((state.get("maybe_result") or {}).get("media_links") or {}).get("cdn_url")
            if not url:
                raise RuntimeError("ArtCraft completed without a media URL")
            return url
        if status in TERMINAL_FAILURES:
            raise RuntimeError(f"ArtCraft generation ended: {status}")
        if status not in PENDING_STATES:
            raise RuntimeError(f"Unknown ArtCraft job state: {status}")
        time.sleep(5)
    raise TimeoutError(f"ArtCraft job timed out after {max_wait}s")


def _download_and_validate(url, destination):
    response = requests.get(url, stream=True, timeout=90)
    response.raise_for_status()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".part")
    try:
        with temp.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    handle.write(chunk)
        if not temp.is_file() or temp.stat().st_size < 10_000:
            raise RuntimeError("ArtCraft returned an empty or undersized video")
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_type,width,height",
             "-of", "json", str(temp)],
            check=True, capture_output=True, text=True,
        )
        streams = json.loads(probe.stdout).get("streams", [])
        if not streams or not streams[0].get("width") or not streams[0].get("height"):
            raise RuntimeError("ArtCraft output has no valid video stream")
        temp.replace(destination)
    finally:
        if temp.exists():
            temp.unlink()


def generate_fallback(scene, sentence_context, seconds, output_path, run_state):
    """Generate one optional cut; return None when disabled or on safe fallback."""
    if not is_enabled():
        return None
    limit = int(os.getenv("ARTCRAFT_MAX_GENERATIONS", "0"))
    if run_state.get("generated", 0) >= limit:
        print("  ArtCraft generation budget exhausted; keeping science fallback.")
        return None

    try:
        print("  No verified stock match; requesting an ArtCraft scene-specific cut.")
        token = _submit(scene, sentence_context, seconds)
        url = _wait_for_result(token)
        _download_and_validate(url, output_path)
        run_state["generated"] = run_state.get("generated", 0) + 1
        return str(output_path)
    except (requests.RequestException, RuntimeError, TimeoutError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"  ArtCraft fallback unavailable: {str(exc)[:240]}")
        return None
