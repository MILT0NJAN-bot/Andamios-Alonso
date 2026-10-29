from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from .pricing import unit_total, tariff_label, line_charge
from .operations import Operations
from .taxes import amounts,percent
from .client_files import ClientFiles


def cents(value):
    try:
        amount = Decimal(str(value).strip())
        if not amount.is_finite() or amount < 0 or amount.as_tuple().exponent < -2:
            raise ValueError()
        return int(amount * 100)
    except (InvalidOperation, ValueError):
        raise ValueError('El importe debe ser positivo o cero, con máximo dos decimales.') from None


def money(value):
    return f'${value / 100:,.2f}'


class Service(Operations, ClientFiles):
    def __init__(self, db, tax_rates=(0,0)):
        self.db = db
        self.tax_rates=(tax_rates[0],0)

    def save_item(self, item_id, name, total, price, pricing_mode=None, week=None, month=None,replacement_cost=None):
        name = name.strip()
        total = int(total)
        price = cents(price)
        if not name or total < 0:
            raise ValueError('Escribe un nombre y una cantidad total válida.')
        with self.db.conn:
            if item_id:
                row = self.db.rows('SELECT * FROM items WHERE id=?', (item_id,))[0]
                rented = row['total'] - row['available']-row['maintenance']
                if total < rented+row['maintenance']:
                    raise ValueError(f"Hay {rented} piezas rentadas y {row['maintenance']} en revisión. El total no puede ser menor.")
                self.db.conn.execute('UPDATE items SET name=?, total=?, available=?, price_cents=? WHERE id=?',
                                     (name, total, total-rented-row['maintenance'], price, item_id))
            else:
                self.db.conn.execute('INSERT INTO items(name,total,available,price_cents) VALUES (?,?,?,?)',
                                     (name, total, total, price))
                item_id = self.db.conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            if pricing_mode is not None:
                if pricing_mode not in ('daily','scaffold'):
                    raise ValueError('Selecciona una tarifa válida.')
                weekly, monthly = cents(week or '0'), cents(month or '0')
                if pricing_mode == 'scaffold' and (not weekly or not price):
                    raise ValueError('Configura semana y día extra mayores a cero. Mes en cero desactiva la tarifa mensual.')
                self.db.conn.execute('UPDATE items SET pricing_mode=?,week_cents=?,month_cents=? WHERE id=?',
                                     (pricing_mode,weekly,monthly,item_id))
            if replacement_cost is not None:
                value=cents(replacement_cost) if str(replacement_cost).strip() else None
                self.db.conn.execute('UPDATE items SET replacement_cents=? WHERE id=?',(value,item_id))
                if value is not None:
                    for table in ('rental_lines','reservation_lines'):
                        self.db.conn.execute(f'UPDATE {table} SET replacement_cents=? WHERE item_id=? AND replacement_cents IS NULL',(value,item_id))
            for reservation in self.db.rows("SELECT r.departure,r.due FROM reservations r JOIN reservation_lines l ON l.reservation_id=r.id WHERE r.status='Confirmada' AND l.item_id=?",(item_id,)):
                if self.period_available(item_id,reservation['departure'],reservation['due'])<0:
                    raise ValueError('Ese stock dejaría reservaciones sin piezas. Revisa primero los apartados.')

    def save_client(self, client_id, name, phone, ratings, notes, address=''):
        name, phone = name.strip(), phone.strip()
        if not name or sum(c.isdigit() for c in phone) < 7:
            raise ValueError('Escribe el nombre y un teléfono de al menos 7 dígitos.')
        confirmed = ratings is not None
        if confirmed and (len(ratings) != 3 or any(not 1 <= int(x) <= 5 for x in ratings)):
            raise ValueError('Las calificaciones deben estar entre 1 y 5.')
        with self.db.conn:
            args = (name, phone, *map(int, ratings if confirmed else [3,3,3]), notes.strip(), int(confirmed))
            if client_id:
                self.db.conn.execute('UPDATE clients SET name=?,phone=?,payment_rating=?,return_rating=?,care_rating=?,notes=?,ratings_confirmed=? WHERE id=?', args+(client_id,))
            else:
                client_id = self.db.conn.execute('INSERT INTO clients(name,phone,payment_rating,return_rating,care_rating,notes,ratings_confirmed) VALUES (?,?,?,?,?,?,?)', args).lastrowid
            if address.strip():
                self.db.conn.execute('INSERT OR IGNORE INTO addresses(client_id,address) VALUES (?,?)', (client_id,address.strip()))
        return client_id

    def rate_client(self, client_id, ratings):
        if len(ratings) != 3 or any(str(x) not in ('1','2','3','4','5') for x in ratings):
            raise ValueError('Selecciona una calificación de 1 a 5 en los tres criterios.')
        with self.db.conn:
            cursor = self.db.conn.execute('UPDATE clients SET payment_rating=?,return_rating=?,care_rating=?,ratings_confirmed=1 WHERE id=?',
                                         (*map(int,ratings),client_id))
            if not cursor.rowcount:
                raise ValueError('El cliente no existe.')

    def _resolve_client(self,client_id,client_data):
        conn=self.db.conn
        if client_data is not None:
            name,phone=client_data['name'].strip(),client_data['phone'].strip()
            normalized=''.join(c for c in phone if c.isdigit())
            if not name or len(normalized)<7:
                raise ValueError('Escribe el nombre y un teléfono de al menos 7 dígitos.')
            if client_id is None:
                if any(''.join(c for c in row['phone'] if c.isdigit())==normalized for row in conn.execute('SELECT phone FROM clients')):
                    raise ValueError('Este teléfono ya está registrado. Selecciona al cliente de las sugerencias.')
                client_id=conn.execute('INSERT INTO clients(name,phone) VALUES (?,?)',(name,phone)).lastrowid
            else:
                conn.execute('UPDATE clients SET name=?,phone=? WHERE id=?',(name,phone,client_id))
        client=conn.execute('SELECT * FROM clients WHERE id=?',(client_id,)).fetchone()
        if not client:
            raise ValueError('Selecciona o captura un cliente.')
        return client

    def create_rental(self, client_id, address, departure, due, quantities, client_data=None, initial_payment=None,
                      delivery_states=None,_in_transaction=False,_reservation_id=None,_tariffs=None,_tax_rates=None,invoice_required=None,freight='0',extra_planks=0):
        freight_value=cents(freight or '0')
        if str(extra_planks)!=str(int(extra_planks)) or int(extra_planks)<0:
            raise ValueError('Captura una cantidad entera de tablones, cero si no aplica.')
        extra_planks=int(extra_planks);plank_value=extra_planks*5000
        start, end = date.fromisoformat(departure), date.fromisoformat(due)
        days = (end-start).days
        if days < 1:
            raise ValueError('La devolución debe ser posterior a la salida (mínimo un día).')
        if not address.strip() or not quantities:
            raise ValueError('Selecciona una dirección y al menos un equipo.')
        conn = self.db.conn
        try:
            if not _in_transaction:
                conn.execute('BEGIN IMMEDIATE')
            client=self._resolve_client(client_id,client_data)
            client_id=client['id']
            lines = []
            for item_id, quantity in quantities.items():
                if not isinstance(quantity, int) or quantity < 1:
                    raise ValueError('Las cantidades deben ser enteros positivos.')
                item = conn.execute('SELECT * FROM items WHERE id=?', (item_id,)).fetchone()
                if not item or quantity > item['available']:
                    raise ValueError('Stock insuficiente. Actualiza la selección de equipos.')
                if quantity>self.period_available(item_id,start,end,exclude_reservation=_reservation_id):
                    raise ValueError('Las piezas están comprometidas en reservaciones para esas fechas.')
                if _tariffs:
                    item=dict(item)
                    for field in ('price_cents','pricing_mode','week_cents','month_cents','replacement_cents'):
                        item[field]=_tariffs[item_id][field]
                if item['price_cents'] == 0:
                    raise ValueError(f"Configura el precio de {item['name']} antes de rentarlo.")
                lines.append((item, quantity))
                unit_total(item,days)
            conn.execute('INSERT OR IGNORE INTO addresses(client_id,address) VALUES (?,?)', (client_id,address.strip()))
            address_id = conn.execute('SELECT id FROM addresses WHERE client_id=? AND address=?', (client_id,address.strip())).fetchone()[0]
            subtotal = sum(unit_total(item,days)*quantity for item, quantity in lines)+freight_value+plank_value
            vat=(_tax_rates if _tax_rates is not None else self.tax_rates)[0] if invoice_required is None else (1600 if invoice_required else 0)
            breakdown=amounts(subtotal,vat,0)
            total=breakdown['total_cents']
            rental_id = conn.execute('INSERT INTO rentals(client_id,address_id,client_name,client_phone,work_address,departure,due,days,total_cents) VALUES (?,?,?,?,?,?,?,?,?)',
                (client_id,address_id,client['name'],client['phone'],address.strip(),departure,due,days,total)).lastrowid
            conn.execute('UPDATE rentals SET subtotal_cents=?,vat_bp=?,isr_bp=?,vat_cents=?,isr_cents=? WHERE id=?',
                (subtotal,breakdown['vat_bp'],breakdown['isr_bp'],breakdown['vat_cents'],breakdown['isr_cents'],rental_id))
            conn.execute('UPDATE rentals SET freight_cents=?,extra_planks=?,plank_cents=? WHERE id=?',(freight_value,extra_planks,plank_value,rental_id))
            for item, quantity in lines:
                conn.execute('INSERT INTO rental_lines(rental_id,item_id,item_name,quantity,price_cents,pricing_mode,week_cents,month_cents) VALUES (?,?,?,?,?,?,?,?)',
                    (rental_id,item['id'],item['name'],quantity,item['price_cents'],item['pricing_mode'],item['week_cents'],item['month_cents']))
                conn.execute('UPDATE items SET available=available-? WHERE id=?', (quantity,item['id']))
                conn.execute('UPDATE rental_lines SET replacement_cents=? WHERE rental_id=? AND item_id=?',(item['replacement_cents'],rental_id,item['id']))
                state=(delivery_states or {}).get(item['id'],{})
                condition=state.get('condition','Bueno')
                if condition not in ('Bueno','Malo'):
                    raise ValueError('Selecciona Bueno o Malo para el estado del equipo.')
                conn.execute('UPDATE rental_lines SET delivery_condition=?,delivery_notes=? WHERE rental_id=? AND item_id=?',
                    (condition,state.get('notes','').strip() if condition=='Malo' else '',rental_id,item['id']))
            if initial_payment is not None:
                self._insert_payment(rental_id,**initial_payment)
            if not _in_transaction:
                conn.commit()
            return rental_id
        except Exception:
            if not _in_transaction:
                conn.rollback()
            raise

    def payment_summary(self,rental_id):
        rows=self.db.rows('SELECT total_cents FROM rentals WHERE id=?',(rental_id,))
        if not rows:
            raise ValueError('La renta no existe.')
        paid=self.db.rows('SELECT COALESCE(SUM(amount_cents),0) FROM payments WHERE rental_id=? AND cancelled_at IS NULL',(rental_id,))[0][0]
        total=rows[0]['total_cents']
        balance=total-paid
        status='Saldo a favor' if balance<0 else ('Liquidada' if balance==0 else ('Pago parcial' if paid else 'Sin pagos'))
        return {'total_cents':total,'paid_cents':paid,'pending_cents':max(0,balance),'credit_cents':max(0,-balance),'status':status}

    def _insert_payment(self,rental_id,amount,method='Efectivo',paid_on=None,reference='',kind='Abono'):
        amount=cents(amount)
        if amount<=0:
            raise ValueError('El pago debe ser mayor a cero.')
        if method not in ('Efectivo','Transferencia','Tarjeta') or kind not in ('Anticipo','Abono','Liquidación'):
            raise ValueError('Selecciona un tipo y método de pago válidos.')
        paid_on=paid_on or date.today().isoformat()
        payment_date=date.fromisoformat(paid_on)
        if payment_date>date.today():
            raise ValueError('Un pago recibido no puede tener una fecha futura.')
        summary=self.payment_summary(rental_id)
        if amount>summary['pending_cents']:
            raise ValueError(f"El pago supera el saldo pendiente de {money(summary['pending_cents'])}.")
        if kind=='Liquidación' and amount!=summary['pending_cents']:
            raise ValueError('Para liquidar, el importe debe ser igual al saldo pendiente.')
        if amount==summary['pending_cents']:
            kind='Liquidación'
        return self.db.conn.execute('INSERT INTO payments(rental_id,amount_cents,kind,method,paid_on,reference) VALUES (?,?,?,?,?,?)',
            (rental_id,amount,kind,method,payment_date.isoformat(),reference.strip())).lastrowid

    def record_payment(self,rental_id,amount,method='Efectivo',paid_on=None,reference='',kind='Abono'):
        try:
            self.db.conn.execute('BEGIN IMMEDIATE')
            key=self._insert_payment(rental_id,amount,method,paid_on,reference,kind)
            self.db.conn.commit()
            return key
        except Exception:
            self.db.conn.rollback()
            raise

    def cancel_payment(self,payment_id,reason):
        if not reason.strip():
            raise ValueError('Escribe el motivo de la anulación.')
        with self.db.conn:
            cursor=self.db.conn.execute('UPDATE payments SET cancelled_at=CURRENT_TIMESTAMP,cancellation_reason=? WHERE id=? AND cancelled_at IS NULL',
                (reason.strip(),payment_id))
            if not cursor.rowcount:
                raise ValueError('El pago no existe o ya fue anulado.')

    def overdue(self, today=None):
        today = today or date.today()
        return self.db.rows('SELECT * FROM rentals WHERE returned_at IS NULL AND due < ? ORDER BY due,id',
                            (today.isoformat(),))

    def extension_quote(self, rental_id, added_days):
        if not isinstance(added_days, int) or isinstance(added_days, bool) or added_days < 1 or added_days > 3650:
            raise ValueError('Escribe días enteros entre 1 y 3650.')
        rows = self.db.rows('SELECT * FROM rentals WHERE id=?', (rental_id,))
        if not rows or rows[0]['returned_at']:
            raise ValueError('Solo se pueden ampliar rentas activas.')
        rental = rows[0]
        lines = self.db.rows('SELECT * FROM rental_lines WHERE rental_id=?',(rental_id,))
        new_due=date.fromisoformat(rental['due'])+timedelta(days=added_days)
        for line in lines:
            pending=line['quantity']-line['returned_qty']
            if pending>self.period_available(line['item_id'],date.today(),max(new_due,date.today()+timedelta(days=1)),exclude_rental=rental_id):
                raise ValueError('La ampliación coincide con una reservación sin suficientes piezas.')
        subtotal = sum(line_charge(self.db,line,rental['days']+added_days) for line in lines)+rental['freight_cents']+rental['plank_cents']
        breakdown=amounts(subtotal,rental['vat_bp'],0)
        total=breakdown['total_cents']
        return {'previous_due': rental['due'],
                'new_due': (date.fromisoformat(rental['due'])+timedelta(days=added_days)).isoformat(),
                'added_cents': total-rental['total_cents'], **breakdown}

    def extend_rental(self, rental_id, added_days):
        conn = self.db.conn
        try:
            conn.execute('BEGIN IMMEDIATE')
            quote = self.extension_quote(rental_id, added_days)
            conn.execute('INSERT INTO rental_extensions(rental_id,previous_due,new_due,added_days,added_cents,adjustment_cents) VALUES (?,?,?,?,?,?)',
                         (rental_id,quote['previous_due'],quote['new_due'],added_days,max(0,quote['added_cents']),quote['added_cents']))
            conn.execute('UPDATE rentals SET due=?,days=days+?,total_cents=? WHERE id=?',
                         (quote['new_due'],added_days,quote['total_cents'],rental_id))
            conn.execute('UPDATE rentals SET subtotal_cents=?,vat_cents=?,isr_cents=? WHERE id=?',
                (quote['subtotal_cents'],quote['vat_cents'],quote['isr_cents'],rental_id))
            conn.commit()
            return quote
        except Exception:
            conn.rollback()
            raise

    def return_rental(self, rental_id):
        return self.return_partial(rental_id,[{'line_id':r['id'],'quantity':r['pending'],'condition':'Bueno'} for r in self.remaining_lines(rental_id) if r['pending']])

    def apply_taxes(self,rental_id):
        rows=self.db.rows('SELECT vat_bp FROM rentals WHERE id=?',(rental_id,))
        if rows and rows[0]['vat_bp']==1600:
            raise ValueError('Esta renta ya tiene IVA.')
        return self.set_invoice(rental_id,True)

    def set_invoice(self,rental_id,required):
        try:
            self.db.conn.execute('BEGIN IMMEDIATE')
            rows=self.db.rows('SELECT * FROM rentals WHERE id=?',(rental_id,))
            if not rows:
                raise ValueError('La renta no existe.')
            rental=rows[0]
            breakdown=amounts(rental['subtotal_cents'],1600 if required else 0,0)
            self.db.conn.execute('UPDATE rentals SET vat_bp=?,isr_bp=?,vat_cents=?,isr_cents=?,total_cents=? WHERE id=?',
                (breakdown['vat_bp'],breakdown['isr_bp'],breakdown['vat_cents'],breakdown['isr_cents'],breakdown['total_cents'],rental_id))
            self.db.conn.execute('INSERT INTO tax_adjustments(record_type,record_id,previous_total,new_total,reason) VALUES (?,?,?,?,?)',
                ('rentals',rental_id,rental['total_cents'],breakdown['total_cents'],'Factura solicitada' if required else 'Sin factura'))
            self.db.conn.commit()
            return breakdown
        except Exception:
            self.db.conn.rollback()
            raise

    def note(self, rental_id):
        rental = self.db.rows('SELECT * FROM rentals WHERE id=?', (rental_id,))[0]
        lines = self.db.rows('SELECT * FROM rental_lines WHERE rental_id=?', (rental_id,))
        text = [f'ANDAMIOS ALONSO — NOTA DE RENTA #{rental_id:06d}', '',
                f"Cliente: {rental['client_name']}", f"Teléfono: {rental['client_phone']}",
                f"Obra: {rental['work_address']}", f"Salida: {rental['departure']}",
                f"Devolución estimada: {rental['due']} | Días: {rental['days']}", '']
        for line in lines:
            text.append(f"{line['quantity']} × {line['item_name']} | {tariff_label(line)} | {money(line_charge(self.db,line,rental['days']))}")
            text.append(f"  Entregadas: {line['quantity']} · Devueltas: {line['returned_qty']} · Pendientes: {line['quantity']-line['returned_qty']} · Estado al entregar: {line['delivery_condition']}")
            if line['delivery_notes']:
                text.append('  Observaciones de entrega: '+line['delivery_notes'])
        for received in self.db.rows('SELECT r.*,l.item_name FROM rental_returns r JOIN rental_lines l ON l.id=r.line_id WHERE r.rental_id=? ORDER BY r.id',(rental_id,)):
            text.append(f"Devolución {received['returned_on']}: {received['quantity']} × {received['item_name']} · {received['condition']}"+(f" · {received['notes']}" if received['notes'] else ''))
        extensions = self.db.rows('SELECT * FROM rental_extensions WHERE rental_id=? ORDER BY id', (rental_id,))
        if extensions:
            text.extend(['', 'AMPLIACIONES (ya incluidas en el total):'])
            for extension in extensions:
                adjustment = extension['adjustment_cents'] if extension['adjustment_cents'] is not None else extension['added_cents']
                text.append(f"+{extension['added_days']} días | {extension['previous_due']} → {extension['new_due']} | Ajuste {money(adjustment)}")
        summary=self.payment_summary(rental_id)
        text.extend([f"Flete: {money(rental['freight_cents'])}",f"Tablones extra: {rental['extra_planks']} × $50 = {money(rental['plank_cents'])}"])
        text.extend(['',f"SUBTOTAL: {money(rental['subtotal_cents'])}",f"IVA {percent(rental['vat_bp'])}: {money(rental['vat_cents'])}",
            f"Factura: {'Solicitada' if rental['vat_bp'] else 'No solicitada'}", f"TOTAL: {money(rental['total_cents'])} MXN", f"PAGADO: {money(summary['paid_cents'])} MXN",
            f"SALDO PENDIENTE: {money(summary['pending_cents'])} MXN",f"SALDO A FAVOR: {money(summary['credit_cents'])} MXN",f"Pago: {summary['status']}",
            f"Estado: {'Devuelta el '+rental['returned_at'] if rental['returned_at'] else 'Activa'}", '', 'Firma cliente: ____________________', 'Firma entrega: ____________________'])
        return '\n'.join(text)
