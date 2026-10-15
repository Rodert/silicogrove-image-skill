# Silico Grove Image API

- Preferred base URL: `https://ai.silicogrove.com`; fallback URL: `https://api.silicogrove.com`.
- Auth: `Authorization: Bearer sk-...`.
- Submit generation: `POST /v1/images/tasks` with JSON fields `model`, `prompt`, optional `size`, `quality`, and `n`.
- Submit edits: `POST /v1/images/tasks` with `images: [{ "image_url": "data:image/...;base64,..." }]`. The platform documents multipart or JSON; the bundled client uses this JSON form because multipart task requests may reject otherwise valid form fields.
- Task submission returns HTTP 202 and `{ "id": "task_...", "status": "queued" }`. Query with `GET /v1/images/tasks/{task_id}` every 2-5 seconds. Statuses are `queued`, `processing`, `completed`, and `failed`.
- Task creation is not safely retryable when the response is lost, because the task may have been accepted. Task-status requests are read-only and can be retried. Continue normal polling through 120 seconds; then check the task status and local output directory before continuing.
- The bundled client writes one local task record per accepted task in `OUTPUT_DIR/.silicogrove-tasks/`, allowing `status TASK_ID` to resume polling after an interrupted process.
- A completed task contains OpenAI-style `{ "data": [{ "url": "..." }] }` results that have been persisted by Silico Grove. Image URLs should be downloaded promptly with the same `Authorization: Bearer` API Key used for the task; some result URLs return `403` without it.
- The client retries transient result-download failures up to three times after the initial download attempt. It does not retry definitive 4xx download errors.
- List models with `GET /v1/models`; model availability depends on the API key and group.
- Use a key from the API Key group associated with the model's provider. Both default models, `gpt-image-2.5-flare` and `gpt-image-2.5-sunburst`, are OpenAI/GPT models. Console group labels vary, so verify availability through `GET /v1/models` rather than relying on an exact group name.
- The skill's supported default image models are `gpt-image-2.5-flare` and `gpt-image-2.5-sunburst` when visible in the model list.
- Use `quality=high` for ordinary flare requests. Supported sizes and qualities vary by model; select sunburst only for explicit refinement, high-resolution, commercial, print, or final-delivery requests.
- Edits accept PNG, JPG, JPEG, and WebP reference images. The documented playground limit is one image up to 10 MiB.

Source: https://docs.silicogrove.com/zh-cn/api/#images
