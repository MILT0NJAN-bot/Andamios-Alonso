import tempfile
import unittest
from pathlib import Path
from datetime import date,timedelta
from openpyxl import load_workbook
from app.database import Database
from app.service import Service
from app.excel_note import export_note


class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'payments.sqlite3'
        self.db=Database(self.path)
        self.service=Service(self.db, tax_rates=(0,0))
        self.item=self.db.rows("SELECT id FROM items WHERE name='Revolvedoras'")[0][0]
        self.service.save_item(self.item,'Revolvedoras',5,'450','daily')
        self.client=self.service.save_client(None,'Cliente','3121112222',None,'')
        self.key=self.service.create_rental(self.client,'Obra','2026-10-01','2026-10-03',{self.item:1})

    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()

    def test_deposit_partial_and_settlement(self):
        self.service.record_payment(self.key,'200','Efectivo',kind='Anticipo')
        self.assertEqual(self.service.payment_summary(self.key)['pending_cents'],70000)
        self.service.record_payment(self.key,'250','Transferencia',reference='Referencia 123')
        self.service.record_payment(self.key,'450','Tarjeta')
        summary=self.service.payment_summary(self.key)
        self.assertEqual(summary['paid_cents'],90000)
        self.assertEqual(summary['pending_cents'],0)
        self.assertEqual(summary['status'],'Pagado')
        self.assertEqual(self.db.rows('SELECT kind FROM payments ORDER BY id DESC')[0][0],'Liquidación')
        self.assertIn('PAGADO: $900.00',self.service.note(self.key))

    def test_invalid_payments_do_not_change_balance(self):
        for amount in ('0','-1','901','abc','0.001','NaN'):
            with self.assertRaises(ValueError):
                self.service.record_payment(self.key,amount)
        with self.assertRaises(ValueError):
            self.service.record_payment(self.key,'100',kind='Liquidación')
        with self.assertRaises(ValueError):
            self.service.record_payment(self.key,'100',method='Desconocido')
        with self.assertRaises(ValueError):
            self.service.record_payment(self.key,'100',paid_on=(date.today()+timedelta(days=1)).isoformat())
        self.assertEqual(len(self.db.rows('SELECT * FROM payments')),0)
        self.assertEqual(self.service.payment_summary(self.key)['pending_cents'],90000)

    def test_initial_payment_atomic_and_rollback(self):
        before=self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0]
        with self.assertRaises(ValueError):
            self.service.create_rental(None,'Obra','2026-10-01','2026-10-02',{self.item:1},
                client_data={'name':'Cliente nuevo','phone':'3127770000'},initial_payment={'amount':'999'})
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],before)
        self.assertEqual(len(self.db.rows("SELECT * FROM clients WHERE name='Cliente nuevo'")),0)
        key=self.service.create_rental(self.client,'Obra','2026-10-01','2026-10-02',{self.item:1},initial_payment={'amount':'150','kind':'Anticipo'})
        self.assertEqual(self.service.payment_summary(key)['pending_cents'],30000)

    def test_cancellation_preserves_history_and_reopens_balance(self):
        payment=self.service.record_payment(self.key,'900')
        with self.assertRaises(ValueError):
            self.service.cancel_payment(payment,' ')
        self.service.cancel_payment(payment,'Captura duplicada')
        summary=self.service.payment_summary(self.key)
        self.assertEqual(summary['paid_cents'],0)
        self.assertEqual(summary['pending_cents'],90000)
        self.assertEqual(len(self.db.rows('SELECT * FROM payments')),1)
        with self.assertRaises(ValueError):
            self.service.cancel_payment(payment,'Otra vez')

    def test_payment_after_return_and_balance_after_extension(self):
        self.service.record_payment(self.key,'900')
        self.service.extend_rental(self.key,1)
        self.assertEqual(self.service.payment_summary(self.key)['pending_cents'],45000)
        self.service.return_rental(self.key)
        self.service.record_payment(self.key,'450')
        self.assertEqual(self.service.payment_summary(self.key)['status'],'Pagado')

    def test_monthly_reduction_keeps_actual_payments_and_marks_paid(self):
        item=self.db.rows("SELECT id FROM items WHERE name='Andamios'")[0][0]
        self.service.save_item(item,'Andamios',5,'30','scaffold','200','450')
        key=self.service.create_rental(self.client,'Obra','2026-10-01','2026-10-30',{item:1})
        self.service.record_payment(key,'860')
        self.service.extend_rental(key,1)
        summary=self.service.payment_summary(key)
        self.assertEqual(summary['paid_cents'],86000)
        self.assertEqual(summary['status'],'Pagado')
        self.assertNotIn('credit_cents',summary)
        self.assertEqual(summary['pending_cents'],0)
        with self.assertRaises(ValueError):
            self.service.record_payment(key,'1')

    def test_second_connection_cannot_overpay(self):
        other=Database(self.path)
        try:
            Service(other).record_payment(self.key,'600')
            with self.assertRaises(ValueError):
                self.service.record_payment(self.key,'600')
            self.assertEqual(self.service.payment_summary(self.key)['paid_cents'],60000)
        finally:
            other.conn.close()

    def test_excel_balances_and_ledger_include_cancelled_payments(self):
        self.service.record_payment(self.key,'200',reference='=REFERENCIA')
        void=self.service.record_payment(self.key,'50')
        self.service.cancel_payment(void,'Error de importe')
        path=export_note(self.db,self.key,Path(self.temp.name)/'note.xlsx')
        wb=load_workbook(path,data_only=True)
        self.assertEqual(wb['Nota de renta']['I18'].value,200)
        self.assertEqual(wb['Nota de renta']['I19'].value,700)
        self.assertEqual(wb['Pagos']['F3'].data_type,'s')
        self.assertEqual(wb['Pagos']['G4'].value,'Anulado')
        self.assertIsNone(wb['Pagos'].freeze_panes)
        wb.close()


if __name__=='__main__':
    unittest.main()
