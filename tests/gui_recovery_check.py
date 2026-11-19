import sys
import tempfile
import time
import subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import customtkinter as ctk
from app.database import Database
from app.desktop import Application


def seed(path):
        app=Application(Database(path))
        try:
            app.rental_name.set('Cliente pendiente');app.rental_phone.set('3121234567')
            app.address_editor.fields['street'].set('Reforma 123');app.address_editor.fields['postal_code'].set('01')
            app.cart[next(iter(app.items))]=2;app.freight.set('150')
            app.save_rental_draft()
            assert app.draft_store.load()
        finally:app.close()


def run():
    ctk.set_appearance_mode('light')
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'recovery.sqlite3'
        subprocess.run([sys.executable,__file__,'--seed',str(path)],check=True)
        app=Application(Database(path))
        errors=[];app.report_callback_exception=lambda kind,value,tb:errors.append(value)
        try:
            assert app.pending_draft and not app.draft_active
            app.save_rental_draft() # No sobrescribir el borrador con el formulario vacío.
            assert app.draft_store.load()['payload']['name']=='Cliente pendiente'
            app.restore_rental_draft();app.update()
            assert app.rental_name.get()=='Cliente pendiente'
            assert app.address_editor.fields['postal_code'].get()=='01'
            assert app.cart and app.freight.get()=='150'
            assert not app.db.rows('SELECT * FROM rentals')
            assert not app.db.rows('SELECT * FROM payments')
            # Simular que transcurrió una hora con cambios.
            app.journal_last=time.monotonic()-3601
            app.journal_changes=-1
            app.recovery_tick()
            deadline=time.monotonic()+10
            while not list((path.parent/'respaldos').glob('jornada-*.sqlite3')) and time.monotonic()<deadline:
                ready=ctk.BooleanVar(value=False);app.after(100,lambda:ready.set(True));app.wait_variable(ready)
            app.recovery_tick();app.update()
            assert list((path.parent/'respaldos').glob('jornada-*.sqlite3'))
            assert not errors,errors
            print('GUI recuperacion: borrador, captura parcial, reinicio, sin duplicados y respaldo horario correctos.')
        finally:app.close()


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--seed':seed(Path(sys.argv[2]))
    else:run()
