"""Interfaz de escritorio basada en la referencia visual de Alonso."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta
import customtkinter as ctk
from PIL import Image
from .resources import LOGO_PATH
from .ui import Application as BaseApplication
from .service import Service, money
from .calendar_picker import CalendarPicker
from .pricing import tariff_label
from .analytics import report
from .charts import BarChart
from .payments_ui import PaymentsUI
from .operations_ui import OperationsUI
from .service import cents

NAVY = '#203F78'
ORANGE = '#F47724'
BG = '#F3F6FA'
INK = '#263445'
MUTED = '#748195'
NEW_ADDRESS = 'Agregar nueva dirección de obra'


class Pages:
    def __init__(self, parent):
        self.frames = {}
        self.parent = parent

    def add(self, name):
        frame = ctk.CTkFrame(self.parent, fg_color=BG, corner_radius=0)
        self.frames[name] = frame
        return frame

    def tab(self, name):
        return self.frames[name]


class Application(OperationsUI,PaymentsUI,BaseApplication):
    def __init__(self, db):
        ctk.CTk.__init__(self)
        self.db, self.service = db, Service(db)
        self.client_id = None
        self.cart = {}
        self.cart_conditions={}
        self.matches = {}
        self.alert_window = None
        self.notified = set()
        self._closing = False
        self.title('Alonso | Control de rentas')
        self.geometry('1360x900')
        self.minsize(1060, 720)
        self.configure(fg_color=BG)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Treeview', background='white', fieldbackground='white', foreground=INK,
                        rowheight=42, font=('Segoe UI', 11), borderwidth=0)
        style.configure('Treeview.Heading', background='#EAF0F7', foreground=NAVY,
                        font=('Segoe UI', 10, 'bold'), padding=12, relief='flat')
        style.map('Treeview', background=[('selected', '#DAE7FB')], foreground=[('selected', NAVY)])
        header = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0, height=86)
        header.pack(fill='x')
        self.brand_image=ctk.CTkImage(light_image=Image.open(LOGO_PATH),dark_image=Image.open(LOGO_PATH),size=(82,82))
        ctk.CTkLabel(header,text='',image=self.brand_image,fg_color='transparent',corner_radius=0).pack(side='left',padx=(22,0),pady=10)
        brand = ctk.CTkFrame(header, fg_color='transparent')
        brand.pack(side='left', padx=26, pady=14)
        ctk.CTkLabel(brand, text='Alonso · Control de rentas', text_color='white', font=ctk.CTkFont(size=26, weight='bold')).pack(anchor='w')
        ctk.CTkLabel(brand, text='RENTA DE ANDAMIOS Y MAQUINARIA LIGERA', text_color='#DBE6FA',
                     font=ctk.CTkFont(size=11, weight='bold')).pack(anchor='w')
        self.clock = ctk.CTkLabel(header, text='', text_color='white', justify='right')
        self.clock.pack(side='right', padx=26)
        ctk.CTkFrame(self, fg_color=ORANGE, corner_radius=0, height=4).pack(fill='x')
        layout = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        layout.pack(fill='both', expand=True)
        sidebar = ctk.CTkFrame(layout, fg_color='white', width=210, corner_radius=0)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        ctk.CTkLabel(sidebar, text='CONTROL DE RENTAS', text_color=MUTED,
                     font=ctk.CTkFont(size=11, weight='bold')).pack(anchor='w', padx=20, pady=(25, 15))
        content = ctk.CTkFrame(layout, fg_color=BG, corner_radius=0)
        content.pack(side='left', fill='both', expand=True, padx=22, pady=18)
        self.tabs = Pages(content)
        self.nav_buttons = {}
        nav_scroll=ctk.CTkScrollableFrame(sidebar,fg_color='white',corner_radius=0)
        nav_scroll.pack(fill='both',expand=True)
        for name, label in [('Inicio', 'Inicio'), ('Nueva Renta', '+  Registrar renta'),
                            ('Rentas activas', 'Rentas activas'), ('Clientes', 'Clientes'),
                            ('Inventario/Precios', 'Inventario y precios'), ('Historial de Rentas', 'Historial de rentas'),
                            ('Gráficas', 'Gráficas y resultados'), ('Pagos y saldos','Pagos y saldos'),
                            ('Reservaciones','Reservaciones'),('Respaldos','Respaldos')]:
            self.tabs.add(name)
            button = ctk.CTkButton(nav_scroll, text=label, height=46, anchor='w', corner_radius=8,
                fg_color='white', text_color=INK, hover_color='#EAF0F7', font=ctk.CTkFont(size=14),
                command=lambda n=name: self.navigate(n))
            button.pack(fill='x', padx=12, pady=4)
            self.nav_buttons[name] = button
        ctk.CTkLabel(sidebar, text='Operación local · MXN\nCel. 312 298 32 50', text_color=MUTED, justify='left').pack(side='bottom', padx=15, pady=18)
        ctk.CTkButton(sidebar, text='Respaldar datos', height=40, fg_color=NAVY, command=self.backup).pack(side='bottom', padx=15, pady=8)
        self.make_dashboard()
        self.make_rental()
        self.make_clients()
        self.make_inventory()
        self.make_active()
        self.make_history()
        self.make_analytics()
        self.make_payments()
        self.make_reservations()
        self.make_backups()
        self.refresh()
        self.navigate('Inicio')
        self.tick()
        self.alert_job = self.after(1500, self.check_due)
        self.protocol('WM_DELETE_WINDOW', self.close)

    def close(self):
        self._closing = True
        if self.db.conn.total_changes:
            self.db.automatic_backup(force=True)
        for name in ('clock_job', 'alert_job'):
            if hasattr(self, name):
                self.after_cancel(getattr(self, name))
        super().close()

    def tick(self):
        self.clock.configure(text=datetime.now().strftime('%d/%m/%Y\n%H:%M:%S'))
        self.clock_job = self.after(1000, self.tick)

    def navigate(self, name):
        if name == 'Gráficas' and hasattr(self,'chart_rentals'):
            self.safe(self.refresh_analytics)
        for key, frame in self.tabs.frames.items():
            frame.pack_forget()
            self.nav_buttons[key].configure(fg_color='#EAF0F7' if key == name else 'white',
                text_color=NAVY if key == name else INK)
        self.tabs.tab(name).pack(fill='both', expand=True)

    def heading(self, parent, title, subtitle):
        ctk.CTkLabel(parent, text=title, text_color=INK, font=ctk.CTkFont(size=26, weight='bold')).pack(anchor='w')
        ctk.CTkLabel(parent, text=subtitle, text_color=MUTED, wraplength=900, justify='left').pack(anchor='w', pady=(0, 16))

    def panel(self, parent, title):
        panel = ctk.CTkFrame(parent, fg_color='white', corner_radius=12, border_width=1, border_color='#E2E8F0')
        panel.pack(fill='x', pady=(0, 14))
        inner = ctk.CTkFrame(panel, fg_color='transparent')
        inner.pack(fill='both', expand=True, padx=20, pady=16)
        if title:
            ctk.CTkLabel(inner, text=title, text_color=NAVY, font=ctk.CTkFont(size=17, weight='bold')).pack(anchor='w', pady=(0, 10))
        return inner

    def pair(self, parent):
        row = ctk.CTkFrame(parent, fg_color='transparent')
        row.pack(fill='x')
        left = ctk.CTkFrame(row, fg_color='transparent')
        right = ctk.CTkFrame(row, fg_color='transparent')
        left.pack(side='left', fill='x', expand=True, padx=(0, 14))
        right.pack(side='left', fill='x', expand=True)
        return left, right

    def entry(self, parent, label, default=''):
        ctk.CTkLabel(parent, text=label, text_color=INK, font=ctk.CTkFont(size=12, weight='bold')).pack(anchor='w', pady=(0, 4))
        var = tk.StringVar(value=default)
        widget = ctk.CTkEntry(parent, textvariable=var, height=40, fg_color='white', border_color='#CFD8E3', text_color=INK)
        widget.pack(fill='x', pady=(0, 10))
        return var

    def date_field(self, parent, label, initial):
        ctk.CTkLabel(parent,text=label,text_color=INK,font=ctk.CTkFont(size=12,weight='bold')).pack(anchor='w',pady=(0,4))
        row = ctk.CTkFrame(parent,fg_color='transparent')
        row.pack(fill='x',pady=(0,10))
        value = tk.StringVar(value=initial)
        ctk.CTkEntry(row,textvariable=value,height=40,state='readonly',fg_color='white').pack(side='left',fill='x',expand=True,padx=(0,6))
        ctk.CTkButton(row,text='Calendario',width=105,height=40,fg_color=NAVY,
            command=lambda:CalendarPicker(self,value,label)).pack(side='right')
        return value

    def make_dashboard(self):
        page = self.tabs.tab('Inicio')
        self.heading(page, 'Panel principal', 'Disponibilidad, rentas en curso y clientes que requieren seguimiento.')
        cards = ctk.CTkFrame(page, fg_color='transparent')
        cards.pack(fill='x', pady=(0, 18))
        self.stats = []
        for index, title in enumerate(['Tipos de equipos', 'Unidades disponibles', 'Rentas activas', 'Rentas vencidas']):
            cards.columnconfigure(index, weight=1)
            card = ctk.CTkFrame(cards, fg_color='white', corner_radius=12, border_width=1, border_color='#E2E8F0')
            card.grid(row=0, column=index, sticky='nsew', padx=(0, 10))
            title_label=ctk.CTkLabel(card, text=title, text_color=MUTED)
            title_label.pack(anchor='w', padx=16, pady=(16, 0))
            count = ctk.CTkLabel(card, text='0', text_color=ORANGE if index == 3 else NAVY,
                                font=ctk.CTkFont(size=32, weight='bold'))
            count.pack(anchor='w', padx=16, pady=(3, 15))
            self.stats.append(count)
            action = (lambda:self.navigate('Inventario/Precios')) if index < 2 else (
                (lambda:self.navigate('Rentas activas')) if index == 2 else self.open_due_alerts)
            for widget in (card,title_label,count):
                widget.configure(cursor='hand2')
                widget.bind('<Button-1>',lambda event,callback=action:self.safe(callback))
        self.dashboard_alert = ctk.CTkLabel(page, text='', fg_color='#FFF0E6', text_color='#9D4310',
            corner_radius=8, anchor='w', height=44)
        self.dashboard_alert.pack(fill='x', pady=(0, 12))
        ctk.CTkLabel(page, text='Próximas devoluciones y rentas vencidas', text_color=INK,
                     font=ctk.CTkFont(size=18, weight='bold')).pack(anchor='w')
        self.dashboard_table = self.table(page, ('Folio', 'Cliente', 'Teléfono', 'Devolución', 'Estado'), height=7)
        self.dashboard_table.bind('<Double-1>',self.open_dashboard_rental)
        self.dashboard_table.bind('<Return>',self.open_dashboard_rental)
        ctk.CTkLabel(page,text='Doble clic en una renta para abrirla en Rentas activas.',text_color=MUTED).pack(anchor='w')
        buttons = ctk.CTkFrame(page, fg_color='transparent')
        buttons.pack(fill='x', pady=10)
        ctk.CTkButton(buttons, text='+ Registrar renta', height=44, fg_color=NAVY, command=lambda: self.navigate('Nueva Renta')).pack(side='left', padx=(0, 8))
        ctk.CTkButton(buttons, text='Consultar alertas', height=44, fg_color=ORANGE, hover_color='#D96015', command=self.open_due_alerts).pack(side='left', padx=8)

    def open_dashboard_rental(self,event):
        # Ignorar encabezados y espacio vacío, aunque otra fila siga seleccionada.
        if event.keysym == 'Return':
            selected=self.dashboard_table.selection()
            key=selected[0] if selected else ''
        else:
            key=self.dashboard_table.identify_row(event.y)
        if not key:
            return
        self.active_filter.set('')
        self.refresh_active()
        self.navigate('Rentas activas')
        if self.active_table.exists(key):
            self.active_table.selection_set(key)
            self.active_table.focus(key)
            self.active_table.see(key)
            self.active_table.focus_set()

    def make_rental(self):
        page = self.tabs.tab('Nueva Renta')
        self.heading(page, 'Registrar nueva renta', 'Completa los datos del cliente, la dirección de obra y los equipos.')
        scroll = ctk.CTkScrollableFrame(page, fg_color=BG, corner_radius=0)
        scroll.pack(fill='both', expand=True)
        customer = self.panel(scroll, '1. Datos del cliente y dirección de obra')
        left, right = self.pair(customer)
        self.rental_name = self.entry(left, 'Nombre del cliente *')
        self.rental_phone = self.entry(right, 'Teléfono de contacto *')
        self._loading_client = False
        self._loaded_client = None
        self.suggestions = ctk.CTkFrame(customer,fg_color='#EDF3FC',corner_radius=8)
        self.client_context = ctk.CTkFrame(customer,fg_color='transparent')
        self.client_info = ctk.CTkLabel(self.client_context, text='',
            fg_color='#EDF3FC', text_color=NAVY, corner_radius=8, anchor='w', wraplength=850, justify='left')
        self.client_info.pack(fill='x', pady=(0, 12), ipady=8)
        self.rate_button = ctk.CTkButton(self.client_context,text='Calificar al cliente',height=38,fg_color=NAVY,state='disabled',
            command=lambda:self.safe(lambda:self.rating_dialog(self.client_id)))
        self.rate_button.pack(anchor='w',pady=(0,12))
        ctk.CTkButton(self.client_context,text='Limpiar datos del cliente',height=34,fg_color='#EAF0F7',text_color=NAVY,
            command=self.reset_client).pack(anchor='w',pady=(0,10))
        self.address_history=ctk.CTkFrame(customer,fg_color='transparent')
        ctk.CTkLabel(self.address_history, text='Direcciones anteriores', text_color=INK).pack(anchor='w')
        self.address_choice = tk.StringVar(value=NEW_ADDRESS)
        self.address_menu = ctk.CTkOptionMenu(self.address_history, values=[NEW_ADDRESS], variable=self.address_choice,
            height=38, fg_color=NAVY, command=self.address_changed)
        self.address_menu.pack(fill='x', pady=(3, 8))
        self.address_field=ctk.CTkFrame(customer,fg_color='transparent')
        self.address_field.pack(fill='x')
        self.new_address = self.entry(self.address_field, 'Dirección donde se utilizará el equipo *')
        self.rental_name.trace_add('write',lambda *_:self.suggest('name'))
        self.rental_phone.trace_add('write',lambda *_:self.suggest('phone'))
        equipment = self.panel(scroll, '2. Fechas y equipos de la renta')
        left, right = self.pair(equipment)
        self.departure = self.date_field(left, 'Fecha de salida', date.today().isoformat())
        self.due = self.date_field(right, 'Devolución estimada', (date.today()+timedelta(days=1)).isoformat())
        shortcuts=ctk.CTkFrame(equipment,fg_color='transparent')
        shortcuts.pack(fill='x',pady=4)
        ctk.CTkLabel(shortcuts,text='Duración rápida:').pack(side='left',padx=(0,10))
        for duration,title in [(1,'1 día'),(7,'1 semana'),(30,'1 mes (30 días)')]:
            ctk.CTkButton(shortcuts,text=title,width=130,fg_color=NAVY,
                command=lambda d=duration:self.safe(lambda:self.set_duration(d))).pack(side='left',padx=4)
        ctk.CTkLabel(equipment,text='Andamios: mínimo 7 días · $200/semana inicial · $30/día extra · $450/30 días',
            text_color=MUTED,wraplength=760).pack(anchor='w',pady=6)
        self.product_filter=self.entry(equipment,'Elegir equipo · filtra por nombre y pulsa su tarjeta')
        self.product_filter.trace_add('write',lambda *_:self.render_products())
        self.product_cards=ctk.CTkScrollableFrame(equipment,fg_color=BG,height=160)
        self.product_cards.pack(fill='x',pady=(0,10))
        self.selected_product=ctk.CTkLabel(equipment,text='Selecciona un equipo',text_color=NAVY,wraplength=800)
        self.selected_product.pack(anchor='w')
        row = ctk.CTkFrame(equipment, fg_color='transparent'); row.pack(fill='x', pady=8)
        row.columnconfigure(0, weight=1)
        self.item_choice = tk.StringVar()
        # Se conserva el selector interno para los componentes compartidos;
        # la selección visible se hace mediante las tarjetas.
        self.item_menu = ctk.CTkOptionMenu(row, values=[''], variable=self.item_choice, height=40, fg_color=NAVY)
        ctk.CTkLabel(row,text='Cantidad del equipo seleccionado:').grid(row=0,column=0,sticky='w')
        self.quantity = tk.StringVar(value='1')
        ctk.CTkEntry(row, textvariable=self.quantity, width=70, height=40).grid(row=0, column=1, padx=5)
        ctk.CTkButton(row, text='+ Agregar equipo', height=40, fg_color=NAVY,
            command=lambda: self.safe(self.add_cart)).grid(row=0, column=2, padx=5)
        condition_box=ctk.CTkFrame(equipment,fg_color='transparent');condition_box.pack(fill='x',pady=6)
        ctk.CTkLabel(condition_box,text='Estado al entregar el equipo seleccionado:').pack(side='left',padx=(0,10))
        self.delivery_condition=tk.StringVar(value='Bueno')
        delivery_notes_box=ctk.CTkFrame(equipment,fg_color='transparent')
        self.delivery_notes_box=delivery_notes_box
        self.delivery_notes=self.entry(delivery_notes_box,'Notas de entrega (opcional)')
        ctk.CTkOptionMenu(condition_box,values=['Bueno','Malo'],variable=self.delivery_condition,
            command=lambda value:delivery_notes_box.pack(fill='x',after=condition_box) if value=='Malo' else delivery_notes_box.pack_forget()).pack(side='left')
        self.cart_table = self.table(equipment, ('Artículo', 'Cantidad', 'Tarifa contratada', 'Subtotal'), height=3)
        ctk.CTkButton(equipment, text='Quitar equipo seleccionado', fg_color='#EAF0F7', text_color=NAVY,
            command=lambda: self.safe(self.remove_cart)).pack(anchor='w', pady=5)
        self.alert = ctk.CTkLabel(equipment, text='', text_color='#B52B27', wraplength=800)
        self.alert.pack(fill='x')
        payment=self.panel(scroll,'3. Anticipo o pago inicial (opcional)')
        extras=self.panel(scroll,'Flete y tablones extra (opcionales)')
        left,right=self.pair(extras)
        self.freight=self.entry(left,'Flete acordado - MXN (0 si no aplica)','0.00')
        self.extra_planks=self.entry(right,'Cantidad de tablones extra - $50 cada uno','0')
        ctk.CTkLabel(extras,text='Cargos por pedido. No se multiplican por los dias ni al ampliar.',text_color=MUTED).pack(anchor='w')
        self.invoice_required=tk.BooleanVar(value=False)
        ctk.CTkCheckBox(payment,text='Requiere factura · agregar IVA 16%',variable=self.invoice_required,command=self.update_total).pack(anchor='w',pady=(0,12))
        left,right=self.pair(payment)
        self.initial_amount=self.entry(left,'Importe recibido · MXN','0.00')
        ctk.CTkLabel(right,text='Método de pago').pack(anchor='w')
        self.initial_method=tk.StringVar(value='Efectivo')
        ctk.CTkOptionMenu(right,values=['Efectivo','Transferencia','Tarjeta'],variable=self.initial_method,height=40).pack(fill='x',pady=5)
        self.initial_reference=self.entry(payment,'Referencia (opcional)')
        ctk.CTkLabel(payment,text='Deja $0.00 si no ha pagado. El pago y la renta se guardan juntos.',text_color=MUTED).pack(anchor='w')
        ctk.CTkButton(payment,text='Guardar reservación para estas fechas',height=40,fg_color=NAVY,
            command=lambda:self.safe(self.reserve_current)).pack(anchor='w',pady=8)
        bottom = ctk.CTkFrame(page, fg_color='white', corner_radius=12)
        bottom.pack(fill='x', pady=(12, 0))
        self.total_label = ctk.CTkLabel(bottom, text='TOTAL: $0.00', text_color=NAVY,
            font=ctk.CTkFont(size=17, weight='bold'),justify='left')
        self.total_label.pack(side='left', padx=18, pady=18)
        ctk.CTkButton(bottom, text='Guardar renta y generar nota', height=46, fg_color=ORANGE,
            hover_color='#D96015', command=lambda: self.safe(self.confirm_rental)).pack(side='right', padx=18, pady=12)
        for var in (self.departure, self.due, self.freight, self.extra_planks):
            var.trace_add('write', lambda *_: self.update_total())

    def reset_client(self):
        self._loading_client = True
        self.client_id = None
        self.rate_button.configure(state='disabled')
        self.rental_name.set('')
        self.rental_phone.set('')
        self.new_address.set('')
        self.address_menu.configure(values=[NEW_ADDRESS])
        self.address_choice.set(NEW_ADDRESS)
        self._loaded_client = None
        self.matches = {}
        self.suggestions.pack_forget()
        self.client_context.pack_forget()
        self.address_history.pack_forget()
        self._loading_client = False

    def suggest(self,field):
        if self._loading_client:
            return
        if self.client_id is not None:
            old=self._loaded_client
            current=self.rental_phone.get() if field=='phone' else self.rental_name.get()
            original=old['phone'] if field=='phone' else old['name']
            normalize=lambda value: ''.join(c for c in value if c.isdigit()) if field=='phone' else value.strip().casefold()
            if normalize(current)==normalize(original):
                return
            # Cambiar de identidad no debe sobrescribir al cliente seleccionado antes.
            self._loading_client=True
            self.client_id = None
            self.rate_button.configure(state='disabled')
            other=self.rental_name if field=='phone' else self.rental_phone
            if other.get()==old['name' if field=='phone' else 'phone']:
                other.set('')
            if self.new_address.get()==old['address']:
                self.new_address.set('')
            self.address_menu.configure(values=[NEW_ADDRESS])
            self.address_choice.set(NEW_ADDRESS)
            self.client_context.pack_forget()
            self.address_history.pack_forget()
            self._loaded_client=None
            self._loading_client=False
        term = (self.rental_phone.get() if field=='phone' else self.rental_name.get()).strip().casefold()
        by_phone = field=='phone'
        normalized = ''.join(c for c in term if c.isdigit()) if by_phone else term
        self.matches = {}
        for row in self.db.rows('SELECT * FROM clients ORDER BY name'):
            value = ''.join(c for c in row['phone'] if c.isdigit()) if by_phone else row['name'].casefold()
            if normalized and normalized in value:
                self.matches[f"{row['name']} · {row['phone']} · #{row['id']}"] = row['id']
        values = list(self.matches)[:30]
        for widget in self.suggestions.winfo_children():
            widget.destroy()
        if not values:
            self.suggestions.pack_forget()
            return
        self.suggestions.pack(fill='x',pady=(0,12),before=self.address_field)
        ctk.CTkLabel(self.suggestions,text='Clientes registrados · selecciona una coincidencia',text_color=MUTED).pack(anchor='w',padx=12,pady=(6,2))
        for label in values[:5]:
            ctk.CTkButton(self.suggestions,text=label,anchor='w',height=36,fg_color='transparent',text_color=NAVY,hover_color='#DAE7FB',
                command=lambda value=label:self.choose_suggestion(value)).pack(fill='x',padx=6,pady=3)
        if len(values)>5:
            ctk.CTkLabel(self.suggestions,text='Escribe más letras o dígitos para precisar la búsqueda.',text_color=MUTED).pack(anchor='w',padx=12,pady=5)

    def select_client(self, key):
        self._loading_client=True
        self.client_id = key
        row = self.db.rows('SELECT * FROM clients WHERE id=?', (key,))[0]
        self.rental_name.set(row['name'])
        self.rental_phone.set(row['phone'])
        self.update_reputation(key)
        self.rate_button.configure(state='normal')
        addresses = self.db.rows('SELECT a.*, (SELECT MAX(r.id) FROM rentals r WHERE r.address_id=a.id) last_used FROM addresses a WHERE client_id=? ORDER BY last_used DESC,a.id DESC', (key,))
        values = [r['address'] for r in addresses]+[NEW_ADDRESS]
        self.address_menu.configure(values=values)
        self.address_choice.set(values[0])
        self.address_changed(values[0])
        self._loaded_client={'name':row['name'],'phone':row['phone'],'address':self.new_address.get()}
        self.suggestions.pack_forget()
        self.client_context.pack(fill='x',before=self.address_field)
        self.address_history.pack(fill='x',before=self.address_field)
        self._loading_client=False

    def update_reputation(self,key):
        row = self.db.rows('SELECT * FROM clients WHERE id=?',(key,))[0]
        history = self.db.rows('SELECT COUNT(*) total, SUM(CASE WHEN returned_at > due THEN 1 ELSE 0 END) late FROM rentals WHERE client_id=?',(key,))[0]
        rating = (f"Calificación de la secretaria · Pago {row['payment_rating']}/5 | Entrega {row['return_rating']}/5 | Cuidado {row['care_rating']}/5"
                  if row['ratings_confirmed'] else 'Sin calificar · La secretaria aún no ha evaluado al cliente')
        self.client_info.configure(text=rating+f"\nHistorial automático: {history['total']} rentas · {history['late'] or 0} devoluciones fuera de fecha"
            +(f"\nObservaciones: {row['notes']}" if row['notes'] else ''))

    def rating_dialog(self,key):
        if key is None:
            raise ValueError('Guarda o selecciona un cliente antes de calificarlo.')
        row = self.db.rows('SELECT * FROM clients WHERE id=?',(key,))[0]
        win,body = self.dialog('Calificar al cliente')
        ctk.CTkLabel(body,text=row['name'],font=ctk.CTkFont(size=22,weight='bold'),text_color=NAVY).pack(anchor='w',pady=10)
        ctk.CTkLabel(body,text='Evaluación manual de la secretaria.\nEl conteo de retrasos no asigna estas puntuaciones.',justify='left',text_color=MUTED).pack(anchor='w',pady=10)
        scores=[]
        for column,title in [('payment_rating','Puntualidad de pago'),('return_rating','Devolución a tiempo'),('care_rating','Cuidado de la maquinaria')]:
            ctk.CTkLabel(body,text=title,font=ctk.CTkFont(size=15,weight='bold')).pack(anchor='w',pady=(12,5))
            value=tk.StringVar(value=str(row[column]) if row['ratings_confirmed'] else 'Seleccionar')
            ctk.CTkOptionMenu(body,values=['Seleccionar','1','2','3','4','5'],variable=value,height=40).pack(fill='x')
            scores.append(value)
        ctk.CTkLabel(body,text='1 = Malo · 2 = Deficiente · 3 = Regular\n4 = Bueno · 5 = Excelente',justify='left',text_color=MUTED).pack(anchor='w',pady=18)
        def save():
            self.service.rate_client(key,[s.get() for s in scores])
            win.destroy()
            self.refresh_clients()
            if self.client_id == key:
                self.update_reputation(key)
        ctk.CTkButton(body,text='Guardar calificación',height=44,fg_color=ORANGE,command=lambda:self.safe(save)).pack(fill='x',pady=12)

    def address_changed(self, value):
        self.new_address.set('' if value == NEW_ADDRESS else value)

    def confirm_rental(self):
        initial=cents(self.initial_amount.get())
        if not messagebox.askyesno('Guardar renta', self.total_label.cget('text')+'\n¿Confirmar los datos y registrar la renta?', parent=self):
            return
        key = self.service.create_rental(self.client_id, self.new_address.get(), self.departure.get(), self.due.get(), self.cart,
            client_data={'name': self.rental_name.get(), 'phone': self.rental_phone.get()},
            initial_payment={'amount':self.initial_amount.get(),'method':self.initial_method.get(),'reference':self.initial_reference.get(),'kind':'Anticipo'} if initial else None,
            delivery_states=self.cart_conditions,invoice_required=self.invoice_required.get(),freight=self.freight.get(),extra_planks=self.extra_planks.get())
        self.cart.clear()
        self.cart_conditions.clear()
        self.reset_client()
        self.initial_amount.set('0.00')
        self.initial_reference.set('')
        self.initial_method.set('Efectivo')
        self.freight.set('0.00');self.extra_planks.set('0')
        self.invoice_required.set(False)
        self.refresh()
        self.show_note(key)

    def make_clients(self):
        self.heading(self.tabs.tab('Clientes'), 'Directorio de clientes', 'Consulta sus datos, obras anteriores y reputación de pago, entrega y cuidado.')
        super().make_clients()
        ctk.CTkButton(self.tabs.tab('Clientes'),text='Calificar cliente seleccionado',height=42,fg_color=NAVY,
            command=lambda:self.safe(lambda:self.rating_dialog(self.selected(self.clients)))).pack(anchor='w',pady=10)

    def make_inventory(self):
        self.heading(self.tabs.tab('Inventario/Precios'), 'Inventario y precios', 'Administra equipos, existencias y tarifas diarias del negocio.')
        super().make_inventory()
        ctk.CTkButton(self.tabs.tab('Inventario/Precios'),text='Liberar piezas revisadas / reparadas',height=40,fg_color='#18865B',
            command=lambda:self.safe(self.release_dialog)).pack(anchor='w',pady=8)

    def make_history(self):
        self.heading(self.tabs.tab('Historial de Rentas'), 'Historial de rentas', 'Consulta todas las notas y sus importes actualizados, incluidas las ampliaciones.')
        super().make_history()
        ctk.CTkButton(self.tabs.tab('Historial de Rentas'),text='Pagos y saldo de la renta',height=40,fg_color='#18865B',
            command=lambda:self.safe(lambda:self.payment_dialog(self.selected(self.history)))).pack(anchor='w',pady=8)
        ctk.CTkButton(self.tabs.tab('Historial de Rentas'), text='Agregar días a la renta seleccionada', height=40, fg_color=NAVY,
            command=lambda: self.safe(lambda: self.extension_dialog(self.selected(self.history)))).pack(anchor='w', pady=8)

    def make_active(self):
        page = self.tabs.tab('Rentas activas')
        self.heading(page, 'Rentas activas', 'Equipos fuera del negocio. Consulta datos de contacto, amplía la renta o registra su devolución.')
        self.active_filter = self.entry(page, 'Buscar por cliente, teléfono, material o dirección')
        self.active_table = self.table(page, ('Folio', 'Cliente / teléfono', 'Material', 'Dirección', 'Devolución', 'Total', 'Estado'))
        self.active_filter.trace_add('write', lambda *_: self.refresh_active())
        bar = ctk.CTkFrame(page, fg_color='transparent'); bar.pack(fill='x', pady=10)
        for text, action, color in [('Ver nota', lambda: self.show_note(self.selected(self.active_table)), NAVY),
                                    ('Pagos y saldo',lambda:self.payment_dialog(self.selected(self.active_table)),'#18865B'),
                                    ('Agregar días', lambda: self.extension_dialog(self.selected(self.active_table)), ORANGE),
                                    ('Registrar devolución', self.return_active, '#18865B')]:
            ctk.CTkButton(bar, text=text, height=44, fg_color=color, command=lambda a=action: self.safe(a)).pack(side='left', padx=5)

    def rental_material(self, key):
        return ', '.join(f"{r['pending']} pendientes de {r['quantity']} × {r['item_name']}" for r in self.service.remaining_lines(key) if r['pending'])

    def refresh_active(self):
        term = self.active_filter.get().casefold().strip()
        rows = []
        for r in self.db.rows('SELECT * FROM rentals WHERE returned_at IS NULL ORDER BY due,id'):
            material = self.rental_material(r['id'])
            searchable = f"{r['client_name']} {r['client_phone']} {material} {r['work_address']}".casefold()
            if term in searchable:
                rows.append((r['id'], (f"{r['id']:06d}", f"{r['client_name']} / {r['client_phone']}", material,
                    r['work_address'], r['due'], money(r['total_cents']), 'Vencida' if r['due'] < date.today().isoformat() else 'Activa')))
        self.fill(self.active_table, rows)
        for key, values in rows:
            if values[-1] == 'Vencida':
                self.active_table.item(str(key), tags=('overdue',))
        self.active_table.tag_configure('overdue', foreground='#AF3029', background='#FFF1EF')

    def refresh(self):
        super().refresh()
        self.render_products()
        self.refresh_active()
        self.refresh_dashboard()
        self.refresh_payments()
        self.refresh_reservations()
        self.refresh_backups()
        views=[]
        for key,text in getattr(self,'note_views',[]):
            if text.winfo_exists():
                text.configure(state='normal')
                text.delete('1.0','end')
                text.insert('1.0',self.service.note(key))
                text.configure(state='disabled')
                views.append((key,text))
        self.note_views=views
        if hasattr(self,'chart_rentals'):
            self.safe(self.refresh_analytics)

    def make_analytics(self):
        page=self.tabs.tab('Gráficas')
        self.heading(page,'Gráficas y resultados','Seguimiento por periodo · Los importes son ingresos esperados, no utilidad neta ni pagos cobrados.')
        controls=ctk.CTkFrame(page,fg_color='white',corner_radius=10)
        controls.pack(fill='x',pady=(0,12))
        left,right=self.pair(controls)
        self.analytics_start=self.date_field(left,'Desde',(date.today()-timedelta(days=29)).isoformat())
        self.analytics_end=self.date_field(right,'Hasta',date.today().isoformat())
        bar=ctk.CTkFrame(controls,fg_color='transparent');bar.pack(fill='x',padx=10,pady=(0,10))
        for count in (7,30,90):
            ctk.CTkButton(bar,text=f'Últimos {count} días',width=140,fg_color=NAVY,
                command=lambda n=count:self.analytics_period(n)).pack(side='left',padx=4)
        ctk.CTkButton(bar,text='Ver resultados',fg_color=ORANGE,command=lambda:self.safe(self.refresh_analytics)).pack(side='right',padx=4)
        scroll=ctk.CTkScrollableFrame(page,fg_color=BG)
        scroll.pack(fill='both',expand=True)
        self.analytics_summary=ctk.CTkLabel(scroll,text='',text_color=NAVY,font=ctk.CTkFont(size=17,weight='bold'),justify='left',wraplength=850)
        self.analytics_summary.pack(fill='x',pady=12)
        self.chart_rentals=BarChart(scroll,'Nuevas rentas por día · número de notas')
        self.chart_income=BarChart(scroll,'Ingreso esperado por día · reparto del importe contratado',money)
        self.chart_occupancy=BarChart(scroll,'Unidades en renta por día')
        self.chart_popular=BarChart(scroll,'Productos más rentados · unidades que salieron en el periodo')
        ctk.CTkLabel(scroll,text='Ingreso esperado: importe repartido entre los días contratados; no representa cobros ni descuenta gastos.\nLas rentas vencidas siguen ocupando equipos, pero no generan cargos extra hasta que se amplíen.',
            text_color=MUTED,wraplength=850,justify='left').pack(anchor='w',pady=10)
        self.analytics_daily=self.table(scroll,('Fecha','Nuevas rentas','Unidades entregadas','Unidades en renta','Ingreso esperado'),height=7)

    def analytics_period(self,days):
        self.analytics_start.set((date.today()-timedelta(days=days-1)).isoformat())
        self.analytics_end.set(date.today().isoformat())
        self.safe(self.refresh_analytics)

    def refresh_analytics(self):
        data=report(self.db,date.fromisoformat(self.analytics_start.get()),date.fromisoformat(self.analytics_end.get()))
        series=data['days']
        rentals=sum(v['rentals'] for v in series.values())
        units=sum(v['units'] for v in series.values())
        total=sum(v['expected_cents'] for v in series.values())
        best=data['popular'][0]['name'] if data['popular'] else 'Sin movimientos'
        self.analytics_summary.configure(text=f"{rentals} rentas nuevas · {units} unidades entregadas · {data['current_units']} unidades actualmente fuera\n"
            f"Ingreso esperado del periodo: {money(total)} MXN · Más rentado: {best}")
        labels=[(d.strftime('%d/%m'),v) for d,v in series.items()]
        self.chart_rentals.set_values([(d,v['rentals']) for d,v in labels])
        self.chart_income.set_values([(d,v['expected_cents']) for d,v in labels])
        self.chart_occupancy.set_values([(d,v['in_use']) for d,v in labels])
        self.chart_popular.set_values([(r['name'],r['units']) for r in data['popular'][:10]])
        self.fill(self.analytics_daily,[(i,(d.isoformat(),v['rentals'],v['units'],v['in_use'],money(v['expected_cents'])))
            for i,(d,v) in enumerate(series.items(),1)])

    def set_duration(self, days):
        self.due.set((date.fromisoformat(self.departure.get())+timedelta(days=days)).isoformat())

    def render_products(self):
        if not hasattr(self,'items'):
            return
        for child in self.product_cards.winfo_children():
            child.destroy()
        term=self.product_filter.get().casefold().strip()
        rows=[r for r in self.items.values() if term in r['name'].casefold()]
        for index,row in enumerate(rows):
            self.product_cards.columnconfigure(index%2,weight=1)
            label=next(label for label,key in self.item_labels.items() if key == row['id'])
            try:
                available=max(0,self.service.period_available(row['id'],self.departure.get(),self.due.get()))
            except ValueError:
                available=0
            ready=available>0 and row['price_cents']>0
            compact=(f"7d {money(row['week_cents'])} · Extra {money(row['price_cents'])} · Mes {money(row['month_cents'])}"
                     if row['pricing_mode']=='scaffold' else tariff_label(row))
            button=ctk.CTkButton(self.product_cards,text=f"{row['name']} · {available} para esas fechas\n{compact}",
                height=65,anchor='w',fg_color='white',text_color=NAVY,hover_color='#DAE7FB',border_width=1,border_color='#D4DEEC',
                state='normal' if ready else 'disabled',font=ctk.CTkFont(size=12),
                command=lambda l=label:self.choose_product(l))
            button.grid(row=index//2,column=index%2,sticky='ew',padx=5,pady=5)
        if not rows:
            ctk.CTkLabel(self.product_cards,text='No hay equipos con ese nombre.').pack(pady=10)
        self.selected_product.configure(text='Elige un equipo en las tarjetas; los precios pendientes se configuran en Inventario.')
        self.item_choice.set('')

    def choose_product(self,label):
        self.item_choice.set(label)
        row=self.items[self.item_labels[label]]
        state=self.cart_conditions.get(row['id'],{})
        self.delivery_condition.set(state.get('condition','Bueno'))
        self.delivery_notes.set(state.get('notes',''))
        if self.delivery_condition.get()=='Malo':
            self.delivery_notes_box.pack(fill='x',before=self.cart_table.master)
        else:
            self.delivery_notes_box.pack_forget()
        self.selected_product.configure(text=f"Seleccionado: {row['name']} · {tariff_label(row)}")
        if row['pricing_mode']=='scaffold':
            try:
                if (date.fromisoformat(self.due.get())-date.fromisoformat(self.departure.get())).days < 7:
                    self.set_duration(7)
            except ValueError:
                pass

    def add_cart(self):
        key=self.item_labels.get(self.item_choice.get())
        if key is None:
            raise ValueError('Selecciona un equipo.')
        quantity=int(self.quantity.get())
        if quantity<1:
            raise ValueError('La cantidad debe ser mayor a cero.')
        requested=self.cart.get(key,0)+quantity
        if requested>self.service.period_available(key,self.departure.get(),self.due.get()):
            raise ValueError('La cantidad supera la disponibilidad para esas fechas.')
        self.cart[key]=requested
        self.cart_conditions[key]={'condition':self.delivery_condition.get(),'notes':self.delivery_notes.get()}
        self.update_total()

    def update_total(self):
        super().update_total()
        if hasattr(self,'items'):
            for key,quantity in self.cart.items():
                values=list(self.cart_table.item(str(key),'values'))
                values[0]=f"{self.items[key]['name']} · {self.cart_conditions.get(key,{}).get('condition','Bueno')}"
                self.cart_table.item(str(key),values=values)
                try:
                    if quantity>self.service.period_available(key,self.departure.get(),self.due.get()):
                        self.alert.configure(text='Hay piezas comprometidas en esas fechas. Revisa disponibilidad antes de confirmar.')
                except ValueError:
                    pass
        if hasattr(self,'product_cards'):
            # Actualizar las tarjetas al cambiar fechas, conservando la selección vigente.
            selected=self.item_choice.get()
            self.render_products()
            if selected in self.item_labels:
                self.choose_product_without_dates(selected)

    def choose_product_without_dates(self,label):
        self.item_choice.set(label)
        row=self.items[self.item_labels[label]]
        self.selected_product.configure(text=f"Seleccionado: {row['name']} · {tariff_label(row)}")

    def refresh_dashboard(self):
        active = self.db.rows('SELECT * FROM rentals WHERE returned_at IS NULL ORDER BY due,id')
        overdue = self.service.overdue()
        values = [len(self.items), sum(r['available'] for r in self.items.values()), len(active), len(overdue)]
        for widget, value in zip(self.stats, values):
            widget.configure(text=str(value))
        self.dashboard_alert.configure(text=f'   {len(overdue)} rentas vencidas requieren seguimiento. Usa «Consultar alertas».' if overdue
            else '   Sin rentas vencidas. Las devoluciones están al día.')
        if self.db.backup_error:
            self.dashboard_alert.configure(text='   No se pudo crear el respaldo automático. Revisa el apartado Respaldos.')
        self.fill(self.dashboard_table, [(r['id'], (f"{r['id']:06d}", r['client_name'], r['client_phone'], r['due'],
            'Vencida' if r['due'] < date.today().isoformat() else 'Vigente')) for r in active[:20]])

    def return_active(self):
        self.return_dialog(self.selected(self.active_table))

    def return_selected(self):
        self.return_dialog(self.selected(self.history))

    def extension_dialog(self, key, on_saved=None):
        self.service.extension_quote(key, 1)  # Valida antes de abrir la ventana.
        rental = self.db.rows('SELECT * FROM rentals WHERE id=?', (key,))[0]
        win, body = self.dialog(f'Ampliar renta #{key:06d}')
        ctk.CTkLabel(body, text='Agregar días de renta', text_color=NAVY, font=ctk.CTkFont(size=24, weight='bold')).pack(anchor='w', pady=(0, 12))
        ctk.CTkLabel(body, text=f"{rental['client_name']}\nTel. {rental['client_phone']}\n{self.rental_material(key)}\nObra: {rental['work_address']}",
            wraplength=450, justify='left', text_color=INK).pack(anchor='w', pady=10)
        ctk.CTkLabel(body, text=f"Devolución actual: {rental['due']}\nTotal actual: {money(rental['total_cents'])} MXN", justify='left').pack(anchor='w')
        days = self.entry(body, '¿Cuántos días adicionales?', '3')
        summary = ctk.CTkLabel(body, text='', justify='left', text_color=NAVY, font=ctk.CTkFont(size=17, weight='bold'))
        summary.pack(anchor='w', pady=18)
        ctk.CTkLabel(body, text='Los días se suman a la fecha de devolución actual.\nSe respeta la tarifa contratada; al completar un mes\npuede haber una reducción del importe.', text_color=MUTED, justify='left').pack(anchor='w')
        def preview(*_):
            try:
                q = self.service.extension_quote(key, int(days.get()))
                summary.configure(text=f"Nueva devolución: {q['new_due']}\nAjuste del importe: {money(q['added_cents'])}\nNuevo total: {money(q['total_cents'])} MXN", text_color=NAVY)
            except ValueError:
                summary.configure(text='Escribe un número válido de días (1–3650).', text_color='#B52B27')
        def save():
            added = int(days.get())
            q = self.service.extension_quote(key, added)
            if not messagebox.askyesno('Confirmar ampliación', f"Agregar {added} días hasta {q['new_due']}\nNuevo total: {money(q['total_cents'])} MXN\n¿Guardar ampliación?", parent=win):
                return
            self.service.extend_rental(key, added)
            win.destroy()
            self.refresh()
            if on_saved:
                on_saved()
        days.trace_add('write', preview)
        preview()
        ctk.CTkButton(body, text='Guardar ampliación', fg_color=ORANGE, hover_color='#D96015', height=46,
            command=lambda: self.safe(save)).pack(fill='x', pady=20)

    def check_due(self):
        if self._closing:
            return
        self.db.automatic_backup()
        self.refresh_backups()
        self.refresh_dashboard()
        pending = [r for r in self.service.overdue() if (r['id'], r['due']) not in self.notified]
        # No interrumpir una captura en otra ventana; el aviso espera a que termine.
        if pending and self.grab_current() is None and self.alert_window is None:
            self.open_due_alerts(pending)
        self.alert_job = self.after(60000, self.check_due)

    def open_due_alerts(self, rows=None):
        if self.alert_window is not None and self.alert_window.winfo_exists():
            self.alert_window.lift()
            return
        rows = self.service.overdue() if rows is None else rows
        if not rows:
            messagebox.showinfo('Seguimiento de rentas', 'No hay rentas vencidas.', parent=self)
            return
        win = ctk.CTkToplevel(self)
        self.alert_window = win
        win.title('Alonso | Rentas vencidas')
        win.geometry('760x640')
        win.transient(self)
        win.configure(fg_color=BG)
        self.notified.update((r['id'], r['due']) for r in rows)
        ctk.CTkLabel(win, text='Hay rentas vencidas', text_color='#B52B27', font=ctk.CTkFont(size=25, weight='bold')).pack(anchor='w', padx=22, pady=(20, 4))
        ctk.CTkLabel(win, text='Contacta al cliente o agrega los días que haya solicitado.', text_color=MUTED).pack(anchor='w', padx=22)
        body = ctk.CTkScrollableFrame(win, fg_color=BG)
        body.pack(fill='both', expand=True, padx=15, pady=12)
        def close():
            self.alert_window = None
            win.destroy()
        def rebuild():
            close()
            remaining = self.service.overdue()
            if remaining:
                self.open_due_alerts(remaining)
        for rental in rows:
            key = rental['id']
            card = self.panel(body, f"Renta #{key:06d} · Venció el {rental['due']}")
            late = (date.today()-date.fromisoformat(rental['due'])).days
            ctk.CTkLabel(card, text=f"Cliente: {rental['client_name']}\nTeléfono: {rental['client_phone']}\nMaterial: {self.rental_material(key)}\nObra: {rental['work_address']}\n{late} días vencida · Total registrado: {money(rental['total_cents'])} MXN",
                wraplength=640, justify='left', text_color=INK).pack(anchor='w')
            ctk.CTkButton(card, text='Agregar días / recalcular importe', height=40, fg_color=ORANGE,
                hover_color='#D96015', command=lambda k=key: self.safe(lambda: self.extension_dialog(k, rebuild))).pack(anchor='w', pady=(12, 0))
        ctk.CTkButton(win, text='Aceptar · continuar trabajando', height=44, fg_color=NAVY, command=close).pack(fill='x', padx=22, pady=(0, 18))
        win.protocol('WM_DELETE_WINDOW', close)

