---
name: silicogrove-image
description: Generate images and edit reference images through the Silico Grove Image API. Use for Silico Grove text-to-image, image-to-image, restyling, or image revisions. On first use, ask for the user's Silico Grove API Key and save it with the bundled local client; never require an environment variable.
---

# Silico Grove Image

Run the bundled client from this Skill's directory. Resolve `SKILL_DIR` as the directory containing this `SKILL.md`; do not use an absolute path from another machine.

The client creates an asynchronous task at `https://ai.silicogrove.com/v1/images/tasks`, then polls it until the generated image has been persisted. A local connection interruption after the task is accepted does not stop image generation. The client does not automatically resubmit an interrupted task creation request, because the service may already have accepted and billed it.

## Update check

Before every `generate` or `edit`, check this Skill's Git remote for updates. When no update is available, continue silently. When `origin/main` is ahead, explicitly tell the user that a Skill update was found because it may contain required bug fixes or compatibility changes. When the working tree is clean, fast-forward to it and use the updated Skill before making an image request. If local modifications prevent the update, do not make the image request: repeatedly remind the user that the available update must be applied or the local changes resolved first. Do not overwrite local changes. If the Skill is not a Git checkout, has no `origin`, or the check or update fails, explicitly warn the user before the image request that update status could not be verified.

```bash
if git -C "$SKILL_DIR" remote get-url origin >/dev/null 2>&1; then
  git -C "$SKILL_DIR" fetch --quiet origin
  if [ "$(git -C "$SKILL_DIR" rev-list --count HEAD..origin/main)" -gt 0 ]; then
    if [ -z "$(git -C "$SKILL_DIR" status --porcelain)" ]; then
      git -C "$SKILL_DIR" pull --ff-only origin main
    fi
  fi
fi
```

## Credential workflow

1. Run `python3 "$SKILL_DIR/scripts/silicogrove_image.py" config --show-status`.
2. If it prints `not configured`, ask for a key from the API Key group associated with the selected model's provider. `gpt-image-2` is an OpenAI/GPT model; `gemini-3.1-flash-image` is a Google/Gemini model. Do not assume a key issued for one provider's models can invoke another provider's models, and do not assume the console's group name follows a fixed naming convention.
3. Keep the key out of prompts, project files, output, and terminal arguments.
4. When the runtime supports interactive terminal input, run `config --set-key` and enter the key without echoing it.
5. When an Agent can securely send an already-provided key through process standard input, use `config --set-key-stdin`. Do not put it in a command-line argument or environment variable.

The client stores the key in the current user's configuration directory: `~/.config/silicogrove-image/config.json` on macOS/Linux (or `$XDG_CONFIG_HOME/silicogrove-image/config.json`) and `%APPDATA%\\silicogrove-image\\config.json` on Windows. It applies owner-only permissions where supported.

## Generate

List models with `python3 "$SKILL_DIR/scripts/silicogrove_image.py" models`, then use an image model visible to the user's key. Defaults are `gpt-image-2`, `1024x1024`, and `high` quality. Use an API Key from the group associated with that model's provider: `gpt-image-2` is OpenAI/GPT, while `gemini-3.1-flash-image` is Google/Gemini and commonly uses `2k` quality. Check `references/api.md` before choosing a model-specific size or quality.

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

The image must be PNG, JPG, JPEG, or WebP and must not exceed 10 MiB. Use `gemini-3.1-flash-image` with `--quality 2k` for a Gemini image workflow when that model is available to the key. `--no-wait` and `status TASK_ID` work for asynchronous edits as well.

## Error handling

Report only the bundled client's summarized error. Do not expose request URLs, upstream host names, HTTP response bodies, proxy or firewall details, or API keys. For authentication, authorization, or task failures, identify the selected model's provider and ask the user to use a Key from that provider's model group, then verify model access and balance. Do not name or infer an exact console group label. For any model, confirm it appears in `models` for the saved key. For rate limits or temporary service failures, ask them to retry later. See `references/api.md` before extending request fields or endpoint behavior.

## Submission and waiting

Track every accepted task ID. Do not invoke `generate` or `edit` again while a submission is unresolved; task polling requests may retry because they do not create work. After a command exits, check its exit status and confirm that the printed output paths exist. If a duplicate request was submitted accidentally, query every known task ID and deliver the local images from every completed task; explain that all completed requests were returned.

For an explicit request to generate multiple times, submit the requested number of separate tasks, track every task ID, and deliver every completed task's images. Do not collapse them into one result.

Treat the first 30 seconds as normal waiting. From 30 through 120 seconds, continue polling without resubmitting. After 120 seconds, check the task status and output directory, then continue polling unless an explicit error occurs. Handle authentication, authorization, rate-limit, parameter, network, or service errors immediately rather than waiting for a time threshold.
