import tempfile
import unittest
from pathlib import Path
from datetime import date,timedelta
from contextlib import ExitStack,contextmanager
from unittest.mock import patch
from app.database import Database
from app.service import Service
from app.cash import Cash


@contextmanager
def clock(day):
    class FixedDate(date):
        @classmethod
        def today(cls):return day
    with ExitStack() as stack:
        for module in ('app.operations','app.service','app.reservation_payments','app.cash'):
            stack.enter_context(patch(module+'.date',FixedDate))
        yield


class ScheduledReservationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.db=Database(self.root/'test.sqlite3');self.service=Service(self.db,require_cash_open=True);self.cash=Cash(self.db)
        self.today=date.today();self.cash.open_day(self.today.isoformat(),'0','Prueba')
        self.client=self.service.save_client(None,'Cliente','3121234567',None,'')
        self.item=self.db.rows("SELECT id FROM items WHERE name='Revolvedoras'")[0][0]
        self.service.save_item(self.item,'Revolvedoras',1,'100','daily')
        self.start=self.today+timedelta(days=6);self.end=self.start+timedelta(days=7)

    def tearDown(self):self.db.conn.close();self.temp.cleanup()

    def reserve(self,**kwargs):
        return self.service.create_reservation(self.client,'Obra',self.start.isoformat(),self.end.isoformat(),{self.item:1},**kwargs)

    def test_half_required_and_no_stock_hold_until_received(self):
        key=self.reserve()
        self.assertFalse(self.service.reservation_payment_summary(key)['confirmed'])
        self.assertEqual(self.service.period_available(self.item,self.start,self.end),1)
        with self.assertRaises(ValueError):self.service.record_reservation_payment(key,'349.99')
        self.service.record_reservation_payment(key,'350')
        self.assertTrue(self.service.reservation_payment_summary(key)['confirmed'])
        self.assertEqual(self.service.period_available(self.item,self.start,self.end),0)
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],1)

    def test_example_19_21_23_24_25(self):
        key=self.reserve(initial_payment=dict(amount='350'))
        rental_day=self.today+timedelta(days=2)
        with clock(rental_day):
            self.cash.open_day(rental_day.isoformat(),'0','Prueba')
            # Retornar el día 24 quitaría el único día completo de preparación.
            with self.assertRaises(ValueError):
                self.service.create_rental(self.client,'Otra obra',rental_day.isoformat(),(self.today+timedelta(days=5)).isoformat(),{self.item:1})
            rental=self.service.create_rental(self.client,'Otra obra',rental_day.isoformat(),(self.today+timedelta(days=4)).isoformat(),{self.item:1})
        with clock(self.today+timedelta(days=4)):self.service.return_rental(rental)
        with clock(self.start):
            self.cash.open_day(self.start.isoformat(),'0','Prueba')
            delivered=self.service.start_reservation(key)
        self.assertEqual(self.service.payment_summary(delivered)['paid_cents'],35000)
        self.assertEqual(self.service.payment_summary(delivered)['pending_cents'],35000)

    def test_conversion_after_closed_cash_does_not_duplicate_income(self):
        key=self.reserve(initial_payment=dict(amount='350'))
        old=self.cash.day_report(self.today.isoformat())
        self.cash.close(self.today.isoformat(),'350','Prueba')
        with clock(self.start):
            self.cash.open_day(self.start.isoformat(),'0','Prueba')
            rental=self.service.start_reservation(key)
            self.assertEqual(self.cash.day_report(self.today.isoformat())['operating_income'],old['operating_income'])
            self.assertEqual(self.cash.day_report(self.start.isoformat())['operating_income'],0)
            self.service.record_payment(rental,'350')
            self.assertEqual(self.cash.day_report(self.start.isoformat())['operating_income'],35000)
        self.assertEqual(len(self.db.rows('SELECT * FROM financial_payments')),2)

    def test_invoice_deposit_and_receipt_follow_to_rental(self):
        receipt=self.root/'receipt.pdf';receipt.write_bytes(b'%PDF-1.4\nTest')
        with self.assertRaises(ValueError):self.reserve(invoice_required=True,initial_payment=dict(amount='406',method='Efectivo'))
        key=self.reserve(invoice_required=True,initial_payment=dict(amount='406',method='Transferencia',receipt_path=receipt))
        payment=self.db.rows('SELECT id FROM financial_payments WHERE reservation_id=?',(key,))[0][0]
        self.assertEqual(len(self.service.transfer_documents(payment)),1)
        self.service.export_accountant_receipts(self.today.isoformat(),self.today.isoformat(),self.root/'before.zip')
        with clock(self.start):
            self.cash.open_day(self.start.isoformat(),'0','Prueba')
            rental=self.service.start_reservation(key)
        self.assertEqual(self.service.payment_summary(rental)['paid_cents'],40600)
        self.assertEqual(self.db.rows('SELECT rental_id FROM financial_payments WHERE id=?',(payment,))[0][0],rental)
        self.assertEqual(len(self.service.client_documents(self.client)),1)

    def test_unfunded_competing_quote_cannot_take_paid_reservation(self):
        a=self.reserve();b=self.reserve()
        self.service.record_reservation_payment(a,'350')
        with self.assertRaises(ValueError):self.service.record_reservation_payment(b,'350')
        self.assertEqual(self.service.reservation_payment_summary(b)['paid_cents'],0)

    def test_cancel_keeps_money_and_frees_dates(self):
        key=self.reserve(initial_payment=dict(amount='350'))
        self.service.cancel_reservation(key)
        self.assertEqual(self.service.period_available(self.item,self.start,self.end),1)
        self.assertEqual(self.cash.day_report(self.today.isoformat())['operating_income'],35000)

    def test_overdue_previous_rental_flags_booking_risk(self):
        self.reserve(initial_payment=dict(amount='350'))
        rental_day=self.today+timedelta(days=2)
        with clock(rental_day):
            self.cash.open_day(rental_day.isoformat(),'0','Prueba')
            self.service.create_rental(self.client,'Otra obra',rental_day.isoformat(),(self.today+timedelta(days=4)).isoformat(),{self.item:1})
        with clock(self.today+timedelta(days=5)):
            self.assertEqual(len(self.service.reservation_conflicts()),1)

    def test_future_rental_must_use_reservations(self):
        with self.assertRaises(ValueError):self.service.create_rental(self.client,'Obra',self.start.isoformat(),self.end.isoformat(),{self.item:1})
