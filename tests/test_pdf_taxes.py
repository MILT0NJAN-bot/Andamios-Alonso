import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path
from pypdf import PdfReader
from app.database import Database
from app.service import Service
from app.taxes import amounts
from app.pdf_note import export_pdf


class PdfTaxTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=Database(Path(self.temp.name)/'tax.sqlite3')
        self.service=Service(self.db)
        self.item=self.db.rows("SELECT id FROM items WHERE name='Revolvedoras'")[0][0]
        self.service.save_item(self.item,'Revolvedoras',100,'100','daily',replacement_cost='25000')
        self.client=self.service.save_client(None,'Cliente Álvarez & Hermanos','3121112222',None,'')

    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()

    def rent(self,quantity=1,invoice=False):
        return self.service.create_rental(self.client,'Obra de prueba',date.today().isoformat(),(date.today()+timedelta(days=2)).isoformat(),{self.item:quantity},invoice_required=invoice)

    def test_reference_calculation_and_half_up(self):
        data=amounts(2460000,1600,0)
        self.assertEqual(data['vat_cents'],393600)
        self.assertEqual(data['isr_cents'],0)
        self.assertEqual(data['total_cents'],2853600)
        self.assertEqual(amounts(40)['total_cents'],40)

    def test_new_rental_payments_extension_and_return_use_gross(self):
        key=self.rent(invoice=True)
        self.assertEqual(self.service.payment_summary(key)['total_cents'],23200)
        self.service.record_payment(key,'100','Transferencia')
        self.assertEqual(self.service.payment_summary(key)['pending_cents'],13200)
        self.assertEqual(self.service.extend_rental(key,1)['total_cents'],34800)
        line=self.service.remaining_lines(key)[0]
        self.service.return_partial(key,[{'line_id':line['id'],'quantity':1,'condition':'Bueno'}])
        self.assertEqual(self.service.payment_summary(key)['pending_cents'],24800)

    def test_historical_note_taxes_explicit_once_keep_payments(self):
        old=Service(self.db,tax_rates=(0,0))
        key=old.create_rental(self.client,'Obra',date.today().isoformat(),(date.today()+timedelta(days=2)).isoformat(),{self.item:1})
        old.record_payment(key,'200','Transferencia')
        self.assertEqual(self.service.payment_summary(key)['pending_cents'],0)
        self.service.apply_taxes(key)
        self.assertEqual(self.service.payment_summary(key)['paid_cents'],20000)
        self.assertEqual(self.service.payment_summary(key)['pending_cents'],3200)
        with self.assertRaises(ValueError):
            self.service.apply_taxes(key)

    def test_reservation_uses_tax_snapshot(self):
        start=date.today();end=start+timedelta(days=2)
        key=self.service.create_reservation(self.client,'Obra',start.isoformat(),end.isoformat(),{self.item:1},invoice_required=True,_legacy_without_deposit=True)
        rental=Service(self.db,tax_rates=(0,0)).start_reservation(key)
        self.assertEqual(self.service.payment_summary(rental)['total_cents'],23200)

    def test_migration_keeps_old_total_and_payments(self):
        old=Service(self.db,tax_rates=(0,0))
        key=old.create_rental(self.client,'Obra',date.today().isoformat(),(date.today()+timedelta(days=2)).isoformat(),{self.item:1})
        old.record_payment(key,'200','Transferencia')
        self.db.conn.execute('DROP VIEW financial_payments')
        for table in ('rentals','reservations'):
            for column in ('subtotal_cents','vat_bp','isr_bp','vat_cents','isr_cents'):
                self.db.conn.execute(f'ALTER TABLE {table} DROP COLUMN {column}')
        self.db.conn.commit()
        path=self.db.path
        self.db.conn.close()
        self.db=Database(path)
        self.service=Service(self.db)
        self.assertEqual(self.service.payment_summary(key)['pending_cents'],0)
        row=self.db.rows('SELECT * FROM rentals WHERE id=?',(key,))[0]
        self.assertEqual(row['subtotal_cents'],20000)
        self.assertEqual(row['vat_bp'],0)

    def test_pdf_contains_table_bank_taxes_and_balances(self):
        key=self.rent(2,invoice=True)
        self.service.record_payment(key,'100','Transferencia')
        path=export_pdf(self.db,key,Path(self.temp.name)/'note.pdf')
        reader=PdfReader(path)
        self.assertEqual(len(reader.pages),1)
        text='\n'.join(page.extract_text() for page in reader.pages)
        for value in ('PIEZAS','Revolvedoras','AOJM740531IH9','0159067418','012090001590674189','PYME BBVA',
                      'Miguel','IVA 16%','$464.00','$364.00','$50,000.00'):
            self.assertIn(value,text)
        self.assertNotIn('ISR',text)
        self.assertTrue(any('/XObject' in page['/Resources'] for page in reader.pages))
        for page in reader.pages:
            self.assertAlmostEqual(float(page.mediabox.width),612)

    def test_pdf_is_one_page_without_return_annex_and_keeps_notes_in_database(self):
        key=self.rent()
        line=self.service.remaining_lines(key)[0]
        self.service.return_partial(key,[{'line_id':line['id'],'quantity':1,'condition':'Malo','notes':'Observación de prueba. '*150}])
        path=export_pdf(self.db,key,Path(self.temp.name)/'long.pdf')
        reader=PdfReader(path)
        text='\n'.join(page.extract_text() for page in reader.pages)
        self.assertNotIn('Observación de prueba',text)
        self.assertEqual(len(reader.pages),1)
        self.assertIn('Observación',self.db.rows('SELECT notes FROM rental_returns WHERE line_id=?',(line['id'],))[0][0])

    def test_no_invoice_default_and_invoice_toggle_preserves_payments(self):
        key=self.rent()
        self.assertEqual(self.service.payment_summary(key)['total_cents'],20000)
        self.service.record_payment(key,'200','Transferencia')
        self.service.set_invoice(key,True)
        self.assertEqual(self.service.payment_summary(key)['pending_cents'],3200)
        self.service.set_invoice(key,False)
        self.assertEqual(self.service.payment_summary(key)['paid_cents'],20000)
        self.assertEqual(self.service.payment_summary(key)['pending_cents'],0)
        path=export_pdf(self.db,key,Path(self.temp.name)/'no-invoice.pdf')
        text='\n'.join(page.extract_text() for page in PdfReader(path).pages)
        self.assertNotIn('ISR',text)
        self.assertNotIn('IVA 16%',text)
        self.assertIn('Sin IVA',text)

    def test_equipment_value_snapshot_does_not_charge_rental(self):
        key=self.rent(2)
        self.service.save_item(self.item,'Revolvedoras',100,'100','daily',replacement_cost='30000')
        line=self.db.rows('SELECT * FROM rental_lines WHERE rental_id=?',(key,))[0]
        self.assertEqual(line['replacement_cents'],2500000)
        self.assertEqual(self.service.payment_summary(key)['total_cents'],40000)

    def test_missing_value_can_be_completed_without_invented_amounts(self):
        self.service.save_item(self.item,'Revolvedoras',100,'100','daily',replacement_cost='')
        key=self.rent()
        path=export_pdf(self.db,key,Path(self.temp.name)/'unknown.pdf')
        text='\n'.join(page.extract_text() for page in PdfReader(path).pages)
        self.assertIn('Por definir',text)
        self.service.save_item(self.item,'Revolvedoras',100,'100','daily',replacement_cost='28000')
        self.assertEqual(self.db.rows('SELECT replacement_cents FROM rental_lines WHERE rental_id=?',(key,))[0][0],2800000)

    def test_reserved_equipment_value_is_preserved_on_delivery(self):
        start=date.today();end=start+timedelta(days=2)
        key=self.service.create_reservation(self.client,'Obra',start.isoformat(),end.isoformat(),{self.item:1},_legacy_without_deposit=True)
        self.service.save_item(self.item,'Revolvedoras',100,'100','daily',replacement_cost='30000')
        rental=self.service.start_reservation(key)
        self.assertEqual(self.db.rows('SELECT replacement_cents FROM rental_lines WHERE rental_id=?',(rental,))[0][0],2500000)

    def test_previous_isr_removed_once_with_audit_and_same_payments(self):
        key=self.rent(invoice=True)
        self.service.record_payment(key,'100','Transferencia')
        self.db.conn.execute('UPDATE rentals SET isr_bp=125,isr_cents=250,total_cents=22950 WHERE id=?',(key,))
        self.db.conn.execute("DELETE FROM migrations WHERE name='optional_vat_no_isr_v1'")
        self.db.conn.commit()
        path=self.db.path;self.db.conn.close()
        self.db=Database(path);self.service=Service(self.db)
        row=self.db.rows('SELECT * FROM rentals WHERE id=?',(key,))[0]
        self.assertEqual(row['isr_bp'],0)
        self.assertEqual(row['total_cents'],23200)
        self.assertEqual(self.service.payment_summary(key)['paid_cents'],10000)
        self.assertEqual(len(self.db.rows('SELECT * FROM tax_adjustments WHERE record_id=?',(key,))),1)


if __name__=='__main__':
    unittest.main()
