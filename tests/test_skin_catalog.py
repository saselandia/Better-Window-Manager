"""Catálogo oficial: publicación desde manifiestos y lectura remota sin ejecutar código."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "config/hypr/scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("skin_catalog", SCRIPTS / "bwm-skin-catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def entry(sid="new-desktop"):
    return {"id": sid, "name": "Nuevo escritorio", "description": "Una skin publicada",
            "imitates": "Escritorio original", "delivery": "external-release",
            "version": "1.0.0", "compatibility": "Probada con una revisión concreta de BWM",
            "previewUrl": "https://example.org/preview.png", "sourceUrl": "https://example.org/source",
            "installationUrl": "https://example.org/install"}


class SkinCatalogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.index = self.root / "skins.json"
        self.cache = self.root / "cache.json"
        self.data = {"schemaVersion": 2, "catalogId": "bwm-extra-skins", "skins": [entry()]}
        self.index.write_text(json.dumps(self.data))

    def test_bundled_catalog_is_empty_and_separate_from_builtins(self):
        self.assertEqual(catalog.read_index(catalog.INDEX)["skins"], [])
        self.assertTrue(all("/bwm-skins/" in url for url in catalog.SOURCES))
        self.assertNotEqual(catalog.CACHE.name, "skin-catalog.json")

    def test_old_catalog_cache_and_builtin_skins_are_rejected(self):
        with self.assertRaises(ValueError):
            catalog.validate({"schemaVersion": 1, "skins": []})
        for sid in catalog.bwm_skins.ORDER:
            with self.subTest(sid=sid), self.assertRaises(ValueError):
                catalog.validate({**self.data, "skins": [entry(sid)]})

    def test_untrusted_links_duplicates_and_unknown_delivery_are_rejected(self):
        for link in ("file:///tmp/script", "javascript:alert(1)", "https://user:password@example.org/x"):
            data = copy.deepcopy(self.data)
            data["skins"][0]["installationUrl"] = link
            with self.subTest(link=link), self.assertRaises(ValueError):
                catalog.validate(data)
        with self.assertRaises(ValueError):
            catalog.validate({"schemaVersion": 2, "catalogId": "bwm-extra-skins", "skins": [entry(), entry()]})
        data = copy.deepcopy(self.data)
        data["skins"][0]["delivery"] = "run-shell-installer"
        with self.assertRaises(ValueError):
            catalog.validate(data)

    def test_incomplete_remote_catalog_falls_back_to_bundled(self):
        broken = copy.deepcopy(self.data)
        del broken["skins"][0]["previewUrl"]
        def invalid_fetch(url):
            return catalog.validate(broken)
        with patch.object(catalog, "fetch", side_effect=invalid_fetch):
            data, source, _ = catalog.catalog(cache=self.cache, index=self.index)
        self.assertEqual(source, "bundled")
        self.assertEqual(data, self.data)

    def test_fresh_cache_avoids_network_and_refresh_fetches_new_publications(self):
        self.cache.write_text(json.dumps(self.data))
        new = {"schemaVersion": 2, "catalogId": "bwm-extra-skins", "skins": [entry("newer-desktop")]}
        with patch.object(catalog, "fetch", return_value=new) as fetch:
            result, source, _ = catalog.catalog(cache=self.cache, index=self.index)
            self.assertEqual(source, "cache")
            fetch.assert_not_called()
            result, source, _ = catalog.catalog(refresh=True, cache=self.cache, index=self.index)
            self.assertEqual(source, "remote")
            self.assertEqual(result["skins"][0]["id"], "newer-desktop")
            self.assertEqual(catalog.read_index(self.cache), new)

    def test_offline_keeps_cache_then_uses_bundled_catalog(self):
        with patch.object(catalog, "fetch", side_effect=OSError("offline")):
            data, source, warning = catalog.catalog(cache=self.cache, index=self.index)
            self.assertEqual(source, "bundled")
            self.assertEqual(data, self.data)
            self.cache.write_text(json.dumps(self.data))
            data, source, warning = catalog.catalog(refresh=True, cache=self.cache, index=self.index)
            self.assertEqual(source, "cache")
            self.assertTrue(warning)

    def test_cache_write_failure_does_not_discard_a_valid_remote_catalog(self):
        with patch.object(catalog, "fetch", return_value=self.data), \
                patch.object(catalog, "save_cache", side_effect=OSError("read-only")):
            data, source, warning = catalog.catalog(refresh=True, cache=self.cache, index=self.index)
        self.assertEqual(source, "remote")
        self.assertEqual(data, self.data)

    def test_new_remote_skin_is_visible_without_installing_or_activating_it(self):
        with patch.object(catalog, "catalog", return_value=(self.data, "remote", "")), \
                patch.object(catalog.bwm_skins, "all_skins", return_value=[]):
            result = catalog.discover()
        self.assertEqual(result["skins"][0]["id"], "new-desktop")
        self.assertFalse(result["skins"][0]["installed"])
        self.assertEqual(result["skins"][0]["status"], "Disponible por separado")

    def test_publishing_only_scans_external_entries_and_requires_the_right_folder(self):
        with self.assertRaises(ValueError):
            catalog.build(self.root)
        folder = self.root / "skins/new-desktop"
        folder.mkdir(parents=True)
        (folder / "catalog.json").write_text(json.dumps(entry()))
        # A template is not a publication and builtin manifests are not scanned.
        template = self.root / "templates"
        template.mkdir()
        (template / "catalog-entry.json").write_text(json.dumps(entry("template")))
        self.assertEqual(catalog.build(self.root), self.data)
        (folder / "catalog.json").write_text(json.dumps(entry("wrong-id")))
        with self.assertRaises(ValueError):
            catalog.build(self.root)

    def test_local_catalog_does_not_contact_the_network(self):
        with patch.object(catalog, "fetch") as fetch:
            data, source, warning = catalog.catalog(local=True, cache=self.cache, index=self.index)
        fetch.assert_not_called()
        self.assertEqual(source, "bundled")


if __name__ == "__main__":
    unittest.main()
