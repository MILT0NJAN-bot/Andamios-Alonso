from datetime import date,timedelta
import unittest
from tests import test_service
from app.pricing import unit_total


class ExtrasTests(unittest.TestCase):
    setUp=test_service.RentalTests.setUp
    tearDown=test_service.RentalTests.tearDown
    def test_extras_invoice_extension_and_pdf(self):
        key=self.service.create_rental(self.client,'Obra','2026-10-14','2026-10-17',
            {self.item:2},freight='200',extra_planks='2',invoice_required=True)
        row=self.db.rows('SELECT * FROM rentals WHERE id=?',(key,))[0]
        self.assertEqual(row['subtotal_cents'],105300)
        self.assertEqual(row['total_cents'],122148)
        quote=self.service.extension_quote(key,1)
        self.assertEqual(quote['subtotal_cents'],130400)
        from app.pdf_note import export_pdf
        from pypdf import PdfReader
        output=self.db.path.parent/'extra.pdf'
        export_pdf(self.db,key,output)
        text=' '.join(p.extract_text() for p in PdfReader(output).pages)
        self.assertIn('FLETE',text)
        self.assertIn('TABLONES EXTRA',text)

    def test_boards_week_and_extra_days(self):
        row=self.db.rows("SELECT * FROM items WHERE name='Tablas para cimbra'")[0]
        for days,total in ((7,25000),(8,26000),(30,48000),(37,55000)):
            self.assertEqual(unit_total(row,days),total)
        with self.assertRaises(ValueError): unit_total(row,6)

    def test_reservation_preserves_extras(self):
        today=date.today()
        key=self.service.create_reservation(self.client,'Obra',today.isoformat(),
            (today+timedelta(days=2)).isoformat(),{self.item:1},freight='150',extra_planks=3,_legacy_without_deposit=True)
        rental=self.service.start_reservation(key)
        row=self.db.rows('SELECT * FROM rentals WHERE id=?',(rental,))[0]
        self.assertEqual(row['total_cents'],55100)
        self.assertEqual(row['extra_planks'],3)

    def test_invalid_extras_do_not_change_stock(self):
        for freight,planks in (('-1',0),('0',-1),('0','1.5')):
            with self.assertRaises(ValueError):
                self.service.create_rental(self.client,'Obra','2026-10-14','2026-10-17',
                    {self.item:1},freight=freight,extra_planks=planks)
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],5)
