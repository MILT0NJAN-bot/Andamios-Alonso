import json
import sqlite3
import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path
from unittest.mock import patch
from app.cash import Cash
from app.database import Database
from app.service import Service


class CashTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=Database(Path(self.temp.name)/'db.sqlite3');self.cash=Cash(self.db)
        self.day=date.today().isoformat()
        self.cash.open_day(self.day,'500','Secretaria')
        self.employee=self.cash.catalog('Empleado','Ana')
        self.vehicle=self.cash.catalog('Vehículo','Camioneta 1')
        self.service=Service(self.db)
        self.item=self.db.rows('SELECT id FROM items LIMIT 1')[0][0]
        self.service.save_item(self.item,'Equipo',5,'100','daily')
        self.client=self.service.save_client(None,'Cliente','3121234567',None,'','Obra')
        self.rental=self.service.create_rental(self.client,'Obra',self.day,(date.today()+timedelta(days=10)).isoformat(),{self.item:1})

    def tearDown(self):
        self.db.conn.close();self.temp.cleanup()

    def spend(self, amount='100',category='Otros gastos',method='Efectivo',entity=None,period=''):
        return self.cash.add(self.day,category,amount,method,'Concepto','Ana',entity,period)

    def test_cash_card_and_owner_separated(self):
        self.service.record_payment(self.rental,'300','Efectivo')
        self.service.record_payment(self.rental,'200','Transferencia')
        self.service.record_payment(self.rental,'100','Tarjeta')
        self.spend('50','Gasolina',entity=self.vehicle)
        self.spend('200','Sueldos',entity=self.employee,period='Semana 1')
        self.spend('100','Retiro del dueño')
        self.spend('80','Aportación del dueño')
        r=self.cash.day_report(self.day)
        self.assertEqual(r['operating_income'],60000)
        self.assertEqual(r['expenses'],25000)
        self.assertEqual(r['expected'],53000)
        self.assertEqual(r['incoming']['Transferencia'],20000)

    def test_close_locks_payments_and_expenses(self):
        payment=self.service.record_payment(self.rental,'100')
        movement=self.spend('50')
        key=self.cash.close(self.day,'550','Ana')
        with self.assertRaises(ValueError):self.spend()
        with self.assertRaises(ValueError):self.cash.cancel(movement,'Error','Ana')
        with self.assertRaises(sqlite3.IntegrityError):self.service.record_payment(self.rental,'1')
        with self.assertRaises(sqlite3.IntegrityError):self.service.cancel_payment(payment,'Error')
        with self.assertRaises(ValueError):self.cash.close(self.day,'550','Ana')
        snap=json.loads(self.db.rows('SELECT snapshot FROM cash_closings WHERE id=?',(key,))[0][0])
        self.assertEqual(snap['difference'],0)

    def test_reopen_retains_previous_snapshot(self):
        key=self.cash.close(self.day,'490','Ana','Faltan diez pesos')
        with self.assertRaises(ValueError):self.cash.reopen(self.day,'','Ana')
        self.cash.reopen(self.day,'Corregir gasto','Supervisor')
        self.spend('10')
        self.cash.close(self.day,'490','Ana')
        self.assertEqual(len(self.db.rows('SELECT * FROM cash_closings')),2)
        first=json.loads(self.db.rows('SELECT snapshot FROM cash_closings WHERE id=?',(key,))[0][0])
        self.assertEqual(first['expected'],50000)
        self.assertEqual(first['difference'],-1000)

    def test_difference_requires_explanation(self):
        with self.assertRaises(ValueError):self.cash.close(self.day,'499','Ana')
        self.assertEqual(self.cash.day_report(self.day)['status'],'Abierta')

    def test_desktop_policy_requires_open_before_rental_and_payment(self):
        strict=Service(self.db,require_cash_open=True)
        with self.db.conn:self.db.conn.execute('DELETE FROM cash_days')
        before=self.db.rows('SELECT COUNT(*) FROM rentals')[0][0]
        with self.assertRaises(ValueError):
            strict.create_rental(self.client,'Obra',self.day,(date.today()+timedelta(days=2)).isoformat(),{self.item:1})
        with self.assertRaises(ValueError):strict.record_payment(self.rental,'100')
        self.assertEqual(self.db.rows('SELECT COUNT(*) FROM rentals')[0][0],before)
        self.cash.open_day(self.day,'0','Laura')
        strict.record_payment(self.rental,'100')
        self.cash.close(self.day,'100','Laura')
        with self.assertRaises(ValueError):strict.record_payment(self.rental,'10')

    def test_void_preserves_record_excludes_amount(self):
        key=self.spend()
        self.cash.cancel(key,'Captura duplicada','Ana')
        r=self.cash.day_report(self.day)
        self.assertEqual(r['expected'],50000)
        self.assertTrue(r['entries'][0]['cancelled'])
        with self.assertRaises(ValueError):self.cash.cancel(key,'Otra','Ana')

    def test_validation_employee_vehicle_period(self):
        for category,entity,period in [('Sueldos',self.vehicle,'Semana'),('Sueldos',self.employee,''),('Gasolina',None,''),('Mantenimiento',self.employee,'')]:
            with self.assertRaises(ValueError):self.spend(category=category,entity=entity,period=period)
        for amount in ('-1','0','1.001','nan'):
            with self.assertRaises(ValueError):self.spend(amount)
        with self.assertRaises(ValueError):self.cash.open_day(self.day,'100','Otra')
        with self.assertRaises(ValueError):self.cash.open_day((date.today()+timedelta(days=1)).isoformat(),'100','Ana')

    def test_pdf_and_snapshot_immutable(self):
        from app.cash_pdf import export_cash
        from pypdf import PdfReader
        key=self.cash.close(self.day,'500','Ana')
        snapshot=json.loads(self.db.rows('SELECT snapshot FROM cash_closings WHERE id=?',(key,))[0][0])
        output=Path(self.temp.name)/'cash.pdf';export_cash(snapshot,output)
        self.assertIn('CORTE CERRADO',PdfReader(output).pages[0].extract_text())
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.conn:self.db.conn.execute("UPDATE cash_closings SET snapshot='{}' WHERE id=?",(key,))

    def test_preview_copies_without_modifying_source(self):
        from preview_cash import preview_path
        with patch('preview_cash.default_path',return_value=self.db.path):
            target=preview_path()
            clone=Database(target)
            with clone.conn:clone.conn.execute('DELETE FROM cash_days')
            clone.conn.close()
            self.assertEqual(len(self.db.rows('SELECT * FROM cash_days')),1)
            self.assertEqual(preview_path(),target)
