import tkinter as tk
from tkinter import messagebox,filedialog
from datetime import date,timedelta
import json
import customtkinter as ctk
from .cash import Cash,CATEGORIES,METHODS,INCOME_CATEGORIES
from .service import money


class CashUI:
    def cash_restore_modal(self, window, previous):
        def restore(event):
            if event.widget==window and previous and previous.winfo_exists():
                previous.grab_set()
        window.bind('<Destroy>',restore,add='+')

    def make_cash_banner(self, parent):
        frame=ctk.CTkFrame(parent,fg_color='#FFF0E5',corner_radius=12)
        frame.pack(fill='x',pady=(0,14))
        text=ctk.CTkLabel(frame,text='',justify='left',anchor='w',font=ctk.CTkFont(size=15,weight='bold'),wraplength=600)
        text.pack(side='left',fill='x',expand=True,padx=18,pady=15)
        button=ctk.CTkButton(frame,text='Abrir caja',height=46,width=170,command=lambda:self.safe(self.cash_today_action))
        button.pack(side='right',padx=16,pady=12)
        if not hasattr(self,'cash_banners'):self.cash_banners=[]
        self.cash_banners.append((frame,text,button))

    def refresh_cash_status(self):
        today=date.today().isoformat()
        self.cash_banner_day=today
        rows=self.db.rows('SELECT * FROM cash_days WHERE day=?',(today,))
        status=rows[0]['status'] if rows else 'Sin apertura'
        pending=self.db.rows("SELECT COUNT(*) FROM cash_days WHERE day<? AND status='Abierta'",(today,))[0][0]
        if status=='Sin apertura':
            title=f'CAJA SIN ABRIR · {date.today():%d/%m/%Y}\nAbre caja para registrar rentas, cobros y gastos.'
            label='Abrir caja';color='#FFF0E5';button_color='#F47724'
        elif status=='Abierta':
            title=f"CAJA ABIERTA · {date.today():%d/%m/%Y}\nResponsable: {rows[0]['responsible']} · Fondo inicial: {money(rows[0]['opening_cents'])}"
            label='Realizar corte';color='#E8F5EE';button_color='#18865B'
        else:
            title=f'CAJA CERRADA · {date.today():%d/%m/%Y}\nEl día está cerrado. Para continuar, reabre con un motivo.'
            label='Consultar / reabrir';color='#EAF0F7';button_color='#203F78'
        if pending:title+=f'\nAtención: {pending} caja(s) de fechas anteriores pendientes de corte.'
        for frame,text,button in getattr(self,'cash_banners',[]):
            frame.configure(fg_color=color);text.configure(text=title,text_color='#203F78')
            button.configure(text=label,fg_color=button_color)

    def cash_today_action(self):
        rows=self.db.rows('SELECT 1 FROM cash_days WHERE day=?',(date.today().isoformat(),))
        if rows:self.cash_day_dialog(date.today().isoformat())
        else:self.cash_open_dialog()

    def ensure_cash_open(self):
        rows=self.db.rows("SELECT 1 FROM cash_days WHERE day=? AND status='Abierta'",(date.today().isoformat(),))
        if rows:return True
        self.cash_today_action()
        return False

    def cash_open_dialog(self):
        previous=self.grab_current()
        win,body=self.dialog('Abrir caja del día')
        self.cash_restore_modal(win,previous)
        ctk.CTkLabel(body,text=f'INICIAR JORNADA · {date.today():%d/%m/%Y}',font=ctk.CTkFont(size=22,weight='bold'),text_color='#203F78').pack(pady=16)
        ctk.CTkLabel(body,text='Antes de registrar rentas, pagos o gastos, indica quién atiende\ny cuánto efectivo hay realmente en el cajón.',justify='left').pack(pady=8)
        opening=self.entry(body,'Fondo inicial en efectivo · MXN','0.00')
        responsible=self.entry(body,'Responsable de caja')
        def save():
            self.cash.open_day(date.today().isoformat(),opening.get(),responsible.get())
            win.destroy();self.refresh_cash_status();self.refresh_cash()
        ctk.CTkButton(body,text='Abrir caja e iniciar jornada',height=48,fg_color='#18865B',command=lambda:self.safe(save)).pack(fill='x',pady=18)
        ctk.CTkLabel(body,text='Tu formulario de renta se conserva. Al abrir caja, vuelve a pulsar Guardar renta.',wraplength=450,text_color='#748195').pack(pady=6)

    def make_cash(self):
        self.cash=Cash(self.db)
        container=self.tabs.tab('Caja y gastos')
        # Keep the complete report accessible when the window is short or Windows
        # uses display scaling. The table retains its own scrollbar for rows.
        page=ctk.CTkScrollableFrame(container,fg_color='transparent',corner_radius=0)
        page.pack(fill='both',expand=True)
        self.cash_content=page
        self.heading(page,'Caja y gastos','Cobros recibidos, gastos y cortes auditables · Los importes pendientes de renta no son ingresos de caja.')
        self.make_cash_banner(page)
        controls=ctk.CTkFrame(page,fg_color='white');controls.pack(fill='x',pady=8)
        a,b=self.pair(controls)
        self.cash_start=self.date_field(a,'Desde',date.today().isoformat())
        self.cash_end=self.date_field(b,'Hasta',date.today().isoformat())
        actions=ctk.CTkFrame(controls,fg_color='transparent');actions.pack(fill='x',pady=10)
        actions.grid_columnconfigure((0,1),weight=1,uniform='cash_actions')
        for index,(label,action) in enumerate([('Consultar',self.refresh_cash),('Registrar movimiento',self.cash_movement),('Apertura / corte',self.cash_day_dialog),('Empleados / vehículos',self.cash_catalog)]):
            ctk.CTkButton(actions,text=label,height=40,width=155,command=lambda f=action:self.safe(f)).grid(row=index//2,column=index%2,sticky='ew',padx=4,pady=4)
        self.cash_summary=ctk.CTkLabel(page,text='',font=ctk.CTkFont(size=16,weight='bold'),text_color='#203F78',justify='left',wraplength=1000)
        self.cash_summary.pack(fill='x',pady=10)
        self.cash_breakdown=ctk.CTkLabel(page,text='',text_color='#748195',justify='left',wraplength=1000)
        self.cash_breakdown.pack(fill='x',pady=(0,6))
        self.cash_table=self.table(page,('Fecha','Categoría','Concepto / empleado / vehículo','Método','Entrada','Salida','Estado'),height=8)
        for column in self.cash_table['columns']:
            self.cash_table.column(column,width=95,minwidth=65)
        self.cash_table.column('Concepto / empleado / vehículo',width=280,minwidth=170)
        bar=ctk.CTkFrame(page,fg_color='transparent');bar.pack(fill='x',pady=8)
        bar.grid_columnconfigure((0,1),weight=1,uniform='cash_reports')
        self.cash_report_buttons=[]
        for index,(label,action) in enumerate([('Anular movimiento',self.cash_cancel),('Historial de cortes',self.cash_history),('Exportar PDF',self.cash_export),('Imprimir reporte',self.cash_print)]):
            button=ctk.CTkButton(bar,text=label,height=40,command=lambda f=action:self.safe(f))
            button.grid(row=index//2,column=index%2,sticky='ew',padx=4,pady=4)
            self.cash_report_buttons.append(button)

    def refresh_cash(self):
        if not hasattr(self,'cash_table'):return
        self.refresh_cash_status()
        r=self.cash.report(self.cash_start.get(),self.cash_end.get())
        self.cash_summary.configure(text=f"Ingresos operativos: {money(r['operating_income'])}   Gastos: {money(r['expenses'])}   Flujo operativo: {money(r['net'])}\n"+
            '   |   '.join(f"{m}: entradas {money(r['incoming'][m])} / salidas {money(r['outgoing'][m])}" for m in METHODS))
        self.cash_breakdown.configure(text='   ·   '.join(f'{category}: {money(value)}' for category,value in r['by_category'].items() if value) or 'Sin gastos ni movimientos adicionales en este periodo.')
        self.fill(self.cash_table,[(e['id'],(e['day'],e['category'],e['description'],e['method'],money(e['amount']) if e['direction']==1 else '',
            money(e['amount']) if e['direction']==-1 else '', 'Anulado' if e['cancelled'] else 'Vigente')) for e in r['entries']])
        self.cash_table.tag_configure('void',foreground='#748195')
        for e in r['entries']:
            if e['cancelled']:self.cash_table.item(e['id'],tags=('void',))

    def cash_catalog(self):
        win,body=self.dialog('Empleados y vehículos')
        kind=tk.StringVar(value='Empleado')
        ctk.CTkOptionMenu(body,variable=kind,values=['Empleado','Vehículo']).pack(fill='x',pady=10)
        name=self.entry(body,'Nombre del empleado o identificación del vehículo')
        listing=self.table(body,('Tipo','Nombre'),height=6)
        def refresh():self.fill(listing,[(r['id'],(r['kind'],r['name'])) for r in self.db.rows('SELECT * FROM cash_entities ORDER BY kind,name')])
        def save():
            self.cash.catalog(kind.get(),name.get());name.set('');refresh()
        ctk.CTkButton(body,text='Agregar al catálogo',height=42,command=lambda:self.safe(save)).pack(fill='x',pady=10)
        refresh()

    def cash_movement(self):
        if not self.ensure_cash_open():return
        win,body=self.dialog('Registrar gasto o ingreso')
        day=self.date_field(body,'Fecha del movimiento',date.today().isoformat())
        category=tk.StringVar(value='Gasolina');method=tk.StringVar(value='Efectivo')
        ctk.CTkLabel(body,text='Categoría').pack(anchor='w')
        ctk.CTkOptionMenu(body,variable=category,values=list(CATEGORIES)).pack(fill='x',pady=5)
        direction=ctk.CTkLabel(body,text='',height=42,corner_radius=8,font=ctk.CTkFont(size=17,weight='bold'))
        direction.pack(fill='x',pady=8)
        amount_label=ctk.CTkLabel(body,text='')
        amount_label.pack(anchor='w')
        amount=tk.StringVar()
        ctk.CTkEntry(body,textvariable=amount,height=40).pack(fill='x',pady=(0,5))
        def category_changed(*_):
            incoming=category.get() in INCOME_CATEGORIES
            direction.configure(text='ENTRADA DE DINERO · Ingreso' if incoming else 'SALIDA DE DINERO · Egreso',
                text_color='#18865B' if incoming else '#AF3029',fg_color='#E8F5EE' if incoming else '#FFF1EF')
            amount_label.configure(text='Importe recibido · MXN' if incoming else 'Importe pagado · MXN')
        category.trace_add('write',category_changed)
        category_changed()
        win.cash_category=category
        win.cash_direction=direction
        win.cash_amount_label=amount_label
        ctk.CTkOptionMenu(body,variable=method,values=list(METHODS)).pack(fill='x',pady=5)
        entities={f"{r['kind']} · {r['name']}":r['id'] for r in self.db.rows('SELECT * FROM cash_entities ORDER BY kind,name')}
        entity=tk.StringVar(value='No aplica')
        ctk.CTkLabel(body,text='Empleado / vehículo (agregar primero en el catálogo)').pack(anchor='w')
        ctk.CTkOptionMenu(body,variable=entity,values=['No aplica',*entities]).pack(fill='x',pady=5)
        period=self.entry(body,'Periodo pagado (obligatorio en sueldos)')
        description=self.entry(body,'Concepto / descripción')
        reference=self.entry(body,'Referencia del comprobante (opcional)')
        responsible=self.entry(body,'Responsable de la captura')
        ctk.CTkLabel(body,text='Los cobros de rentas se incluyen automáticamente. No los dupliques aquí.',wraplength=450,text_color='#AF3029').pack(pady=8)
        def save():
            kind='ENTRADA DE DINERO' if category.get() in INCOME_CATEGORIES else 'SALIDA DE DINERO'
            if not messagebox.askyesno('Confirmar movimiento',f'{kind}\n{category.get()} · {amount.get()} MXN · {method.get()}\n¿Guardar?',parent=win):return
            self.cash.add(day.get(),category.get(),amount.get(),method.get(),description.get(),responsible.get(),entities.get(entity.get()),period.get(),reference.get())
            win.destroy();self.refresh_cash()
        ctk.CTkButton(body,text='Guardar movimiento',height=44,command=lambda:self.safe(save)).pack(fill='x',pady=10)

    def cash_cancel(self):
        selection=self.cash_table.selection()
        if not selection:raise ValueError('Selecciona el movimiento que deseas anular.')
        key=selection[0]
        if not key.startswith('M'):raise ValueError('Los cobros de renta se corrigen desde Pagos y saldos.')
        win,body=self.dialog('Anular movimiento sin eliminarlo')
        reason=self.entry(body,'Motivo de la anulación');responsible=self.entry(body,'Responsable')
        def save():
            self.cash.cancel(int(key[1:]),reason.get(),responsible.get());win.destroy();self.refresh_cash()
        ctk.CTkButton(body,text='Confirmar anulación',height=42,fg_color='#AF3029',command=lambda:self.safe(save)).pack(fill='x',pady=12)

    def cash_day_dialog(self, day_value=None):
        previous=self.grab_current()
        win,body=self.dialog('Apertura y corte de caja')
        self.cash_restore_modal(win,previous)
        day=self.date_field(body,'Día de caja',day_value or self.cash_end.get())
        summary=ctk.CTkLabel(body,text='',justify='left',font=ctk.CTkFont(size=16,weight='bold'));summary.pack(fill='x',pady=12)
        opening=self.entry(body,'Fondo inicial en efectivo · MXN','0.00')
        counted=self.entry(body,'Efectivo contado al cerrar · MXN','0.00')
        responsible=self.entry(body,'Responsable de apertura / cierre / reapertura')
        notes=self.entry(body,'Observaciones / motivo (obligatorio si hay diferencia o reapertura)')
        def refresh():
            self.refresh_cash_status()
            r=self.cash.day_report(day.get())
            summary.configure(text=f"{r['status']} · {day.get()}\nFondo: {money(r['opening'])}\nEntradas efectivo: {money(r['incoming']['Efectivo'])}\nSalidas efectivo: {money(r['outgoing']['Efectivo'])}\nEfectivo esperado: {money(r['expected'])}")
            for label,status in [('Registrar apertura','Sin apertura'),('Cerrar caja','Abierta'),('Reabrir con motivo','Cerrada')]:
                buttons[label].configure(state='normal' if r['status']==status else 'disabled')
        def open_day():self.cash.open_day(day.get(),opening.get(),responsible.get());refresh();self.refresh_cash()
        def close():
            from .service import cents
            r=self.cash.day_report(day.get());difference=cents(counted.get())-r['expected']
            if not messagebox.askyesno('Confirmar corte',f"Esperado: {money(r['expected'])}\nContado: {money(cents(counted.get()))}\nDiferencia: {money(difference)}\n¿Cerrar y bloquear esta fecha?",parent=win):return
            self.cash.close(day.get(),counted.get(),responsible.get(),notes.get());refresh();self.refresh_cash()
        def reopen():
            if messagebox.askyesno('Reabrir caja','Se conservará el corte anterior y se registrará el motivo. ¿Continuar?',parent=win):
                self.cash.reopen(day.get(),notes.get(),responsible.get());refresh()
        buttons={}
        for label,action in [('Consultar día',refresh),('Registrar apertura',open_day),('Cerrar caja',close),('Imprimir corte / reporte',lambda:self.cash_print(self.cash.day_report(day.get()))),('Reabrir con motivo',reopen)]:
            buttons[label]=ctk.CTkButton(body,text=label,height=40,command=lambda f=action:self.safe(f))
            buttons[label].pack(fill='x',pady=4)
        refresh()

    def cash_history(self):
        win,body=self.dialog('Historial de cortes y reaperturas')
        listing=self.table(body,('Fecha','Responsable','Esperado','Contado','Diferencia'),height=8)
        rows=self.db.rows('SELECT * FROM cash_closings ORDER BY id DESC')
        snapshots={r['id']:json.loads(r['snapshot']) for r in rows}
        self.fill(listing,[(key,(r['start'],r['responsible'],money(r['expected']),money(r['counted']),money(r['difference']))) for key,r in snapshots.items()])
        def export():
            key=self.selected(listing);self.cash_export(snapshots[key])
        ctk.CTkButton(body,text='PDF del corte seleccionado',command=lambda:self.safe(export)).pack(fill='x',pady=10)
        ctk.CTkButton(body,text='Imprimir corte seleccionado',height=42,command=lambda:self.safe(lambda:self.cash_print(snapshots[self.selected(listing)]))).pack(fill='x',pady=6)
        history='\n'.join(f"{r['day']} · {r['responsible']} · {r['reason']}" for r in self.db.rows('SELECT * FROM cash_reopenings ORDER BY id DESC LIMIT 20'))
        ctk.CTkLabel(body,text='Últimas reaperturas:\n'+(history or 'Sin reaperturas'),wraplength=450,justify='left').pack(fill='x',pady=10)

    def cash_export(self, snapshot=None):
        from .cash_pdf import export_cash
        r=snapshot or self.cash.report(self.cash_start.get(),self.cash_end.get())
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.pdf',initialfile=f"Caja_{r['start']}_{r['end']}.pdf",filetypes=[('PDF','*.pdf')])
        if path:
            export_cash(r,path)
            messagebox.showinfo('PDF','Reporte guardado correctamente.',parent=self)

    def cash_print(self,snapshot=None):
        import tempfile
        from pathlib import Path
        from .cash_pdf import export_cash
        from .printing import print_pdf
        if snapshot is None:
            if self.cash_start.get()==self.cash_end.get():snapshot=self.cash.day_report(self.cash_end.get())
            else:snapshot=self.cash.report(self.cash_start.get(),self.cash_end.get())
        if snapshot.get('status')=='Cerrada' and 'counted' not in snapshot:
            rows=self.db.rows('SELECT snapshot FROM cash_closings WHERE day=? ORDER BY id DESC LIMIT 1',(snapshot['start'],))
            if rows:snapshot=json.loads(rows[0][0])
        path=Path(tempfile.mkdtemp(prefix='alonso-impresion-'))/f"Caja_{snapshot['start']}_{snapshot['end']}.pdf"
        export_cash(snapshot,path)
        if print_pdf(path)=='preview':
            messagebox.showinfo('Imprimir reporte','Se abrió el PDF del reporte. Pulsa Ctrl+P para elegir la impresora y las copias.',parent=self)
