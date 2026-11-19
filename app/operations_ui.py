import tkinter as tk
from datetime import date,timedelta,datetime
from tkinter import messagebox
import customtkinter as ctk
from .service import cents,money


class OperationsUI:
    def return_dialog(self,key):
        lines=[r for r in self.service.remaining_lines(key) if r['pending']]
        if not lines:
            raise ValueError('La renta ya fue devuelta o no existe.')
        win,body=self.dialog(f'Recibir equipos · Renta #{key:06d}')
        win.geometry('850x780')
        ctk.CTkLabel(body,text='¿Cuántas piezas regresan hoy?',font=ctk.CTkFont(size=24,weight='bold'),text_color='#203F78').pack(anchor='w',pady=10)
        ctk.CTkLabel(body,text='Captura solo lo que recibes. Las demás piezas seguirán en renta.\nBueno vuelve a disponible; Malo queda en revisión. Las notas son opcionales.',justify='left').pack(anchor='w',pady=8)
        controls=[]
        def all_pending():
            for line,qty,_,_ in controls:
                qty.set(str(line['pending']))
        ctk.CTkButton(body,text='Recibir todas las piezas pendientes',command=all_pending).pack(anchor='w',pady=8)
        for line in lines:
            box=self.panel(body,f"{line['item_name']} · Pendientes: {line['pending']} de {line['quantity']}")
            left,right=self.pair(box)
            qty=self.entry(left,'Piezas que recibes','0')
            ctk.CTkLabel(right,text='Estado al recibir').pack(anchor='w')
            condition=tk.StringVar(value='Bueno')
            note_box=ctk.CTkFrame(box,fg_color='transparent')
            notes=self.entry(note_box,'Notas (opcional)')
            ctk.CTkOptionMenu(right,values=['Bueno','Malo'],variable=condition,height=40,
                command=lambda value,b=note_box:b.pack(fill='x',pady=6) if value=='Malo' else b.pack_forget()).pack(fill='x',pady=5)
            controls.append((line,qty,condition,notes))
        def save():
            entries=[]
            for line,qty,condition,notes in controls:
                count=int(qty.get())
                if count<0:
                    raise ValueError('Las piezas no pueden ser negativas.')
                if count:
                    entries.append({'line_id':line['id'],'quantity':count,'condition':condition.get(),'notes':notes.get()})
            if not entries:
                raise ValueError('Indica cuántas piezas se reciben.')
            if not messagebox.askyesno('Confirmar recepción',f"Se recibirán {sum(e['quantity'] for e in entries)} piezas. ¿Guardar devolución?",parent=win):
                return
            completed=self.service.return_partial(key,entries)
            win.destroy()
            self.refresh()
            if completed:
                client=self.db.rows('SELECT client_id FROM rentals WHERE id=?',(key,))[0][0]
                self.rating_dialog(client)
        ctk.CTkLabel(body,text='La devolución no modifica lo ya contratado ni liquida el saldo.\nSi necesitas ampliar, se cobrarán días extra únicamente a las piezas pendientes.',justify='left',text_color='#748195').pack(anchor='w',pady=10)
        ctk.CTkButton(body,text='Guardar devolución',height=44,fg_color='#18865B',command=lambda:self.safe(save)).pack(fill='x',pady=12)

    def release_dialog(self):
        key=self.selected(self.inventory)
        item=self.db.rows('SELECT * FROM items WHERE id=?',(key,))[0]
        if not item['maintenance']:
            raise ValueError('Este equipo no tiene piezas en revisión.')
        win,body=self.dialog('Liberar equipo revisado')
        ctk.CTkLabel(body,text=f"{item['name']} · {item['maintenance']} piezas en revisión",wraplength=450).pack(anchor='w',pady=10)
        qty=self.entry(body,'Piezas reparadas y listas para rentar','1')
        def save():
            self.service.release_equipment(key,int(qty.get()))
            win.destroy()
            self.refresh()
        ctk.CTkButton(body,text='Volver a disponibles',height=44,command=lambda:self.safe(save)).pack(fill='x',pady=10)

    def make_reservations(self):
        page=self.tabs.tab('Reservaciones')
        self.heading(page,'Reservaciones','Apartados por fecha · Se comprueba disponibilidad antes de reservar y antes de entregar.')
        self.reservation_filter=self.entry(page,'Buscar cliente, teléfono o folio')
        self.reservation_filter.trace_add('write',lambda *_:self.refresh_reservations())
        self.reservations_table=self.table(page,('Folio','Cliente','Salida','Devolución','Equipos','Total','Anticipo','Restante','Estado'),height=10)
        bar=ctk.CTkFrame(page,fg_color='transparent');bar.pack(fill='x',pady=10)
        def new():
            self.new_reservation_dialog()
        ctk.CTkButton(bar,text='+ Nueva reservación',height=44,command=new).pack(side='left',padx=5)
        ctk.CTkButton(bar,text='Entregar e iniciar renta',height=44,fg_color='#18865B',command=lambda:self.safe(self.start_selected_reservation)).pack(side='left',padx=5)
        ctk.CTkButton(bar,text='Cancelar reservación',height=44,fg_color='#B52B27',command=lambda:self.safe(self.cancel_selected_reservation)).pack(side='left',padx=5)
        more=ctk.CTkFrame(page,fg_color='transparent');more.pack(fill='x',pady=5)
        ctk.CTkButton(more,text='Registrar anticipo',command=lambda:self.safe(self.reservation_deposit_dialog)).pack(side='left',padx=5)
        ctk.CTkButton(more,text='Pagos de la reservación',command=lambda:self.safe(self.reservation_payment_history)).pack(side='left',padx=5)
        ctk.CTkLabel(page,text='Confirmación con anticipo mínimo del 50%. Las piezas siguen rentándose antes del apartado si queda un día completo para prepararlas.\nLas reservaciones anteriores conservan su confirmación histórica. El anticipo no se cobra otra vez al iniciar la renta.',text_color='#748195',justify='left',wraplength=850).pack(anchor='w',pady=10)

    def refresh_reservations(self):
        if not hasattr(self,'reservations_table'):
            return
        term=self.reservation_filter.get().strip().casefold()
        rows=[]
        for row in self.db.rows('SELECT * FROM reservations ORDER BY id DESC'):
            if term not in f"{row['id']:06d} {row['client_name']} {row['client_phone']}".casefold():
                continue
            lines=self.db.rows('SELECT * FROM reservation_lines WHERE reservation_id=?',(row['id'],))
            status=row['status']
            summary=self.service.reservation_payment_summary(row['id'])
            if status=='Confirmada':
                conflict=any(self.service.period_available(line['item_id'],row['departure'],row['due'],for_reservation=True)<0 for line in lines)
                if not summary['confirmed']:status='Pendiente anticipo 50%'
                elif conflict:
                    status='Revisar disponibilidad'
                elif row['departure']<date.today().isoformat():
                    status='Pendiente de entrega'
            rows.append((row['id'],(f"{row['id']:06d}",f"{row['client_name']} · {row['client_phone']}",row['departure'],row['due'],
                ', '.join(f"{line['quantity']} × {line['item_name']}" for line in lines),money(row['total_cents']),money(summary['paid_cents']),money(summary['pending_cents']),status)))
        self.fill(self.reservations_table,rows)

    def reserve_current(self):
        self.new_reservation_dialog()

    def start_selected_reservation(self):
        if not self.ensure_cash_open():
            return
        key=self.selected(self.reservations_table)
        if messagebox.askyesno('Entregar reservación','¿Confirmas que se entregan hoy los equipos y empieza el periodo de renta?',parent=self):
            rental=self.service.start_reservation(key)
            self.refresh();self.navigate('Rentas activas')
            self.active_table.selection_set(str(rental))
            self.notify_exhausted_stock(rental)
            self.show_note(rental)

    def cancel_selected_reservation(self):
        key=self.selected(self.reservations_table)
        paid=self.service.reservation_payment_summary(key)['paid_cents']
        warning=f'\nAnticipo recibido: {money(paid)}. Se conserva el cobro; cancelar no devuelve dinero automáticamente.' if paid else ''
        if messagebox.askyesno('Cancelar reservación','¿Cancelar este apartado y liberar sus fechas?'+warning,parent=self):
            self.service.cancel_reservation(key);self.refresh()

    def make_backups(self):
        page=self.tabs.tab('Respaldos')
        self.heading(page,'Respaldos','Copias diarias y al cerrar; durante la jornada, una copia cada hora si hubo cambios. Se conservan 30 copias automáticas y 48 de jornada.')
        self.backup_status=ctk.CTkLabel(page,text='',text_color='#203F78',justify='left',wraplength=850)
        self.backup_status.pack(anchor='w',pady=10)
        self.backup_table=self.table(page,('Archivo','Fecha','Tamaño'),height=10)
        bar=ctk.CTkFrame(page,fg_color='transparent');bar.pack(fill='x',pady=10)
        def now():
            path=self.db.automatic_backup(force=True)
            self.refresh_backups()
            if not path:
                raise OSError('No se pudo guardar el respaldo: '+self.db.backup_error)
            messagebox.showinfo('Respaldo guardado',str(path),parent=self)
        ctk.CTkButton(bar,text='Crear respaldo ahora',height=44,command=lambda:self.safe(now)).pack(side='left',padx=5)
        ctk.CTkButton(bar,text='Guardar copia en otra ubicación',height=44,command=self.backup).pack(side='left',padx=5)
        ctk.CTkLabel(page,text='Las copias automáticas están en la misma computadora. Guarda también copias en otra unidad.\nPara restaurar: cierra el programa, conserva una copia de la base actual y reemplázala por el respaldo.\nEl respaldo contiene clientes, expedientes de facturación con sus documentos, inventario, rentas, pagos, devoluciones y reservaciones.',wraplength=850,text_color='#748195',justify='left').pack(anchor='w',pady=10)

    def refresh_backups(self):
        if not hasattr(self,'backup_table'):
            return
        directory=self.db.path.parent/'respaldos'
        error=self.db.backup_error or getattr(self,'recovery_error','')
        self.backup_status.configure(text=error if error else f'Ubicación: {directory}')
        rows=[]
        if directory.exists():
            paths=list(directory.glob('automatico-*.sqlite3'))+list(directory.glob('jornada-*.sqlite3'))
            paths.sort(key=lambda p:p.stat().st_mtime,reverse=True)
            for index,path in enumerate(paths,1):
                stat=path.stat()
                rows.append((index,(path.name,datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M'),f'{stat.st_size/1024:,.0f} KB')))
        self.fill(self.backup_table,rows)
        if rows and not error:self.backup_status.configure(text=f'Último respaldo: {rows[0][1][1]}\nUbicación: {directory}')
