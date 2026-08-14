#!/usr/bin/env python3
"""Portable standard-library client for the Silico Grove Image API."""

import argparse
import base64
import getpass
import json
import mimetypes
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URLS = ("https://ai.silicogrove.com", "https://api.silicogrove.com")
DEFAULT_TIMEOUT_SECONDS = 300
POLL_INTERVAL_SECONDS = 3
ESCALATED_WAIT_SECONDS = 120
MAX_DOWNLOAD_RETRIES = 3
MAX_IMAGE_BYTES = 10 * 1024 * 1024
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def config_path():
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "silicogrove-image" / "config.json"


def fail(message):
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def private_mode(path, mode):
    if os.name != "nt":
        os.chmod(path, mode)


def save_key(key):
    key = key.strip()
    if not key:
        fail("API key cannot be empty.")
    path = config_path()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    private_mode(path.parent, 0o700)
    temporary = path.parent / f".{path.name}.{secrets.token_hex(8)}.tmp"
    try:
        with open(temporary, "w", encoding="utf-8") as handle:
            private_mode(temporary, 0o600)
            json.dump({"api_key": key}, handle)
            handle.write("\n")
        os.replace(temporary, path)
        private_mode(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_key():
    try:
        with open(config_path(), encoding="utf-8") as handle:
            key = json.load(handle).get("api_key", "").strip()
    except (OSError, json.JSONDecodeError):
        key = ""
    if not key:
        fail("No Silico Grove API key is saved. Ask the user for their key, then run config --set-key or config --set-key-stdin.")
    return key


def request_failure_summary(failures):
    statuses = {status for kind, status in failures if kind == "http"}
    if 401 in statuses:
        return "Silico Grove could not authenticate the request. Check the saved API key and its access."
    if 403 in statuses:
        return "Silico Grove did not authorize this image request. Check API key access, model availability, and balance."
    if 429 in statuses:
        return "Silico Grove is rate-limiting image requests. Retry after a short delay."
    if any(status >= 500 for status in statuses) or any(kind == "network" for kind, _ in failures):
        return "Silico Grove image service is temporarily unavailable. Please retry later."
    return "Silico Grove could not complete the image request. Please retry later."


def api_request(method, endpoint, body=None, content_type=None, base_url=None, allow_fallback=True):
    headers = {"Authorization": f"Bearer {load_key()}", "Accept": "application/json", "User-Agent": "SilicoGroveImageSkill/1.0 (portable local client)"}
    if content_type:
        headers["Content-Type"] = content_type
    if allow_fallback:
        bases = BASE_URLS if base_url is None else (base_url,) + tuple(base for base in BASE_URLS if base != base_url)
    else:
        bases = (base_url or BASE_URLS[0],)
    failures = []
    for index, base in enumerate(bases):
        request = urllib.request.Request(base + endpoint, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
                return response.read(), response.headers.get_content_type(), base
        except urllib.error.HTTPError as error:
            failures.append(("http", error.code))
            if index == 0 and error.code == 404:
                continue
            fail(request_failure_summary(failures))
        except (urllib.error.URLError, TimeoutError):
            failures.append(("network", None))
            if index == 0:
                continue
            fail(request_failure_summary(failures))
    fail(request_failure_summary(failures))


def json_request(method, endpoint, payload=None, base_url=None, allow_fallback=True):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    raw, _, used_base = api_request(method, endpoint, body, "application/json" if body else None, base_url, allow_fallback)
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail("Silico Grove returned an invalid image response. Please retry later.")
    if not isinstance(result, dict):
        fail("Silico Grove returned an invalid image response. Please retry later.")
    return result, used_base


def multipart(fields, image_path):
    boundary = "----SilicoGrove" + secrets.token_hex(16)
    path = Path(image_path)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parts = []
    for name, value in fields.items():
        parts.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), str(value).encode(), b"\r\n"])
    parts.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="image"; filename="{path.name}"\r\n'.encode(), f"Content-Type: {mime}\r\n\r\n".encode(), path.read_bytes(), b"\r\n", f"--{boundary}--\r\n".encode()])
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def validate_image(raw_path):
    path = Path(raw_path).expanduser().resolve()
    if not path.is_file():
        fail(f"Image file does not exist: {path}")
    if path.suffix.lower() not in IMAGE_EXTENSIONS:
        fail("Unsupported image format. Choose PNG, JPG, JPEG, or WebP.")
    if path.stat().st_size > MAX_IMAGE_BYTES:
        fail("Image exceeds the 10 MiB upload limit.")
    return path


def image_extension(content_type):
    return {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(content_type.split(";", 1)[0].lower(), "png")


def png_dimensions(raw):
    if raw[:8] == b"\x89PNG\r\n\x1a\n" and raw[12:16] == b"IHDR":
        return int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")
    return None


def download_url(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        fail("Silico Grove returned an invalid image URL.")
    for attempt in range(MAX_DOWNLOAD_RETRIES + 1):
        try:
            with urllib.request.urlopen(url, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
                raw = response.read()
                content_type = response.headers.get_content_type()
            if not raw:
                raise urllib.error.URLError("empty image")
            return raw, image_extension(content_type)
        except urllib.error.HTTPError as error:
            if error.code < 500 or attempt == MAX_DOWNLOAD_RETRIES:
                fail("Could not download the generated image. Please retry later.")
        except (urllib.error.URLError, TimeoutError):
            if attempt == MAX_DOWNLOAD_RETRIES:
                fail("Could not download the generated image. Please retry later.")
        time.sleep(attempt + 1)


def save_results(response, output_dir):
    entries = response.get("data")
    if not isinstance(entries, list) or not entries:
        fail("Silico Grove returned no image data.")
    directory = Path(output_dir).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    for index, item in enumerate(entries, 1):
        if not isinstance(item, dict):
            fail("Silico Grove returned invalid image data.")
        if isinstance(item.get("b64_json"), str):
            try:
                raw = base64.b64decode(item["b64_json"], validate=True)
            except (ValueError, TypeError):
                fail("Silico Grove returned invalid Base64 image data.")
            suffix = "png"
        elif isinstance(item.get("url"), str):
            raw, suffix = download_url(item["url"])
        else:
            fail("Silico Grove returned image data without a URL or Base64 content.")
        path = directory / f"silicogrove-{timestamp}-{index}.{suffix}"
        path.write_bytes(raw)
        message = str(path)
        dimensions = png_dimensions(raw)
        if dimensions:
            message += f" ({dimensions[0]}x{dimensions[1]})"
        print(message)


def output_image_count(output_dir):
    directory = Path(output_dir).expanduser().resolve()
    if not directory.is_dir():
        return 0
    return sum(path.is_file() and path.name.startswith("silicogrove-") for path in directory.iterdir())


def list_models():
    response, _ = json_request("GET", "/v1/models")
    models = response.get("data")
    if not isinstance(models, list):
        fail("Silico Grove returned an invalid model list.")
    for model in models:
        if isinstance(model, dict) and isinstance(model.get("id"), str):
            print(model["id"])


def task_id_from(response):
    task_id = response.get("id")
    if not isinstance(task_id, str) or not task_id:
        fail("Silico Grove did not return an image task ID.")
    return task_id


def task_status(response):
    status = response.get("status", "")
    return status.lower() if isinstance(status, str) else ""


def submit_task(args, fields, body=None, content_type=None):
    # A lost response after POST may mean the task was accepted. Never resubmit it automatically.
    if body is None:
        response, used_base = json_request("POST", "/v1/images/tasks", fields, allow_fallback=False)
    else:
        raw, _, used_base = api_request("POST", "/v1/images/tasks", body, content_type, allow_fallback=False)
        try:
            response = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            fail("Silico Grove returned an invalid image task response. Please retry later.")
        if not isinstance(response, dict):
            fail("Silico Grove returned an invalid image task response. Please retry later.")
    return task_id_from(response), used_base


def wait_for_task(task_id, output_dir, base_url):
    endpoint = f"/v1/images/tasks/{urllib.parse.quote(task_id, safe='')}"
    started_at = time.monotonic()
    escalated = False
    while True:
        response, used_base = json_request("GET", endpoint, base_url=base_url)
        status = task_status(response)
        if status == "completed":
            save_results(response, output_dir)
            return
        if status == "failed":
            fail("Silico Grove image generation did not complete. Check the prompt, model access, and balance, then retry.")
        if status not in {"queued", "processing"}:
            fail("Silico Grove returned an invalid image task status. Please retry later.")
        elapsed = time.monotonic() - started_at
        if elapsed >= ESCALATED_WAIT_SECONDS and not escalated:
            print(
                f"Image task {task_id} is still {status} after {int(elapsed)} seconds. "
                f"Checked output directory: {Path(output_dir).expanduser().resolve()} "
                f"({output_image_count(output_dir)} existing image file(s)). Continuing without resubmitting.",
                file=sys.stderr,
            )
            escalated = True
        time.sleep(POLL_INTERVAL_SECONDS)


def run_image(args):
    if not args.prompt.strip() or not args.model.strip():
        fail("model and prompt cannot be empty.")
    if not args.size.strip() or not args.quality.strip():
        fail("size and quality cannot be empty.")
    if not 1 <= args.n <= 4:
        fail("n must be between 1 and 4.")
    fields = {"model": args.model, "prompt": args.prompt, "size": args.size, "quality": args.quality, "n": args.n}
    if args.action == "generate":
        task_id, used_base = submit_task(args, fields)
    else:
        image = validate_image(args.image)
        body, content_type = multipart(fields, image)
        task_id, used_base = submit_task(args, fields, body, content_type)
    if args.no_wait:
        print(task_id)
        return
    wait_for_task(task_id, args.output_dir, used_base)


def main():
    parser = argparse.ArgumentParser(description="Silico Grove Image API client")
    commands = parser.add_subparsers(dest="action", required=True)
    config = commands.add_parser("config")
    config.add_argument("--show-status", action="store_true")
    config.add_argument("--set-key", action="store_true")
    config.add_argument("--set-key-stdin", action="store_true")
    commands.add_parser("models")
    for action in ("generate", "edit"):
        command = commands.add_parser(action)
        command.add_argument("--prompt", required=True)
        command.add_argument("--model", default="gpt-image-2")
        command.add_argument("--size", default="1024x1024")
        command.add_argument("--quality", default="high")
        command.add_argument("--n", type=int, default=1)
        command.add_argument("--output-dir", default="outputs")
        command.add_argument("--no-wait", action="store_true")
        if action == "edit":
            command.add_argument("--image", required=True)
    status = commands.add_parser("status")
    status.add_argument("task_id")
    status.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    if args.action in {"generate", "edit"}:
        run_image(args)
    elif args.action == "status":
        wait_for_task(args.task_id, args.output_dir, None)
    elif args.action == "models":
        list_models()
    elif args.set_key_stdin:
        save_key(sys.stdin.read())
        print("Silico Grove API key saved securely.")
    elif args.set_key:
        try:
            save_key(getpass.getpass("Silico Grove API Key: "))
        except (EOFError, KeyboardInterrupt):
            fail("API key entry was cancelled.")
        print("Silico Grove API key saved securely.")
    elif args.show_status:
        print("configured" if config_path().is_file() else "not configured")
    else:
        fail("Use --show-status, --set-key, or --set-key-stdin.")


if __name__ == "__main__":
    main()
