import unittest
import sqlite3
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch
from tests import test_service
from app.database import Database
from app.printing import print_pdf


class RemovalTests(unittest.TestCase):
    setUp=test_service.RentalTests.setUp
    tearDown=test_service.RentalTests.tearDown

    def test_remove_keeps_history_and_cannot_rent_again(self):
        key=self.service.create_rental(self.client,'Obra','2026-11-07','2026-11-09',{self.item:1})
        with self.assertRaises(ValueError):self.service.delete_item(self.item)
        self.service.return_rental(key)
        self.service.delete_item(self.item)
        self.assertIn('Equipo',self.service.note(key))
        with self.assertRaises(ValueError):self.service.create_rental(self.client,'Obra','2026-11-07','2026-11-09',{self.item:1})
        other=Database(self.db.path)
        try:self.assertEqual(other.rows('SELECT archived FROM items WHERE id=?',(self.item,))[0][0],1)
        finally:other.conn.close()

    def test_remove_respects_future_reservations(self):
        start=date.today()+timedelta(days=2)
        self.service.create_reservation(self.client,'Obra',start.isoformat(),(start+timedelta(days=2)).isoformat(),{self.item:1},_legacy_without_deposit=True)
        with self.assertRaises(ValueError):self.service.delete_item(self.item)
        self.assertEqual(self.db.rows('SELECT archived FROM items WHERE id=?',(self.item,))[0][0],0)

    def test_windows_print_and_preview_fallback(self):
        pdf=self.db.path.parent/'report.pdf';pdf.write_bytes(b'%PDF-1.4\n')
        with patch('app.printing.os.startfile') as shell:
            self.assertEqual(print_pdf(pdf),'print');self.assertEqual(shell.call_args.args[1],'print')
        with patch('app.printing.os.startfile',side_effect=[OSError('Sin manejador de impresion'),None]) as shell:
            self.assertEqual(print_pdf(pdf),'preview');self.assertEqual(shell.call_args.args[1],'open')

    def test_payment_classifies_itself_and_only_balance_determines_paid(self):
        key=self.service.create_rental(self.client,'Obra','2026-11-07','2026-11-09',{self.item:1})
        first=self.service.record_payment(key,'50')
        self.assertEqual(self.service.payment_summary(key)['status'],'Pendiente')
        self.assertEqual(self.db.rows('SELECT kind FROM payments WHERE id=?',(first,))[0][0],'Anticipo')
        remainder=self.service.payment_summary(key)['pending_cents']
        final=self.service.record_payment(key,str(remainder/100))
        self.assertEqual(self.db.rows('SELECT kind FROM payments WHERE id=?',(final,))[0][0],'Liquidación')
        self.assertEqual(self.service.payment_summary(key)['status'],'Pagado')
