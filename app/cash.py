"""Caja local: importes en centavos y cierres con fotografía inmutable."""
import json
from datetime import date

METHODS = ('Efectivo','Transferencia','Tarjeta')
CATEGORIES = ('Sueldos','Gasolina','Mantenimiento','Reparaciones','Compras','Otros gastos','Retiro del dueño','Aportación del dueño','Otros ingresos')
INCOME_CATEGORIES = ('Aportación del dueño','Otros ingresos')


class Cash:
    def __init__(self, db):
        self.db=db

    def valid_day(self, value):
        day=date.fromisoformat(value).isoformat()
        if day>date.today().isoformat():
            raise ValueError('No se pueden registrar operaciones futuras de caja.')
        return day

    def editable(self, day):
        self.valid_day(day)
        if self.db.rows("SELECT 1 FROM cash_days WHERE day=? AND status='Cerrada'",(day,)):
            raise ValueError('La caja de esa fecha está cerrada. Reábrela con un motivo para corregirla.')

    def require_open(self, day):
        self.editable(day)
        if not self.db.rows("SELECT 1 FROM cash_days WHERE day=? AND status='Abierta'",(day,)):
            raise ValueError('Primero abre la caja de esta fecha desde Inicio o Caja y gastos.')

    def catalog(self, kind, name):
        if kind not in ('Empleado','Vehículo') or not name.strip():
            raise ValueError('Escribe un nombre válido.')
        with self.db.conn:
            return self.db.conn.execute('INSERT INTO cash_entities(kind,name) VALUES (?,?)',(kind,name.strip())).lastrowid

    def open_day(self, day, opening, responsible):
        from .service import cents
        day=self.valid_day(day); amount=cents(opening)
        if not responsible.strip(): raise ValueError('Escribe el responsable de caja.')
        with self.db.conn:
            if self.db.rows('SELECT 1 FROM cash_days WHERE day=?',(day,)):
                raise ValueError('Esta fecha ya tiene apertura registrada.')
            self.db.conn.execute('INSERT INTO cash_days(day,opening_cents,responsible) VALUES (?,?,?)',(day,amount,responsible.strip()))

    def add(self, day, category, amount, method, description, responsible, entity=None, period='', reference=''):
        from .service import cents
        day=self.valid_day(day); amount=cents(amount)
        if category not in CATEGORIES or method not in METHODS or amount<=0:
            raise ValueError('Selecciona categoría, método e importe mayor a cero.')
        if not description.strip() or not responsible.strip():
            raise ValueError('Escribe concepto y responsable de la captura.')
        if len(description)>500 or len(responsible)>100 or len(period)>200 or len(reference)>200:
            raise ValueError('Usa hasta 500 caracteres en concepto, 100 en responsable y 200 en periodo o referencia.')
        if category in ('Sueldos','Gasolina','Mantenimiento'):
            expected='Empleado' if category=='Sueldos' else 'Vehículo'
            if not self.db.rows('SELECT 1 FROM cash_entities WHERE id=? AND kind=?',(entity,expected)):
                raise ValueError('Selecciona el empleado o vehículo correspondiente.')
        if category=='Sueldos' and not period.strip(): raise ValueError('Indica el periodo de sueldo pagado.')
        with self.db.conn:
            self.editable(day)
            if not self.db.rows('SELECT 1 FROM cash_days WHERE day=?',(day,)):
                raise ValueError('Registra primero la apertura de caja de esta fecha.')
            return self.db.conn.execute('''INSERT INTO cash_movements(day,category,amount_cents,method,description,responsible,entity_id,period,reference)
                VALUES (?,?,?,?,?,?,?,?,?)''',(day,category,amount,method,description.strip(),responsible.strip(),entity,period.strip(),reference.strip())).lastrowid

    def cancel(self, key, reason, responsible):
        if not reason.strip() or not responsible.strip(): raise ValueError('Escribe motivo y responsable de la anulación.')
        with self.db.conn:
            rows=self.db.rows('SELECT * FROM cash_movements WHERE id=? AND cancelled_at IS NULL',(key,))
            if not rows: raise ValueError('Movimiento inexistente o ya anulado.')
            self.editable(rows[0]['day'])
            self.db.conn.execute('UPDATE cash_movements SET cancelled_at=CURRENT_TIMESTAMP,cancel_reason=?,cancel_by=? WHERE id=?',(reason.strip(),responsible.strip(),key))

    def report(self, start, end):
        start=self.valid_day(start);end=self.valid_day(end)
        if start>end: raise ValueError('El inicio debe ser anterior o igual al final.')
        entries=[]
        for r in self.db.rows('SELECT * FROM financial_payments WHERE paid_on BETWEEN ? AND ? ORDER BY paid_on,id',(start,end)):
            operation=f"Anticipo reservación {r['reservation_id']:06d}" if r['reservation_id'] else f"Renta {r['rental_id']:06d}"
            entries.append(dict(id=f"P{r['id']}",day=r['paid_on'],category='Cobro de renta',description=f"{operation} · {r['client_name']}",
                amount=r['amount_cents'],method=r['method'],direction=1,cancelled=bool(r['cancelled_at']),responsible='Cobro de renta',reference=r['reference'],
                cancel_reason=r['cancellation_reason'] or ''))
        for r in self.db.rows('''SELECT m.*,e.name FROM cash_movements m LEFT JOIN cash_entities e ON e.id=m.entity_id
                WHERE day BETWEEN ? AND ? ORDER BY day,m.id''',(start,end)):
            entries.append(dict(id=f"M{r['id']}",day=r['day'],category=r['category'],description=' · '.join(x for x in (r['description'],r['name'],r['period']) if x),
                amount=r['amount_cents'],method=r['method'],direction=1 if r['category'] in INCOME_CATEGORIES else -1,
                cancelled=bool(r['cancelled_at']),responsible=r['responsible'],reference=r['reference'],cancel_reason=r['cancel_reason'] or '',cancel_by=r['cancel_by'] or ''))
        active=[e for e in entries if not e['cancelled']]
        incoming={m:sum(e['amount'] for e in active if e['method']==m and e['direction']==1) for m in METHODS}
        outgoing={m:sum(e['amount'] for e in active if e['method']==m and e['direction']==-1) for m in METHODS}
        operating_income=sum(e['amount'] for e in active if e['direction']==1 and e['category']!='Aportación del dueño')
        expenses=sum(e['amount'] for e in active if e['direction']==-1 and e['category']!='Retiro del dueño')
        by_category={c:sum(e['amount'] for e in active if e['category']==c) for c in CATEGORIES}
        return dict(start=start,end=end,entries=sorted(entries,key=lambda e:(e['day'],e['id'])),incoming=incoming,outgoing=outgoing,
            operating_income=operating_income,expenses=expenses,net=operating_income-expenses,by_category=by_category)

    def day_report(self, day):
        result=self.report(day,day)
        rows=self.db.rows('SELECT * FROM cash_days WHERE day=?',(day,))
        opening=rows[0]['opening_cents'] if rows else 0
        result.update(opening=opening,status=rows[0]['status'] if rows else 'Sin apertura',
            expected=opening+result['incoming']['Efectivo']-result['outgoing']['Efectivo'])
        return result

    def close(self, day, counted, responsible, notes=''):
        from .service import cents
        counted=cents(counted)
        if not responsible.strip(): raise ValueError('Escribe quién realiza el corte.')
        conn=self.db.conn
        try:
            conn.execute('BEGIN IMMEDIATE')
            self.editable(day)
            result=self.day_report(day)
            if result['status']=='Sin apertura': raise ValueError('Registra primero la apertura.')
            difference=counted-result['expected']
            if difference and not notes.strip(): raise ValueError('Explica el faltante o sobrante antes de cerrar.')
            result.update(counted=counted,difference=difference,responsible=responsible.strip(),notes=notes.strip())
            key=conn.execute('INSERT INTO cash_closings(day,snapshot) VALUES (?,?)',(day,json.dumps(result,ensure_ascii=False))).lastrowid
            conn.execute("UPDATE cash_days SET status='Cerrada' WHERE day=?",(day,))
            conn.commit();return key
        except Exception:
            conn.rollback();raise

    def reopen(self, day, reason, responsible):
        if not reason.strip() or not responsible.strip(): raise ValueError('Escribe motivo y responsable de la reapertura.')
        with self.db.conn:
            if not self.db.rows("SELECT 1 FROM cash_days WHERE day=? AND status='Cerrada'",(day,)):
                raise ValueError('Esta caja no está cerrada.')
            self.db.conn.execute('INSERT INTO cash_reopenings(day,reason,responsible) VALUES (?,?,?)',(day,reason.strip(),responsible.strip()))
            self.db.conn.execute("UPDATE cash_days SET status='Abierta' WHERE day=?",(day,))
