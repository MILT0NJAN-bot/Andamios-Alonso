"""Carátula de entrega y cuidado del equipo, adaptada a Alonso."""
from datetime import date
from html import escape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Table,TableStyle,Paragraph,Spacer,Image,KeepTogether
from .business import OWNER,PHONE,RFC,BANK_ACCOUNT_NAME,ACCOUNT,CLABE,BANK_CLIENT
from .resources import LOGO_PATH
from .pricing import unit_total,line_charge,tariff_label
from .service import Service,money

NAVY=colors.HexColor('#203F78')
PALE=colors.HexColor('#EDF3FC')
ORANGE=colors.HexColor('#FFF0E5')


def main_note(db,key,width):
    rows=db.rows('SELECT * FROM rentals WHERE id=?',(key,))
    if not rows:
        raise ValueError('La renta no existe.')
    rental=rows[0]
    lines=db.rows('SELECT * FROM rental_lines WHERE rental_id=? ORDER BY id',(key,))
    payment=Service(db).payment_summary(key)
    normal=ParagraphStyle('NoteBody',fontName='Helvetica',fontSize=8.5,leading=11,textColor=NAVY)
    bold=ParagraphStyle('NoteBold',parent=normal,fontName='Helvetica-Bold')
    small=ParagraphStyle('NoteSmall',parent=normal,fontSize=8,leading=10)
    white=ParagraphStyle('NoteWhite',parent=bold,textColor=colors.white,alignment=1)
    def p(text,style=normal):
        return Paragraph(escape(str(text)).replace('\n','<br/>'),style)
    def table(data,widths,*,header=False):
        result=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1 if header else 0)
        result.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        return result
    story=[]
    logo=Image(str(LOGO_PATH),width=98,height=98,mask='auto')
    header=table([[logo,p('RENTA DE ANDAMIOS\nY MAQUINARIA LIGERA',bold),p(f'NOTA DE RENTA\nFOLIO {key:06d}\nSalida: {date.fromisoformat(rental["departure"]).strftime("%d/%m/%Y")}',bold)]],[112,width-268,156])
    story.extend([header,Spacer(1,5)])
    bar=table([[p('ALONSO · ENTREGA, RENTA Y CUIDADO DEL EQUIPO',white)]],[width])
    bar.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),NAVY)]))
    story.extend([bar,Spacer(1,8)])
    customer=table([
        [p('CLIENTE',bold),p(rental['client_name']),p('TELÉFONO',bold),p(rental['client_phone'])],
        [p('OBRA / ENTREGA',bold),p(rental['work_address']),p('DEVOLUCIÓN',bold),p(date.fromisoformat(rental['due']).strftime('%d/%m/%Y'))],
        [p('DÍAS DE RENTA',bold),p(rental['days']),p('FACTURA',bold),p('Solicitada · IVA 16%' if rental['vat_bp'] else 'No solicitada · Sin IVA')],
        [p('TOTAL PIEZAS',bold),p(sum(line['quantity'] for line in lines)),p('ESTADO',bold),p('Devuelta' if rental['returned_at'] else ('Activa · Devolución parcial' if any(line['returned_qty'] for line in lines) else 'Activa'))],
    ],[94,width-306,80,132])
    customer.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),PALE),('BACKGROUND',(2,0),(2,-1),PALE),('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#D4DEEC'))]))
    story.extend([customer,Spacer(1,10)])
    heading=table([[p('OBJETOS DADOS EN RENTA',white)]],[width])
    heading.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),NAVY)]))
    story.append(heading)
    data=[[p(value,white) for value in ('PIEZAS','DESCRIPCIÓN DEL EQUIPO','DÍAS','PRECIO\nPERIODO','IMPORTE\nRENTA','VALOR\nEQUIPO')]]
    for line in lines:
        base=unit_total(line,rental['days'])
        charge=line_charge(db,line,rental['days'])
        value=line['replacement_cents']
        info=f"{line['item_name']}\n{tariff_label(line)}\nDevueltas: {line['returned_qty']} · Pendientes: {line['quantity']-line['returned_qty']}"
        info+=f"\nValor por pieza: {money(value)}" if value is not None else '\nValor por pieza: por definir'
        data.append([p(line['quantity'],bold),p(info,small),p(rental['days']),p(money(base) if charge==base*line['quantity'] else 'Periodos distintos'),
            p(money(charge),bold),p(money(value*line['quantity']) if value is not None else 'Por definir',bold)])
    equipment=table(data,[48,width-332,40,74,82,88],header=True)
    equipment.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('GRID',(0,1),(-1,-1),.35,colors.HexColor('#D4DEEC')),
        ('BACKGROUND',(0,1),(0,-1),ORANGE),('BACKGROUND',(5,1),(5,-1),ORANGE)]))
    story.extend([equipment,Spacer(1,10)])
    complete=all(line['replacement_cents'] is not None for line in lines)
    equipment_total=sum((line['replacement_cents'] or 0)*line['quantity'] for line in lines)
    info=table([[p('VALOR TOTAL DEL EQUIPO ENTREGADO',bold),p(money(equipment_total) if complete else 'Por definir: faltan valores de equipo',bold)]],[width-190,190])
    info.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),ORANGE)]))
    story.append(info)
    totals=[['RENTA DE EQUIPOS',money(rental['subtotal_cents']-rental['freight_cents']-rental['plank_cents'])]]
    if rental['freight_cents']:
        totals.append(['FLETE',money(rental['freight_cents'])])
    if rental['extra_planks']:
        totals.append([f"TABLONES EXTRA ({rental['extra_planks']} x $50)",money(rental['plank_cents'])])
    totals.append(['SUBTOTAL',money(rental['subtotal_cents'])])
    if rental['vat_bp']:
        totals.append(['IVA 16%',money(rental['vat_cents'])])
    totals.extend([['TOTAL DE RENTA',money(rental['total_cents'])],['PAGADO',money(payment['paid_cents'])],['SALDO PENDIENTE',money(payment['pending_cents'])]])
    if payment['credit_cents']:
        totals.append(['SALDO A FAVOR',money(payment['credit_cents'])])
    amount_table=table([[p(label,bold),p(value,bold)] for label,value in totals],[190,100])
    amount_table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('ALIGN',(1,0),(1,-1),'RIGHT')]))
    amount_table.hAlign='RIGHT'
    story.extend([Spacer(1,6),amount_table,Spacer(1,10)])
    care=p('CUIDADO Y RECEPCIÓN DEL EQUIPO',bold)
    instructions=p('El valor del equipo muestra su costo completo para conocimiento del cliente y cuidado del material. '
        'Es informativo: no se suma a la renta, no es un depósito ni genera un cargo automático. '
        'Al recibir, revisa cantidad, accesorios y estado. Evita usos distintos al previsto y reporta daños o faltantes. '
        'Las observaciones de entrega y las devoluciones se detallan en el anexo. Esta nota no sustituye un comprobante fiscal.',small)
    story.extend([care,Spacer(1,4),instructions,Spacer(1,8)])
    bank=table([[p(f'{BANK_ACCOUNT_NAME} · {OWNER}',bold)],
        [p(f'Cuenta: {ACCOUNT}   ·   CLABE: {CLABE}   ·   RFC: {RFC}\nNo. de cliente BBVA: {BANK_CLIENT}',small)]],[width])
    bank.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE)]))
    story.extend([bank,Spacer(1,18)])
    signatures=table([[p('________________________________'),p('________________________________')],
        [p('CLIENTE · NOMBRE Y FIRMA',bold),p('ENTREGA · ALONSO',bold)]],[width/2,width/2])
    story.append(KeepTogether([signatures]))
    return story
