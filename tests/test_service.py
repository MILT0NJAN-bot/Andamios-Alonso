import tempfile
import unittest
from pathlib import Path
from app.database import Database
from app.service import Service, cents


class RentalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name)/'test.sqlite3')
        self.service = Service(self.db, tax_rates=(0,0))
        self.item = self.db.rows('SELECT id FROM items LIMIT 1')[0]['id']
        self.service.save_item(self.item,'Equipo',5,'125.50','daily')
        self.client = self.service.save_client(None,'Ana Pérez','5551234567',[5,4,3],'Buen cuidado','Obra 1')

    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()

    def rent(self, quantity=2):
        return self.service.create_rental(self.client,'Obra 2','2026-10-14','2026-10-17',{self.item:quantity})

    def test_total_stock_and_return_once(self):
        key = self.rent()
        self.assertEqual(self.db.rows('SELECT total_cents FROM rentals')[0][0],75300)
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],3)
        self.service.return_rental(key)
        with self.assertRaises(ValueError):
            self.service.return_rental(key)
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],5)

    def test_failed_rental_leaves_no_changes(self):
        second = self.db.rows('SELECT id FROM items WHERE id != ? LIMIT 1',(self.item,))[0][0]
        with self.assertRaises(ValueError):
            self.service.create_rental(self.client,'No guardar','2026-10-14','2026-10-17',{self.item:2,second:1})
        self.assertEqual(len(self.db.rows('SELECT * FROM rentals')),0)
        self.assertEqual(len(self.db.rows("SELECT * FROM addresses WHERE address='No guardar'")),0)
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],5)

    def test_stock_edit_cannot_remove_rented_units(self):
        self.rent(4)
        with self.assertRaises(ValueError):
            self.service.save_item(self.item,'Equipo',3,'200')
        self.service.save_item(self.item,'Equipo nuevo',7,'200')
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],3)

    def test_historical_note_preserves_data(self):
        key=self.rent()
        self.service.save_item(self.item,'Otro nombre',5,'999')
        self.service.save_client(self.client,'Otro cliente','5559876543',[1,1,1],'')
        note=self.service.note(key)
        self.assertIn('Ana Pérez',note)
        self.assertIn('$125.50',note)
        self.assertIn('Equipo',note)

    def test_invalid_dates_quantity_and_price(self):
        for departure,due in [('2026-10-17','2026-10-14'),('2026-10-14','2026-10-14')]:
            with self.assertRaises(ValueError):
                self.service.create_rental(self.client,'Obra',departure,due,{self.item:1})
        for quantity in [0,-1,6,1.5]:
            with self.assertRaises(ValueError):
                self.rent(quantity)
        for price in ['NaN','Infinity','-1','1.001','abc']:
            with self.assertRaises(ValueError):
                cents(price)

    def test_backup(self):
        self.rent()
        backup=Path(self.temp.name)/'backup.sqlite3'
        self.db.backup(backup)
        other=Database(backup)
        self.assertEqual(len(other.rows('SELECT * FROM rentals')),1)
        other.conn.close()

    def test_manual_ratings_and_unrated_new_client(self):
        key = self.service.create_rental(None,'Obra','2026-10-14','2026-10-15',{self.item:1},
            client_data={'name':'Sin evaluación','phone':'3129990000'})
        client = self.db.rows('SELECT client_id FROM rentals WHERE id=?',(key,))[0][0]
        self.assertEqual(self.db.rows('SELECT ratings_confirmed FROM clients WHERE id=?',(client,))[0][0],0)
        with self.assertRaises(ValueError):
            self.service.rate_client(client,['Seleccionar',4,5])
        self.service.rate_client(client,[3,3,3])
        self.assertEqual(self.db.rows('SELECT ratings_confirmed FROM clients WHERE id=?',(client,))[0][0],1)
        self.service.return_rental(key)
        self.assertEqual(self.db.rows('SELECT payment_rating FROM clients WHERE id=?',(client,))[0][0],3)

    def test_legacy_ratings_migration_preserves_values(self):
        import sqlite3
        path=Path(self.temp.name)/'legacy.sqlite3'
        connection=sqlite3.connect(path)
        schema=Path('app/schema.sql').read_text(encoding='utf-8')
        schema=schema.replace(" ,ratings_confirmed INTEGER NOT NULL DEFAULT 0 CHECK(ratings_confirmed IN (0,1))\n",'')
        connection.executescript(schema)
        connection.execute("INSERT INTO clients(name,phone) VALUES ('Automático','3121111111')")
        connection.execute("INSERT INTO clients(name,phone,payment_rating) VALUES ('Evaluado','3122222222',5)")
        connection.commit()
        connection.close()
        migrated=Database(path)
        rows=migrated.rows('SELECT * FROM clients ORDER BY id')
        self.assertEqual(rows[0]['ratings_confirmed'],0)
        self.assertEqual(rows[1]['ratings_confirmed'],1)
        self.assertEqual(rows[1]['payment_rating'],5)
        migrated.conn.close()

    def test_new_client_and_rental_saved_together(self):
        key = self.service.create_rental(None,'Obra nueva','2026-10-14','2026-10-15',{self.item:1},
            client_data={'name':'Luis López','phone':'312 123 4567'})
        rental = self.db.rows('SELECT * FROM rentals WHERE id=?',(key,))[0]
        self.assertEqual(rental['client_name'],'Luis López')
        self.assertEqual(len(self.db.rows('SELECT * FROM clients')),2)
        with self.assertRaises(ValueError):
            self.service.create_rental(None,'Obra','2026-10-14','2026-10-15',{self.item:1},
                client_data={'name':'Luis','phone':'3121234567'})
        self.assertEqual(len(self.db.rows('SELECT * FROM clients')),2)

    def test_failed_rental_does_not_save_new_client(self):
        with self.assertRaises(ValueError):
            self.service.create_rental(None,'Obra nueva','2026-10-14','2026-10-15',{self.item:99},
                client_data={'name':'Luis López','phone':'3121234567'})
        self.assertEqual(len(self.db.rows('SELECT * FROM clients')),1)

    def test_extension_uses_original_price_and_keeps_stock(self):
        key = self.rent()
        self.service.save_item(self.item,'Equipo',5,'999')
        quote = self.service.extend_rental(key,3)
        self.assertEqual(quote['new_due'],'2026-10-20')
        self.assertEqual(quote['added_cents'],75300)
        self.assertEqual(quote['total_cents'],150600)
        self.assertEqual(self.db.rows('SELECT days FROM rentals WHERE id=?',(key,))[0][0],6)
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],3)
        self.assertIn('+3 días',self.service.note(key))
        self.service.extend_rental(key,1)
        self.assertEqual(len(self.db.rows('SELECT * FROM rental_extensions')),2)

    def test_extensions_invalid_and_returned_rentals(self):
        key = self.rent()
        for days in [0,-1,1.5,True,3651]:
            with self.assertRaises(ValueError):
                self.service.extend_rental(key,days)
        self.service.return_rental(key)
        with self.assertRaises(ValueError):
            self.service.extend_rental(key,3)
        self.assertEqual(len(self.db.rows('SELECT * FROM rental_extensions')),0)

    def test_overdue_only_active_past_due_and_extension_clears(self):
        from datetime import date
        key = self.rent()
        self.assertEqual(len(self.service.overdue(date(2026,10,17))),0)
        self.assertEqual(len(self.service.overdue(date(2026,10,18))),1)
        self.service.extend_rental(key,3)
        self.assertEqual(len(self.service.overdue(date(2026,10,18))),0)
        self.service.return_rental(key)
        self.assertEqual(len(self.service.overdue(date(2026,11,1))),0)


if __name__ == '__main__':
    unittest.main()
