import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import customtkinter as ctk
from app.database import Database
from app.desktop import Application


def run():
    ctk.set_appearance_mode('light')
    with tempfile.TemporaryDirectory() as folder:
        app=Application(Database(Path(folder)/'gui.sqlite3'))
        errors=[];app.report_callback_exception=lambda kind,value,tb:errors.append(value)
        def settle():
            ready=ctk.BooleanVar(value=False);app.after(180,lambda:ready.set(True));app.wait_variable(ready)
        def descendants(widget):
            for w in widget.winfo_children():yield w;yield from descendants(w)
        try:
            app.cash.open_day(date.today().isoformat(),'0','Secretaria')
            item=app.db.rows("SELECT id FROM items WHERE name='Revolvedoras'")[0][0]
            app.service.save_item(item,'Revolvedoras',3,'100','daily');app.refresh()
            app.rental_name.set('Captura actual sin modificar')
            assert not any(isinstance(w,ctk.CTkButton) and 'Guardar reservación' in w.cget('text') for w in descendants(app.tabs.tab('Nueva Renta')))
            app.navigate('Reservaciones');app.new_reservation_dialog();settle()
            win=app.grab_current();fields=win.reservation_fields
            fields['name'].set('Cliente nuevo reserva');fields['phone'].set('3125550000')
            fields['address'].fields['street'].set('Reforma 20')
            fields['quantities'][item].set('1');settle()
            assert fields['deposit'].get()=='350.00'
            with patch('app.reservation_ui.messagebox.askyesno',return_value=True):fields['save']()
            settle()
            reservation=app.db.rows('SELECT * FROM reservations')[0]
            self_summary=app.service.reservation_payment_summary(reservation['id'])
            assert self_summary['paid_cents']==35000 and self_summary['confirmed']
            assert app.rental_name.get()=='Captura actual sin modificar'
            assert app.db.rows('SELECT available FROM items WHERE id=?',(item,))[0][0]==3
            assert app.cash.day_report(date.today().isoformat())['operating_income']==35000
            app.reservations_table.selection_set(str(reservation['id']))
            app.reservation_payment_history();settle()
            modal=app.grab_current();assert modal;modal.destroy()
            assert not errors,errors
            print('GUI reservaciones: formulario propio, 50%, caja, stock futuro e historial correctos.')
        finally:app.close()


if __name__=='__main__':run()
