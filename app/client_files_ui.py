"""Captura y exportación del expediente de un cliente."""
import sqlite3
import tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from .client_files import BILLING_FIELDS, DOCUMENT_CATEGORIES, DOCUMENT_EXTENSIONS, safe_filename


class ClientBillingDialog(ctk.CTkToplevel):
    def __init__(self, parent, client_id):
        self.service = parent.service
        self.client_id = client_id
        client = self.service._billing_client(client_id)
        self.saved_details = self.service.billing_details(client_id)
        super().__init__(parent)
        self.title(f'Expediente para facturación · {client["name"]}')
        width = min(880, max(760, self.winfo_screenwidth() - 60))
        height = min(720, max(600, self.winfo_screenheight() - 100))
        self.geometry(f'{width}x{height}+{max(0, (self.winfo_screenwidth() - width) // 2)}'
                      f'+{max(0, (self.winfo_screenheight() - height) // 2 - 20)}')
        self.minsize(760, 600)
        self.transient(parent)
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.close)
        ctk.CTkLabel(self, text=client['name'], font=ctk.CTkFont(size=23, weight='bold'),
                     wraplength=700, anchor='w').pack(fill='x', padx=22, pady=(18, 0))
        ctk.CTkLabel(self, text=f'Cliente #{client_id} · Tel. {client["phone"]}',
                     text_color='#748195').pack(anchor='w', padx=22)

        footer = ctk.CTkFrame(self, fg_color='transparent')
        footer.pack(side='bottom', fill='x', padx=22, pady=(8, 18))
        ctk.CTkButton(footer, text='Cerrar', width=90, command=self.close).pack(side='right', padx=(10, 0))
        ctk.CTkButton(footer, text='Exportar expediente ZIP', height=40, fg_color='#18865B',
                     command=lambda: self.run(self.export_zip)).pack(side='right')
        self.status = ctk.CTkLabel(self, text='', wraplength=700, justify='left', anchor='w')
        self.status.pack(side='bottom', fill='x', padx=22)
        ctk.CTkLabel(self, text='El ZIP incluye todos los documentos y los datos de esta ficha. '
                     'Guárdalo para enviarlo a la contadora.', wraplength=700, justify='left',
                     text_color='#748195').pack(side='bottom', fill='x', padx=22)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(fill='both', expand=True, padx=16, pady=8)
        self.make_documents(self.tabs.add('Documentos'))
        self.make_details(self.tabs.add('Datos para factura'))
        self.refresh_documents()

    def run(self, action):
        try:
            action()
        except (ValueError, OSError, sqlite3.Error) as exc:
            messagebox.showerror('No se pudo completar', str(exc), parent=self)

    def make_documents(self, page):
        ctk.CTkLabel(page, text='Agrega los archivos que entregue el cliente. Se guardan al adjuntarlos.',
                     wraplength=700, justify='left').pack(anchor='w', padx=8, pady=(6, 0))
        ctk.CTkLabel(page, text='PDF o imágenes JPG, PNG, WEBP, HEIC, TIFF y BMP · Máximo 20 MB por archivo.',
                     wraplength=700, justify='left', text_color='#748195').pack(anchor='w', padx=8)
        bar = ctk.CTkFrame(page, fg_color='transparent')
        bar.pack(fill='x', padx=8, pady=10)
        self.category = tk.StringVar(value=DOCUMENT_CATEGORIES[0])
        ctk.CTkOptionMenu(bar, values=list(DOCUMENT_CATEGORIES), variable=self.category,
                          width=300).pack(side='left')
        ctk.CTkButton(bar, text='Agregar archivos…', command=lambda: self.run(self.add_documents)).pack(side='left', padx=10)

        actions = ctk.CTkFrame(page, fg_color='transparent')
        actions.pack(side='bottom', fill='x', padx=8, pady=8)
        self.copy_button = ctk.CTkButton(actions, text='Guardar copia…', command=lambda: self.run(self.save_copy))
        self.copy_button.pack(side='left')
        self.delete_button = ctk.CTkButton(actions, text='Quitar documento', fg_color='#9B3535',
                                           command=lambda: self.run(self.delete_document))
        self.delete_button.pack(side='left', padx=10)
        self.document_count = ctk.CTkLabel(page, text='', anchor='w', wraplength=700)
        self.document_count.pack(side='bottom', fill='x', padx=8)
        table_frame = ctk.CTkFrame(page)
        table_frame.pack(fill='both', expand=True, padx=8, pady=6)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.documents = ttk.Treeview(table_frame, columns=('type', 'name', 'size', 'date'),
                                      show='headings', selectmode='browse', height=5)
        for column, label, width in [('type', 'Documento', 235), ('name', 'Archivo', 230),
                                      ('size', 'Tamaño', 85), ('date', 'Agregado', 145)]:
            self.documents.heading(column, text=label)
            self.documents.column(column, width=width, minwidth=70)
        vertical = ttk.Scrollbar(table_frame, orient='vertical', command=self.documents.yview)
        horizontal = ttk.Scrollbar(table_frame, orient='horizontal', command=self.documents.xview)
        self.documents.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.documents.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        self.documents.bind('<<TreeviewSelect>>', lambda _: self.update_selection())

    def make_details(self, page):
        ctk.CTkLabel(page, text='Datos opcionales: captura lo que el cliente te haya proporcionado. '
                     'Puedes guardar y exportar aunque falte información.', wraplength=700,
                     justify='left').pack(anchor='w', padx=8, pady=8)
        ctk.CTkButton(page, text='Guardar datos para factura', height=38,
                     command=lambda: self.run(self.save_details)).pack(side='bottom', fill='x', padx=8, pady=8)
        body = ctk.CTkScrollableFrame(page, fg_color='transparent')
        body.pack(fill='both', expand=True)
        body.columnconfigure((0, 1), weight=1)
        self.fields = {}
        for index, (field, label) in enumerate(BILLING_FIELDS.items()):
            if field == 'notes':
                continue
            cell = ctk.CTkFrame(body, fg_color='transparent')
            cell.grid(row=index // 2, column=index % 2, sticky='ew', padx=8, pady=5)
            ctk.CTkLabel(cell, text=label, anchor='w').pack(fill='x')
            value = tk.StringVar(value=self.saved_details[field])
            self.fields[field] = value
            ctk.CTkEntry(cell, textvariable=value, height=36).pack(fill='x')
        ctk.CTkLabel(body, text=BILLING_FIELDS['notes'], anchor='w').grid(row=4, column=0, columnspan=2, sticky='ew', padx=8)
        self.notes = ctk.CTkTextbox(body, height=85)
        self.notes.grid(row=5, column=0, columnspan=2, sticky='ew', padx=8, pady=(0, 8))
        self.notes.insert('1.0', self.saved_details['notes'])

    def details(self):
        return {**{name: value.get().strip() for name, value in self.fields.items()},
                'notes': self.notes.get('1.0', 'end-1c').strip()}

    def save_details(self):
        self.saved_details = self.service.save_billing_details(self.client_id, self.details())
        for name, value in self.fields.items():
            value.set(self.saved_details[name])
        self.status.configure(text='Datos para factura guardados en este cliente.')

    def refresh_documents(self):
        rows = self.service.client_documents(self.client_id)
        self.documents.delete(*self.documents.get_children())
        for row in rows:
            size = f'{row["size_bytes"] / 1024:,.0f} KB' if row['size_bytes'] >= 1024 else f'{row["size_bytes"]} B'
            added = datetime.fromisoformat(row['created_at']).replace(tzinfo=timezone.utc).astimezone()
            self.documents.insert('', 'end', iid=str(row['id']), values=(row['category'], row['filename'], size, added.strftime('%d/%m/%Y %H:%M')))
        self.document_count.configure(text=f'{len(rows)} documento(s) guardado(s).' if rows else
                                      'Todavía no hay documentos. Elige el tipo y pulsa Agregar archivos.')
        self.update_selection()

    def update_selection(self):
        state = 'normal' if self.documents.selection() else 'disabled'
        self.copy_button.configure(state=state)
        self.delete_button.configure(state=state)

    def selected_document(self):
        selected = self.documents.selection()
        if not selected:
            raise ValueError('Selecciona un documento de la lista.')
        return int(selected[0])

    def add_documents(self):
        paths = filedialog.askopenfilenames(parent=self, title='Agregar documentos del cliente',
            filetypes=[('PDF e imágenes', ' '.join('*' + suffix for suffix in DOCUMENT_EXTENSIONS))])
        if not paths:
            return
        result = self.service.add_client_documents(self.client_id, self.category.get(), paths)
        self.refresh_documents()
        self.status.configure(text=f'{result["added"]} archivo(s) guardado(s). '
                              f'{result["skipped"]} repetido(s) omitido(s) en este tipo de documento.')

    def save_copy(self):
        document_id = self.selected_document()
        row = next(row for row in self.service.client_documents(self.client_id) if row['id'] == document_id)
        original = Path(row['filename'])
        path = filedialog.asksaveasfilename(parent=self, title='Guardar copia del documento',
            initialfile=f'{document_id}_{safe_filename(original.stem)}{original.suffix.lower()}',
            defaultextension=original.suffix.lower(), filetypes=[('Documento', '*' + original.suffix.lower())])
        if path:
            self.service.export_client_document(self.client_id, document_id, path)
            self.status.configure(text=f'Copia guardada: {path}')

    def delete_document(self):
        document_id = self.selected_document()
        name = self.documents.item(str(document_id), 'values')[1]
        if messagebox.askyesno('Quitar documento', f'¿Quitar «{name}» del expediente de este cliente?\n'
                               'El archivo original y los ZIP o respaldos anteriores se conservan.', parent=self):
            self.service.delete_client_document(self.client_id, document_id)
            self.refresh_documents()
            self.status.configure(text='Documento quitado del expediente.')

    def export_zip(self):
        if not self.service.client_documents(self.client_id) and not any(self.details().values()):
            raise ValueError('Agrega documentos o datos para facturación antes de exportar el expediente.')
        path = filedialog.asksaveasfilename(parent=self, title='Guardar expediente para la contadora',
            initialfile=self.service.billing_zip_name(self.client_id), defaultextension='.zip',
            filetypes=[('Archivo ZIP', '*.zip')])
        if not path:
            return
        if self.details() != self.saved_details:
            self.save_details()
        count = self.service.export_client_billing(self.client_id, path)
        self.status.configure(text=f'ZIP guardado con {count} documento(s): {path}')
        messagebox.showinfo('Expediente exportado', f'Se guardaron {count} documento(s) y la ficha de datos.\n\n{path}', parent=self)

    def close(self):
        if self.details() != self.saved_details:
            answer = messagebox.askyesnocancel('Datos sin guardar', '¿Guardar los cambios en los datos para factura antes de cerrar?', parent=self)
            if answer is None:
                return
            if answer:
                try:
                    self.save_details()
                except (ValueError, OSError, sqlite3.Error) as exc:
                    messagebox.showerror('No se pudo guardar', str(exc), parent=self)
                    return
        self.destroy()
