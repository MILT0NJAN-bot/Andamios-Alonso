from datetime import date,timedelta
from .pricing import unit_total
from .taxes import amounts


class Operations:
    def remaining_lines(self,rental_id):
        return self.db.rows('SELECT *,quantity-returned_qty AS pending FROM rental_lines WHERE rental_id=? ORDER BY id',(rental_id,))

    def return_partial(self,rental_id,entries,returned_on=None):
        conn=self.db.conn
        try:
            conn.execute('BEGIN IMMEDIATE')
            rows=self.db.rows('SELECT * FROM rentals WHERE id=?',(rental_id,))
            if not rows or rows[0]['returned_at']:
                raise ValueError('La renta no existe o ya fue devuelta por completo.')
            rental=rows[0]
            returned_on=returned_on or date.today().isoformat()
            received=date.fromisoformat(returned_on)
            if received>date.today() or received<date.fromisoformat(rental['departure']):
                raise ValueError('La devolución debe estar entre la salida y el día de hoy.')
            previous=self.db.rows('SELECT MAX(returned_on) FROM rental_returns WHERE rental_id=?',(rental_id,))[0][0]
            if previous and returned_on<previous:
                raise ValueError('La fecha no puede ser anterior a la última devolución registrada.')
            lines={r['id']:r for r in self.remaining_lines(rental_id)}
            seen=set()
            if not entries:
                raise ValueError('Indica al menos una pieza que se recibe.')
            for entry in entries:
                key=entry['line_id'];quantity=entry['quantity'];condition=entry.get('condition','Bueno')
                if key in seen or key not in lines or type(quantity) is not int or not 1<=quantity<=lines[key]['pending']:
                    raise ValueError('La cantidad recibida supera las piezas pendientes o no es válida.')
                if condition not in ('Bueno','Malo'):
                    raise ValueError('Selecciona estado Bueno o Malo.')
                seen.add(key)
                line=lines[key]
                notes=entry.get('notes','').strip() if condition=='Malo' else ''
                conn.execute('INSERT INTO rental_returns(rental_id,line_id,quantity,condition,notes,returned_on,unit_cents) VALUES (?,?,?,?,?,?,?)',
                    (rental_id,key,quantity,condition,notes,returned_on,unit_total(line,rental['days'])))
                conn.execute('UPDATE rental_lines SET returned_qty=returned_qty+? WHERE id=?',(quantity,key))
                if condition=='Bueno':
                    conn.execute('UPDATE items SET available=available+? WHERE id=?',(quantity,line['item_id']))
                else:
                    conn.execute('UPDATE items SET maintenance=maintenance+? WHERE id=?',(quantity,line['item_id']))
            pending=self.db.rows('SELECT SUM(quantity-returned_qty) FROM rental_lines WHERE rental_id=?',(rental_id,))[0][0]
            if not pending:
                conn.execute('UPDATE rentals SET returned_at=? WHERE id=?',(returned_on,rental_id))
            conn.commit()
            return not pending
        except Exception:
            conn.rollback()
            raise

    def release_equipment(self,item_id,quantity):
        if type(quantity) is not int or quantity<1:
            raise ValueError('Indica una cantidad entera mayor a cero.')
        with self.db.conn:
            cursor=self.db.conn.execute('UPDATE items SET maintenance=maintenance-?,available=available+? WHERE id=? AND maintenance>=?',
                (quantity,quantity,item_id,quantity))
            if not cursor.rowcount:
                raise ValueError('La cantidad supera las piezas en revisión.')

    def period_available(self,item_id,start,end,exclude_reservation=None,exclude_rental=None):
        start=date.fromisoformat(start) if isinstance(start,str) else start
        end=date.fromisoformat(end) if isinstance(end,str) else end
        if end<=start:
            raise ValueError('La devolución debe ser posterior a la salida.')
        item=self.db.rows('SELECT * FROM items WHERE id=?',(item_id,))
        if not item:
            raise ValueError('El equipo no existe.')
        capacity=item[0]['total']-item[0]['maintenance']
        events=[]
        def occupy(begin,finish,quantity):
            begin=max(start,begin);finish=min(end,finish)
            if begin<finish and quantity:
                events.extend([(begin,quantity),(finish,-quantity)])
        for row in self.db.rows('SELECT r.*,l.quantity-l.returned_qty AS pending FROM rentals r JOIN rental_lines l ON l.rental_id=r.id WHERE r.returned_at IS NULL AND l.item_id=?',(item_id,)):
            if row['id']==exclude_rental:
                continue
            due=date.fromisoformat(row['due'])
            # Una renta vencida sin devolución no tiene una fecha fiable de liberación.
            occupy(min(date.fromisoformat(row['departure']),date.today()),end if due<date.today() else due,row['pending'])
        for row in self.db.rows("SELECT r.*,l.quantity FROM reservations r JOIN reservation_lines l ON l.reservation_id=r.id WHERE r.status='Confirmada' AND l.item_id=?",(item_id,)):
            if row['id']!=exclude_reservation:
                occupy(date.fromisoformat(row['departure']),date.fromisoformat(row['due']),row['quantity'])
        current=peak=0
        for _,change in sorted(events,key=lambda x:(x[0],x[1])):
            current+=change;peak=max(peak,current)
        return capacity-peak

    def create_reservation(self,client_id,address,departure,due,quantities,client_data=None,invoice_required=None,freight='0',extra_planks=0):
        from .service import cents
        freight_value=cents(freight or '0')
        if str(extra_planks)!=str(int(extra_planks)) or int(extra_planks)<0:
            raise ValueError('Captura una cantidad entera de tablones, cero si no aplica.')
        extra_planks=int(extra_planks);plank_value=extra_planks*5000
        start,end=date.fromisoformat(departure),date.fromisoformat(due)
        if start<date.today() or end<=start:
            raise ValueError('Selecciona una salida desde hoy y una devolución posterior.')
        if not quantities or not address.strip():
            raise ValueError('Completa dirección y equipos para reservar.')
        conn=self.db.conn
        try:
            conn.execute('BEGIN IMMEDIATE')
            client=self._resolve_client(client_id,client_data)
            lines=[]
            for key,quantity in quantities.items():
                if type(quantity) is not int or quantity<1 or quantity>self.period_available(key,start,end):
                    raise ValueError('No hay suficientes piezas disponibles en esas fechas. Revisa las reservaciones.')
                row=self.db.rows('SELECT * FROM items WHERE id=?',(key,))[0]
                unit_total(row,(end-start).days)
                lines.append((row,quantity))
            subtotal=sum(unit_total(row,(end-start).days)*q for row,q in lines)+freight_value+plank_value
            breakdown=amounts(subtotal,self.tax_rates[0] if invoice_required is None else (1600 if invoice_required else 0),0)
            total=breakdown['total_cents']
            key=conn.execute('INSERT INTO reservations(client_id,client_name,client_phone,work_address,departure,due,days,total_cents) VALUES (?,?,?,?,?,?,?,?)',
                (client['id'],client['name'],client['phone'],address.strip(),departure,due,(end-start).days,total)).lastrowid
            conn.execute('UPDATE reservations SET subtotal_cents=?,vat_bp=?,isr_bp=?,vat_cents=?,isr_cents=? WHERE id=?',
                (subtotal,breakdown['vat_bp'],breakdown['isr_bp'],breakdown['vat_cents'],breakdown['isr_cents'],key))
            conn.execute('UPDATE reservations SET freight_cents=?,extra_planks=?,plank_cents=? WHERE id=?',(freight_value,extra_planks,plank_value,key))
            for row,quantity in lines:
                conn.execute('INSERT INTO reservation_lines(reservation_id,item_id,item_name,quantity,price_cents,pricing_mode,week_cents,month_cents) VALUES (?,?,?,?,?,?,?,?)',
                    (key,row['id'],row['name'],quantity,row['price_cents'],row['pricing_mode'],row['week_cents'],row['month_cents']))
                conn.execute('UPDATE reservation_lines SET replacement_cents=? WHERE reservation_id=? AND item_id=?',(row['replacement_cents'],key,row['id']))
            conn.execute('INSERT OR IGNORE INTO addresses(client_id,address) VALUES (?,?)',(client['id'],address.strip()))
            conn.commit()
            return key
        except Exception:
            conn.rollback()
            raise

    def cancel_reservation(self,key):
        with self.db.conn:
            result=self.db.conn.execute("UPDATE reservations SET status='Cancelada' WHERE id=? AND status='Confirmada'",(key,))
            if not result.rowcount:
                raise ValueError('Solo se pueden cancelar reservaciones confirmadas.')

    def start_reservation(self,key):
        conn=self.db.conn
        try:
            conn.execute('BEGIN IMMEDIATE')
            rows=self.db.rows("SELECT * FROM reservations WHERE id=? AND status='Confirmada'",(key,))
            if not rows:
                raise ValueError('La reservación ya fue entregada, cancelada o no existe.')
            reservation=rows[0]
            if reservation['departure']>date.today().isoformat():
                raise ValueError('La entrega se puede registrar a partir de la fecha reservada.')
            start=date.today();end=start+timedelta(days=reservation['days'])
            lines=self.db.rows('SELECT * FROM reservation_lines WHERE reservation_id=?',(key,))
            rental_id=self.create_rental(reservation['client_id'],reservation['work_address'],start.isoformat(),end.isoformat(),
                {line['item_id']:line['quantity'] for line in lines},_in_transaction=True,_reservation_id=key,_tariffs={line['item_id']:line for line in lines},
                _tax_rates=(reservation['vat_bp'],0),freight=str(reservation['freight_cents']/100),extra_planks=reservation['extra_planks'])
            conn.execute("UPDATE reservations SET status='Entregada',rental_id=? WHERE id=?",(rental_id,key))
            conn.commit()
            return rental_id
        except Exception:
            conn.rollback()
            raise
