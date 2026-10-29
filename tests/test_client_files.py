import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest.mock import patch
from zipfile import ZipFile

from app.client_files import DOCUMENT_CATEGORIES, MAX_DOCUMENT_BYTES
from app.database import Database
from app.service import Service


class ClientFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.path = self.folder / 'test.sqlite3'
        self.db = Database(self.path)
        self.service = Service(self.db)
        self.client = self.service.save_client(None, 'Ana Pérez', '3121234567', None, 'Nota interna privada')
        self.other = self.service.save_client(None, 'Otro cliente', '3127654321', None, '')
        self.category = DOCUMENT_CATEGORIES[0]
        self.content = b'%PDF-1.7\nDocumento de prueba\n%%EOF'
        self.source = self.folder / 'Constancia fiscal.pdf'
        self.source.write_bytes(self.content)

    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()

    def add(self, client=None, category=None, paths=None):
        return self.service.add_client_documents(client or self.client, category or self.category, paths or [self.source])

    def test_copies_bytes_and_survives_original_deletion_and_restart(self):
        self.add()
        self.source.unlink()
        self.db.conn.close()
        self.db = Database(self.path)
        self.service = Service(self.db)
        row = self.service.client_documents(self.client)[0]
        self.assertNotIn('content', row.keys())
        self.assertEqual(row['size_bytes'], len(self.content))
        destination = self.folder / 'recuperado.pdf'
        self.service.export_client_document(self.client, row['id'], destination)
        self.assertEqual(destination.read_bytes(), self.content)

    def test_details_are_optional_independent_and_update_without_duplicates(self):
        self.assertFalse(any(self.service.billing_details(self.client).values()))
        self.service.save_billing_details(self.client, {'rfc': '  aaa010101aaa ', 'notes': 'Dato pendiente'})
        self.assertEqual(self.service.billing_details(self.client)['rfc'], 'AAA010101AAA')
        self.assertFalse(any(self.service.billing_details(self.other).values()))
        self.service.save_billing_details(self.client, {'legal_name': 'Razón social'})
        self.assertEqual(len(self.db.rows('SELECT * FROM client_billing')), 1)
        self.assertEqual(self.service.billing_details(self.client)['rfc'], '')

    def test_duplicate_content_skipped_only_within_same_client_and_category(self):
        self.assertEqual(self.add(), {'added': 1, 'skipped': 0})
        renamed = self.folder / 'otro_nombre.pdf'
        renamed.write_bytes(self.content)
        self.assertEqual(self.add(paths=[renamed]), {'added': 0, 'skipped': 1})
        self.assertEqual(self.add(client=self.other)['added'], 1)
        self.assertEqual(self.add(category=DOCUMENT_CATEGORIES[1])['added'], 1)

    def test_failed_batch_rolls_back_every_attachment(self):
        wrong = self.folder / 'no_es_foto.jpg'
        wrong.write_bytes(b'archivo ejecutable')
        with self.assertRaisesRegex(ValueError, 'formato'):
            self.add(paths=[self.source, wrong])
        self.assertEqual(self.service.client_documents(self.client), [])
        with self.assertRaises(ValueError):
            self.add(paths=[self.source, self.folder / 'ausente.pdf'])
        self.assertEqual(self.service.client_documents(self.client), [])

    def test_rejects_empty_oversized_unsupported_and_invalid_client(self):
        for filename, content in [('vacio.pdf', b''), ('programa.exe', b'MZ')]:
            with self.subTest(filename=filename):
                path = self.folder / filename
                path.write_bytes(content)
                with self.assertRaises(ValueError):
                    self.add(paths=[path])
        large = self.folder / 'grande.pdf'
        with large.open('wb') as stream:
            stream.truncate(MAX_DOCUMENT_BYTES + 1)
        with self.assertRaisesRegex(ValueError, '20 MB'):
            self.add(paths=[large])
        with self.assertRaises(ValueError):
            self.add(category='Tipo inválido')
        with self.assertRaises(ValueError):
            self.add(client=999999)
        with self.assertRaises(ValueError):
            self.service.save_billing_details(999999, {'rfc': 'RFC'})
        self.assertEqual(self.service.client_documents(self.client), [])

    def test_same_name_different_files_preserved_with_unique_safe_zip_members(self):
        self.add()
        self.source.write_bytes(self.content + b' actualizado')
        self.add()
        # Incluso un nombre antiguo importado con rutas no puede salir del ZIP.
        with self.db.conn:
            self.db.conn.execute('UPDATE client_documents SET filename=? WHERE client_id=?',
                                 ('../../CON.pdf', self.client))
        target = self.folder / 'seguro.zip'
        self.service.export_client_billing(self.client, target)
        with ZipFile(target) as archive:
            names = archive.namelist()
            self.assertEqual(len(names), len(set(names)))
            self.assertEqual(len(names), 3)
            for name in names:
                self.assertFalse(PurePosixPath(name).is_absolute())
                self.assertNotIn('..', PurePosixPath(name).parts)

    def test_zip_contains_only_chosen_client_documents_and_billing_details(self):
        self.add()
        self.add(client=self.other)
        self.service.save_billing_details(self.client, {'rfc': 'AAA010101AAA', 'legal_name': 'Ana Fiscal', 'notes': 'Enviar por correo'})
        target = self.folder / 'contadora.zip'
        self.assertEqual(self.service.export_client_billing(self.client, target), 1)
        with ZipFile(target) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len(archive.namelist()), 2)
            summary = archive.read('Datos_para_facturacion.txt').decode('utf-8-sig')
            for text in ('Ana Pérez', '3121234567', 'AAA010101AAA', 'Ana Fiscal', 'Enviar por correo'):
                self.assertIn(text, summary)
            self.assertNotIn('Otro cliente', summary)
            self.assertNotIn('Nota interna privada', summary)
            attachment = next(name for name in archive.namelist() if name.startswith('Documentos/'))
            self.assertEqual(archive.read(attachment), self.content)

    def test_no_empty_exports_but_partial_details_can_be_exported(self):
        target = self.folder / 'parcial.zip'
        with self.assertRaises(ValueError):
            self.service.export_client_billing(self.client, target)
        self.assertFalse(target.exists())
        self.service.save_billing_details(self.client, {'notes': 'Pendiente la constancia'})
        self.assertEqual(self.service.export_client_billing(self.client, target), 0)
        with ZipFile(target) as archive:
            self.assertEqual(archive.namelist(), ['Datos_para_facturacion.txt'])

    def test_failed_export_preserves_previous_zip_and_removes_temporary(self):
        self.add()
        target = self.folder / 'anterior.zip'
        target.write_bytes(b'contenido anterior')
        with patch('app.client_files.ZipFile.writestr', side_effect=OSError('Sin espacio')):
            with self.assertRaises(OSError):
                self.service.export_client_billing(self.client, target)
        self.assertEqual(target.read_bytes(), b'contenido anterior')
        self.assertEqual(list(self.folder.glob('.expediente-*.tmp')), [])

    def test_wrong_destination_does_not_overwrite_database(self):
        self.add()
        original = self.path.read_bytes()
        with self.assertRaises(ValueError):
            self.service.export_client_billing(self.client, self.path)
        self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaises(ValueError):
            self.service.export_client_billing(self.client, self.folder / 'incorrecto.pdf')

    def test_document_operations_are_scoped_and_delete_preserves_original(self):
        self.add()
        document = self.service.client_documents(self.client)[0]['id']
        with self.assertRaises(ValueError):
            self.service.export_client_document(self.other, document, self.folder / 'ajeno.pdf')
        with self.assertRaises(ValueError):
            self.service.delete_client_document(self.other, document)
        self.assertEqual(len(self.service.client_documents(self.client)), 1)
        self.service.delete_client_document(self.client, document)
        self.assertEqual(self.service.client_documents(self.client), [])
        self.assertEqual(self.source.read_bytes(), self.content)

    def test_corrupted_content_is_not_exported(self):
        self.add()
        with self.db.conn:
            self.db.conn.execute('UPDATE client_documents SET sha256=?', ('incorrecto',))
        target = self.folder / 'corrupto.zip'
        with self.assertRaisesRegex(ValueError, 'verificar'):
            self.service.export_client_billing(self.client, target)
        self.assertFalse(target.exists())

    def test_backup_restores_fiscal_profile_and_document_bytes(self):
        self.add()
        self.service.save_billing_details(self.client, {'rfc': 'AAA010101AAA'})
        backup = self.folder / 'respaldo.sqlite3'
        self.db.backup(backup)
        self.service.delete_client_document(self.client, self.service.client_documents(self.client)[0]['id'])
        restored = Database(backup)
        try:
            service = Service(restored)
            self.assertEqual(service.billing_details(self.client)['rfc'], 'AAA010101AAA')
            row = service.client_documents(self.client)[0]
            self.assertEqual(row['sha256'], hashlib.sha256(self.content).hexdigest())
            service.export_client_document(self.client, row['id'], self.folder / 'restaurado.pdf')
            self.assertEqual((self.folder / 'restaurado.pdf').read_bytes(), self.content)
        finally:
            restored.conn.close()

    def test_upgrades_database_without_documents_without_changing_clients(self):
        self.db.conn.execute('DROP TABLE client_documents')
        self.db.conn.execute('DROP TABLE client_billing')
        self.db.conn.commit()
        self.db.conn.close()
        self.db = Database(self.path)
        self.service = Service(self.db)
        self.assertEqual(self.db.rows('SELECT name FROM clients WHERE id=?', (self.client,))[0][0], 'Ana Pérez')
        self.assertEqual(self.service.client_documents(self.client), [])
        self.add()
        self.assertEqual(len(self.service.client_documents(self.client)), 1)


if __name__ == '__main__':
    unittest.main()
