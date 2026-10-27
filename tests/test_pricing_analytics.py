import tempfile
import unittest
from pathlib import Path
from datetime import date,timedelta
from app.database import Database
from app.service import Service
from app.pricing import unit_total
from app.analytics import report


class TariffTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.path=Path(self.folder.name)/'test.sqlite3'
        self.db=Database(self.path)
        self.service=Service(self.db, tax_rates=(0,0))
        self.scaffold=self.db.rows("SELECT * FROM items WHERE name='Andamios'")[0]
        self.key=self.scaffold['id']
        self.service.save_item(self.key,'Andamios',20,'30','scaffold','200','450')
        self.client=self.service.save_client(None,'Cliente','3121112222',None,'')

    def tearDown(self):
        self.db.conn.close()
        self.folder.cleanup()

    def rent(self,days,quantity=1):
        return self.service.create_rental(self.client,'Obra','2026-10-01',(date(2026,10,1)+timedelta(days=days)).isoformat(),{self.key:quantity})

    def test_week_extras_month_and_month_extras(self):
        for days,expected in [(7,20000),(8,23000),(10,29000),(29,86000),(30,45000),(31,48000),(60,90000)]:
            with self.subTest(days=days):
                self.assertEqual(unit_total(self.scaffold,days),expected)
        for days in (1,6):
            with self.assertRaises(ValueError):
                self.rent(days)

    def test_monthly_extension_negative_adjustment_is_recorded(self):
        key=self.rent(29,2)
        quote=self.service.extend_rental(key,1)
        self.assertEqual(quote['total_cents'],90000)
        self.assertEqual(quote['added_cents'],-82000)
        extension=self.db.rows('SELECT * FROM rental_extensions')[0]
        self.assertEqual(extension['adjustment_cents'],-82000)
        self.assertIn('$900.00',self.service.note(key))
        self.service.save_item(self.key,'Andamios',20,'99','scaffold','800','1000')
        self.assertEqual(self.service.extend_rental(key,1)['total_cents'],96000)

    def test_reports_daily_totals_no_double_count_and_units(self):
        self.rent(7,2)
        data=report(self.db,date(2026,10,1),date(2026,10,7))
        self.assertEqual(sum(v['expected_cents'] for v in data['days'].values()),40000)
        self.assertEqual(sum(v['rentals'] for v in data['days'].values()),1)
        self.assertEqual(sum(v['units'] for v in data['days'].values()),2)
        self.assertEqual(data['popular'][0]['units'],2)
        self.assertEqual(data['current_units'],2)
        next_day=report(self.db,date(2026,10,8),date(2026,10,8))
        self.assertEqual(next_day['days'][date(2026,10,8)]['expected_cents'],0)

    def test_migration_once_does_not_reset_user_tariff(self):
        self.service.save_item(self.key,'Andamios',20,'35','scaffold','220','500')
        self.db.conn.close()
        self.db=Database(self.path)
        row=self.db.rows('SELECT * FROM items WHERE id=?',(self.key,))[0]
        self.assertEqual(row['price_cents'],3500)
        self.assertEqual(row['month_cents'],50000)
        self.assertEqual(self.db.rows("SELECT price_cents FROM items WHERE name='Revolvedoras'")[0][0],45000)

    def test_empty_report_and_period_validation(self):
        data=report(self.db,date(2026,10,1),date(2026,10,7))
        self.assertEqual(data['popular'],[])
        self.assertEqual(sum(v['expected_cents'] for v in data['days'].values()),0)
        with self.assertRaises(ValueError):
            report(self.db,date(2026,10,7),date(2026,10,1))


if __name__=='__main__':
    unittest.main()
