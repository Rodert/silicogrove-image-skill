# Silico Grove Image API

- Preferred base URL: `https://ai.silicogrove.com`; fallback URL: `https://api.silicogrove.com`.
- Auth: `Authorization: Bearer sk-...`.
- Submit generation: `POST /v1/images/tasks` with JSON fields `model`, `prompt`, optional `size`, `quality`, and `n`.
- Submit edits: `POST /v1/images/tasks` as `multipart/form-data` with `model`, `prompt`, `image`, optional `size`, `quality`, and `n`.
- Task submission returns HTTP 202 and `{ "id": "task_...", "status": "queued" }`. Query with `GET /v1/images/tasks/{task_id}` every 2-5 seconds. Statuses are `queued`, `processing`, `completed`, and `failed`.
- Task creation is not safely retryable when the response is lost, because the task may have been accepted. Task-status requests are read-only and can be retried. Continue normal polling through 120 seconds; then check the task status and local output directory before continuing.
- A completed task contains OpenAI-style `{ "data": [{ "url": "..." }] }` results that have been persisted by Silico Grove. Image URLs should be downloaded promptly with the same `Authorization: Bearer` API Key used for the task; some result URLs return `403` without it.
- The client retries transient result-download failures up to three times after the initial download attempt. It does not retry definitive 4xx download errors.
- List models with `GET /v1/models`; model availability depends on the API key and group.
- Use a key from the API Key group associated with the model's provider. For example, `gpt-image-2` is OpenAI/GPT and `gemini-3.1-flash-image` is Google/Gemini. Console group labels vary, so verify availability through `GET /v1/models` rather than relying on an exact group name.
- Supported documented image models include `gpt-image-2`, `gpt-image-2-all`, `gemini-3-pro-image`, `gemini-3.1-flash-image`, `gemini-3-pro-image-preview`, `gemini-3.1-flash-image-preview`, `gemini-2.5-flash-image`, `grok-imagine-image`, and `grok-imagine-image-pro` when visible in the model list.
- The API examples use `quality=high` for `gpt-image-2` and `quality=2k` for Gemini. Supported sizes and qualities vary by model.
- Edits accept PNG, JPG, JPEG, and WebP reference images. The documented playground limit is one image up to 10 MiB.

Source: https://docs.silicogrove.com/zh-cn/api/#images
