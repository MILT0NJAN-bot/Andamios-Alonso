import csv
import io
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from datetime import date,timedelta
from app.database import Database
from app.service import Service


class TransferReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.db=Database(self.root/'db.sqlite3');self.service=Service(self.db)
        self.client=self.service.save_client(None,'Ana','3121234567',None,'','Obra')
        self.item=self.db.rows('SELECT id FROM items LIMIT 1')[0][0]
        self.service.save_item(self.item,'Equipo',20,'500','daily')
        self.day=date.today().isoformat();self.due=(date.today()+timedelta(days=2)).isoformat()
        self.file=self.root/'Transferencia.pdf';self.file.write_bytes(b'%PDF-1.4\nDemo receipt')

    def tearDown(self):self.db.conn.close();self.temp.cleanup()

    def rent(self,invoice=False,initial=None):
        return self.service.create_rental(self.client,'Obra',self.day,self.due,{self.item:1},invoice_required=invoice,initial_payment=initial)

    def test_invoice_rejects_cash_card_including_initial_transaction(self):
        rental=self.rent(True)
        for method in ('Efectivo','Tarjeta'):
            with self.assertRaises(ValueError):self.service.record_payment(rental,'100',method)
            count=self.db.rows('SELECT COUNT(*) FROM rentals')[0][0]
            with self.assertRaises(ValueError):self.rent(True,dict(amount='100',method=method))
            self.assertEqual(self.db.rows('SELECT COUNT(*) FROM rentals')[0][0],count)
        self.assertEqual(len(self.db.rows('SELECT * FROM payments')),0)

    def test_receipt_in_profile_and_accountant_zip(self):
        rental=self.rent(True)
        payment=self.service.record_payment(rental,'100','Transferencia',receipt_path=self.file)
        rows=self.service.client_documents(self.client)
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['category'],'Comprobantes de transferencia')
        self.assertEqual(self.service.transfer_payments()[0]['receipt_count'],1)
        output=self.root/'contador.zip';self.service.export_accountant_receipts(self.day,self.day,output)
        with ZipFile(output) as archive:
            names=archive.namelist();member=next(n for n in names if n.endswith('.pdf'))
            self.assertIn(f'Pago_{payment}',member);self.assertEqual(archive.read(member),self.file.read_bytes())
            self.assertIn('VIGENTE',archive.read('Relacion_de_transferencias.csv').decode('utf-8-sig'))
        profile=self.root/'cliente.zip';self.service.export_client_billing(self.client,profile)
        with ZipFile(profile) as archive:self.assertTrue(any(n.endswith('.pdf') for n in archive.namelist()))

    def test_non_invoice_transfer_profile_only(self):
        rental=self.rent(False)
        payment=self.service.record_payment(rental,'100','Transferencia',receipt_path=self.file)
        self.assertEqual(len(self.service.client_documents(self.client)),1)
        self.assertFalse(self.service.transfer_payments(invoice_only=True))
        self.assertEqual(self.service.transfer_payments(invoice_only=False)[0]['id'],payment)
        with self.assertRaises(ValueError):self.service.export_accountant_receipts(self.day,self.day,self.root/'empty.zip')
        self.service.record_payment(rental,'100','Efectivo')
        self.service.record_payment(rental,'100','Tarjeta')

    def test_optional_missing_then_late_attachment_and_duplicates(self):
        rental=self.rent(True);payment=self.service.record_payment(rental,'100','Transferencia')
        result=self.service.export_accountant_receipts(self.day,self.day,self.root/'pending.zip')
        self.assertEqual(result,dict(documents=0,pending=1))
        from app.cash import Cash
        Cash(self.db).open_day(self.day,'0','Laura');Cash(self.db).close(self.day,'0','Laura')
        self.service.attach_transfer_receipt(payment,self.file)
        self.service.attach_transfer_receipt(payment,self.file)
        self.assertEqual(len(self.service.transfer_documents(payment)),1)
        self.assertEqual(self.service.payment_summary(rental)['paid_cents'],10000)

    def test_bad_file_rolls_back_initial_payment_and_rental(self):
        invalid=self.root/'bad.pdf';invalid.write_bytes(b'Not a PDF')
        with self.assertRaises(ValueError):self.rent(True,dict(amount='100',method='Transferencia',receipt_path=invalid))
        self.assertFalse(self.db.rows('SELECT * FROM rentals'))
        self.assertFalse(self.db.rows('SELECT * FROM client_documents'))
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],20)

    def test_invoice_transition_and_void_evidence(self):
        rental=self.rent();cash=self.service.record_payment(rental,'100','Efectivo')
        with self.assertRaises(ValueError):self.service.set_invoice(rental,True)
        self.assertEqual(self.db.rows('SELECT method FROM payments WHERE id=?',(cash,))[0][0],'Efectivo')
        self.service.cancel_payment(cash,'Error de captura')
        self.service.set_invoice(rental,True)
        payment=self.service.record_payment(rental,'100','Transferencia',receipt_path=self.file)
        document=self.service.transfer_documents(payment)[0]['id']
        with self.assertRaises(ValueError):self.service.delete_client_document(self.client,document)
        self.service.cancel_payment(payment,'Error de captura')
        with self.assertRaises(ValueError):self.service.attach_transfer_receipt(payment,self.file)
        self.service.export_accountant_receipts(self.day,self.day,self.root/'void.zip')
        with ZipFile(self.root/'void.zip') as archive:self.assertTrue(any(n.startswith('Anulados/') for n in archive.namelist()))

    def test_dates_and_non_transfer_attachment(self):
        rental=self.rent();payment=self.service.record_payment(rental,'100','Efectivo')
        with self.assertRaises(ValueError):self.service.attach_transfer_receipt(payment,self.file)
        with self.assertRaises(ValueError):self.service.record_payment(rental,'100','Tarjeta',receipt_path=self.file)
        with self.assertRaises(ValueError):self.service.transfer_payments(self.due,self.day)
