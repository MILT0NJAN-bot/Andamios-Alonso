import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path
from app.database import Database
from app.service import Service
from app.analytics import report


class OperationTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.path=Path(self.folder.name)/'test.sqlite3'
        self.db=Database(self.path)
        self.service=Service(self.db, tax_rates=(0,0))
        self.item=self.db.rows("SELECT id FROM items WHERE name='Revolvedoras'")[0][0]
        self.service.save_item(self.item,'Revolvedoras',10,'100','daily')
        self.client=self.service.save_client(None,'Cliente','3121112222',None,'')
        self.today=date.today()

    def tearDown(self):
        self.db.conn.close()
        self.folder.cleanup()

    def rent(self,quantity=6):
        key=self.service.create_rental(self.client,'Obra',self.today.isoformat(),(self.today+timedelta(days=7)).isoformat(),{self.item:quantity})
        return key,self.service.remaining_lines(key)[0]['id']

    def reserve(self,quantity,start=8,duration=7):
        return self.service.create_reservation(self.client,'Obra reservada',(self.today+timedelta(days=start)).isoformat(),
            (self.today+timedelta(days=start+duration)).isoformat(),{self.item:quantity})

    def test_partial_good_then_bad_closes_once_and_holds_damaged(self):
        key,line=self.rent()
        self.assertFalse(self.service.return_partial(key,[{'line_id':line,'quantity':4,'condition':'Bueno'}]))
        item=self.db.rows('SELECT * FROM items WHERE id=?',(self.item,))[0]
        self.assertEqual(item['available'],8)
        self.assertEqual(self.service.remaining_lines(key)[0]['pending'],2)
        self.assertTrue(self.service.return_partial(key,[{'line_id':line,'quantity':2,'condition':'Malo','notes':''}]))
        item=self.db.rows('SELECT * FROM items WHERE id=?',(self.item,))[0]
        self.assertEqual(item['available'],8)
        self.assertEqual(item['maintenance'],2)
        with self.assertRaises(ValueError):
            self.service.return_rental(key)
        self.service.release_equipment(self.item,1)
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],9)

    def test_invalid_receipt_rolls_back_all_lines_and_stock(self):
        key,line=self.rent()
        for entries in ([{'line_id':line,'quantity':7}], [{'line_id':line,'quantity':-1}],
                        [{'line_id':line,'quantity':1},{'line_id':line,'quantity':1}],
                        [{'line_id':line,'quantity':1,'condition':'Otro'}]):
            with self.assertRaises(ValueError):
                self.service.return_partial(key,entries)
        self.assertEqual(self.service.remaining_lines(key)[0]['pending'],6)
        self.assertEqual(len(self.db.rows('SELECT * FROM rental_returns')),0)

    def test_extensions_charge_only_remaining_units_and_payments_stay(self):
        key,line=self.rent()
        self.service.record_payment(key,'100')
        self.service.return_partial(key,[{'line_id':line,'quantity':4,'condition':'Bueno','notes':'No conservar en Bueno'}])
        quote=self.service.extend_rental(key,3)
        self.assertEqual(quote['added_cents'],60000)
        self.assertEqual(quote['total_cents'],480000)
        self.assertEqual(self.service.payment_summary(key)['paid_cents'],10000)
        self.assertEqual(self.db.rows('SELECT notes FROM rental_returns')[0][0],'')
        self.assertIn('$4,800.00',self.service.note(key))

    def test_bad_return_not_rented_or_removed_from_stock(self):
        key,line=self.rent(10)
        self.service.return_partial(key,[{'line_id':line,'quantity':10,'condition':'Malo','notes':'Cable roto'}])
        with self.assertRaises(ValueError):
            self.service.save_item(self.item,'Revolvedoras',9,'100','daily')
        with self.assertRaises(ValueError):
            self.reserve(1)
        with self.assertRaises(ValueError):
            self.service.release_equipment(self.item,11)
        self.assertEqual(report(self.db,self.today,self.today)['current_units'],0)

    def test_reservations_overlap_adjacent_and_cancel(self):
        first=self.reserve(7)
        with self.assertRaises(ValueError):
            self.reserve(4,start=9)
        self.reserve(3,start=9)
        self.reserve(10,start=22)
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],10)
        self.service.cancel_reservation(first)
        self.reserve(7,start=8)
        with self.assertRaises(ValueError):
            self.service.cancel_reservation(first)

    def test_sweep_allows_non_overlapping_reservations_in_same_query(self):
        self.reserve(10,start=8,duration=2)
        self.reserve(10,start=10,duration=2)
        self.assertEqual(self.service.period_available(self.item,self.today+timedelta(days=8),self.today+timedelta(days=12)),0)

    def test_convert_reserved_prices_once_without_duplicate_stock(self):
        key=self.reserve(4,start=0)
        self.service.save_item(self.item,'Revolvedoras',10,'999','daily')
        rental=self.service.start_reservation(key)
        self.assertEqual(self.db.rows('SELECT total_cents FROM rentals WHERE id=?',(rental,))[0][0],280000)
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],6)
        with self.assertRaises(ValueError):
            self.service.start_reservation(key)
        with self.assertRaises(ValueError):
            self.service.cancel_reservation(key)

    def test_future_delivery_and_direct_rental_conflict(self):
        key=self.reserve(9,start=2)
        with self.assertRaises(ValueError):
            self.service.start_reservation(key)
        with self.assertRaises(ValueError):
            self.rent(2)
        self.assertEqual(len(self.db.rows('SELECT * FROM rentals')),0)

    def test_extension_cannot_take_reserved_stock(self):
        rental,_=self.rent(6)
        self.reserve(7,start=8)
        with self.assertRaises(ValueError):
            self.service.extend_rental(rental,3)

    def test_legacy_closed_rental_stays_closed_on_reopen(self):
        key,_=self.rent()
        self.service.return_rental(key)
        for column in ('returned_qty','delivery_condition','delivery_notes'):
            self.db.conn.execute(f'ALTER TABLE rental_lines DROP COLUMN {column}')
        self.db.conn.execute('ALTER TABLE items DROP COLUMN maintenance')
        self.db.conn.commit()
        self.db.conn.close()
        self.db=Database(self.path)
        self.service=Service(self.db, tax_rates=(0,0))
        self.assertEqual(self.service.remaining_lines(key)[0]['pending'],0)
        self.assertEqual(self.service.remaining_lines(key)[0]['delivery_condition'],'Sin registro previo')

    def test_backups_are_consistent_and_retained(self):
        self.rent()
        target=self.db.automatic_backup(force=True)
        other=Database(target)
        self.assertEqual(len(other.rows('SELECT * FROM rentals')),1)
        other.conn.close()
        for index in range(35):
            self.db.automatic_backup(force=True,today=self.today+timedelta(days=index))
        self.assertEqual(len(list((self.path.parent/'respaldos').glob('automatico-*.sqlite3'))),30)

    def test_backup_failure_is_reported_without_losing_data(self):
        from unittest.mock import patch
        with patch.object(self.db,'backup',side_effect=OSError('Disco de prueba lleno')):
            self.assertIsNone(self.db.automatic_backup(force=True))
            self.assertIn('lleno',self.db.backup_error)
        self.assertEqual(len(self.db.rows('SELECT * FROM items')),7)


if __name__=='__main__':
    unittest.main()
