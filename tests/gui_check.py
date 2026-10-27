"""Comprobación con GUI real, ejecutada manualmente con Python desde la raíz."""
import sys
import tempfile
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import customtkinter as ctk
from app.database import Database
from app.desktop import Application, NEW_ADDRESS
from app.calendar_picker import CalendarPicker


def run():
    ctk.set_appearance_mode('light')
    with tempfile.TemporaryDirectory() as folder:
        app = Application(Database(Path(folder)/'gui.sqlite3'))
        errors = []
        app.report_callback_exception = lambda kind, value, tb: errors.append(value)
        def settle():
            ready=ctk.BooleanVar(value=False)
            app.after(180,lambda:ready.set(True))
            app.wait_variable(ready)
        try:
            settle()
            item = next(iter(app.items))
            app.service.save_item(item,'Revolvedora de prueba',10,'200','daily')
            client = app.service.save_client(None,'Ana Prueba','312 123 4567',[5,4,5],'Entrega cuidadosa','Obra inicial')
            app.refresh()
            app.navigate('Nueva Renta')
            app.rental_phone.set('312123')
            assert client in app.matches.values()
            app.update()
            assert app.suggestions.winfo_ismapped()
            app.choose_suggestion(next(iter(app.matches)))
            assert app.client_id == client and app.rental_name.get() == 'Ana Prueba'
            assert app.new_address.get() == 'Obra inicial'
            assert not app.suggestions.winfo_ismapped()
            assert 'Pago 5/5' in app.client_info.cget('text')
            app.rating_dialog(client)
            settle()
            for widget in app.winfo_children():
                if isinstance(widget,ctk.CTkToplevel):
                    widget.destroy()
            calendar = CalendarPicker(app,app.departure)
            settle()
            calendar.year,calendar.month=2028,2
            calendar.render()
            calendar.move(1)
            assert calendar.month == 3
            calendar.move(-1)
            calendar.choose(date(2028,2,29))
            assert app.departure.get() == '2028-02-29'
            calendar = CalendarPicker(app,app.due)
            settle()
            calendar.choose(date(2028,3,3))
            app.update()
            app.address_choice.set(NEW_ADDRESS)
            app.address_changed(NEW_ADDRESS)
            assert app.new_address.get() == ''
            app.reset_client()
            assert app.client_id is None and app.rental_name.get() == ''
            app.rental_name.set('Cliente capturado')
            app.rental_phone.set('9998887777')
            app.new_address.set('Obra nueva sin coincidencias')
            app.update()
            assert not app.suggestions.winfo_ismapped()
            assert app.rental_name.get()=='Cliente capturado'
            app.rental_name.set('Ana')
            assert client in app.matches.values()
            assert app.rental_phone.get()=='9998887777'
            app.choose_suggestion(next(iter(app.matches)))
            app.rental_phone.set('9990001111')
            assert app.client_id is None
            assert app.rental_phone.get()=='9990001111'
            assert app.rental_name.get()==''
            app.update()
            assert not app.suggestions.winfo_ismapped()
            app.choose_product(next(label for label,key in app.item_labels.items() if key == item))
            app.quantity.set('2')
            app.add_cart()
            assert '$1,200.00' in app.total_label.cget('text')
            app.invoice_required.set(True);app.update_total()
            assert '$1,392.00' in app.total_label.cget('text')
            app.invoice_required.set(False);app.update_total()
            yesterday = date.today()-timedelta(days=1)
            key = app.service.create_rental(client,'Obra inicial',(yesterday-timedelta(days=1)).isoformat(),yesterday.isoformat(),{item:1})
            app.refresh()
            from types import SimpleNamespace
            from unittest.mock import patch
            excel_path=Path(folder)/'gui-note.pdf'
            app.show_note(key)
            settle()
            def descendants(widget):
                for child in widget.winfo_children():
                    yield child
                    yield from descendants(child)
            export_button=next(widget for widget in descendants(app)
                if isinstance(widget,ctk.CTkButton) and widget.cget('text')=='PDF')
            with patch('app.ui.filedialog.asksaveasfilename',return_value=str(excel_path)), patch('app.ui.messagebox.showinfo'):
                export_button.invoke()
            assert excel_path.exists()
            assert excel_path.read_bytes().startswith(b'%PDF-')
            for widget in app.winfo_children():
                if isinstance(widget,ctk.CTkToplevel):
                    widget.destroy()
            app.payment_dialog(key)
            settle()
            payment_window=next(w for w in app.winfo_children() if isinstance(w,ctk.CTkToplevel))
            amount_entry=next(w for w in descendants(payment_window) if isinstance(w,ctk.CTkEntry) and w.cget('state')=='normal')
            amount_entry.insert(0,'50')
            register=next(w for w in descendants(payment_window) if isinstance(w,ctk.CTkButton) and w.cget('text')=='Registrar pago')
            with patch('app.payments_ui.messagebox.askyesno',return_value=True):
                register.invoke()
            settle()
            assert app.service.payment_summary(key)['paid_cents']==5000
            assert app.service.payment_summary(key)['pending_cents']==15000
            payment_window=next(w for w in app.winfo_children() if isinstance(w,ctk.CTkToplevel))
            liquidate=next(w for w in descendants(payment_window) if isinstance(w,ctk.CTkButton) and w.cget('text')=='Completar importe para liquidar')
            liquidate.invoke()
            register=next(w for w in descendants(payment_window) if isinstance(w,ctk.CTkButton) and w.cget('text')=='Registrar pago')
            with patch('app.payments_ui.messagebox.askyesno',return_value=True):
                register.invoke()
            settle()
            assert app.service.payment_summary(key)['pending_cents']==0
            for widget in app.winfo_children():
                if isinstance(widget,ctk.CTkToplevel):
                    widget.destroy()
            app.navigate('Inicio')
            app.update()
            for index,target in [(0,'Inventario/Precios'),(1,'Inventario/Precios'),(2,'Rentas activas')]:
                app.navigate('Inicio')
                settle()
                app.stats[index]._label.event_generate('<Button-1>',x=5,y=5)
                settle()
                assert app.tabs.tab(target).winfo_ismapped()
            app.navigate('Inicio')
            app.update()
            app.active_filter.set('Filtro que oculta la renta')
            bbox=app.dashboard_table.bbox(str(key))
            app.open_dashboard_rental(SimpleNamespace(keysym='??',y=bbox[1]+bbox[3]//2))
            app.update()
            assert app.tabs.tab('Rentas activas').winfo_ismapped()
            assert app.active_table.selection() == (str(key),)
            assert app.active_filter.get() == ''
            app.open_due_alerts()
            assert app.alert_window is not None
            app.alert_window.destroy()
            app.alert_window = None
            app.extension_dialog(key)
            app.update()
            app.service.extend_rental(key,3)
            app.refresh()
            assert not app.service.overdue()
            # Recibir una parte desde el formulario, dejando el resto activo.
            partial=app.service.create_rental(client,'Obra parcial',date.today().isoformat(),(date.today()+timedelta(days=7)).isoformat(),{item:3})
            app.return_dialog(partial)
            settle()
            return_window=next(w for w in app.winfo_children() if isinstance(w,ctk.CTkToplevel) and 'Recibir equipos' in w.title())
            quantity_entry=next(w for w in descendants(return_window) if isinstance(w,ctk.CTkEntry))
            quantity_entry.delete(0,'end');quantity_entry.insert(0,'1')
            receive=next(w for w in descendants(return_window) if isinstance(w,ctk.CTkButton) and w.cget('text')=='Guardar devolución')
            with patch('app.operations_ui.messagebox.askyesno',return_value=True):
                receive.invoke()
            assert app.service.remaining_lines(partial)[0]['pending']==2
            app.return_dialog(partial)
            settle()
            return_window=next(w for w in app.winfo_children() if isinstance(w,ctk.CTkToplevel) and 'Recibir equipos' in w.title())
            quantity_entry=next(w for w in descendants(return_window) if isinstance(w,ctk.CTkEntry))
            quantity_entry.delete(0,'end');quantity_entry.insert(0,'1')
            condition=next(w for w in descendants(return_window) if isinstance(w,ctk.CTkOptionMenu))
            condition.set('Malo');condition.cget('command')('Malo')
            receive=next(w for w in descendants(return_window) if isinstance(w,ctk.CTkButton) and w.cget('text')=='Guardar devolución')
            with patch('app.operations_ui.messagebox.askyesno',return_value=True):
                receive.invoke()
            assert app.service.remaining_lines(partial)[0]['pending']==1
            assert app.db.rows('SELECT maintenance FROM items WHERE id=?',(item,))[0][0]==1
            # Reservar desde la misma captura y comprobar que no descuenta stock físico.
            app.cart.clear();app.cart_conditions.clear()
            app.select_client(client)
            app.departure.set((date.today()+timedelta(days=12)).isoformat())
            app.set_duration(7)
            app.choose_product(next(label for label,key in app.item_labels.items() if key==item))
            app.quantity.set('2');app.add_cart()
            before=app.db.rows('SELECT available FROM items WHERE id=?',(item,))[0][0]
            with patch('app.operations_ui.messagebox.askyesno',return_value=True):
                app.reserve_current()
            assert len(app.db.rows('SELECT * FROM reservations'))==1
            assert app.db.rows('SELECT available FROM items WHERE id=?',(item,))[0][0]==before
            assert app.db.automatic_backup(force=True).exists()
            for page in app.tabs.frames:
                app.navigate(page)
                app.update()
            assert not errors, errors
            print('GUI: navegación, búsqueda, formulario, total, alertas y ampliación correctos.')
        finally:
            app.close()


if __name__ == '__main__':
    run()
