"""Genera una nota de ejemplo con datos ficticios, sin tocar la base del negocio."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import Database
from app.service import Service
from app.pdf_note import export_pdf


def main():
    with tempfile.TemporaryDirectory() as folder:
        db=Database(Path(folder)/'sample.sqlite3')
        try:
            service=Service(db)
            scaffold=db.rows("SELECT id FROM items WHERE name='Andamios'")[0][0]
            mixer=db.rows("SELECT id FROM items WHERE name='Revolvedoras'")[0][0]
            service.save_item(scaffold,'Andamios',20,'30','scaffold','200','450',replacement_cost='1500')
            service.save_item(mixer,'Revolvedoras',5,'450','daily',replacement_cost='18000')
            client=service.save_client(None,'CLIENTE DE EJEMPLO · DATOS FICTICIOS','0000000000',None,'')
            key=service.create_rental(client,'Obra de ejemplo · Calle y colonia de referencia','2026-10-21','2026-10-28',{scaffold:4,mixer:1})
            service.extend_rental(key,3)
            service.record_payment(key,'1000','Efectivo',kind='Anticipo')
            service.record_payment(key,'500','Transferencia',reference='Abono de ejemplo')
            path=Path(__file__).with_name('Nota_Alonso_Ejemplo.pdf')
            export_pdf(db,key,path)
            print(path)
        finally:
            db.conn.close()


if __name__=='__main__':
    main()
