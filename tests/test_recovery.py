import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch
from tests import test_service
from app.recovery import DraftStore,journal_backup
from app.database import Database


class RecoveryTests(unittest.TestCase):
    setUp=test_service.RentalTests.setUp
    tearDown=test_service.RentalTests.tearDown

    def test_draft_roundtrip_and_unchanged_snapshot_does_not_write(self):
        store=DraftStore(self.db);payload=dict(version=1,name='Ana',address={'postal_code':'01'},cart={'1':3})
        self.assertTrue(store.save(payload))
        before=self.db.conn.total_changes
        self.assertFalse(store.save(payload));self.assertEqual(before,self.db.conn.total_changes)
        other=Database(self.db.path)
        try:self.assertEqual(DraftStore(other).load()['payload'],payload)
        finally:other.conn.close()

    def test_rental_and_draft_clear_commit_together(self):
        store=DraftStore(self.db);store.save(dict(version=1,name='Borrador'))
        with self.assertRaises(ValueError):
            self.service.create_rental(self.client,'Obra','2026-11-05','2026-11-07',{self.item:99},clear_draft=True)
        self.assertIsNotNone(store.load())
        self.service.create_rental(self.client,'Obra','2026-11-05','2026-11-07',{self.item:1},clear_draft=True)
        self.assertIsNone(store.load())

    def test_other_rental_does_not_erase_pending_form(self):
        store=DraftStore(self.db);store.save(dict(version=1,name='Otro borrador'))
        self.service.create_rental(self.client,'Obra','2026-11-05','2026-11-07',{self.item:1})
        self.assertIsNotNone(store.load())

    def test_journal_snapshot_is_valid_and_retention_separate(self):
        paths=[journal_backup(self.db.path,keep=2) for _ in range(3)]
        directory=self.db.path.parent/'respaldos'
        self.assertEqual(len(list(directory.glob('jornada-*.sqlite3'))),2)
        self.assertTrue(list(directory.glob('automatico-*.sqlite3')))
        self.assertFalse(list(directory.glob('*.tmp')))
        conn=sqlite3.connect(paths[-1])
        try:
            self.assertEqual(conn.execute('PRAGMA quick_check').fetchone()[0],'ok')
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM clients').fetchone()[0],1)
        finally:conn.close()

    def test_failed_publish_keeps_previous_copies_and_removes_temp(self):
        previous=journal_backup(self.db.path)
        with patch.object(Path,'replace',side_effect=OSError('Disco lleno')):
            with self.assertRaises(OSError):journal_backup(self.db.path)
        self.assertTrue(previous.exists())
        self.assertEqual(len(list(previous.parent.glob('jornada-*.sqlite3'))),1)
        self.assertFalse(list(previous.parent.glob('*.tmp')))
