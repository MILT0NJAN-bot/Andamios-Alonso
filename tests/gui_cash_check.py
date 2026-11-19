"""Prueba manual con GUI real y base temporal: python tests/gui_cash_check.py."""
import sys
import tempfile
from pathlib import Path
from datetime import date
from unittest.mock import patch
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
        try:
            app.navigate('Caja y gastos');settle()
            today=date.today().isoformat()
            assert 'CAJA SIN ABRIR' in app.cash_banners[0][1].cget('text')
            app.confirm_rental();settle()
            modal=app.grab_current();assert modal and modal.title()=='Abrir caja del día'
            modal.destroy();settle()
            app.cash.open_day(today,'500','Laura')
            employee=app.cash.catalog('Empleado','Juan')
            app.cash.add(today,'Sueldos','100','Efectivo','Pago semanal','Laura',employee,'Semana 1')
            app.refresh_cash();settle()
            assert 'CAJA ABIERTA' in app.cash_banners[0][1].cget('text')
            assert len(app.cash_table.get_children())==1
            assert '$100.00' in app.cash_summary.cget('text')
            for dialog in (app.cash_catalog,app.cash_movement,app.cash_day_dialog):
                dialog();settle()
                modal=app.grab_current();assert modal and modal.winfo_exists();modal.destroy();settle()
            app.cash_movement();settle()
            modal=app.grab_current()
            for category in ('Gasolina','Sueldos','Retiro del dueño'):
                modal.cash_category.set(category);settle()
                assert 'SALIDA DE DINERO' in modal.cash_direction.cget('text')
                assert 'Importe pagado' in modal.cash_amount_label.cget('text')
            for category in ('Aportación del dueño','Otros ingresos'):
                modal.cash_category.set(category);settle()
                assert 'ENTRADA DE DINERO' in modal.cash_direction.cget('text')
                assert 'Importe recibido' in modal.cash_amount_label.cget('text')
            modal.destroy();settle()
            with patch('app.printing.print_pdf',return_value='print') as printer:
                app.cash_print(app.cash.day_report(today))
                from pypdf import PdfReader
                print_path=printer.call_args.args[0]
                text=' '.join(p.extract_text() for p in PdfReader(print_path).pages)
                assert 'Efectivo que debe haber en caja' in text
                assert '$400.00' in text
            app.cash.close(today,'400','Laura')
            app.refresh_cash_status()
            assert 'CAJA CERRADA' in app.cash_banners[0][1].cget('text')
            with patch('app.printing.print_pdf',return_value='print') as printer:
                app.cash_print(app.cash.day_report(today))
                text=' '.join(p.extract_text() for p in PdfReader(printer.call_args.args[0]).pages)
                assert 'CORTE CERRADO' in text
            app.cash_history();settle()
            modal=app.grab_current();assert modal;modal.destroy();settle()
            with patch('app.cash_ui.filedialog.asksaveasfilename',return_value=str(Path(folder)/'report.pdf')),patch('app.cash_ui.messagebox.showinfo'):
                app.cash_export()
            assert (Path(folder)/'report.pdf').read_bytes().startswith(b'%PDF')
            assert not errors,errors
            print('GUI caja: catalogos, movimientos, apertura, corte, historial y PDF correctos.')
        finally:app.close()


if __name__=='__main__':run()
