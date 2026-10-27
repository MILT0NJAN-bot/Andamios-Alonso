import tempfile
import unittest
from datetime import date,timedelta
from pathlib import Path
from openpyxl import load_workbook
from app.database import Database
from app.service import Service
from app.excel_note import export_note


class ExcelNoteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=Database(Path(self.temp.name)/'note.sqlite3')
        self.service=Service(self.db, tax_rates=(0,0))
        self.item=self.db.rows("SELECT id FROM items WHERE name='Andamios'")[0][0]
        self.service.save_item(self.item,'Andamios',10,'30','scaffold','200','450')
        self.client=self.service.save_client(None,'=CLIENTE DE PRUEBA','3121112222',None,'')
        self.key=self.service.create_rental(self.client,'Obra de prueba','2026-10-01','2026-10-08',{self.item:2})

    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()

    def test_professional_note_totals_history_and_print_settings(self):
        path=export_note(self.db,self.key,Path(self.temp.name)/'note.xlsx')
        self.service.save_client(self.client,'Nombre cambiado','3123334444',None,'')
        wb=load_workbook(path,data_only=True)
        sheet=wb['Nota de renta']
        self.assertEqual(sheet['C6'].value,'=CLIENTE DE PRUEBA')
        self.assertEqual(sheet['C6'].data_type,'s')
        self.assertEqual(sheet['E11'].value,'PIEZAS')
        self.assertEqual(sheet['E12'].value,2)
        self.assertEqual(sheet['C10'].value,2)
        self.assertEqual(sheet['E12'].number_format,'0')
        self.assertTrue(sheet['E12'].font.bold)
        self.assertIsNone(sheet.freeze_panes)
        self.assertEqual(sheet['G12'].value,7)
        self.assertEqual(sheet['H12'].value,200)
        self.assertEqual(sheet['I12'].value,400)
        self.assertEqual(sheet['I14'].value,400)  # Subtotal.
        self.assertEqual(sheet['I17'].value,400)  # Total sin impuestos de la nota histórica de prueba.
        self.assertEqual(sheet.page_setup.fitToWidth,1)
        self.assertFalse(sheet.sheet_view.showGridLines)
        self.assertEqual(wb.sheetnames,['Nota de renta','Estado y devoluciones'])
        wb.close()

    def test_extensions_and_monthly_adjustments_in_excel(self):
        self.service.extend_rental(self.key,22)
        self.service.extend_rental(self.key,1)
        path=export_note(self.db,self.key,Path(self.temp.name)/'month.xlsx')
        wb=load_workbook(path,data_only=True)
        self.assertEqual(wb['Nota de renta']['G12'].value,30)
        self.assertEqual(wb['Nota de renta']['H12'].value,450)
        self.assertEqual(wb['Nota de renta']['I17'].value,900)
        self.assertEqual(wb['Ampliaciones']['E4'].value,-820)
        self.assertIsNone(wb['Ampliaciones'].freeze_panes)
        wb.close()

    def test_invalid_rental_and_extension(self):
        with self.assertRaises(ValueError):
            export_note(self.db,999,Path(self.temp.name)/'note.xlsx')
        with self.assertRaises(ValueError):
            export_note(self.db,self.key,Path(self.temp.name)/'note.txt')


if __name__=='__main__':
    unittest.main()
