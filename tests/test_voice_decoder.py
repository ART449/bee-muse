import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'service'))
import voice_bridge


class DecoderEnvironmentTests(unittest.TestCase):
    def test_windows_cli_can_probe_both_names_without_losing_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'system-ffmpeg.exe';source.write_bytes(b'fixture')
            scratch=root/'request';scratch.mkdir()
            with patch.object(voice_bridge.shutil,'which',return_value=str(source)),patch.dict(os.environ,{'Path':'existing-tools'},clear=True):
                env=voice_bridge.decoder_environment(scratch,windows=True)
            self.assertEqual((scratch/'ffmpeg').read_bytes(),source.read_bytes())
            self.assertEqual((scratch/'ffmpeg.exe').read_bytes(),source.read_bytes())
            self.assertEqual(env['PATH'],str(scratch)+os.pathsep+'existing-tools')
            self.assertEqual([key for key in env if key.upper()=='PATH'],['PATH'])

    def test_system_decoder_on_unix_does_not_change_environment(self):
        with tempfile.TemporaryDirectory() as folder,patch.object(voice_bridge.shutil,'which',return_value='/usr/bin/ffmpeg'):
            self.assertEqual(voice_bridge.decoder_environment(folder,windows=False),os.environ.copy())


if __name__=='__main__':unittest.main()
