import tkinter as tk
from tkinter import messagebox,filedialog
from datetime import date,timedelta
import customtkinter as ctk
from .address_fields import AddressFields
from .pricing import unit_total,tariff_label
from .service import cents,money
from .taxes import amounts


class ReservationUI:
    def new_reservation_dialog(self):
        if not self.ensure_cash_open():return
        win,body=self.dialog('Nueva reservación · anticipo mínimo 50%')
        win.geometry('1050x850')
        ctk.CTkLabel(body,text='Reservar para una fecha futura',font=ctk.CTkFont(size=25,weight='bold'),text_color='#203F78').pack(anchor='w',pady=10)
        left,right=self.pair(body)
        name=self.entry(left,'Nombre del cliente');phone=self.entry(right,'Teléfono')
        suggestions=ctk.CTkFrame(body,fg_color='transparent');suggestions.pack(fill='x')
        state=dict(client_id=None,loading=False,minimum=0,total=0,auto_amount=True,updating=False)
        address=AddressFields(body);address.pack(fill='x',pady=8)
        history=tk.StringVar(value='Agregar dirección nueva')
        history_menu=ctk.CTkOptionMenu(body,values=['Agregar dirección nueva'],variable=history,
            command=lambda value:address.load_saved(self.db,state['client_id'],'' if value=='Agregar dirección nueva' else value))
        history_menu.pack(fill='x',pady=6)
        def choose(client):
            state['loading']=True;state['client_id']=client['id']
            name.set(client['name']);phone.set(client['phone'])
            addresses=self.db.rows('SELECT address FROM addresses WHERE client_id=? ORDER BY id DESC',(client['id'],))
            values=[r['address'] for r in addresses]+['Agregar dirección nueva']
            history_menu.configure(values=values);history.set(values[0]);address.load_saved(self.db,client['id'],addresses[0]['address'] if addresses else '')
            for w in suggestions.winfo_children():w.destroy()
            state['loading']=False
        def suggest(field):
            if state['loading']:return
            state['client_id']=None
            for w in suggestions.winfo_children():w.destroy()
            text=(phone.get() if field=='phone' else name.get()).strip().casefold()
            if not text:return
            normalize=lambda value:''.join(c for c in value if c.isdigit()) if field=='phone' else value.casefold()
            matches=[r for r in self.db.rows('SELECT * FROM clients ORDER BY name') if normalize(text) and normalize(text) in normalize(r['phone'] if field=='phone' else r['name'])]
            for row in matches[:5]:
                ctk.CTkButton(suggestions,text=f"{row['name']} · {row['phone']}",fg_color='#EAF0F7',text_color='#203F78',command=lambda r=row:choose(r)).pack(fill='x',pady=2)
        name.trace_add('write',lambda *_:suggest('name'));phone.trace_add('write',lambda *_:suggest('phone'))
        left,right=self.pair(body)
        start=self.date_field(left,'Entrega programada',(date.today()+timedelta(days=2)).isoformat())
        end=self.date_field(right,'Devolución programada',(date.today()+timedelta(days=9)).isoformat())
        ctk.CTkLabel(body,text='Se reserva un día completo antes de la entrega para recoger y preparar las piezas.',text_color='#748195').pack(anchor='w',pady=6)
        products=ctk.CTkFrame(body,fg_color='transparent');products.pack(fill='x')
        quantities={};availability={}
        for item in self.items.values():
            row=ctk.CTkFrame(products,fg_color='white');row.pack(fill='x',pady=3)
            ctk.CTkLabel(row,text=item['name'],width=350,wraplength=350,anchor='w').pack(side='left',padx=8)
            var=tk.StringVar(value='0');quantities[item['id']]=var
            ctk.CTkEntry(row,textvariable=var,width=65).pack(side='left',padx=8,pady=7)
            availability[item['id']]=ctk.CTkLabel(row,text='',wraplength=400)
            availability[item['id']].pack(side='left',padx=8)
        left,right=self.pair(body)
        freight=self.entry(left,'Flete (opcional) · MXN','0');planks=self.entry(right,'Tablones extra · $50 cada uno','0')
        invoice=tk.BooleanVar(value=False)
        ctk.CTkCheckBox(body,text='Requiere factura · IVA 16%',variable=invoice).pack(anchor='w',pady=8)
        summary=ctk.CTkLabel(body,text='',font=ctk.CTkFont(size=18,weight='bold'),text_color='#203F78');summary.pack(fill='x',pady=10)
        left,right=self.pair(body)
        deposit=self.entry(left,'Anticipo recibido · mínimo 50%','0.00')
        method=tk.StringVar(value='Efectivo')
        ctk.CTkLabel(right,text='Método del anticipo').pack(anchor='w')
        method_menu=ctk.CTkOptionMenu(right,values=['Efectivo','Transferencia','Tarjeta'],variable=method);method_menu.pack(fill='x',pady=5)
        receipt=self.receipt_picker(body,method)
        reference=self.entry(body,'Referencia del anticipo (opcional)')
        def total(*_):
            try:
                days=(date.fromisoformat(end.get())-date.fromisoformat(start.get())).days
                amount=0
                for key,var in quantities.items():
                    qty=int(var.get() or '0')
                    if qty<0:raise ValueError('Las cantidades no pueden ser negativas.')
                    free=self.service.period_available(key,start.get(),end.get(),for_reservation=True)
                    availability[key].configure(text=f"Disponibles en esas fechas: {max(0,free)} · {tariff_label(self.items[key])}")
                    if qty:amount+=unit_total(self.items[key],days)*qty
                extra=int(planks.get() or '0')
                if extra<0:raise ValueError('Los tablones extra no pueden ser negativos.')
                breakdown=amounts(amount+cents(freight.get() or '0')+extra*5000,1600 if invoice.get() else 0,0)
                state['total']=breakdown['total_cents'];state['minimum']=(state['total']+1)//2
                summary.configure(text=f"Total: {money(state['total'])} · Anticipo mínimo 50%: {money(state['minimum'])}",text_color='#203F78')
                if state['auto_amount']:
                    state['updating']=True;deposit.set(f"{state['minimum']/100:.2f}");state['updating']=False
            except (ValueError,KeyError) as exc:
                state['total']=state['minimum']=0;summary.configure(text=str(exc),text_color='#AF3029')
        def deposit_changed(*_):
            if not state['updating']:state['auto_amount']=False
        deposit.trace_add('write',deposit_changed)
        def invoice_changed(*_):
            method_menu.configure(values=['Transferencia'] if invoice.get() else ['Efectivo','Transferencia','Tarjeta'])
            if invoice.get():method.set('Transferencia')
            total()
        invoice.trace_add('write',invoice_changed)
        for var in [start,end,freight,planks,*quantities.values()]:var.trace_add('write',total)
        def save():
            total()
            if date.fromisoformat(start.get())<=date.today():raise ValueError('La reservación es para una fecha futura. Para entregar hoy utiliza Nueva renta.')
            if not state['total'] or cents(deposit.get())<state['minimum']:raise ValueError('Recibe al menos el 50% del total para confirmar la reservación.')
            selected={key:int(var.get()) for key,var in quantities.items() if int(var.get() or '0')}
            if not messagebox.askyesno('Confirmar reservación',f"Entrega: {start.get()}\nTotal: {money(state['total'])}\nAnticipo recibido: {deposit.get()} por {method.get()}\n¿Confirmar el apartado y registrar el anticipo?",parent=win):return
            key=self.service.create_reservation(state['client_id'],address.value.get(),start.get(),end.get(),selected,
                client_data=dict(name=name.get(),phone=phone.get()),invoice_required=invoice.get(),freight=freight.get(),extra_planks=planks.get(),address_data=address.parts(),
                initial_payment=dict(amount=deposit.get(),method=method.get(),reference=reference.get(),receipt_path=receipt.get() or None))
            win.destroy();self.refresh();self.navigate('Reservaciones');self.reservations_table.selection_set(str(key))
        ctk.CTkButton(body,text='Confirmar reservación y recibir anticipo',height=48,fg_color='#18865B',command=lambda:self.safe(save)).pack(fill='x',pady=14)
        win.reservation_fields=dict(name=name,phone=phone,start=start,end=end,quantities=quantities,deposit=deposit,method=method,invoice=invoice,address=address,save=save,total=total)
        total()

    def reservation_deposit_dialog(self):
        key=self.selected(self.reservations_table);summary=self.service.reservation_payment_summary(key)
        reservation=self.db.rows('SELECT * FROM reservations WHERE id=?',(key,))[0]
        if reservation['status']=='Entregada':self.payment_dialog(reservation['rental_id']);return
        if not self.ensure_cash_open():return
        win,body=self.dialog('Anticipo de reservación')
        ctk.CTkLabel(body,text=f"Reserva #{key:06d} · {reservation['client_name']}\nTotal: {money(summary['total_cents'])} · Recibido: {money(summary['paid_cents'])}\nMínimo para confirmar: {money(summary['minimum_cents'])}",wraplength=470).pack(pady=10)
        amount=self.entry(body,'Importe recibido',f"{max(0,summary['minimum_cents']-summary['paid_cents'])/100:.2f}")
        method=tk.StringVar(value='Transferencia' if reservation['vat_bp'] else 'Efectivo')
        ctk.CTkOptionMenu(body,values=['Transferencia'] if reservation['vat_bp'] else ['Efectivo','Transferencia','Tarjeta'],variable=method).pack(fill='x',pady=5)
        receipt=self.receipt_picker(body,method);reference=self.entry(body,'Referencia (opcional)')
        def save():
            self.service.record_reservation_payment(key,amount.get(),method.get(),reference=reference.get(),receipt_path=receipt.get() or None)
            win.destroy();self.refresh()
        ctk.CTkButton(body,text='Registrar anticipo',command=lambda:self.safe(save)).pack(fill='x',pady=10)

    def reservation_payment_history(self):
        key=self.selected(self.reservations_table)
        win,body=self.dialog('Pagos de la reservación')
        tree=self.table(body,('Pago','Fecha','Método','Importe','Estado'),height=7)
        rows=self.db.rows('SELECT * FROM financial_payments WHERE reservation_id=? ORDER BY paid_on,id',(key,))
        self.fill(tree,[(r['id'],(f"A{abs(r['id'])}",r['paid_on'],r['method'],money(r['amount_cents']),'Anulado' if r['cancelled_at'] else 'Recibido')) for r in rows])
        reason=self.entry(body,'Motivo para anular (solo si fue una captura incorrecta)')
        def cancel():
            self.service.cancel_payment(self.selected(tree),reason.get());win.destroy();self.refresh()
        ctk.CTkButton(body,text='Anular pago seleccionado',fg_color='#AF3029',command=lambda:self.safe(cancel)).pack(fill='x',pady=8)
        ctk.CTkButton(body,text='Ver comprobantes seleccionados',command=lambda:self.safe(lambda:self.receipt_documents_dialog(self.selected(tree)))).pack(fill='x',pady=6)
