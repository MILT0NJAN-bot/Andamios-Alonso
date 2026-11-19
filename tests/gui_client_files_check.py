"""Prueba de la ventana con base temporal; --preview permite revisar el diseño."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import customtkinter as ctk
from PIL import Image
from app.client_files_ui import ClientBillingDialog
from app.database import Database
from app.desktop import Application


def run(preview=False):
    ctk.set_appearance_mode('light')
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        app = Application(Database(root / 'gui.sqlite3'))
        errors = []
        app.report_callback_exception = lambda kind, value, tb: errors.append(value)

        def settle():
            ready = ctk.BooleanVar(value=False)
            app.after(150, lambda: ready.set(True))
            app.wait_variable(ready)

        try:
            client = app.service.save_client(None, 'Ana Pérez · Prueba', '3121234567', None, '')
            app.refresh()
            app.navigate('Clientes')
            app.clients.selection_set(str(client))
            settle()
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            button = next(w for w in descendants(app.tabs.tab('Clientes'))
                          if isinstance(w, ctk.CTkButton) and w.cget('text') == 'Expediente para facturación')
            button.invoke()
            settle()
            window = next(w for w in app.winfo_children() if isinstance(w, ClientBillingDialog))
            assert window.copy_button.cget('state') == 'disabled'
            image = root / 'Comprobante domicilio.png'
            Image.new('RGB', (64, 64), 'white').save(image)
            with patch('app.client_files_ui.filedialog.askopenfilenames', return_value=(str(image),)):
                window.category.set('Comprobante de domicilio')
                window.add_documents()
                window.add_documents()
            settle()
            assert len(window.documents.get_children()) == 1
            assert 'repetido' in window.status.cget('text')
            window.fields['legal_name'].set('Ana Pérez')
            window.fields['rfc'].set('aaa010101aaa')
            window.fields['postal_code'].set('28000')
            window.notes.insert('1.0', 'Datos ficticios para comprobar el expediente.')
            output = root / 'contadora.zip'
            with patch('app.client_files_ui.filedialog.asksaveasfilename', return_value=str(output)), \
                 patch('app.client_files_ui.messagebox.showinfo'):
                window.export_zip()
            with ZipFile(output) as archive:
                assert len(archive.namelist()) == 2
                assert 'AAA010101AAA' in archive.read('Datos_para_facturacion.txt').decode('utf-8-sig')
            assert app.grab_current() is None
            assert not window.transient()
            for _ in range(3):
                window.iconify();app.iconify();settle()
                app.deiconify();window.deiconify();settle()
                assert app.state()=='normal'
                assert window.state()=='normal'
                assert app.grab_current() is None
                app.navigate('Inicio');settle()
                assert app.tabs.tab('Inicio').winfo_ismapped()
            window.iconify();settle()
            assert app.client_billing_dialog(client) is window
            settle()
            assert window.state()=='normal'
            assert len([w for w in app.winfo_children() if isinstance(w,ClientBillingDialog)])==1
            assert window.fields['rfc'].get() == 'AAA010101AAA'
            document = window.documents.get_children()[0]
            window.documents.selection_set(document)
            settle()
            assert window.copy_button.cget('state') == 'normal'
            copy = root / 'copia.png'
            with patch('app.client_files_ui.filedialog.asksaveasfilename', return_value=str(copy)):
                window.copy_button.invoke()
            assert copy.read_bytes() == image.read_bytes()
            with patch('app.client_files_ui.messagebox.askyesno', return_value=False):
                window.delete_button.invoke()
            assert len(window.documents.get_children()) == 1
            with patch('app.client_files_ui.messagebox.askyesno', return_value=True):
                window.delete_button.invoke()
            assert not window.documents.get_children()
            assert image.exists()
            window.fields['email'].set('prueba@example.com')
            with patch('app.client_files_ui.filedialog.asksaveasfilename', return_value=''):
                window.export_zip()
            assert app.service.billing_details(client)['email'] == ''
            with patch('app.client_files_ui.messagebox.askyesnocancel', return_value=None):
                window.close()
            assert window.winfo_exists()
            with patch('app.client_files_ui.messagebox.askyesnocancel', return_value=True):
                window.close()
            assert app.service.billing_details(client)['email'] == 'prueba@example.com'
            app.clients.selection_set(str(client));settle()
            assert app.clients.item(str(client),'values')[3]=='prueba@example.com'
            app.copy_email_button.invoke()
            assert app.clipboard_get()=='prueba@example.com'
            app.client_filter.set('PRUEBA@EXAMPLE.COM');settle()
            assert app.clients.get_children()==(str(client),)
            app.client_filter.set('');settle()
            window = app.client_billing_dialog(client)
            settle()
            assert window.fields['email'].get() == 'prueba@example.com'
            window.fields['email'].set('descartar@example.com')
            with patch('app.client_files_ui.messagebox.askyesnocancel', return_value=False):
                window.close()
            assert app.service.billing_details(client)['email'] == 'prueba@example.com'
            window = app.client_billing_dialog(client)
            window.fields['email'].set('pendiente@example.com')
            with patch('app.client_files_ui.messagebox.askyesnocancel', return_value=None):
                app.close()
            assert not app._closing
            assert window.winfo_exists()
            assert app.service.billing_details(client)['email']=='prueba@example.com'
            with patch('app.client_files_ui.messagebox.askyesnocancel', return_value=False):
                window.close()
            assert not errors, errors
            print('GUI expediente: adjuntar, duplicados, guardar, ZIP, copia, quitar y cambios pendientes correctos.', flush=True)
            if preview:
                app.service.add_client_documents(client, 'Comprobante de domicilio', [image])
                window = app.client_billing_dialog(client)
                app.protocol('WM_DELETE_WINDOW', app.quit)
                app.after(240000, app.quit)
                app.mainloop()
        finally:
            if not app._closing:
                app.close()


if __name__ == '__main__':
    run('--preview' in sys.argv)
