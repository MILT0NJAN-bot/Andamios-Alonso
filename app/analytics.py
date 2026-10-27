from datetime import date, timedelta
from collections import defaultdict


def report(db, start, end):
    if end < start or (end-start).days > 365:
        raise ValueError('Selecciona un periodo de hasta 366 días, con inicio anterior al final.')
    days = {start+timedelta(days=i): {'rentals':0,'units':0,'in_use':0,'expected_cents':0}
            for i in range((end-start).days+1)}
    popular = defaultdict(int)
    rentals = db.rows('SELECT * FROM rentals WHERE departure<=?',(end.isoformat(),))
    lines_by_rental = defaultdict(list)
    for line in db.rows('SELECT * FROM rental_lines'):
        lines_by_rental[line['rental_id']].append(line)
    returns_by_line=defaultdict(list)
    for received in db.rows('SELECT * FROM rental_returns'):
        returns_by_line[received['line_id']].append(received)
    for rental in rentals:
        departure, due = date.fromisoformat(rental['departure']), date.fromisoformat(rental['due'])
        lines = lines_by_rental[rental['id']]
        units = sum(line['quantity'] for line in lines)
        if departure in days:
            days[departure]['rentals'] += 1
            days[departure]['units'] += units
            for line in lines:
                popular[(line['item_id'],line['item_name'])] += line['quantity']
        occupied_end = date.fromisoformat(rental['returned_at']) if rental['returned_at'] else max(due,date.today()+timedelta(days=1))
        occupied_end = max(occupied_end,departure+timedelta(days=1))
        daily, remainder = divmod(rental['total_cents'],rental['days'])
        for current, values in days.items():
            if departure <= current < occupied_end:
                for line in lines:
                    returned=sum(r['quantity'] for r in returns_by_line[line['id']]
                        if max(date.fromisoformat(r['returned_on']),departure+timedelta(days=1))<=current)
                    values['in_use']+=max(0,line['quantity']-returned)
            if departure <= current < due:
                offset = (current-departure).days
                values['expected_cents'] += daily+(1 if offset < remainder else 0)
    # Agrupar por ID para mantener unido un producto aunque se haya renombrado.
    merged = {}
    for (key,name),quantity in popular.items():
        merged.setdefault(key,{'name':name,'units':0})['units'] += quantity
    return {'days':days, 'popular':sorted(merged.values(),key=lambda r:r['units'],reverse=True),
            'current_units':db.rows('SELECT COALESCE(SUM(l.quantity-l.returned_qty),0) FROM rental_lines l JOIN rentals r ON r.id=l.rental_id WHERE r.returned_at IS NULL')[0][0]}
