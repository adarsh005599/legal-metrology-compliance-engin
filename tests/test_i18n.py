import unittest
import os
import re
import json

class TestI18nTranslations(unittest.TestCase):
    def setUp(self):
        self.i18n_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'i18n.js')
        self.assertTrue(os.path.exists(self.i18n_path), "i18n.js file must exist")
        
        with open(self.i18n_path, 'r', encoding='utf-8') as f:
            self.content = f.read()

    def test_translation_dictionaries_exist(self):
        """Verify English and Hindi translation dictionaries are defined."""
        self.assertIn("en: {", self.content)
        self.assertIn("hi: {", self.content)

    def test_key_parity_between_en_and_hi(self):
        """Extract keys from en and hi objects in i18n.js and ensure 100% parity."""
        # Extract en dictionary body
        en_match = re.search(r'en:\s*\{(.*?)\n\s*\},', self.content, re.DOTALL)
        self.assertIsNotNone(en_match, "en dictionary must be parseable")
        en_keys = set(re.findall(r'^\s*([a-zA-Z0-9_]+):', en_match.group(1), re.MULTILINE))

        # Extract hi dictionary body
        hi_match = re.search(r'hi:\s*\{(.*?)\n\s*\}\n\};', self.content, re.DOTALL)
        self.assertIsNotNone(hi_match, "hi dictionary must be parseable")
        hi_keys = set(re.findall(r'^\s*([a-zA-Z0-9_]+):', hi_match.group(1), re.MULTILINE))

        missing_in_hi = en_keys - hi_keys
        missing_in_en = hi_keys - en_keys

        self.assertEqual(missing_in_hi, set(), f"Keys missing in Hindi translation: {missing_in_hi}")
        self.assertEqual(missing_in_en, set(), f"Keys missing in English translation: {missing_in_en}")
        self.assertGreater(len(en_keys), 40, "Should have a comprehensive translation set (>40 keys)")

    def test_devanagari_characters_in_hindi(self):
        """Verify that Hindi translations contain authentic Devanagari characters."""
        devanagari_sample = [
            "विधिक मापविज्ञान",
            "लेबल स्कैन करें",
            "अधिकतम खुदरा मूल्य",
            "शुद्ध मात्रा",
            "उपभोक्ता सहायता",
            "स्क्रीनिंग परिणाम"
        ]
        for term in devanagari_sample:
            self.assertIn(term, self.content, f"Devanagari term '{term}' should be in i18n.js")

    def test_html_data_attributes_presence(self):
        """Verify index.html and dashboard.html include i18n script and language switchers."""
        index_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'index.html')
        dashboard_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'dashboard.html')

        with open(index_path, 'r', encoding='utf-8') as f:
            index_html = f.read()
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            dashboard_html = f.read()

        self.assertIn('id="langSwitcher"', index_html)
        self.assertIn('data-lang="hi"', index_html)
        self.assertTrue('src="/static/i18n.js' in index_html or 'i18n.js' in index_html)

        self.assertIn('id="langSwitcher"', dashboard_html)
        self.assertIn('data-lang="hi"', dashboard_html)
        self.assertTrue('src="/static/i18n.js' in dashboard_html or 'i18n.js' in dashboard_html)


if __name__ == '__main__':
    unittest.main()
