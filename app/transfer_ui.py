import tkinter as tk
from tkinter import filedialog,messagebox
from datetime import date
from pathlib import Path
from types import SimpleNamespace
import customtkinter as ctk
from .client_files import DOCUMENT_EXTENSIONS
from .service import money


class TransferUI:
    def receipt_picker(self,parent,method):
        frame=ctk.CTkFrame(parent,fg_color='#EDF3FC')
        path=tk.StringVar(value='')
        label=ctk.CTkLabel(frame,text='Sin archivo: pendiente de comprobante',wraplength=600)
        path.trace_add('write',lambda *_:label.configure(text=Path(path.get()).name if path.get() else 'Sin archivo: pendiente de comprobante'))
        label.pack(fill='x',padx=8,pady=5)
        def choose():
            value=filedialog.askopenfilename(parent=parent.winfo_toplevel(),title='Comprobante de transferencia',
                filetypes=[('PDF o imagen',' '.join('*'+s for s in DOCUMENT_EXTENSIONS))])
            if value:path.set(value);label.configure(text=Path(value).name)
        ctk.CTkButton(frame,text='Adjuntar comprobante de transferencia',command=choose).pack(padx=8,pady=5)
        def clear():path.set('');label.configure(text='Sin archivo: pendiente de comprobante')
        ctk.CTkButton(frame,text='Quitar selección',fg_color='#748195',command=clear).pack(pady=(0,6))
        def update(*_):
            if method.get()=='Transferencia':frame.pack(fill='x',pady=8)
            else:frame.pack_forget();clear()
        method.trace_add('write',update);update()
        return path

    def make_transfer_receipts(self):
        page=self.tabs.tab('Comprobantes')
        self.heading(page,'Transferencias y comprobantes','Con factura: solo transferencia. Los comprobantes también se guardan en el expediente de cada cliente.')
        self.build_transfer_view(page)

    def build_transfer_view(self,parent,client_id=None):
        view=SimpleNamespace(parent=parent,client_id=client_id)
        controls=ctk.CTkFrame(parent,fg_color='transparent');controls.pack(fill='x')
        left,right=self.pair(controls)
        view.start=self.date_field(left,'Pagos desde (AAAA-MM-DD)',date.today().replace(day=1).isoformat())
        view.end=self.date_field(right,'Pagos hasta',date.today().isoformat())
        view.only_invoice=tk.BooleanVar(value=client_id is None)
        if client_id is None:
            ctk.CTkCheckBox(parent,text='Solo rentas que requieren factura (paquete para contador)',variable=view.only_invoice).pack(anchor='w',pady=8)
        view.status=ctk.CTkLabel(parent,text='',text_color='#203F78',wraplength=850);view.status.pack(fill='x',pady=6)
        view.table=self.table(parent,('Pago','Fecha','Renta','Cliente','Importe','Factura','Comprobantes','Estado'),height=8)
        def refresh():
            rows=self.service.transfer_payments(view.start.get(),view.end.get(),view.only_invoice.get(),view.client_id)
            self.fill(view.table,[(r['id'],(f"A{abs(r['id'])}" if r['id']<0 else r['id'],r['paid_on'],f"{r['rental_id']:06d}" if r['rental_id'] else f"Reserva {r['reservation_id']:06d}",r['client_name'],money(r['amount_cents']),
                'Sí' if r['vat_bp'] else 'No',f"{r['receipt_count']} archivo(s)" if r['receipt_count'] else 'Pendiente','Anulado' if r['cancelled_at'] else 'Vigente')) for r in rows])
            pending=sum(not r['receipt_count'] and not r['cancelled_at'] for r in rows)
            view.status.configure(text=f'{len(rows)} transferencia(s) · {pending} pago(s) pendiente(s) de comprobante. Ajusta las fechas para consultar periodos anteriores.')
        view.refresh=refresh
        def attach():
            key=self.selected(view.table)
            paths=filedialog.askopenfilenames(parent=parent.winfo_toplevel(),title='Adjuntar comprobantes al pago seleccionado',
                filetypes=[('PDF o imagen',' '.join('*'+s for s in DOCUMENT_EXTENSIONS))])
            for path in paths:self.service.attach_transfer_receipt(key,path)
            if paths:
                self.refresh_receipt_views()
                for w in self.winfo_children():
                    if hasattr(w,'refresh_documents'):w.refresh_documents()
        def documents():
            self.receipt_documents_dialog(self.selected(view.table))
        def export():
            if client_id is not None:raise ValueError('Exporta el expediente del cliente desde su ficha.')
            path=filedialog.asksaveasfilename(parent=parent.winfo_toplevel(),title='Comprobantes con factura para el contador',defaultextension='.zip',
                initialfile=f'Comprobantes_facturacion_{view.start.get()}_{view.end.get()}.zip',filetypes=[('ZIP','*.zip')])
            if path:
                result=self.service.export_accountant_receipts(view.start.get(),view.end.get(),path)
                view.status.configure(text=f"ZIP guardado: {result['documents']} archivo(s), {result['pending']} pago(s) pendiente(s) de comprobante. {path}")
        bar=ctk.CTkFrame(parent,fg_color='transparent');bar.pack(fill='x',pady=10)
        actions=[('Consultar',refresh),('Adjuntar al pago',attach),('Ver / guardar comprobantes',documents)]
        if client_id is None:actions.append(('ZIP para contador',export))
        for label,action in actions:
            ctk.CTkButton(bar,text=label,height=40,width=150,command=lambda f=action:self.safe(f)).pack(side='left',padx=4)
        if not hasattr(self,'receipt_views'):self.receipt_views=[]
        self.receipt_views.append(view);refresh()

    def refresh_receipt_views(self):
        self.receipt_views=[v for v in getattr(self,'receipt_views',[]) if v.parent.winfo_exists()]
        for view in self.receipt_views:self.safe(view.refresh)

    def transfer_receipts_dialog(self,client_id):
        win,body=self.dialog('Comprobantes de transferencia del cliente')
        win.geometry('1100x750')
        self.build_transfer_view(body,client_id)

    def receipt_documents_dialog(self,payment_id):
        rows=self.service.transfer_documents(payment_id)
        if not rows:raise ValueError('Este pago todavía no tiene comprobantes. Usa Adjuntar al pago.')
        win,body=self.dialog(f'Comprobantes · Pago {payment_id}')
        tree=self.table(body,('Archivo','Tamaño'),height=6)
        self.fill(tree,[(r['id'],(r['filename'],f"{r['size_bytes']/1024:,.0f} KB")) for r in rows])
        def save():
            key=self.selected(tree);row=next(r for r in rows if r['id']==key)
            path=filedialog.asksaveasfilename(parent=win,initialfile=row['filename'],defaultextension=Path(row['filename']).suffix)
            if path:self.service.export_client_document(row['client_id'],key,path)
        ctk.CTkButton(body,text='Guardar copia del comprobante',command=lambda:self.safe(save)).pack(fill='x',pady=10)
