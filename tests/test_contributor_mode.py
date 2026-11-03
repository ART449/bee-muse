import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'service'))
import muse_bridge  # noqa: E402


class ContributorModeTests(unittest.TestCase):
    def test_default_is_off(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop('BEE_MUSE_CONTRIBUTOR_MODE', None)
            self.assertEqual(muse_bridge.contributor_mode(), 'off')

    def test_explicit_on_values(self):
        for value in ('on', 'ON', '1', 'true', 'yes', ' on '):
            with mock.patch.dict(os.environ, {'BEE_MUSE_CONTRIBUTOR_MODE': value}):
                self.assertEqual(muse_bridge.contributor_mode(), 'on', value)

    def test_other_values_stay_off(self):
        for value in ('off', '0', 'false', 'contributor', ''):
            with mock.patch.dict(os.environ, {'BEE_MUSE_CONTRIBUTOR_MODE': value}):
                self.assertEqual(muse_bridge.contributor_mode(), 'off', value)


if __name__ == '__main__':
    unittest.main()
