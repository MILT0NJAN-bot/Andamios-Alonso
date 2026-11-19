from datetime import date


class ReservationPayments:
    def reservation_payment_summary(self,key):
        rows=self.db.rows('SELECT * FROM reservations WHERE id=?',(key,))
        if not rows:raise ValueError('La reservación no existe.')
        row=rows[0]
        paid=self.db.rows('SELECT COALESCE(SUM(amount_cents),0) FROM reservation_payments WHERE reservation_id=? AND cancelled_at IS NULL',(key,))[0][0]
        minimum=(row['total_cents']+1)//2 if row['deposit_required'] else 0
        return dict(total_cents=row['total_cents'],paid_cents=paid,pending_cents=max(0,row['total_cents']-paid),minimum_cents=minimum,confirmed=paid>=minimum)

    def _record_reservation_payment(self,key,amount,method='Efectivo',paid_on=None,reference='',receipt_path=None):
        from .service import cents
        from .cash import Cash
        amount=cents(amount);paid_on=paid_on or date.today().isoformat()
        if date.fromisoformat(paid_on)>date.today():raise ValueError('La fecha del anticipo no puede ser futura.')
        rows=self.db.rows("SELECT * FROM reservations WHERE id=? AND status='Confirmada'",(key,))
        if not rows:raise ValueError('Solo puedes recibir anticipos de reservaciones pendientes de entrega.')
        row=rows[0];summary=self.reservation_payment_summary(key)
        if method not in ('Efectivo','Transferencia','Tarjeta') or (row['vat_bp'] and method!='Transferencia'):
            raise ValueError('Con factura, el anticipo debe ser por transferencia.')
        if receipt_path and method!='Transferencia':raise ValueError('El comprobante corresponde únicamente a transferencias.')
        if not 0<amount<=summary['pending_cents']:raise ValueError('El anticipo debe ser mayor a cero y no superar el total pendiente.')
        if summary['paid_cents']+amount<summary['minimum_cents']:raise ValueError('Para confirmar el apartado debes recibir al menos el 50% del total.')
        if self.require_cash_open:Cash(self.db).require_open(paid_on)
        for line in self.db.rows('SELECT * FROM reservation_lines WHERE reservation_id=?',(key,)):
            if line['quantity']>self.period_available(line['item_id'],row['departure'],row['due'],exclude_reservation=key,for_reservation=True):
                raise ValueError('Ya no hay suficientes piezas para confirmar este apartado con su día de preparación.')
        payment=self.db.conn.execute('INSERT INTO reservation_payments(reservation_id,amount_cents,method,paid_on,reference) VALUES (?,?,?,?,?)',
            (key,amount,method,paid_on,reference.strip())).lastrowid
        if receipt_path:self._attach_transfer_receipt(-payment,receipt_path)
        return -payment

    def record_reservation_payment(self,key,amount,method='Efectivo',paid_on=None,reference='',receipt_path=None):
        try:
            self.db.conn.execute('BEGIN IMMEDIATE')
            result=self._record_reservation_payment(key,amount,method,paid_on,reference,receipt_path)
            self.db.conn.commit();return result
        except Exception:self.db.conn.rollback();raise

    def cancel_reservation_payment(self,payment_id,reason):
        if not reason.strip():raise ValueError('Escribe el motivo de la anulación.')
        try:
            self.db.conn.execute('BEGIN IMMEDIATE')
            payment=self.db.rows('SELECT * FROM reservation_payments WHERE id=? AND cancelled_at IS NULL',(payment_id,))
            if not payment:raise ValueError('El anticipo ya fue anulado o no existe.')
            self.db.conn.execute('UPDATE reservation_payments SET cancelled_at=CURRENT_TIMESTAMP,cancellation_reason=? WHERE id=?',(reason.strip(),payment_id))
            self.db.conn.commit()
        except Exception:self.db.conn.rollback();raise

    def reservation_conflicts(self):
        rows=[]
        for r in self.db.rows("SELECT * FROM reservations WHERE status='Confirmada' ORDER BY departure"):
            if not self.reservation_payment_summary(r['id'])['confirmed']:continue
            if any(self.period_available(l['item_id'],r['departure'],r['due'],for_reservation=True)<0 for l in self.db.rows('SELECT * FROM reservation_lines WHERE reservation_id=?',(r['id'],))):
                rows.append(r)
        return rows
