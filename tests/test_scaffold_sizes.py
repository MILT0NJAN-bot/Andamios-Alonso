import unittest
import tempfile
from pathlib import Path
from datetime import date,timedelta
from tests import test_service
from app.database import Database,SCAFFOLD_SIZES
from app.service import Service


class ScaffoldSizeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.db=Database(Path(self.temp.name)/'sizes.sqlite3');self.service=Service(self.db)
        self.client=self.service.save_client(None,'Cliente','3121234567',None,'')
    tearDown=test_service.RentalTests.tearDown

    def sizes(self):return self.db.rows('SELECT * FROM items WHERE name IN (?,?,?)',SCAFFOLD_SIZES)

    def test_seeded_sizes_have_independent_zero_stock_and_shared_initial_tariff(self):
        sizes=self.sizes();self.assertEqual(len(sizes),3)
        for row in sizes:
            self.assertEqual(row['total'],0);self.assertEqual(row['available'],0)
            self.assertEqual((row['price_cents'],row['week_cents'],row['month_cents']),(3000,20000,45000))
            self.assertIsNone(row['replacement_cents'])
        key=sizes[0]['id'];self.service.save_item(key,sizes[0]['name'],3,'30','scaffold','200','450')
        other=Database(self.db.path)
        try:
            self.assertEqual(other.rows('SELECT total FROM items WHERE id=?',(key,))[0][0],3)
            self.assertEqual(len(other.rows('SELECT * FROM items WHERE name IN (?,?,?)',SCAFFOLD_SIZES)),3)
        finally:other.conn.close()

    def test_classification_conserves_totals_and_does_not_move_rented_items(self):
        source=self.db.rows("SELECT * FROM items WHERE name='Andamios'")[0]
        self.service.save_item(source['id'],'Andamios',5,'30','scaffold','200','450')
        rental=self.service.create_rental(self.client,'Obra','2026-11-05','2026-11-12',{source['id']:1})
        sizes=self.sizes()
        before=self.db.rows('SELECT SUM(total),SUM(available) FROM items')[0]
        self.service.classify_scaffolds({sizes[0]['id']:2,sizes[1]['id']:1})
        after=self.db.rows('SELECT SUM(total),SUM(available) FROM items')[0]
        self.assertEqual(tuple(before),tuple(after))
        self.assertEqual(self.db.rows('SELECT total,available FROM items WHERE id=?',(source['id'],))[0][:],(2,1))
        line=self.service.remaining_lines(rental)[0]
        self.assertEqual(line['item_id'],source['id']);self.assertEqual(line['pending'],1)
        self.assertEqual(len(self.db.rows('SELECT * FROM stock_classifications')),2)

    def test_overclassification_rolls_back(self):
        source=self.db.rows("SELECT * FROM items WHERE name='Andamios'")[0]
        self.service.save_item(source['id'],'Andamios',2,'30','scaffold','200','450')
        with self.assertRaises(ValueError):self.service.classify_scaffolds({self.sizes()[0]['id']:3})
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(source['id'],))[0][0],2)
        self.assertFalse(self.db.rows('SELECT * FROM stock_classifications'))

    def test_classification_cannot_remove_stock_promised_to_reservation(self):
        source=self.db.rows("SELECT * FROM items WHERE name='Andamios'")[0]
        self.service.save_item(source['id'],'Andamios',5,'30','scaffold','200','450')
        start=date.today()+timedelta(days=1)
        self.service.create_reservation(self.client,'Obra',start.isoformat(),(start+timedelta(days=7)).isoformat(),{source['id']:4},_legacy_without_deposit=True)
        with self.assertRaises(ValueError):self.service.classify_scaffolds({self.sizes()[0]['id']:2})
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(source['id'],))[0][0],5)
        self.assertFalse(self.db.rows('SELECT * FROM stock_classifications'))
