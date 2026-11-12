"""Cost-guarded image-to-video adapters for FitFuel.

This module is deliberately inert unless I2V_ENABLED=1. It never tries a
second paid provider after a failure: the caller should fall back to stock.
Input stills are expected at output/i2v_inputs/scene_N.(png|jpg|jpeg).
"""
import base64
import mimetypes
import os
import time
from pathlib import Path

import requests

OUTPUT_DIR = Path("output/i2v")
INPUT_DIR = Path("output/i2v_inputs")
MAX_IMAGE_BYTES = 5 * 1024 * 1024
POLL_SECONDS = 5
MAX_WAIT_SECONDS = 900


class I2VError(RuntimeError):
    """Image-to-video request or result failed."""


class I2VDisabled(I2VError):
    """Generation was not explicitly enabled."""


def is_enabled():
    return os.getenv("I2V_ENABLED", "0").strip().lower() in ("1", "true", "yes", "on")


def configured_provider():
    provider = os.getenv("I2V_PROVIDER", "kling").strip().lower()
    if provider not in ("kling", "runway", "wan"):
        raise I2VError("I2V_PROVIDER must be kling, runway, or wan")
    return provider


def max_scenes():
    try:
        value = int(os.getenv("I2V_MAX_SCENES", "2"))
    except ValueError:
        value = 2
    return max(0, min(value, 2))


def scene_image_path(scene_index):
    for suffix in (".png", ".jpg", ".jpeg"):
        path = INPUT_DIR / f"scene_{scene_index}{suffix}"
        if path.is_file():
            return path
    return None


def scene_is_eligible(scene_index):
    return (
        is_enabled()
        and 1 <= int(scene_index) <= max_scenes()
        and scene_image_path(scene_index) is not None
    )


def _token(provider):
    names = {
        "kling": "KLING_API_KEY",
        "runway": "RUNWAY_API_KEY",
        "wan": "WAN_API_KEY",
    }
    token = os.getenv(names[provider], "").strip()
    if not token:
        raise I2VError(f"{names[provider]} is not configured")
    return token


def _image_data_uri(path):
    path = Path(path)
    if not path.is_file():
        raise I2VError(f"Input image not found: {path}")
    size = path.stat().st_size
    if size <= 0 or size > MAX_IMAGE_BYTES:
        raise I2VError("Input image must be between 1 byte and 5 MB")
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    if mime not in ("image/png", "image/jpeg"):
        raise I2VError("Only PNG and JPEG scene images are supported")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _download(url, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=(20, 180)) as response:
        response.raise_for_status()
        with destination.open("wb") as handle:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    handle.write(chunk)
    if not destination.is_file() or destination.stat().st_size < 10_000:
        destination.unlink(missing_ok=True)
        raise I2VError("Provider returned an empty or invalid video file")
    return str(destination)


def _poll_kling(token, task_id):
    deadline = time.monotonic() + MAX_WAIT_SECONDS
    url = "https://api-singapore.klingai.com/tasks"
    while time.monotonic() < deadline:
        response = requests.get(
            url,
            params={"task_ids": task_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("code") not in (None, 0):
            raise I2VError(f"Kling task query failed: {payload.get('message', 'unknown error')}")
        data = payload.get("data") or []
        if isinstance(data, dict):
            data = data.get("result") or [data]
        task = next((item for item in data if item.get("id") == task_id), None)
        if task:
            status = str(task.get("status", "")).lower()
            if status == "succeeded":
                outputs = task.get("outputs") or []
                video = next((item.get("url") for item in outputs if item.get("type") == "video" and item.get("url")), None)
                if not video:
                    raise I2VError("Kling completed without a video URL")
                return video
            if status == "failed":
                raise I2VError(f"Kling generation failed: {task.get('message', 'no reason supplied')}")
        time.sleep(POLL_SECONDS)
    raise I2VError("Kling generation timed out while polling")


def _generate_kling(token, image_uri, prompt):
    create_url = "https://api-singapore.klingai.com/image-to-video/kling-2.5-turbo"
    response = requests.post(
        create_url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "contents": [
                {"type": "prompt", "text": prompt[:2500]},
                {"type": "first_frame", "url": image_uri},
            ],
            "settings": {"resolution": "720p", "duration": 5},
            "options": {"watermark_info": {"enabled": True}},
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") not in (None, 0):
        raise I2VError(f"Kling rejected generation: {payload.get('message', 'unknown error')}")
    task_id = (payload.get("data") or {}).get("id")
    if not task_id:
        raise I2VError("Kling did not return a task ID")
    return _poll_kling(token, task_id)


def _generate_runway(token, image_uri, prompt):
    base = "https://api.dev.runwayml.com"
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Runway-Version": "2024-11-06",
        "Content-Type": "application/json",
    }
    response = requests.post(
        f"{base}/v1/image_to_video",
        headers=headers,
        json={
            "model": "gen4_turbo",
            "promptImage": image_uri,
            "promptText": prompt[:1000],
            "ratio": "768:1280",
            "duration": 5,
        },
        timeout=60,
    )
    response.raise_for_status()
    task_id = response.json().get("id")
    if not task_id:
        raise I2VError("Runway did not return a task ID")

    deadline = time.monotonic() + MAX_WAIT_SECONDS
    while time.monotonic() < deadline:
        task_response = requests.get(
            f"{base}/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}", "X-Runway-Version": "2024-11-06"},
            timeout=45,
        )
        task_response.raise_for_status()
        task = task_response.json()
        status = str(task.get("status", "")).upper()
        if status == "SUCCEEDED":
            output = task.get("output")
            if isinstance(output, list) and output:
                return output[0]
            if isinstance(output, str):
                return output
            raise I2VError("Runway completed without a video URL")
        if status in ("FAILED", "CANCELED"):
            raise I2VError(f"Runway generation {status.lower()}: {task.get('failure', task.get('error', 'unknown error'))}")
        time.sleep(POLL_SECONDS)
    raise I2VError("Runway generation timed out while polling")


def _generate_wan(token, image_uri, prompt):
    base = "https://api.replicate.com/v1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "wait=60",
    }
    response = requests.post(
        f"{base}/models/wan-video/wan-2.2-i2v-a14b/predictions",
        headers=headers,
        json={"input": {
            "image": image_uri,
            "prompt": prompt[:2000],
            "resolution": "480p",
            "num_frames": 81,
            "frames_per_second": 16,
        }},
        timeout=90,
    )
    response.raise_for_status()
    prediction = response.json()
    poll_url = (prediction.get("urls") or {}).get("get")
    if not poll_url:
        raise I2VError("Replicate did not return a prediction polling URL")

    deadline = time.monotonic() + MAX_WAIT_SECONDS
    while time.monotonic() < deadline:
        if prediction.get("status") == "succeeded":
            output = prediction.get("output")
            if isinstance(output, list) and output:
                return output[0]
            if isinstance(output, str):
                return output
            raise I2VError("Wan 2.2 completed without a video URL")
        if prediction.get("status") in ("failed", "canceled"):
            raise I2VError(f"Wan 2.2 generation {prediction.get('status')}: {prediction.get('error', 'unknown error')}")
        time.sleep(POLL_SECONDS)
        poll = requests.get(
            poll_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=45,
        )
        poll.raise_for_status()
        prediction = poll.json()
    raise I2VError("Wan 2.2 generation timed out while polling")


def generate_video(image_path, prompt, destination, provider=None):
    """Generate one 5-second clip. A single provider call is made; no paid retries."""
    if not is_enabled():
        raise I2VDisabled("I2V is disabled; no provider was contacted")
    provider = (provider or configured_provider()).strip().lower()
    if provider not in ("kling", "runway", "wan"):
        raise I2VError("Provider must be kling, runway, or wan")
    token = _token(provider)
    image_uri = _image_data_uri(image_path)
    safe_prompt = (
        "Create premium photorealistic live-action footage from the reference frame. "
        "Preserve the exact people, objects, clothing, location and composition. "
        "Use only subtle physically plausible movement and a gentle cinematic camera move. "
        "Do not create CGI, 3D anatomy, overlays, text, labels, logos, extra limbs, "
        "new people or objects, or change the subject. "
        + str(prompt or "Subtle cinematic movement")
    )
    generators = {
        "kling": _generate_kling,
        "runway": _generate_runway,
        "wan": _generate_wan,
    }
    video_url = generators[provider](token, image_uri, safe_prompt)
    return _download(video_url, destination)
