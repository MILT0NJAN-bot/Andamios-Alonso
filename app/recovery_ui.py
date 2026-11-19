import json
import sqlite3
import queue
import threading
import time
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk
from .recovery import DraftStore,journal_backup


class RecoveryUI:
    def init_recovery(self):
        self.draft_store=DraftStore(self.db)
        self.recovery_error=''
        try:self.pending_draft=self.draft_store.load()
        except (ValueError,OSError) as exc:
            self.pending_draft={'error':str(exc)}
            self.recovery_error='No se pudo leer el borrador anterior. Se conservará hasta que decidas descartarlo.'
        self.draft_active=not bool(self.pending_draft)
        self.draft_baseline=self.rental_snapshot()
        self.recovery_banners=[]
        for name in ('Inicio','Nueva Renta'):
            page=self.tabs.tab(name);frame=ctk.CTkFrame(page,fg_color='#FFF0E5')
            text=ctk.CTkLabel(frame,text='',text_color='#203F78',wraplength=550,justify='left')
            text.pack(side='left',fill='x',expand=True,padx=12,pady=8)
            ctk.CTkButton(frame,text='Recuperar renta',width=125,command=lambda:self.safe(self.restore_rental_draft)).pack(side='right',padx=5)
            ctk.CTkButton(frame,text='Descartar',width=95,fg_color='#748195',command=lambda:self.safe(self.discard_rental_draft)).pack(side='right',padx=5)
            self.recovery_banners.append((page,frame,text))
        self.show_recovery_banners()
        self.backup_queue=queue.Queue();self.journal_busy=False
        self.journal_last=time.monotonic();self.journal_changes=self.db.conn.total_changes
        self.recovery_job=self.after(5000,self.recovery_tick)

    def rental_snapshot(self):
        return dict(version=1,client_id=self.client_id,name=self.rental_name.get(),phone=self.rental_phone.get(),
            email=self.rental_email.get(),
            address={key:var.get() for key,var in self.address_editor.fields.items()},
            departure=self.departure.get(),due=self.due.get(),cart={str(key):q for key,q in self.cart.items()},
            conditions=self.cart_conditions,freight=self.freight.get(),extra_planks=self.extra_planks.get(),
            invoice=self.invoice_required.get(),amount=self.initial_amount.get(),method=self.initial_method.get(),
            reference=self.initial_reference.get(),receipt=self.initial_receipt.get())

    def meaningful_draft(self,payload):
        # Comparar también cambios de fechas; no validar campos a medio escribir.
        return payload!=self.draft_baseline and bool(payload['name'].strip() or payload['phone'].strip() or payload['cart']
            or any(payload['address'].values()) or payload['invoice'] or payload['reference'] or payload['receipt']
            or payload['amount'] not in ('','0','0.00') or payload['freight'] not in ('','0','0.00')
            or payload['extra_planks'] not in ('','0') or payload['departure']!=self.draft_baseline['departure'] or payload['due']!=self.draft_baseline['due'])

    def save_rental_draft(self):
        if not getattr(self,'draft_active',False) or self.db.conn.in_transaction:return
        payload=self.rental_snapshot()
        if self.meaningful_draft(payload):self.draft_store.save(payload)
        else:self.draft_store.clear()

    def show_recovery_banners(self):
        for page,frame,text in self.recovery_banners:
            if self.pending_draft:
                children=[w for w in page.winfo_children() if w is not frame]
                frame.pack(fill='x',pady=(0,8),before=children[0])
                text.configure(text=self.recovery_error or 'Hay una captura de renta pendiente de recuperar.\nGuardada: '+self.pending_draft['saved_at'])
            else:frame.pack_forget()

    def discard_rental_draft(self):
        if not messagebox.askyesno('Descartar borrador','¿Descartar únicamente el borrador anterior? Las rentas registradas se conservan.',parent=self):return
        self.draft_store.clear();self.pending_draft=None;self.draft_active=True
        self.show_recovery_banners();self.save_rental_draft()

    def restore_rental_draft(self):
        if not self.pending_draft or 'payload' not in self.pending_draft:raise ValueError(self.recovery_error or 'No hay borrador recuperable.')
        if self.rental_snapshot()!=self.draft_baseline and not messagebox.askyesno('Recuperar borrador','Se reemplazará la captura que tienes ahora en el formulario. ¿Recuperar el borrador anterior?',parent=self):return
        payload=self.pending_draft['payload']
        if payload.get('version')!=1:raise ValueError('Este borrador tiene un formato no reconocido. Se conserva sin modificar.')
        self.reset_client()
        client=self.db.rows('SELECT * FROM clients WHERE id=?',(payload.get('client_id'),))
        if client and client[0]['name']==payload.get('name') and client[0]['phone']==payload.get('phone'):
            self.select_client(client[0]['id'])
        self._loading_client=True
        try:
            self.rental_name.set(payload.get('name',''));self.rental_phone.set(payload.get('phone',''))
            self.rental_email.set(payload.get('email',self.rental_email.get()))
        finally:self._loading_client=False
        self.address_editor.load(payload.get('address',{}))
        self.departure.set(payload['departure']);self.due.set(payload['due'])
        missing=sum(int(key) not in self.items for key in payload.get('cart',{}))
        self.cart={int(key):int(q) for key,q in payload.get('cart',{}).items() if int(key) in self.items and int(q)>0}
        self.cart_conditions={int(key):value for key,value in payload.get('conditions',{}).items() if int(key) in self.cart}
        self.freight.set(payload.get('freight','0'));self.extra_planks.set(payload.get('extra_planks','0'))
        self.initial_amount.set(payload.get('amount','0'));self.initial_reference.set(payload.get('reference',''))
        self.invoice_required.set(bool(payload.get('invoice')))
        self.initial_method.set('Transferencia' if self.invoice_required.get() else payload.get('method','Efectivo'))
        receipt=payload.get('receipt','')
        self.initial_receipt.set(receipt if receipt and Path(receipt).is_file() else '')
        self.pending_draft=None;self.draft_active=True;self.show_recovery_banners()
        self.update_total();self.render_products();self.navigate('Nueva Renta')
        self.alert.configure(text='Borrador recuperado. Revisa fechas, disponibilidad, precios y comprobante antes de guardar. No se registró ninguna renta ni pago automáticamente.')
        if missing:self.alert.configure(text=f'Borrador recuperado: se omitieron {missing} artículo(s) eliminados del catálogo. Revisa los equipos y el total antes de guardar.')

    def complete_rental_draft(self):
        if not hasattr(self,'draft_store'):return
        self.draft_store.clear();self.pending_draft=None;self.draft_active=True
        self.show_recovery_banners()
        self.draft_baseline=self.rental_snapshot()

    def recovery_tick(self):
        if self._closing:return
        try:
            self.save_rental_draft()
            while not self.backup_queue.empty():
                path,error,changes=self.backup_queue.get_nowait()
                self.journal_busy=False;self.journal_last=time.monotonic()
                if error:
                    self.recovery_error='No se pudo crear el respaldo de jornada: '+error
                    self.journal_last-=3300  # Reintentar en cinco minutos.
                else:
                    self.journal_changes=changes;self.recovery_error=''
                self.refresh_backups()
            if not self.journal_busy and time.monotonic()-self.journal_last>=3600 and self.db.conn.total_changes!=self.journal_changes:
                changes=self.db.conn.total_changes;self.journal_busy=True
                def worker():
                    try:self.backup_queue.put((journal_backup(self.db.path),'',changes))
                    except Exception as exc:self.backup_queue.put((None,str(exc),changes))
                threading.Thread(target=worker,daemon=True).start()
        except (ValueError,OSError,sqlite3.Error) as exc:
            self.recovery_error='No se pudo guardar la captura pendiente: '+str(exc)
            if hasattr(self,'backup_status'):self.backup_status.configure(text=self.recovery_error,text_color='#AF3029')
        finally:self.recovery_job=self.after(5000,self.recovery_tick)
