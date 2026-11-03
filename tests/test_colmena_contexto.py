import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'service'))
import colmena_contexto  # noqa: E402


class ColmenaContextoTests(unittest.TestCase):
    def test_summary_is_bounded_and_mentions_key_terms(self):
        text = colmena_contexto.resumen()
        self.assertLess(len(text), 1500)
        for term in ('iartlabs.lat', 'La Colmena', 'BASE', 'CENTRO', 'ACCIÓN', 'VEREDICTO', 'Nahuallatolli'):
            self.assertIn(term, text)

    def test_detail_has_site_and_no_secrets(self):
        text = colmena_contexto.detalle()
        self.assertIn(colmena_contexto.SITIO, text)
        for marker in ('sk-', 'ghp_', 'AIza', 'BEGIN PRIVATE KEY', 'C:\\Users'):
            self.assertNotIn(marker, text)

    def test_nahuallatolli_is_not_invented(self):
        self.assertIn('sin inventar', colmena_contexto.detalle())


if __name__ == '__main__':
    unittest.main()
