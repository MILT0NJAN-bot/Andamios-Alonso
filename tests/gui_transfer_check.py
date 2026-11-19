"""Regresión del flujo de transferencias y expedientes con GUI real."""
import sys
import tempfile
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import customtkinter as ctk
from app.database import Database
from app.desktop import Application


def run():
    ctk.set_appearance_mode('light')
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);app=Application(Database(root/'gui.sqlite3'))
        errors=[];app.report_callback_exception=lambda kind,value,tb:errors.append(value)
        def settle():
            ready=ctk.BooleanVar(value=False);app.after(180,lambda:ready.set(True));app.wait_variable(ready)
        def descendants(widget):
            for child in widget.winfo_children():
                yield child;yield from descendants(child)
        try:
            today=date.today().isoformat();app.cash.open_day(today,'0','Prueba')
            app.invoice_required.set(True);settle()
            assert app.initial_method.get()=='Transferencia'
            assert app.initial_method_menu.cget('values')==['Transferencia']
            app.invoice_required.set(False);settle()
            assert app.initial_method_menu.cget('values')==['Efectivo','Transferencia','Tarjeta']
            client=app.service.save_client(None,'Cliente transferencia','3121234567',None,'')
            item=next(iter(app.items));app.service.save_item(item,'Equipo',5,'500','daily')
            key=app.service.create_rental(client,'Obra',today,(date.today()+timedelta(days=2)).isoformat(),{item:1},invoice_required=True)
            payment=app.service.record_payment(key,'100','Transferencia');app.refresh()
            app.navigate('Comprobantes');settle()
            view=app.receipt_views[0]
            assert view.table.get_children()==(str(payment),)
            assert 'Pendiente' in view.table.item(str(payment),'values')
            view.table.selection_set(str(payment))
            receipt=root/'comprobante.pdf';receipt.write_bytes(b'%PDF-1.4\nGUI receipt')
            button=next(w for w in descendants(view.parent) if isinstance(w,ctk.CTkButton) and w.cget('text')=='Adjuntar al pago')
            with patch('app.transfer_ui.filedialog.askopenfilenames',return_value=(str(receipt),)):button.invoke()
            settle();assert '1 archivo(s)' in view.table.item(str(payment),'values')
            profile=app.client_billing_dialog(client);settle()
            assert len(profile.documents.get_children())==1
            assert 'Comprobantes de transferencia' in profile.documents.item(profile.documents.get_children()[0],'values')
            profile.close()
            export=next(w for w in descendants(view.parent) if isinstance(w,ctk.CTkButton) and w.cget('text')=='ZIP para contador')
            with patch('app.transfer_ui.filedialog.asksaveasfilename',return_value=str(root/'contador.zip')):export.invoke()
            assert (root/'contador.zip').exists()
            app.payment_dialog(key);settle()
            modal=app.grab_current()
            menus=[w for w in descendants(modal) if isinstance(w,ctk.CTkOptionMenu)]
            assert any(w.cget('values')==['Transferencia'] for w in menus)
            modal.destroy()
            assert not errors,errors
            print('GUI transferencias: metodo por factura, adjuntar, perfil, seguimiento y ZIP correctos.')
        finally:app.close()


if __name__=='__main__':run()
