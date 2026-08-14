import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error


CLIENT = Path(__file__).parents[1] / "scripts" / "silicogrove_image.py"
SPEC = importlib.util.spec_from_file_location("silicogrove_image", CLIENT)
CLIENT_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIENT_MODULE)


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.config = tempfile.TemporaryDirectory()
        self.original_config = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self.config.name
        CLIENT_MODULE.save_key("sk-test-value")

    def tearDown(self):
        if self.original_config is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self.original_config
        self.config.cleanup()

    def response(self, payload):
        response = MagicMock()
        response.read.return_value = json.dumps(payload).encode()
        response.headers.get_content_type.return_value = "application/json"
        response.__enter__.return_value = response
        return response

    def test_save_key_is_private_on_unix(self):
        path = CLIENT_MODULE.config_path()
        self.assertEqual(json.loads(path.read_text())["api_key"], "sk-test-value")
        if os.name != "nt":
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)

    def test_prefers_ai_endpoint(self):
        with patch.object(CLIENT_MODULE.urllib.request, "urlopen", return_value=self.response({"data": []})) as urlopen:
            response, base = CLIENT_MODULE.json_request("GET", "/v1/models")
        self.assertEqual(response["data"], [])
        self.assertEqual(base, "https://ai.silicogrove.com")
        self.assertEqual(urlopen.call_count, 1)

    def test_falls_back_after_404(self):
        error = urllib.error.HTTPError("https://ai.silicogrove.com/v1/models", 404, "missing", {}, None)
        with patch.object(CLIENT_MODULE.urllib.request, "urlopen", side_effect=[error, self.response({"data": []})]) as urlopen:
            _, base = CLIENT_MODULE.json_request("GET", "/v1/models")
        self.assertEqual(base, "https://api.silicogrove.com")
        self.assertEqual(urlopen.call_count, 2)

    def test_task_submission_does_not_retry_after_network_error(self):
        with patch.object(CLIENT_MODULE.urllib.request, "urlopen", side_effect=urllib.error.URLError("unavailable")) as urlopen:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                CLIENT_MODULE.json_request("POST", "/v1/images/tasks", {"model": "m"}, allow_fallback=False)
        self.assertEqual(urlopen.call_count, 1)

    def test_task_polling_can_fall_back_after_network_error(self):
        with patch.object(
            CLIENT_MODULE.urllib.request,
            "urlopen",
            side_effect=[urllib.error.URLError("unavailable"), self.response({"id": "task_1", "status": "queued"})],
        ) as urlopen:
            response, base = CLIENT_MODULE.json_request("GET", "/v1/images/tasks/task_1", base_url="https://ai.silicogrove.com")
        self.assertEqual(response["status"], "queued")
        self.assertEqual(base, "https://api.silicogrove.com")
        self.assertEqual(urlopen.call_count, 2)

    def test_task_status_and_id_are_parsed(self):
        response = {"id": "task_1", "status": "processing"}
        self.assertEqual(CLIENT_MODULE.task_id_from(response), "task_1")
        self.assertEqual(CLIENT_MODULE.task_status(response), "processing")

    def test_does_not_fallback_after_server_error(self):
        error = urllib.error.HTTPError("https://ai.silicogrove.com/v1/models", 503, "unavailable", {}, None)
        with patch.object(CLIENT_MODULE.urllib.request, "urlopen", side_effect=error) as urlopen:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                CLIENT_MODULE.json_request("GET", "/v1/models")
        self.assertEqual(urlopen.call_count, 1)

    def test_png_dimensions(self):
        raw = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (1024).to_bytes(4, "big") + (1536).to_bytes(4, "big")
        self.assertEqual(CLIENT_MODULE.png_dimensions(raw), (1024, 1536))

    def test_invalid_image_extension_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.gif"
            path.write_bytes(b"image")
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                CLIENT_MODULE.validate_image(path)

    def test_oversized_image_is_rejected_before_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.png"
            path.write_bytes(b"x" * (CLIENT_MODULE.MAX_IMAGE_BYTES + 1))
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                CLIENT_MODULE.validate_image(path)

    def test_failure_summary_hides_upstream_details(self):
        message = CLIENT_MODULE.request_failure_summary([("http", 502), ("network", None)])
        self.assertEqual(message, "Silico Grove image service is temporarily unavailable. Please retry later.")
        self.assertNotIn("silicogrove.com", message)
        self.assertNotIn("502", message)

    def test_output_image_count_uses_existing_local_results(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "silicogrove-old.png").write_bytes(b"image")
            (output / "other.png").write_bytes(b"image")
            self.assertEqual(CLIENT_MODULE.output_image_count(output), 1)

    def test_long_wait_checks_status_and_output_without_resubmitting(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "silicogrove-old.png").write_bytes(b"image")
            responses = [
                ({"id": "task_1", "status": "processing"}, "https://ai.silicogrove.com"),
                ({"id": "task_1", "status": "completed", "data": [{"url": "https://example.com/result.png"}]}, "https://ai.silicogrove.com"),
            ]
            with patch.object(CLIENT_MODULE, "json_request", side_effect=responses) as request, patch.object(CLIENT_MODULE, "save_results") as save, patch.object(CLIENT_MODULE.time, "monotonic", side_effect=[0, 121]), patch.object(CLIENT_MODULE.time, "sleep"), contextlib.redirect_stderr(io.StringIO()) as stderr:
                CLIENT_MODULE.wait_for_task("task_1", output, "https://ai.silicogrove.com")
            self.assertEqual(request.call_count, 2)
            save.assert_called_once_with(responses[1][0], output)
            self.assertIn("Checked output directory", stderr.getvalue())
            self.assertIn("Continuing without resubmitting", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
