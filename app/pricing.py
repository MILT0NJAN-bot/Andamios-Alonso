"""Tarifas en centavos, compartidas por notas, capturas y estadísticas."""


def unit_total(row, days):
    if days < 1:
        raise ValueError('La renta debe durar al menos un día.')
    if row['pricing_mode'] == 'scaffold':
        if days < 7:
            raise ValueError('Este equipo se renta por un mínimo de 7 días.')
        months, extra = divmod(days, 30)
        if months and row['month_cents']:
            return months*row['month_cents']+extra*row['price_cents']
        return row['week_cents']+(days-7)*row['price_cents']
    if row['price_cents'] <= 0:
        raise ValueError('Este equipo todavía no tiene precio configurado.')
    return days*row['price_cents']


def tariff_label(row):
    from .service import money
    if row['pricing_mode'] == 'scaffold':
        if not row['month_cents']:
            return f"7 días {money(row['week_cents'])} · extra {money(row['price_cents'])}/día"
        return f"7 días {money(row['week_cents'])} · extra {money(row['price_cents'])}/día · 30 días {money(row['month_cents'])}"
    return f"{money(row['price_cents'])}/día" if row['price_cents'] else 'Precio pendiente'


def line_charge(db,line,days):
    """Las piezas recibidas conservan el periodo que tenían al devolverse."""
    returns=db.rows('SELECT quantity,unit_cents FROM rental_returns WHERE line_id=?',(line['id'],))
    if not returns:
        return unit_total(line,days)*line['quantity']
    return sum(r['quantity']*r['unit_cents'] for r in returns)+(line['quantity']-sum(r['quantity'] for r in returns))*unit_total(line,days)
