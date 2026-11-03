import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'service'))
import file_catalog  # noqa: E402


class FileKindsTests(unittest.TestCase):
    def test_new_categories_by_extension(self):
        cases = {
            'pieza.stl': 'models3d', 'robot.3MF': 'models3d', 'escena.gltf': 'models3d',
            'juego.nsp': 'roms', 'mario.nes': 'roms', 'disco.iso': 'roms', 'recursos.pak': 'roms',
            'backup.zip': 'archives', 'datos.tar.gz': 'archives', 'pack.7z': 'archives',
            'cancion.mp3': 'audio', 'voz.wav': 'audio', 'clip.mp4': 'video', 'peli.mkv': 'video',
            'pagina.html': 'web', 'foto.png': 'photos', 'nota.md': 'documents', 'app.py': 'code',
            'misterio.xyz': 'other',
        }
        for name, expected in cases.items():
            self.assertEqual(file_catalog.kind(name), expected, name)

    def test_kinds_catalog_is_complete_and_labelled(self):
        catalog = file_catalog.kinds_catalog()['kinds']
        ids = [k['id'] for k in catalog]
        self.assertEqual(ids, [*file_catalog.KINDS, 'other'])
        for k in catalog:
            self.assertTrue(k['label'] and k['icon'], k['id'])
            self.assertEqual(sorted(k['extensions']), k['extensions'])

    def test_inventory_accepts_new_categories(self):
        self.assertIn('roms', file_catalog.KINDS)
        self.assertIn('models3d', file_catalog.KINDS)


if __name__ == '__main__':
    unittest.main()
