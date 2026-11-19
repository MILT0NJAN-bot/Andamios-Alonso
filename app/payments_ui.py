import tkinter as tk
from datetime import date
from tkinter import messagebox
import customtkinter as ctk
from .service import money


class PaymentsUI:
    def make_payments(self):
        page=self.tabs.tab('Pagos y saldos')
        self.heading(page,'Pagos y saldos','Consulta cuánto se ha pagado y cuánto falta por cobrar de cada renta.')
        self.payment_filter=self.entry(page,'Buscar por folio, nombre o teléfono')
        self.only_debt=tk.BooleanVar(value=False)
        ctk.CTkCheckBox(page,text='Mostrar solo rentas con saldo pendiente',variable=self.only_debt,
            command=self.refresh_payments).pack(anchor='w',pady=8)
        self.payment_totals=ctk.CTkLabel(page,text='',text_color='#203F78',font=ctk.CTkFont(size=17,weight='bold'),wraplength=850)
        self.payment_totals.pack(anchor='w',pady=8)
        self.payments_table=self.table(page,('Folio','Cliente','Teléfono','Total','Pagado','Pendiente','Estado de pago'),height=10)
        self.payment_filter.trace_add('write',lambda *_:self.refresh_payments())
        ctk.CTkButton(page,text='Cobrar / ver pagos',height=44,fg_color='#18865B',
            command=lambda:self.safe(lambda:self.payment_dialog(self.selected(self.payments_table)))).pack(anchor='w',pady=12)
        self.payments_table.bind('<Double-1>',lambda event:self.safe(lambda:self.payment_dialog(int(self.payments_table.identify_row(event.y))))
            if self.payments_table.identify_row(event.y) else None)

    def refresh_payments(self):
        if not hasattr(self,'payments_table'):
            return
        term=self.payment_filter.get().casefold().strip()
        rows=[];paid=pending=0
        for rental in self.db.rows('SELECT * FROM rentals ORDER BY id DESC'):
            if term not in f"{rental['id']:06d} {rental['client_name']} {rental['client_phone']}".casefold():
                continue
            summary=self.service.payment_summary(rental['id'])
            if self.only_debt.get() and not summary['pending_cents']:
                continue
            paid+=summary['paid_cents'];pending+=summary['pending_cents']
            rows.append((rental['id'],(f"{rental['id']:06d}",rental['client_name'],rental['client_phone'],money(summary['total_cents']),
                money(summary['paid_cents']),money(summary['pending_cents']),summary['status'])))
        self.fill(self.payments_table,rows)
        self.payment_totals.configure(text=f'Mostrando {len(rows)} rentas · Pagado: {money(paid)} · Pendiente: {money(pending)} MXN')

    def payment_dialog(self,key):
        summary=self.service.payment_summary(key)
        rental=self.db.rows('SELECT * FROM rentals WHERE id=?',(key,))[0]
        win,body=self.dialog(f'Pagos · Renta #{key:06d}')
        win.geometry('1000x820')
        ctk.CTkLabel(body,text=f"Renta #{key:06d} · {rental['client_name']}",font=ctk.CTkFont(size=22,weight='bold'),text_color='#203F78').pack(anchor='w')
        ctk.CTkLabel(body,text=f"Total: {money(summary['total_cents'])}   |   Pagado: {money(summary['paid_cents'])}\n"
            f"Saldo pendiente: {money(summary['pending_cents'])}   |   {summary['status']}",
            justify='left',font=ctk.CTkFont(size=17,weight='bold'),text_color='#203F78').pack(anchor='w',pady=14)
        form=ctk.CTkFrame(body,fg_color='transparent')
        if summary['pending_cents']:form.pack(fill='x')
        left,right=self.pair(form)
        amount=self.entry(left,'Importe recibido · MXN')
        ctk.CTkLabel(right,text='Método de pago').pack(anchor='w')
        method=tk.StringVar(value='Transferencia' if rental['vat_bp'] else 'Efectivo')
        ctk.CTkOptionMenu(right,values=['Transferencia'] if rental['vat_bp'] else ['Efectivo','Transferencia','Tarjeta'],variable=method,height=38).pack(fill='x',pady=(0,10))
        if rental['vat_bp']:ctk.CTkLabel(form,text='Factura solicitada: únicamente pagos por transferencia.',text_color='#203F78').pack(anchor='w')
        receipt=self.receipt_picker(form,method)
        extras=ctk.CTkFrame(form,fg_color='transparent')
        paid_on=self.date_field(extras,'Fecha del pago',date.today().isoformat())
        reference=self.entry(extras,'Referencia (opcional)')
        show_extras=tk.BooleanVar(value=False)
        extras_toggle=ctk.CTkCheckBox(form,text='Fecha y referencia',variable=show_extras,
            command=lambda:extras.pack(fill='x',after=extras_toggle,pady=6) if show_extras.get() else extras.pack_forget())
        extras_toggle.pack(anchor='w',pady=8)
        buttons=ctk.CTkFrame(form,fg_color='transparent');buttons.pack(fill='x',pady=8)
        def reopen():
            win.destroy()
            self.refresh()
            self.payment_dialog(key)
        def save():
            if paid_on.get()==date.today().isoformat() and not self.ensure_cash_open():
                return
            from .service import cents
            received=cents(amount.get())
            if not 0<received<=summary['pending_cents']:
                raise ValueError(f"El importe debe ser mayor a cero y no superar {money(summary['pending_cents'])}.")
            if not messagebox.askyesno('Confirmar pago',f"Recibido: {money(received)} por {method.get()}\nQuedará pendiente: {money(summary['pending_cents']-received)}\n¿Guardar el pago de la renta #{key:06d}?",parent=win):
                return
            self.service.record_payment(key,amount.get(),method.get(),paid_on.get(),reference.get(),receipt_path=receipt.get() or None)
            reopen()
        ctk.CTkButton(buttons,text='Registrar pago',height=42,fg_color='#18865B',state='normal' if summary['pending_cents'] else 'disabled',
            command=lambda:self.safe(save)).pack(side='left',padx=(0,10))
        def liquidate():
            amount.set(f"{summary['pending_cents']/100:.2f}")
            self.safe(save)
        ctk.CTkButton(buttons,text='Cobrar todo lo pendiente',height=42,state='normal' if summary['pending_cents'] else 'disabled',
            command=liquidate).pack(side='left')
        history=ctk.CTkFrame(body,fg_color='transparent')
        def toggle_history():
            if history.winfo_manager():history.pack_forget();history_button.configure(text='Ver historial / corregir pagos')
            else:history.pack(fill='both',expand=True,pady=8);history_button.configure(text='Ocultar historial')
        history_button=ctk.CTkButton(body,text='Ver historial / corregir pagos',fg_color='#203F78',command=toggle_history)
        history_button.pack(anchor='w',pady=12)
        ledger=self.table(history,('ID','Fecha','Método','Importe','Comprobante','Estado','Referencia / motivo'),height=5)
        payments=self.db.rows('''SELECT p.*,CASE WHEN p.id>0 THEN (SELECT COUNT(*) FROM transfer_receipts t WHERE t.payment_id=p.id)
            ELSE (SELECT COUNT(*) FROM reservation_payment_receipts t WHERE t.payment_id=-p.id) END AS receipt_count
            FROM financial_payments p WHERE rental_id=? ORDER BY paid_on DESC,id DESC''',(key,))
        self.fill(ledger,[(p['id'],(f"A{abs(p['id'])}" if p['id']<0 else p['id'],p['paid_on'],p['method'],money(p['amount_cents']),
            (f"{p['receipt_count']} archivo(s)" if p['receipt_count'] else 'Pendiente') if p['method']=='Transferencia' else 'No aplica',
            'Anulado' if p['cancelled_at'] else 'Registrado',p['cancellation_reason'] if p['cancelled_at'] else p['reference'])) for p in payments])
        def attach_receipt():
            payment_id=self.selected(ledger)
            from tkinter import filedialog
            from .client_files import DOCUMENT_EXTENSIONS
            path=filedialog.askopenfilename(parent=win,title='Comprobante del pago seleccionado',filetypes=[('PDF o imagen',' '.join('*'+s for s in DOCUMENT_EXTENSIONS))])
            if path:
                self.service.attach_transfer_receipt(payment_id,path)
                self.refresh_receipt_views()
                reopen()
        ctk.CTkButton(history,text='Adjuntar comprobante al pago seleccionado',height=38,command=lambda:self.safe(attach_receipt)).pack(anchor='w',pady=6)
        ctk.CTkButton(history,text='Ver comprobantes del pago seleccionado',height=38,command=lambda:self.safe(lambda:self.receipt_documents_dialog(self.selected(ledger)))).pack(anchor='w',pady=6)
        def cancel():
            payment_id=self.selected(ledger)
            if self.db.rows('SELECT cancelled_at FROM financial_payments WHERE id=?',(payment_id,))[0][0]:
                raise ValueError('Este pago ya fue anulado.')
            popup,inner=self.dialog('Anular pago registrado por error')
            reason=self.entry(inner,'Motivo de la anulación *')
            ctk.CTkLabel(inner,text='El registro se conserva y deja de descontarse del saldo.\nEsto corrige la captura; no registra una salida de dinero.',justify='left').pack(anchor='w',pady=10)
            def apply():
                self.service.cancel_payment(payment_id,reason.get())
                popup.destroy()
                reopen()
            ctk.CTkButton(inner,text='Confirmar anulación',fg_color='#B52B27',command=lambda:self.safe(apply)).pack(fill='x',pady=10)
        ctk.CTkButton(history,text='Anular pago seleccionado por error',fg_color='#B52B27',height=38,command=lambda:self.safe(cancel)).pack(anchor='w',pady=8)
