"""Direcciones de obra desglosadas y compatibles con el historial anterior."""
import json
import tkinter as tk
import customtkinter as ctk

FIELDS=(('street','Calle y número'),('colony','Colonia'),('postal_code','Código postal'),('municipality','Municipio'),('state','Estado'),('references','Referencias de entrega (opcional)'))


def normalized(parts):
    result={key:str(parts.get(key,'')).strip() for key,_ in FIELDS}
    if result['postal_code'] and (len(result['postal_code'])!=5 or not result['postal_code'].isascii() or not result['postal_code'].isdigit()):
        raise ValueError('El código postal debe tener 5 dígitos, o quedar vacío si aún no lo conoces.')
    if any(len(value)>1000 for value in result.values()):raise ValueError('La dirección contiene un campo demasiado largo.')
    if not result['street'] and any(result.values()):raise ValueError('Escribe la calle y número o identificación de la obra.')
    return result


def formatted(parts):
    return ', '.join(filter(None,(parts.get('street','').strip(),
        'Col. '+parts['colony'].strip() if parts.get('colony','').strip() else '',
        'CP '+parts['postal_code'].strip() if parts.get('postal_code','').strip() else '',
        parts.get('municipality','').strip(),parts.get('state','').strip(),
        'Referencias: '+parts['references'].strip() if parts.get('references','').strip() else '')))


def save_address_parts(db,client_id,address,parts):
    if parts is None:return
    clean=normalized(parts)
    if formatted(clean)!=address.strip():raise ValueError('La dirección no coincide con sus campos. Revisa los datos de la obra.')
    if address.strip():
        db.conn.execute('INSERT INTO address_details(client_id,address,data_json) VALUES (?,?,?) ON CONFLICT(client_id,address) DO UPDATE SET data_json=excluded.data_json',
            (client_id,address.strip(),json.dumps(clean,ensure_ascii=False)))


class AddressFields(ctk.CTkFrame):
    def __init__(self,parent):
        super().__init__(parent,fg_color='transparent')
        self.columnconfigure((0,1),weight=1)
        self.value=tk.StringVar();self.fields={};self.loading=False
        for index,(key,label) in enumerate(FIELDS):
            box=ctk.CTkFrame(self,fg_color='transparent');box.grid(row=index//2,column=index%2,sticky='ew',padx=(0,8),pady=4)
            ctk.CTkLabel(box,text=label,anchor='w').pack(fill='x')
            var=tk.StringVar();self.fields[key]=var
            ctk.CTkEntry(box,textvariable=var,height=38).pack(fill='x')
            var.trace_add('write',self.changed)
        self.value.trace_add('write',self.external_value)

    def changed(self,*_):
        if self.loading:return
        self.loading=True
        try:self.value.set(formatted({key:var.get() for key,var in self.fields.items()}))
        finally:self.loading=False

    def external_value(self,*_):
        if self.loading:return
        self.load({'street':self.value.get()})

    def load(self,parts):
        self.loading=True
        try:
            for key,var in self.fields.items():var.set(parts.get(key,''))
            self.value.set(formatted(parts))
        finally:self.loading=False

    def load_saved(self,db,client_id,address):
        rows=db.rows('SELECT data_json FROM address_details WHERE client_id=? AND address=?',(client_id,address))
        self.load(json.loads(rows[0][0]) if rows else {'street':address})

    def parts(self):return normalized({key:var.get() for key,var in self.fields.items()})
