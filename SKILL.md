---
name: silicogrove-image
description: Generate images and edit reference images through the Silico Grove Image API. Use for Silico Grove text-to-image, image-to-image, restyling, or image revisions. On first use, ask for the user's Silico Grove API Key and save it with the bundled local client; never require an environment variable.
---

# Silico Grove Image

Run the bundled client from this Skill's directory. Resolve `SKILL_DIR` as the directory containing this `SKILL.md`; do not use an absolute path from another machine.

The client creates an asynchronous task at `https://ai.silicogrove.com/v1/images/tasks`, then polls it until the generated image has been persisted. A local connection interruption after the task is accepted does not stop image generation. The client does not automatically resubmit an interrupted task creation request, because the service may already have accepted and billed it.

## Update check

Before the first `generate` or `edit` of each calendar day, check this Skill's Git remote for updates. Store the check date in `${XDG_CONFIG_HOME:-$HOME/.config}/silicogrove-image/update-check-date`; when it already contains today's local date, skip the remote check and continue silently. When `origin/main` is ahead, briefly tell the user that a Skill update was found because it may contain required bug fixes or compatibility changes. When the working tree is clean, fast-forward to it and use the updated Skill before making an image request. Never require an update: if local modifications block it, or the Skill is not a Git checkout, has no `origin`, or checking or updating fails, briefly say so and continue the image request using the current local version. Do not overwrite local changes. A normal up-to-date check must remain silent.

```bash
UPDATE_STAMP="${XDG_CONFIG_HOME:-$HOME/.config}/silicogrove-image/update-check-date"
TODAY="$(date +%Y-%m-%d)"
if [ ! -r "$UPDATE_STAMP" ] || [ "$(cat "$UPDATE_STAMP" 2>/dev/null)" != "$TODAY" ]; then
  if ! git -C "$SKILL_DIR" remote get-url origin >/dev/null 2>&1; then
    echo "Silico Grove Image Skill update check unavailable; using the installed version." >&2
  elif ! git -C "$SKILL_DIR" fetch --quiet origin; then
    echo "Silico Grove Image Skill update check failed; using the installed version." >&2
  elif [ "$(git -C "$SKILL_DIR" rev-list --count HEAD..origin/main)" -gt 0 ]; then
    if [ -n "$(git -C "$SKILL_DIR" status --porcelain)" ]; then
      echo "Silico Grove Image Skill update is blocked by local changes; using the installed version." >&2
    else
      echo "Silico Grove Image Skill update found; applying it before the image request." >&2
      if ! git -C "$SKILL_DIR" pull --ff-only origin main; then
        echo "Silico Grove Image Skill update failed; using the installed version." >&2
      fi
    fi
  fi
  mkdir -p "$(dirname "$UPDATE_STAMP")"
  printf '%s\n' "$TODAY" > "$UPDATE_STAMP"
fi
```

## Credential workflow

1. Run `python3 "$SKILL_DIR/scripts/silicogrove_image.py" config --show-status` only on first use or when changing the selected model/provider; reuse the saved key for normal requests.
2. If it prints `not configured`, ask for a key from the API Key group associated with the selected model's provider. `gpt-image-2` is an OpenAI/GPT model; `gemini-3.1-flash-image` is a Google/Gemini model. Do not assume a key issued for one provider's models can invoke another provider's models, and do not assume the console's group name follows a fixed naming convention.
3. Keep the key out of prompts, project files, output, and terminal arguments.
4. When the runtime supports interactive terminal input, run `config --set-key` and enter the key without echoing it.
5. When an Agent can securely send an already-provided key through process standard input, use `config --set-key-stdin`. Do not put it in a command-line argument or environment variable.

The client stores the key in the current user's configuration directory: `~/.config/silicogrove-image/config.json` on macOS/Linux (or `$XDG_CONFIG_HOME/silicogrove-image/config.json`) and `%APPDATA%\\silicogrove-image\\config.json` on Windows. It applies owner-only permissions where supported.

## Generate

Use the saved model directly; do not query the model list before every request. Run `python3 "$SKILL_DIR/scripts/silicogrove_image.py" models` only during initial setup, when switching models, or when the selected model is rejected. Defaults are `gpt-image-2`, `1024x1024`, and `high` quality. Use an API Key from the group associated with that model's provider: `gpt-image-2` is OpenAI/GPT, while `gemini-3.1-flash-image` is Google/Gemini and commonly uses `2k` quality. Check `references/api.md` before choosing a model-specific size or quality.

```bash
python3 "$SKILL_DIR/scripts/silicogrove_image.py" generate \
  --prompt 'A cinematic product photograph of a compact espresso machine, soft studio light, light gray background' \
  --model gpt-image-2 --size 1536x1024 --quality high --output-dir ./outputs
```

Use `--n` only from 1 through 4. The client prints the result paths and PNG dimensions when available. Add `--no-wait` to print the task ID immediately, then resume later with `status TASK_ID --output-dir ./outputs`.

## Edit

```bash
python3 "$SKILL_DIR/scripts/silicogrove_image.py" edit \
  --image /absolute/path/to/source.png \
  --prompt 'Keep the product unchanged and replace the background with a clean white studio backdrop.' \
  --model gpt-image-2 --size 1024x1024 --quality high --output-dir ./outputs
```

The image must be PNG, JPG, JPEG, or WebP and must not exceed 10 MiB. The client submits a local reference image as `images: [{"image_url": "data:image/...;base64,..."}]` because the documented multipart task route may reject valid form fields. Use `gemini-3.1-flash-image` with `--quality 2k` for a Gemini image workflow when that model is available to the key. `--no-wait` and `status TASK_ID` work for asynchronous edits as well.

## Error handling

Report only the bundled client's summarized error. Do not expose request URLs, upstream host names, HTTP response bodies, proxy or firewall details, or API keys. For authentication, authorization, or task failures, identify the selected model's provider and ask the user to use a Key from that provider's model group, then verify model access and balance. Do not name or infer an exact console group label. For any model, confirm it appears in `models` for the saved key. The client retries transient result-download failures up to three times after the initial attempt; it does not retry definitive 4xx download errors. For rate limits or temporary service failures, ask them to retry later. See `references/api.md` before extending request fields or endpoint behavior.

## Submission and waiting

Track every accepted task ID. The client prints the ID immediately and writes one task record at `OUTPUT_DIR/.silicogrove-tasks/TASK_ID.json`. Records contain lifecycle metadata and completed local image paths, never API Keys or prompts. Do not invoke `generate` or `edit` again while a submission is unresolved; task polling requests may retry because they do not create work. After a command exits, check its exit status and confirm that the printed output paths exist. If a duplicate request was submitted accidentally, query every known task ID and deliver the local images from every completed task; explain that all completed requests were returned.

For an explicit request to generate multiple times, submit the requested number of separate tasks, track every task ID, and deliver every completed task's images. Do not collapse them into one result.

Treat the first 30 seconds as normal waiting. From 30 through 120 seconds, continue polling without resubmitting. After 120 seconds, check the task status and output directory, then continue polling unless an explicit error occurs. Handle authentication, authorization, rate-limit, parameter, network, or service errors immediately rather than waiting for a time threshold.
