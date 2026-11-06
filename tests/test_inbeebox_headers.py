import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'service'))
import tools_mcp  # noqa: E402


class InbeeboxHeadersTests(unittest.TestCase):
    def test_api_key_env_sends_x_api_key(self) -> None:
        with mock.patch.dict(os.environ, {'INBEEBOX_API_KEY': 'k' * 64}, clear=True):
            headers = tools_mcp.inbeebox_headers()
        self.assertEqual(headers['X-API-Key'], 'k' * 64)
        self.assertNotIn('X-Agent-Key', headers)
        self.assertEqual(headers['Accept'], 'application/json')

    def test_api_key_file_is_read_and_stripped(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            key_file = Path(folder) / '.inbeebox_api_key'
            key_file.write_text('\ufeffabc123\r\n', encoding='utf-8')
            with mock.patch.dict(os.environ, {'INBEEBOX_API_KEY_FILE': str(key_file)}, clear=True):
                headers = tools_mcp.inbeebox_headers()
        self.assertEqual(headers['X-API-Key'], 'abc123')

    def test_env_wins_over_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            key_file = Path(folder) / 'key'
            key_file.write_text('from-file', encoding='utf-8')
            env = {'INBEEBOX_API_KEY': 'from-env', 'INBEEBOX_API_KEY_FILE': str(key_file)}
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(tools_mcp.inbeebox_headers()['X-API-Key'], 'from-env')

    def test_legacy_agent_key_is_kept_for_old_deployments(self) -> None:
        with mock.patch.dict(os.environ, {'INBEEBOX_AGENT_KEY': 'legacy'}, clear=True):
            headers = tools_mcp.inbeebox_headers()
        self.assertEqual(headers['X-Agent-Key'], 'legacy')
        self.assertNotIn('X-API-Key', headers)

    def test_missing_key_file_does_not_raise(self) -> None:
        with mock.patch.dict(os.environ, {'INBEEBOX_API_KEY_FILE': r'Z:\no\existe'}, clear=True):
            headers = tools_mcp.inbeebox_headers()
        self.assertNotIn('X-API-Key', headers)


if __name__ == '__main__':
    unittest.main()
