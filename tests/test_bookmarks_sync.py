"""Tests for the common Nautilus <-> Dolphin bookmarks synchronizer (bwm-bookmarks-sync.py)."""

import importlib.util
import os
import sys
import tempfile
import threading
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bwm_bookmarks_sync", ROOT / "config/hypr/scripts/bwm-bookmarks-sync.py"
)
bsync = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bsync
SPEC.loader.exec_module(bsync)

SAMPLE_KDE_XBEL = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xbel>
<xbel xmlns:bookmark="http://www.freedesktop.org/standards/desktop-bookmarks" xmlns:kdepriv="http://www.kde.org/kdepriv" xmlns:mime="http://www.freedesktop.org/standards/shared-mime-info">
 <info>
  <metadata owner="http://www.kde.org">
   <kde_places_version>4</kde_places_version>
   <GroupState-Places-IsHidden>false</GroupState-Places-IsHidden>
   <withBaloo>true</withBaloo>
  </metadata>
 </info>
 <bookmark href="file:///home/tester">
  <title>Home</title>
  <info>
   <metadata owner="http://freedesktop.org">
    <bookmark:icon name="user-home"/>
   </metadata>
   <metadata owner="http://www.kde.org">
    <ID>1700000000/0</ID>
    <isSystemItem>true</isSystemItem>
   </metadata>
  </info>
 </bookmark>
 <bookmark href="remote:/">
  <title>Network</title>
  <info>
   <metadata owner="http://freedesktop.org">
    <bookmark:icon name="folder-network"/>
   </metadata>
   <metadata owner="http://www.kde.org">
    <ID>1700000000/1</ID>
    <isSystemItem>true</isSystemItem>
   </metadata>
  </info>
 </bookmark>
 <bookmark href="trash:/">
  <title>Trash</title>
  <info>
   <metadata owner="http://freedesktop.org">
    <bookmark:icon name="user-trash"/>
   </metadata>
   <metadata owner="http://www.kde.org">
    <ID>1700000000/2</ID>
    <isSystemItem>true</isSystemItem>
   </metadata>
  </info>
 </bookmark>
 <bookmark href="timeline:/today">
  <title>Modified Today</title>
  <info>
   <metadata owner="http://freedesktop.org">
    <bookmark:icon name="go-jump-today"/>
   </metadata>
   <metadata owner="http://www.kde.org">
    <ID>1700000000/3</ID>
    <isSystemItem>true</isSystemItem>
   </metadata>
  </info>
 </bookmark>
 <bookmark href="">
  <title>USB Drive</title>
  <info>
   <metadata owner="http://www.kde.org">
    <UDI>/org/freedesktop/UDisks2/block_devices/sdb1</UDI>
   </metadata>
  </info>
 </bookmark>
 <bookmark href="file:///home/tester/HiddenPlace">
  <title>HiddenPlace</title>
  <info>
   <metadata owner="http://www.kde.org">
    <ID>1700000000/4</ID>
    <isHidden>true</isHidden>
   </metadata>
  </info>
 </bookmark>
 <bookmark href="file:///home/tester/AppOnly">
  <title>AppOnly</title>
  <info>
   <metadata owner="http://www.kde.org">
    <ID>1700000000/5</ID>
    <onlyInApp>gwenview</onlyInApp>
   </metadata>
  </info>
 </bookmark>
 <bookmark href="file:///home/tester/KdeOnly">
  <title>KDE Folder</title>
  <info>
   <metadata owner="http://freedesktop.org">
    <bookmark:icon name="folder-development"/>
   </metadata>
   <metadata owner="http://www.kde.org">
    <ID>1700000000/6</ID>
    <customTag>keep-me</customTag>
   </metadata>
  </info>
 </bookmark>
</xbel>
"""


class BookmarksSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.gtk_path = root / "config" / "gtk-3.0" / "bookmarks"
        self.kde_path = root / "share" / "user-places.xbel"
        self.state_path = root / "state" / "bwm" / "bookmarks-sync.json"
        self.syncer = bsync.BookmarksSync(self.gtk_path, self.kde_path, self.state_path)

    def _write_gtk(self, text: str):
        self.gtk_path.parent.mkdir(parents=True, exist_ok=True)
        bsync.atomic_write(self.gtk_path, text.encode("utf-8"))

    def _write_kde(self, text: str):
        self.kde_path.parent.mkdir(parents=True, exist_ok=True)
        bsync.atomic_write(self.kde_path, text.encode("utf-8"))

    def _gtk_map(self):
        doc = bsync.parse_gtk_bookmarks(bsync.read_bytes_or_none(self.gtk_path))
        return {e.canon: e.label for e in doc.entries}

    def _kde_map(self):
        doc = bsync.parse_kde_places(bsync.read_bytes_or_none(self.kde_path))
        return {e.canon: e.label for e in doc.user_entries}

    def test_startup_union_merges_both_without_deleting_and_preserves_kde_specials(self):
        self._write_gtk("file:///mnt/HDD1TB HDD1TB\nfile:///home/tester/Projects Proyectos\n")
        self._write_kde(SAMPLE_KDE_XBEL)

        res = self.syncer.startup()
        self.assertEqual(res["status"], "synced")
        self.assertEqual(res["added_to_gtk"], 1)
        self.assertEqual(res["added_to_kde"], 2)

        expected = {
            "file:///mnt/HDD1TB": "HDD1TB",
            "file:///home/tester/Projects": "Proyectos",
            "file:///home/tester/KdeOnly": "KDE Folder",
        }
        self.assertEqual(self._gtk_map(), expected)
        self.assertEqual(self._kde_map(), expected)

        # Special KDE entries must NOT leak into GTK and must remain intact in XBEL.
        gtk_text = self.gtk_path.read_text(encoding="utf-8")
        for forbidden in ("remote:/", "trash:/", "timeline:/", "HiddenPlace", "AppOnly", "Home"):
            self.assertNotIn(forbidden, gtk_text)

        kde_text = self.kde_path.read_text(encoding="utf-8")
        self.assertTrue(kde_text.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xbel>\n'))
        self.assertIn('xmlns:bookmark="http://www.freedesktop.org/standards/desktop-bookmarks"', kde_text)
        self.assertIn('xmlns:kdepriv="http://www.kde.org/kdepriv"', kde_text)
        self.assertIn('xmlns:mime="http://www.freedesktop.org/standards/shared-mime-info"', kde_text)
        for special in ("remote:/", "trash:/", "timeline:/today", "UDisks2", "HiddenPlace", "AppOnly", "withBaloo", "keep-me"):
            self.assertIn(special, kde_text)

    def test_startup_union_never_deletes_even_if_previous_state_exists(self):
        self._write_gtk("file:///a A\nfile:///b B\n")
        self._write_kde(SAMPLE_KDE_XBEL)
        self.syncer.startup()

        # Simulate offline edit where /b was missing from GTK before next login.
        self._write_gtk("file:///a A\nfile:///home/tester/KdeOnly KDE Folder\n")
        res = self.syncer.startup()
        self.assertEqual(res["status"], "synced")
        self.assertIn("file:///b", self._gtk_map())
        self.assertIn("file:///b", self._kde_map())

    def test_add_rename_delete_from_gtk_to_kde_preserves_icon_id_and_custom_metadata(self):
        self._write_gtk("file:///mnt/HDD1TB HDD1TB\n")
        self._write_kde(SAMPLE_KDE_XBEL)
        self.syncer.startup()

        # Rename KDE Folder from GTK, add /mnt/SSD1TB, delete /mnt/HDD1TB.
        self._write_gtk(
            "file:///home/tester/KdeOnly Renombrado\n"
            "file:///mnt/SSD1TB SSD1TB\n"
        )
        res = self.syncer.sync_once()
        self.assertEqual(res["status"], "synced")

        expected = {
            "file:///home/tester/KdeOnly": "Renombrado",
            "file:///mnt/SSD1TB": "SSD1TB",
        }
        self.assertEqual(self._gtk_map(), expected)
        self.assertEqual(self._kde_map(), expected)

        # Verify KDE metadata (icon, ID, customTag) survived the rename from GTK!
        doc = bsync.parse_kde_places(self.kde_path.read_bytes())
        kde_only = doc.by_canon()["file:///home/tester/KdeOnly"].element
        icon = kde_only.find(f".//{{{bsync.NS_BOOKMARK}}}icon")
        self.assertIsNotNone(icon)
        self.assertEqual(icon.attrib.get("name"), "folder-development")
        self.assertEqual(kde_only.findtext(".//ID"), "1700000000/6")
        self.assertEqual(kde_only.findtext(".//customTag"), "keep-me")

        # Subsequent sync must be a noop and deleted HDD1TB must NOT reappear.
        self.assertEqual(self.syncer.sync_once()["status"], "noop")
        self.assertNotIn("file:///mnt/HDD1TB", self._gtk_map())
        self.assertNotIn("file:///mnt/HDD1TB", self._kde_map())

    def test_add_rename_delete_from_kde_to_gtk(self):
        self._write_gtk("file:///mnt/HDD1TB HDD1TB\n")
        self._write_kde(SAMPLE_KDE_XBEL)
        self.syncer.startup()

        # Mutate KDE XBEL: rename HDD1TB -> Disco, remove KdeOnly, add sftp://server/share
        doc = bsync.parse_kde_places(self.kde_path.read_bytes())
        bsync.kde_set_title(doc.by_canon()["file:///mnt/HDD1TB"], "Disco")
        bsync.kde_remove_bookmark(doc, doc.by_canon()["file:///home/tester/KdeOnly"])
        bsync.kde_add_bookmark(doc, "sftp://server/share", "Servidor")
        bsync.atomic_write(self.kde_path, bsync.render_kde_places(doc))

        res = self.syncer.sync_once()
        self.assertEqual(res["status"], "synced")
        expected = {
            "file:///mnt/HDD1TB": "Disco",
            "sftp://server/share": "Servidor",
        }
        self.assertEqual(self._gtk_map(), expected)
        self.assertEqual(self._kde_map(), expected)
        # Remote URI added in KDE gets folder-remote icon
        doc2 = bsync.parse_kde_places(self.kde_path.read_bytes())
        sftp_elem = doc2.by_canon()["sftp://server/share"].element
        self.assertEqual(sftp_elem.find(f".//{{{bsync.NS_BOOKMARK}}}icon").attrib["name"], "folder-remote")

    def test_system_item_matching_gtk_uri_not_duplicated_and_not_deleted(self):
        kde_with_downloads = SAMPLE_KDE_XBEL.replace(
            "</xbel>",
            """ <bookmark href="file:///home/tester/Downloads">
  <title>Downloads</title>
  <info>
   <metadata owner="http://freedesktop.org">
    <bookmark:icon name="folder-downloads"/>
   </metadata>
   <metadata owner="http://www.kde.org">
    <ID>1700000000/9</ID>
    <isSystemItem>true</isSystemItem>
   </metadata>
  </info>
 </bookmark>
</xbel>""",
        )
        self._write_gtk("file:///home/tester/Downloads Descargas\nfile:///mnt/HDD1TB HDD1TB\n")
        self._write_kde(kde_with_downloads)
        self.syncer.startup()

        # Downloads must NOT be duplicated in KDE, and must stay in GTK.
        root = ET.fromstring(self.kde_path.read_text(encoding="utf-8"))
        dl_nodes = [b for b in root.findall("bookmark") if b.attrib.get("href") == "file:///home/tester/Downloads"]
        self.assertEqual(len(dl_nodes), 1)
        self.assertIn("file:///home/tester/Downloads", self._gtk_map())

        # Unrelated change in KDE must not delete Downloads from GTK.
        doc = bsync.parse_kde_places(self.kde_path.read_bytes())
        bsync.kde_add_bookmark(doc, "file:///mnt/Extra", "Extra")
        bsync.atomic_write(self.kde_path, bsync.render_kde_places(doc))
        self.syncer.sync_once()
        self.assertIn("file:///home/tester/Downloads", self._gtk_map())
        self.assertIn("file:///mnt/Extra", self._gtk_map())

        # Removing Downloads from GTK must NOT touch the KDE isSystemItem.
        self._write_gtk("file:///mnt/HDD1TB HDD1TB\nfile:///home/tester/KdeOnly KDE Folder\nfile:///mnt/Extra Extra\n")
        self.syncer.sync_once()
        self.assertNotIn("file:///home/tester/Downloads", self._gtk_map())
        root2 = ET.fromstring(self.kde_path.read_text(encoding="utf-8"))
        dl_nodes2 = [b for b in root2.findall("bookmark") if b.attrib.get("href") == "file:///home/tester/Downloads"]
        self.assertEqual(len(dl_nodes2), 1)

    def test_disjoint_simultaneous_changes_reconcile_safely(self):
        self._write_gtk("file:///mnt/A A\nfile:///mnt/B B\n")
        self._write_kde(SAMPLE_KDE_XBEL)
        self.syncer.startup()

        # GTK adds /mnt/FromGtk and renames A -> A-GTK
        self._write_gtk(
            "file:///mnt/A A-GTK\n"
            "file:///mnt/B B\n"
            "file:///home/tester/KdeOnly KDE Folder\n"
            "file:///mnt/FromGtk FromGtk\n"
        )
        # Simultaneously KDE deletes /mnt/B and adds /mnt/FromKde
        doc = bsync.parse_kde_places(self.kde_path.read_bytes())
        bsync.kde_remove_bookmark(doc, doc.by_canon()["file:///mnt/B"])
        bsync.kde_add_bookmark(doc, "file:///mnt/FromKde", "FromKde")
        bsync.atomic_write(self.kde_path, bsync.render_kde_places(doc))

        res = self.syncer.sync_once()
        self.assertEqual(res["status"], "synced")
        expected = {
            "file:///mnt/A": "A-GTK",
            "file:///home/tester/KdeOnly": "KDE Folder",
            "file:///mnt/FromGtk": "FromGtk",
            "file:///mnt/FromKde": "FromKde",
        }
        self.assertEqual(self._gtk_map(), expected)
        self.assertEqual(self._kde_map(), expected)

    def test_simultaneous_conflicts_preserve_both_files_and_retry_until_clear(self):
        self._write_gtk("file:///mnt/A Original\n")
        self._write_kde(SAMPLE_KDE_XBEL)
        self.syncer.startup()

        # 1) Rename vs Rename to different names
        self._write_gtk("file:///mnt/A NombreGTK\nfile:///home/tester/KdeOnly KDE Folder\n")
        doc = bsync.parse_kde_places(self.kde_path.read_bytes())
        bsync.kde_set_title(doc.by_canon()["file:///mnt/A"], "NombreKDE")
        bsync.atomic_write(self.kde_path, bsync.render_kde_places(doc))

        gtk_before = self.gtk_path.read_bytes()
        kde_before = self.kde_path.read_bytes()
        res = self.syncer.sync_once()
        self.assertEqual(res["status"], "conflict")
        self.assertTrue(res["retry"])
        self.assertEqual(self.gtk_path.read_bytes(), gtk_before)
        self.assertEqual(self.kde_path.read_bytes(), kde_before)

        # 2) Delete vs Rename
        self._write_gtk("file:///home/tester/KdeOnly KDE Folder\n")  # deleted /mnt/A in GTK while KDE renamed it
        res2 = self.syncer.sync_once()
        self.assertEqual(res2["status"], "conflict")
        self.assertTrue(res2["retry"])
        self.assertIn("file:///mnt/A", self._kde_map())  # Not destroyed!

        # Once KDE aligns (or conflict resolves), retry converges cleanly
        doc2 = bsync.parse_kde_places(self.kde_path.read_bytes())
        bsync.kde_set_title(doc2.by_canon()["file:///mnt/A"], "Original")
        bsync.atomic_write(self.kde_path, bsync.render_kde_places(doc2))
        res3 = self.syncer.sync_once()
        self.assertEqual(res3["status"], "synced")
        self.assertNotIn("file:///mnt/A", self._kde_map())

    def test_incomplete_xbel_mid_write_preserves_files_and_retries(self):
        self._write_gtk("file:///mnt/A A\n")
        self._write_kde(SAMPLE_KDE_XBEL)
        self.syncer.startup()

        gtk_before = self.gtk_path.read_bytes()
        self._write_kde("<xbel><bookmark href='file:///mnt/A'")  # truncated XML
        res = self.syncer.sync_once()
        self.assertEqual(res["status"], "retry")
        self.assertTrue(res["retry"])
        self.assertEqual(self.gtk_path.read_bytes(), gtk_before)

    def test_uri_normalization_spaces_and_trailing_slashes(self):
        self._write_gtk("file://localhost/home/tester/Mis%20Archivos/ Mis Archivos\n")
        self._write_kde(SAMPLE_KDE_XBEL)
        self.syncer.startup()
        self.assertIn("file:///home/tester/Mis%20Archivos", self._kde_map())
        self.assertEqual(self._kde_map()["file:///home/tester/Mis%20Archivos"], "Mis Archivos")

    def test_directory_watcher_catches_atomic_replace_and_debounces_burst(self):
        self._write_gtk("file:///mnt/Initial Initial\n")
        self._write_kde(SAMPLE_KDE_XBEL)

        results = []
        stop = threading.Event()
        t = threading.Thread(
            target=bsync.run_watch_loop,
            args=(self.syncer,),
            kwargs=dict(
                do_startup=True,
                debounce_secs=0.2,
                max_debounce_secs=1.0,
                retry_delays=(0.2, 0.4),
                stop_check=stop.is_set,
                on_result=lambda r: results.append(r),
            ),
            daemon=True,
        )
        t.start()
        try:
            # Wait for startup union to finish
            deadline = time.monotonic() + 3.0
            while not results and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertGreaterEqual(len(results), 1)
            results.clear()

            # Burst of 4 rapid atomic replacements on GTK bookmarks (simulating rapid saves)
            for i in range(4):
                self._write_gtk(
                    "file:///mnt/Initial Initial\n"
                    "file:///home/tester/KdeOnly KDE Folder\n"
                    f"file:///mnt/Burst Burst-{i}\n"
                )
                time.sleep(0.03)

            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                if self._kde_map().get("file:///mnt/Burst") == "Burst-3":
                    break
                time.sleep(0.03)

            self.assertEqual(self._kde_map().get("file:///mnt/Burst"), "Burst-3")
            synced_runs = [r for r in results if r.get("status") == "synced"]
            # Debounce coalesced the 4 writes into 1 (or at most 2) sync executions.
            self.assertLessEqual(len(synced_runs), 2)

            # Now test atomic replacement on KDE user-places.xbel propagating back to GTK
            doc = bsync.parse_kde_places(self.kde_path.read_bytes())
            bsync.kde_add_bookmark(doc, "file:///mnt/FromDolphin", "Desde Dolphin")
            bsync.atomic_write(self.kde_path, bsync.render_kde_places(doc))

            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                if self._gtk_map().get("file:///mnt/FromDolphin") == "Desde Dolphin":
                    break
                time.sleep(0.03)
            self.assertEqual(self._gtk_map().get("file:///mnt/FromDolphin"), "Desde Dolphin")
        finally:
            stop.set()
            t.join(timeout=3.0)


if __name__ == "__main__":
    unittest.main()
