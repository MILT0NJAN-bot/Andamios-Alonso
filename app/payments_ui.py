import tkinter as tk
from datetime import date
from tkinter import messagebox
import customtkinter as ctk
from .service import money


class PaymentsUI:
    def make_payments(self):
        page=self.tabs.tab('Pagos y saldos')
        self.heading(page,'Pagos y saldos','Anticipos, abonos y liquidaciones · Incluye rentas activas y devueltas con saldo pendiente.')
        self.payment_filter=self.entry(page,'Buscar por folio, nombre o teléfono')
        self.only_debt=tk.BooleanVar(value=False)
        ctk.CTkCheckBox(page,text='Mostrar solo rentas con saldo pendiente',variable=self.only_debt,
            command=self.refresh_payments).pack(anchor='w',pady=8)
        self.payment_totals=ctk.CTkLabel(page,text='',text_color='#203F78',font=ctk.CTkFont(size=17,weight='bold'),wraplength=850)
        self.payment_totals.pack(anchor='w',pady=8)
        self.payments_table=self.table(page,('Folio','Cliente','Teléfono','Total','Pagado','Pendiente','A favor','Estado de pago'),height=10)
        self.payment_filter.trace_add('write',lambda *_:self.refresh_payments())
        ctk.CTkButton(page,text='Ver pagos / registrar abono',height=44,fg_color='#18865B',
            command=lambda:self.safe(lambda:self.payment_dialog(self.selected(self.payments_table)))).pack(anchor='w',pady=12)
        self.payments_table.bind('<Double-1>',lambda event:self.safe(lambda:self.payment_dialog(int(self.payments_table.identify_row(event.y))))
            if self.payments_table.identify_row(event.y) else None)

    def refresh_payments(self):
        if not hasattr(self,'payments_table'):
            return
        term=self.payment_filter.get().casefold().strip()
        rows=[];paid=pending=credit=0
        for rental in self.db.rows('SELECT * FROM rentals ORDER BY id DESC'):
            if term not in f"{rental['id']:06d} {rental['client_name']} {rental['client_phone']}".casefold():
                continue
            summary=self.service.payment_summary(rental['id'])
            if self.only_debt.get() and not summary['pending_cents']:
                continue
            paid+=summary['paid_cents'];pending+=summary['pending_cents'];credit+=summary['credit_cents']
            rows.append((rental['id'],(f"{rental['id']:06d}",rental['client_name'],rental['client_phone'],money(summary['total_cents']),
                money(summary['paid_cents']),money(summary['pending_cents']),money(summary['credit_cents']),summary['status'])))
        self.fill(self.payments_table,rows)
        self.payment_totals.configure(text=f'Mostrando {len(rows)} rentas · Pagado: {money(paid)} · Pendiente: {money(pending)} · A favor: {money(credit)} MXN')

    def payment_dialog(self,key):
        summary=self.service.payment_summary(key)
        rental=self.db.rows('SELECT * FROM rentals WHERE id=?',(key,))[0]
        win,body=self.dialog(f'Pagos · Renta #{key:06d}')
        win.geometry('1000x820')
        ctk.CTkLabel(body,text=f"Renta #{key:06d} · {rental['client_name']}",font=ctk.CTkFont(size=22,weight='bold'),text_color='#203F78').pack(anchor='w')
        ctk.CTkLabel(body,text=f"Total: {money(summary['total_cents'])}   |   Pagado: {money(summary['paid_cents'])}\n"
            f"Saldo pendiente: {money(summary['pending_cents'])}   |   Saldo a favor: {money(summary['credit_cents'])}   |   {summary['status']}",
            justify='left',font=ctk.CTkFont(size=17,weight='bold'),text_color='#203F78').pack(anchor='w',pady=14)
        if summary['credit_cents']:
            ctk.CTkLabel(body,text='Hay un saldo a favor por ajuste de tarifa. No se registra una devolución de dinero automáticamente.',text_color='#9D4310').pack(anchor='w')
        left,right=self.pair(body)
        amount=self.entry(left,'Importe recibido · MXN')
        paid_on=self.date_field(right,'Fecha del pago',date.today().isoformat())
        left,right=self.pair(body)
        ctk.CTkLabel(left,text='Tipo de pago').pack(anchor='w')
        kind=tk.StringVar(value='Anticipo' if not summary['paid_cents'] else 'Abono')
        ctk.CTkOptionMenu(left,values=['Anticipo','Abono','Liquidación'],variable=kind,height=38).pack(fill='x',pady=(0,10))
        ctk.CTkLabel(right,text='Método de pago').pack(anchor='w')
        method=tk.StringVar(value='Efectivo')
        ctk.CTkOptionMenu(right,values=['Efectivo','Transferencia','Tarjeta'],variable=method,height=38).pack(fill='x',pady=(0,10))
        reference=self.entry(body,'Referencia u observación (opcional)')
        buttons=ctk.CTkFrame(body,fg_color='transparent');buttons.pack(fill='x',pady=8)
        def reopen():
            win.destroy()
            self.refresh()
            self.payment_dialog(key)
        def save():
            if not messagebox.askyesno('Confirmar pago',f'¿Registrar {amount.get()} MXN por {method.get()} en la renta #{key:06d}?',parent=win):
                return
            self.service.record_payment(key,amount.get(),method.get(),paid_on.get(),reference.get(),kind.get())
            reopen()
        ctk.CTkButton(buttons,text='Registrar pago',height=42,fg_color='#18865B',state='normal' if summary['pending_cents'] else 'disabled',
            command=lambda:self.safe(save)).pack(side='left',padx=(0,10))
        def liquidate():
            amount.set(f"{summary['pending_cents']/100:.2f}")
            kind.set('Liquidación')
        ctk.CTkButton(buttons,text='Completar importe para liquidar',height=42,state='normal' if summary['pending_cents'] else 'disabled',
            command=liquidate).pack(side='left')
        ctk.CTkLabel(body,text='Historial de pagos',font=ctk.CTkFont(size=17,weight='bold')).pack(anchor='w',pady=(15,0))
        ledger=self.table(body,('ID','Fecha','Tipo','Método','Importe','Estado','Referencia / motivo'),height=5)
        payments=self.db.rows('SELECT * FROM payments WHERE rental_id=? ORDER BY id DESC',(key,))
        self.fill(ledger,[(p['id'],(p['id'],p['paid_on'],p['kind'],p['method'],money(p['amount_cents']),
            'Anulado' if p['cancelled_at'] else 'Registrado',p['cancellation_reason'] if p['cancelled_at'] else p['reference'])) for p in payments])
        def cancel():
            payment_id=self.selected(ledger)
            if self.db.rows('SELECT cancelled_at FROM payments WHERE id=?',(payment_id,))[0][0]:
                raise ValueError('Este pago ya fue anulado.')
            popup,inner=self.dialog('Anular pago registrado por error')
            reason=self.entry(inner,'Motivo de la anulación *')
            ctk.CTkLabel(inner,text='El registro se conserva y deja de descontarse del saldo.\nEsto corrige la captura; no registra una salida de dinero.',justify='left').pack(anchor='w',pady=10)
            def apply():
                self.service.cancel_payment(payment_id,reason.get())
                popup.destroy()
                reopen()
            ctk.CTkButton(inner,text='Confirmar anulación',fg_color='#B52B27',command=lambda:self.safe(apply)).pack(fill='x',pady=10)
        ctk.CTkButton(body,text='Anular pago seleccionado por error',fg_color='#B52B27',height=38,command=lambda:self.safe(cancel)).pack(anchor='w',pady=8)
