import subprocess

import numpy as np


def load_audio(path, sr=16000):
    cmd = [
        "ffmpeg", "-nostdin", "-loglevel", "error", "-i", path,
        "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-",
    ]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()