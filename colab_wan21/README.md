# Wan2.1 + Google Colab bridge (FitFuel)

This is an isolated Colab workflow for testing the official Wan2.1 T2V 1.3B model on a free Colab GPU. It does **not** modify the production Shorts workflows or upload generated videos to YouTube.

## Open the notebook

Open `fitfuel_wan21_colab.ipynb` in Google Colab from this branch:

https://colab.research.google.com/github/6d28nf7wz9-web/fitness-shorts-bot/blob/feat/colab-wan21-bridge/colab_wan21/fitfuel_wan21_colab.ipynb

Choose **Runtime → Change runtime type → T4 GPU** (or another available GPU). Run the cells from top to bottom.

## What it does

1. Checks out this GitHub repository's bridge branch in Colab.
2. Reuses an existing `/content/Wan2.1` clone and model folder when present; it does not redownload checkpoints automatically.
3. Checks GPU, RAM, disk, checkpoint files, and the T5 loading patch.
4. Runs the short 17-frame / 20-step FitFuel test while recording process RAM and console output.
5. Verifies the MP4 and displays a preview if generation succeeds.
6. Optionally uploads only the text log to the separate `colab-runs` branch.

## Optional: send logs back to GitHub

In Colab, open the **Secrets** panel (key icon) and add a secret named `GH_TOKEN`. Use a fine-grained GitHub token scoped only to this repository, with **Contents: Read and write**. The notebook never prints the token and uploads only a text log to `colab-runs`; it does not upload model weights or MP4 files.

If you do not add the secret, the notebook still runs normally and leaves the log at `/content/fitfuel_wan21_run.log` for manual download.

## Important limits

- GitHub stores source code and logs, not the 10+ GB model checkpoint.
- GitHub Actions runners do not provide a free persistent Colab T4 GPU. The actual generation runs inside the Colab runtime you open.
- This bridge does not provide unattended remote control of an open Colab tab. It gives the notebook a version-controlled source and an optional secure log-return path.
- Do not commit Hugging Face tokens, Google credentials, API keys, checkpoints, or generated videos to the repository.
- The experiment is isolated from `.github/workflows/daily.yml` and the normal upload pipeline.
