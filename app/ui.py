import sqlite3
import tkinter as tk
from datetime import date, timedelta
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from .service import Service, money
from .pricing import unit_total, tariff_label
from .taxes import amounts
from .client_files_ui import ClientBillingDialog


class Application(ctk.CTk):
    def __init__(self, db):
        super().__init__()
        self.db, self.service = db, Service(db)
        self.title('Andamios Alonso | Control de rentas')
        self.geometry('1180x820')
        self.minsize(1000, 720)
        self.client_id = None
        self.cart = {}
        ctk.CTkLabel(self, text='ANDAMIOS ALONSO', font=ctk.CTkFont(size=26, weight='bold')).pack(anchor='w', padx=24, pady=(18, 4))
        bar = ctk.CTkFrame(self, fg_color='transparent')
        bar.pack(fill='x', padx=24)
        ctk.CTkLabel(bar, text='Inventario · Clientes · Rentas | Operación local en MXN').pack(side='left')
        ctk.CTkButton(bar, text='Respaldar base de datos', command=self.backup).pack(side='right')
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill='both', expand=True, padx=18, pady=12)
        for name in ('Nueva Renta', 'Clientes', 'Inventario/Precios', 'Historial de Rentas'):
            self.tabs.add(name)
        self.make_rental()
        self.make_clients()
        self.make_inventory()
        self.make_history()
        self.refresh()
        self.protocol('WM_DELETE_WINDOW', self.close)

    def close(self):
        self.db.conn.close()
        self.destroy()

    def safe(self, action):
        try:
            action()
        except (ValueError, sqlite3.Error, OSError) as exc:
            messagebox.showerror('No se pudo completar', str(exc), parent=self)

    def table(self, parent, columns, height=8):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill='both', expand=True, pady=8)
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=height, selectmode='browse')
        for col in columns:
            tree.heading(col, text=col, anchor='center')
            tree.column(col, width=125, minwidth=60, anchor='center')
        scroll = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)
        return tree

    def entry(self, parent, label, default=''):
        ctk.CTkLabel(parent, text=label).pack(anchor='w')
        variable = tk.StringVar(value=default)
        ctk.CTkEntry(parent, textvariable=variable, height=34).pack(fill='x', pady=(0, 5))
        return variable

    def selected(self, tree):
        selection = tree.selection()
        if not selection:
            raise ValueError('Selecciona una fila de la lista.')
        return int(selection[0])

    def fill(self, tree, rows):
        tree.delete(*tree.get_children())
        for key, values in rows:
            tree.insert('', 'end', iid=str(key), values=values)

    def refresh(self):
        self.items = {r['id']: r for r in self.db.rows('SELECT * FROM items ORDER BY name')}
        self.item_labels = {f"{r['name']} | Disponibles: {r['available']} | {tariff_label(r)}": key for key,r in self.items.items()}
        labels = list(self.item_labels)
        self.item_menu.configure(values=labels)
        self.item_choice.set(labels[0] if labels else '')
        self.fill(self.inventory, [(key,(key,r['name'],r['total'],r['available'],r['maintenance'],tariff_label(r),money(r['replacement_cents']) if r['replacement_cents'] is not None else 'Por definir')) for key,r in self.items.items()])
        self.refresh_clients()
        rentals = self.db.rows('SELECT * FROM rentals ORDER BY id DESC')
        self.fill(self.history, [(r['id'],(f"{r['id']:06d}",r['client_name'],r['departure'],r['due'],money(r['total_cents']),
                  'Devuelta' if r['returned_at'] else ('Vencida' if r['due'] < date.today().isoformat() else 'Activa'))) for r in rentals])
        self.update_total()

    def make_inventory(self):
        page = self.tabs.tab('Inventario/Precios')
        ctk.CTkLabel(page, text='Disponible = total − unidades en rentas activas. Configura precios antes de rentar.').pack(anchor='w')
        self.inventory = self.table(page, ('ID','Artículo','Total','Disponible','En revisión','Tarifa','Valor completo / pieza'))
        buttons = ctk.CTkFrame(page, fg_color='transparent')
        buttons.pack(fill='x')
        ctk.CTkButton(buttons,text='Agregar artículo',command=lambda:self.item_dialog()).pack(side='left',padx=5,pady=10)
        ctk.CTkButton(buttons,text='Modificar seleccionado',command=lambda:self.safe(lambda:self.item_dialog(self.selected(self.inventory)))).pack(side='left',padx=5)

    def dialog(self, title):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry('550x680')
        win.transient(self)
        win.grab_set()
        body = ctk.CTkScrollableFrame(win)
        body.pack(fill='both',expand=True,padx=16,pady=16)
        return win,body

    def item_dialog(self, key=None):
        row = self.items.get(key)
        win,body = self.dialog('Administrar artículo')
        name = self.entry(body,'Nombre',row['name'] if row else '')
        total = self.entry(body,'Cantidad total',str(row['total']) if row else '0')
        price = self.entry(body,'Precio por día (MXN)',f"{row['price_cents']/100:.2f}" if row else '0.00')
        ctk.CTkLabel(body,text='Tipo de tarifa (el precio diario es el día extra para andamios)').pack(anchor='w')
        mode=tk.StringVar(value='Semanal / mensual' if row and row['pricing_mode']=='scaffold' else 'Por día')
        ctk.CTkOptionMenu(body,values=['Por día','Semanal / mensual'],variable=mode).pack(fill='x',pady=5)
        week=self.entry(body,'Semana (7 días) · MXN',f"{row['week_cents']/100:.2f}" if row else '200.00')
        month=self.entry(body,'Mes de 30 días · MXN (0 = sin tarifa mensual)',f"{row['month_cents']/100:.2f}" if row else '450.00')
        replacement=self.entry(body,'Valor completo del equipo por pieza · MXN (opcional)',f"{row['replacement_cents']/100:.2f}" if row and row['replacement_cents'] is not None else '')
        ctk.CTkLabel(body,text='Se mostrará en la nota como valor del equipo; no se suma al cobro de renta.',wraplength=440,justify='left').pack(anchor='w',pady=6)
        def save():
            self.service.save_item(key,name.get(),total.get(),price.get(),'scaffold' if mode.get()=='Semanal / mensual' else 'daily',week.get(),month.get(),replacement_cost=replacement.get())
            win.destroy()
            self.refresh()
        ctk.CTkButton(body,text='Guardar artículo',height=42,command=lambda:self.safe(save)).pack(fill='x',pady=15)

    def make_clients(self):
        page = self.tabs.tab('Clientes')
        self.client_filter = self.entry(page,'Buscar por nombre o teléfono')
        self.client_filter.trace_add('write',lambda *_:self.refresh_clients())
        self.clients = self.table(page,('ID','Nombre','Teléfono','Pago (1–5)','Entrega (1–5)','Cuidado (1–5)','Saldo pendiente'))
        bar = ctk.CTkFrame(page,fg_color='transparent')
        bar.pack(fill='x')
        ctk.CTkButton(bar,text='Registrar cliente',command=lambda:self.client_dialog()).pack(side='left',padx=5,pady=10)
        ctk.CTkButton(bar,text='Editar / ver direcciones',command=lambda:self.safe(lambda:self.client_dialog(self.selected(self.clients)))).pack(side='left',padx=5)
        ctk.CTkButton(bar,text='Expediente para facturación',fg_color='#18865B',
            command=lambda:self.safe(lambda:self.client_billing_dialog(self.selected(self.clients)))).pack(side='left',padx=5)
        self.clients.bind('<Double-1>',lambda event:self.safe(lambda:self.client_billing_dialog(int(self.clients.identify_row(event.y))))
                          if self.clients.identify_row(event.y) else None)
        self.clients.bind('<Return>',lambda _:self.safe(lambda:self.client_billing_dialog(self.selected(self.clients))))

    def client_billing_dialog(self, key):
        return ClientBillingDialog(self, key)

    def refresh_clients(self):
        if not hasattr(self,'clients'):
            return
        term = self.client_filter.get().casefold().strip()
        rows = self.db.rows('SELECT * FROM clients ORDER BY name')
        self.fill(self.clients,[(r['id'],(r['id'],r['name'],r['phone'],*[r[c] if r['ratings_confirmed'] else 'Sin calificar' for c in ('payment_rating','return_rating','care_rating')],
            money(sum(self.service.payment_summary(rental['id'])['pending_cents'] for rental in self.db.rows('SELECT id FROM rentals WHERE client_id=?',(r['id'],))))))
            for r in rows if term in r['name'].casefold() or term in r['phone']])

    def client_dialog(self,key=None):
        row = self.db.rows('SELECT * FROM clients WHERE id=?',(key,))[0] if key else None
        win,body = self.dialog('Cliente y reputación')
        name = self.entry(body,'Nombre completo',row['name'] if row else '')
        phone = self.entry(body,'Teléfono principal',row['phone'] if row else '')
        ratings=[]
        for column,label in [('payment_rating','Puntualidad de pago'),('return_rating','Puntualidad de devolución'),('care_rating','Cuidado de maquinaria')]:
            ctk.CTkLabel(body,text=label+' (1 = malo, 5 = excelente)').pack(anchor='w')
            value=tk.StringVar(value=str(row[column]) if row and row['ratings_confirmed'] else 'Sin calificar')
            ctk.CTkOptionMenu(body,values=['Sin calificar','1','2','3','4','5'],variable=value).pack(fill='x',pady=4)
            ratings.append(value)
        ctk.CTkLabel(body,text='Observaciones').pack(anchor='w')
        notes=ctk.CTkTextbox(body,height=85)
        notes.pack(fill='x')
        notes.insert('1.0',row['notes'] if row else '')
        if key:
            addresses=self.db.rows('SELECT address FROM addresses WHERE client_id=? ORDER BY id DESC',(key,))
            ctk.CTkLabel(body,text='Direcciones registradas:\n'+'\n'.join(r['address'] for r in addresses),wraplength=450,justify='left').pack(anchor='w',pady=8)
        address=self.entry(body,'Agregar dirección de obra (opcional)')
        def save():
            scores = [v.get() for v in ratings]
            if 'Sin calificar' in scores and scores != ['Sin calificar']*3:
                raise ValueError('Califica los tres criterios o deja los tres sin calificar.')
            self.service.save_client(key,name.get(),phone.get(),None if scores == ['Sin calificar']*3 else scores,notes.get('1.0','end-1c'),address.get())
            win.destroy()
            self.refresh_clients()
            if key == self.client_id:
                self.select_client(key)
        ctk.CTkButton(body,text='Guardar cliente',height=42,command=lambda:self.safe(save)).pack(fill='x',pady=12)

    def make_rental(self):
        page=self.tabs.tab('Nueva Renta')
        self.search=self.entry(page,'Buscar cliente por nombre o teléfono (selecciona una sugerencia)')
        self.search.trace_add('write',lambda *_:self.suggest())
        self.suggestions=ctk.CTkOptionMenu(page,values=['Sin resultados'],command=self.choose_suggestion)
        self.suggestions.pack(fill='x',pady=4)
        self.client_info=ctk.CTkLabel(page,text='Ningún cliente seleccionado',anchor='w')
        self.client_info.pack(fill='x')
        self.address_choice=tk.StringVar()
        self.address_menu=ctk.CTkOptionMenu(page,values=['Agregar nueva dirección de obra'],variable=self.address_choice,command=self.address_changed)
        self.address_menu.pack(fill='x',pady=4)
        self.new_address=self.entry(page,'Nueva dirección de obra (cuando corresponda)')
        dates=ctk.CTkFrame(page,fg_color='transparent')
        dates.pack(fill='x')
        left=ctk.CTkFrame(dates,fg_color='transparent'); left.pack(side='left',fill='x',expand=True,padx=(0,8))
        right=ctk.CTkFrame(dates,fg_color='transparent'); right.pack(side='left',fill='x',expand=True)
        self.departure=self.entry(left,'Fecha de salida (AAAA-MM-DD)',date.today().isoformat())
        self.due=self.entry(right,'Devolución estimada (AAAA-MM-DD)',(date.today()+timedelta(days=1)).isoformat())
        for v in (self.departure,self.due):
            v.trace_add('write',lambda *_:self.update_total())
        bar=ctk.CTkFrame(page,fg_color='transparent'); bar.pack(fill='x',pady=8)
        self.item_choice=tk.StringVar()
        self.item_menu=ctk.CTkOptionMenu(bar,values=[''],variable=self.item_choice,width=470)
        self.item_menu.pack(side='left',padx=(0,8))
        self.quantity=tk.StringVar(value='1')
        ctk.CTkEntry(bar,textvariable=self.quantity,width=70).pack(side='left',padx=5)
        ctk.CTkButton(bar,text='Agregar cantidad',command=lambda:self.safe(self.add_cart)).pack(side='left',padx=5)
        self.cart_table=self.table(page,('Artículo','Cantidad','Precio/día','Subtotal'),height=4)
        bottom=ctk.CTkFrame(page,fg_color='transparent'); bottom.pack(fill='x')
        ctk.CTkButton(bottom,text='Quitar seleccionado',command=lambda:self.safe(self.remove_cart)).pack(side='left')
        self.total_label=ctk.CTkLabel(bottom,text='TOTAL: $0.00',font=ctk.CTkFont(size=23,weight='bold'))
        self.total_label.pack(side='right')
        self.alert=ctk.CTkLabel(page,text='',text_color='#c62828')
        self.alert.pack(fill='x')
        ctk.CTkButton(page,text='Confirmar renta y generar nota',height=44,command=lambda:self.safe(self.confirm_rental)).pack(fill='x',pady=5)

    def suggest(self):
        term=self.search.get().strip().casefold()
        self.matches={f"{r['name']} | {r['phone']} | #{r['id']}":r['id'] for r in self.db.rows('SELECT * FROM clients ORDER BY name') if term and (term in r['name'].casefold() or term in r['phone'])}
        values=list(self.matches)[:30] or ['Sin resultados']
        self.suggestions.configure(values=values)
        self.suggestions.set('Selecciona un cliente' if self.matches else 'Sin resultados')
        self.client_id=None
        self.client_info.configure(text='Selecciona una sugerencia para confirmar el cliente')
        self.address_menu.configure(values=['Agregar nueva dirección de obra'])
        self.address_choice.set('Agregar nueva dirección de obra')

    def choose_suggestion(self,label):
        if label in self.matches:
            self.select_client(self.matches[label])

    def select_client(self,key):
        self.client_id=key
        row=self.db.rows('SELECT * FROM clients WHERE id=?',(key,))[0]
        self.client_info.configure(text=f"{row['name']} · {row['phone']} | Pago {row['payment_rating']}/5 · Entrega {row['return_rating']}/5 · Cuidado {row['care_rating']}/5 | {row['notes']}",wraplength=1000)
        addresses=self.db.rows('SELECT a.*, (SELECT MAX(r.id) FROM rentals r WHERE r.address_id=a.id) AS last_used FROM addresses a WHERE client_id=? ORDER BY last_used DESC,a.id DESC',(key,))
        values=[r['address'] for r in addresses]+['Agregar nueva dirección de obra']
        self.address_menu.configure(values=values)
        self.address_choice.set(values[0])
        self.new_address.set('')

    def address_changed(self,_):
        self.new_address.set('')

    def add_cart(self):
        key=self.item_labels.get(self.item_choice.get())
        quantity=int(self.quantity.get())
        if key is None or quantity < 1:
            raise ValueError('Selecciona un equipo y una cantidad mayor a cero.')
        requested=self.cart.get(key,0)+quantity
        if requested > self.items[key]['available']:
            self.alert.configure(text=f"Stock insuficiente: disponibles {self.items[key]['available']}, solicitados {requested}.")
            raise ValueError('La cantidad solicitada supera el stock disponible.')
        self.cart[key]=requested
        self.update_total()

    def remove_cart(self):
        del self.cart[self.selected(self.cart_table)]
        self.update_total()

    def update_total(self):
        if not hasattr(self,'items'):
            return
        try:
            days=(date.fromisoformat(self.due.get())-date.fromisoformat(self.departure.get())).days
            if days < 1:
                raise ValueError()
            error=''
        except ValueError:
            days=0
            error='Fechas inválidas: utiliza AAAA-MM-DD y una devolución posterior a la salida.'
        rows=[]; total=0
        for key,quantity in self.cart.items():
            row=self.items[key]
            try:
                subtotal=quantity*unit_total(row,days) if days else 0
            except ValueError as exc:
                subtotal=0
                error=str(exc)
            total+=subtotal
            rows.append((key,(row['name'],quantity,tariff_label(row),money(subtotal))))
        self.fill(self.cart_table,rows)
        if hasattr(self,'freight'):
            try:
                from .service import cents
                freight=cents(self.freight.get() or '0')
                planks=int(self.extra_planks.get() or '0')
                if planks<0: raise ValueError()
                total+=freight+planks*5000
            except ValueError:
                error='Captura un flete valido y una cantidad entera de tablones.'
        breakdown=amounts(total,1600 if hasattr(self,'invoice_required') and self.invoice_required.get() else 0,0)
        self.total_label.configure(text=f"TOTAL: {money(breakdown['total_cents'])} MXN · {days} días\n"
            f"Subtotal {money(total)} · IVA {money(breakdown['vat_cents'])}")
        self.alert.configure(text=error)

    def confirm_rental(self):
        address=self.new_address.get() if self.address_choice.get()=='Agregar nueva dirección de obra' else self.address_choice.get()
        if not self.client_id:
            raise ValueError('Selecciona un cliente de las sugerencias.')
        if not messagebox.askyesno('Confirmar renta',self.total_label.cget('text')+'\n¿Registrar la renta y descontar el inventario?',parent=self):
            return
        key=self.service.create_rental(self.client_id,address,self.departure.get(),self.due.get(),self.cart)
        self.cart.clear()
        self.select_client(self.client_id)
        self.refresh()
        self.show_note(key)

    def make_history(self):
        page=self.tabs.tab('Historial de Rentas')
        ctk.CTkLabel(page,text='Selecciona una renta para ver la nota o registrar la devolución completa.').pack(anchor='w')
        self.history=self.table(page,('Folio','Cliente','Salida','Devolución','Total','Estado'))
        bar=ctk.CTkFrame(page,fg_color='transparent'); bar.pack(fill='x')
        ctk.CTkButton(bar,text='Ver / exportar nota',command=lambda:self.safe(lambda:self.show_note(self.selected(self.history)))).pack(side='left',padx=5,pady=10)
        ctk.CTkButton(bar,text='Registrar devolución',command=lambda:self.safe(self.return_selected)).pack(side='left',padx=5)
        ctk.CTkButton(bar,text='Actualizar',command=self.refresh).pack(side='left',padx=5)

    def return_selected(self):
        key=self.selected(self.history)
        if messagebox.askyesno('Devolución',f'¿Confirmas la devolución de TODOS los equipos de la renta #{key:06d}?',parent=self):
            self.service.return_rental(key)
            self.refresh()

    def show_note(self,key):
        win,body=self.dialog(f'Nota de renta #{key:06d}')
        note=self.service.note(key)
        text=ctk.CTkTextbox(body,height=480,wrap='word')
        text.pack(fill='both',expand=True)
        text.insert('1.0',note)
        text.configure(state='disabled')
        self.note_views=getattr(self,'note_views',[])
        self.note_views.append((key,text))
        if hasattr(self,'payment_dialog'):
            ctk.CTkButton(body,text='Pagos y saldo',height=40,command=lambda:self.safe(lambda:self.payment_dialog(key))).pack(fill='x',pady=8)
        def export():
            path=filedialog.asksaveasfilename(parent=win,defaultextension='.txt',initialfile=f'Nota_{key:06d}.txt',filetypes=[('Texto','*.txt')])
            if path:
                from pathlib import Path
                Path(path).write_text(self.service.note(key),encoding='utf-8')
                messagebox.showinfo('Nota guardada','Puedes abrir e imprimir el archivo desde el Bloc de notas.',parent=win)
        def export_pdf():
            path=filedialog.asksaveasfilename(parent=win,defaultextension='.pdf',initialfile=f'Nota_Alonso_{key:06d}.pdf',filetypes=[('Nota PDF','*.pdf')])
            if path:
                from .pdf_note import export_pdf as save_pdf
                save_pdf(self.db,key,path)
                messagebox.showinfo('PDF guardado','Nota PDF guardada, lista para compartir o imprimir.',parent=win)
        rental=self.db.rows('SELECT * FROM rentals WHERE id=?',(key,))[0]
        invoice=tk.BooleanVar(value=bool(rental['vat_bp']))
        ctk.CTkCheckBox(body,text='Requiere factura (agregar IVA 16%)',variable=invoice).pack(anchor='w',pady=8)
        def save_invoice():
            from .taxes import amounts
            preview=amounts(rental['subtotal_cents'],1600 if invoice.get() else 0,0)
            if messagebox.askyesno('Actualizar opción de factura',f"Nuevo total: {money(preview['total_cents'])} MXN\n¿Actualizar la nota y su saldo? Los pagos se conservarán.",parent=win):
                self.service.set_invoice(key,invoice.get())
                self.refresh();win.destroy();self.show_note(key)
        ctk.CTkButton(body,text='Guardar opción de factura',height=36,command=lambda:self.safe(save_invoice)).pack(fill='x',pady=6)
        ctk.CTkButton(body,text='PDF',height=44,fg_color='#18865B',command=lambda:self.safe(export_pdf)).pack(fill='x',pady=10)
        ctk.CTkButton(body,text='Guardar nota para imprimir (.txt)',height=42,command=lambda:self.safe(export)).pack(fill='x',pady=10)

    def backup(self):
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.sqlite3',initialfile=f'Respaldo_{date.today().isoformat()}.sqlite3',filetypes=[('Base SQLite','*.sqlite3')])
        if path:
            self.safe(lambda:self.do_backup(path))

    def do_backup(self,path):
        self.db.backup(path)
        messagebox.showinfo('Respaldo','Respaldo guardado correctamente.',parent=self)
