"""Nota de renta Excel, lista para imprimir y sin dependencia de Microsoft Excel."""
from datetime import date
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.worksheet.page import PageMargins
from openpyxl.workbook.properties import CalcProperties
from .pricing import unit_total, tariff_label, line_charge
from .service import Service
from .taxes import percent
from .business import OWNER,RFC,BANK_ACCOUNT_NAME,ACCOUNT,CLABE,BANK_CLIENT

NAVY = '203F78'
ORANGE = 'F47724'
PALE = 'EDF3FC'
GRAY = '64748B'
MONEY = '"$"#,##0.00;[Red]-"$"#,##0.00'


def export_note(db, rental_id, destination):
    path = Path(destination)
    if path.suffix.lower() != '.xlsx':
        raise ValueError('Guarda la nota con la extensión .xlsx.')
    if path.resolve() == db.path.resolve():
        raise ValueError('El archivo de destino debe ser distinto de la base de datos.')
    wb=build_workbook(db,rental_id)
    try:
        wb.save(path)
    finally:
        wb.close()
    return path


def build_workbook(db,rental_id):
    rows = db.rows('SELECT * FROM rentals WHERE id=?', (rental_id,))
    if not rows:
        raise ValueError('La renta no existe.')
    rental = rows[0]
    lines = db.rows('SELECT * FROM rental_lines WHERE rental_id=? ORDER BY id', (rental_id,))
    extensions = db.rows('SELECT * FROM rental_extensions WHERE rental_id=? ORDER BY id', (rental_id,))
    payments = db.rows('SELECT * FROM financial_payments WHERE rental_id=? ORDER BY paid_on,id',(rental_id,))
    summary=Service(db).payment_summary(rental_id)
    received=db.rows('SELECT r.*,l.item_name FROM rental_returns r JOIN rental_lines l ON l.id=r.line_id WHERE r.rental_id=? ORDER BY r.id',(rental_id,))
    wb = Workbook()
    wb.properties.creator = 'Alonso · Control de rentas'
    wb.properties.title = f'Nota de renta {rental_id:06d}'
    wb.calculation = CalcProperties(calcId=191029, fullCalcOnLoad=True)
    sheet = wb.active
    sheet.title = 'Nota de renta'
    sheet.sheet_view.showGridLines = False
    widths = {'A':10, 'B':16, 'C':13, 'D':13, 'E':10, 'F':10, 'G':12, 'H':18, 'I':19}
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width

    def block(row, first, last, value, *, bold=False, size=10, color=NAVY, fill=None, align='left', height=None):
        if first != last:
            sheet.merge_cells(start_row=row,start_column=first,end_row=row,end_column=last)
        cell=sheet.cell(row,first,value)
        # Los textos capturados por el usuario nunca se interpretan como fórmulas.
        if isinstance(value,str):
            cell.data_type='s'
        cell.font=Font(name='Calibri',size=size,bold=bold,color=color)
        cell.alignment=Alignment(horizontal=align,vertical='center',wrap_text=True)
        for col in range(first,last+1):
            if fill:
                sheet.cell(row,col).fill=PatternFill('solid',fgColor=fill)
        if height:
            sheet.row_dimensions[row].height=height
        return cell

    block(1,1,6,'Alonso',bold=True,size=32,color=ORANGE,height=44)
    block(1,7,9,'NOTA DE RENTA',bold=True,size=15,align='right')
    block(2,1,6,'RENTA DE ANDAMIOS Y MAQUINARIA LIGERA',bold=True,size=11,height=24)
    block(2,7,9,f'FOLIO  {rental_id:06d}',bold=True,size=14,align='right')
    block(3,1,6,'Informes y cotizaciones · Cel. 312 298 32 50',color=GRAY,height=23)
    block(3,7,9,'Moneda: MXN',align='right',color=GRAY)
    block(4,1,9,'CONTROL DE ENTREGA Y RENTA DE EQUIPO',bold=True,color='FFFFFF',fill=NAVY,align='center',height=25)
    block(6,1,2,'CLIENTE',bold=True,fill=PALE,height=30)
    block(6,3,6,rental['client_name'])
    block(6,7,7,'TELÉFONO',bold=True,size=9,fill=PALE)
    block(6,8,9,rental['client_phone'])
    block(7,1,2,'OBRA / ENTREGA',bold=True,fill=PALE,height=48)
    block(7,3,9,rental['work_address'])
    block(8,1,2,'FECHA DE SALIDA',bold=True,fill=PALE,height=28)
    block(8,3,4,date.fromisoformat(rental['departure'])).number_format='dd/mm/yyyy'
    block(8,5,6,'DEVOLUCIÓN ESTIMADA',bold=True,fill=PALE)
    block(8,7,9,date.fromisoformat(rental['due'])).number_format='dd/mm/yyyy'
    block(9,1,2,'DÍAS CONTRATADOS',bold=True,fill=PALE,height=28)
    block(9,3,4,rental['days'])
    block(9,5,6,'ESTADO',bold=True,fill=PALE)
    status=('Devuelta el '+date.fromisoformat(rental['returned_at']).strftime('%d/%m/%Y') if rental['returned_at']
            else ('Vencida' if rental['due'] < date.today().isoformat() else 'Activa'))
    block(9,7,9,status)
    block(10,1,2,'TOTAL DE PIEZAS',bold=True,fill=PALE,height=28)
    block(10,3,4,sum(line['quantity'] for line in lines),bold=True,size=14)
    block(10,5,6,'TIPOS DE EQUIPO',bold=True,fill=PALE)
    block(10,7,9,len(lines))

    headings=[(1,1,'No.'),(2,4,'EQUIPO / TARIFA CONTRATADA'),(5,6,'PIEZAS'),(7,7,'DÍAS'),(8,8,'PRECIO POR PIEZA\nDEL PERIODO'),(9,9,'IMPORTE')]
    for first,last,title in headings:
        block(11,first,last,title,bold=True,color='FFFFFF',fill=NAVY,align='center',height=32)
    thin=Side(style='thin',color='D4DEEC')
    row=12
    for index,line in enumerate(lines,1):
        amount=unit_total(line,rental['days'])
        total_line=line_charge(db,line,rental['days'])
        fill='F5F8FC' if index%2 else 'FFFFFF'
        block(row,1,1,index,align='center',fill=fill,height=66)
        block(row,2,4,f"{line['item_name']}\n{tariff_label(line)}\nDevueltas: {line['returned_qty']} · Pendientes: {line['quantity']-line['returned_qty']}",fill=fill,size=10)
        block(row,5,6,line['quantity'],align='center',fill='FFF0E5',bold=True,size=16,color=NAVY).number_format='0'
        block(row,7,7,rental['days'],align='center',fill=fill)
        block(row,8,8,amount/100 if total_line==amount*line['quantity'] else 'Periodos distintos',align='right',fill=fill).number_format=MONEY
        block(row,9,9,total_line/100,align='right',fill=fill).number_format=MONEY
        for col in range(1,10):
            sheet.cell(row,col).border=Border(bottom=thin)
        row+=1
    row+=1
    for title,amount in [('SUBTOTAL',rental['subtotal_cents']),
                         (f"IVA {percent(rental['vat_bp'])}",rental['vat_cents']),
                         (f"ISR RETENIDO {percent(rental['isr_bp'])}",-rental['isr_cents'])]:
        block(row,6,8,title,bold=True,fill=PALE,height=25,align='right')
        block(row,9,9,amount/100,align='right',fill=PALE).number_format=MONEY
        row+=1
    block(row,6,8,'TOTAL DE RENTA · MXN',bold=True,color='FFFFFF',fill=NAVY,height=32,align='right')
    block(row,9,9,rental['total_cents']/100,bold=True,size=13,color='FFFFFF',fill=NAVY,align='right').number_format=MONEY
    for title,amount in [('PAGADO · MXN',summary['paid_cents']),('SALDO PENDIENTE · MXN',summary['pending_cents'])]:
        row+=1
        block(row,6,8,title,bold=True,fill=PALE,height=27,align='right')
        block(row,9,9,amount/100,bold=True,size=12,fill=PALE,align='right').number_format=MONEY
    row+=1
    block(row,6,9,summary['status'],bold=True,align='right',height=24)
    row+=2
    block(row,1,9,'OBSERVACIONES Y CONDICIONES DE LA NOTA',bold=True,fill=PALE,height=25)
    notes=[
        'El importe es piezas × precio por pieza del periodo completo. Las tarifas se describen por equipo; el mes de renta corresponde a 30 días.',
        'El total incluye ampliaciones confirmadas. Pagado considera solo pagos no anulados. Esta nota no sustituye un comprobante fiscal.',
    ]
    if extensions or payments:
        notes.append('El detalle de ampliaciones y pagos se incluye en las secciones anexas de la nota.')
    if received:
        notes.append('Las piezas recibidas y su estado se detallan en «Estado y devoluciones». Las devueltas no generan días de ampliación posteriores; el periodo original se conserva.')
    for note in notes:
        row+=1
        block(row,1,9,note,size=10,color=GRAY,height=30)
    row+=2
    block(row,1,9,f'{BANK_ACCOUNT_NAME} · {OWNER.upper()}',bold=True,align='center',fill=PALE,height=28)
    row+=1
    block(row,1,5,f'CLABE: {CLABE}',bold=True,fill=PALE,height=26)
    block(row,6,9,f'No. de cuenta: {ACCOUNT}',bold=True,fill=PALE)
    row+=1
    block(row,1,5,f'RFC: {RFC}',bold=True,fill=PALE,height=26)
    block(row,6,9,f'No. de cliente BBVA: {BANK_CLIENT}',bold=True,fill=PALE)
    row+=2
    block(row,1,4,'________________________________',align='center',height=24)
    block(row,6,9,'________________________________',align='center')
    row+=1
    block(row,1,4,'RECIBÍ EQUIPO · NOMBRE Y FIRMA DEL CLIENTE',bold=True,size=9,align='center',height=25)
    block(row,6,9,f'ENTREGÓ · {OWNER.upper()}',bold=True,size=9,align='center')
    row+=2
    block(row,1,9,'ALONSO · RENTA DE ANDAMIOS Y MAQUINARIA LIGERA · 312 298 32 50',size=9,align='center',color=GRAY,height=22)
    sheet.print_area=f'A1:I{row}'
    sheet.print_title_rows='1:11'
    sheet.freeze_panes=None
    sheet.sheet_properties.pageSetUpPr.fitToPage=True
    sheet.page_setup.orientation='portrait'
    sheet.page_setup.paperSize=sheet.PAPERSIZE_LETTER
    sheet.page_setup.fitToWidth=1
    sheet.page_setup.fitToHeight=0
    sheet.page_margins=PageMargins(left=.3,right=.3,top=.4,bottom=.4,header=.15,footer=.15)
    sheet.print_options.horizontalCentered=True
    sheet.oddFooter.center.text='Alonso · Nota de renta'
    sheet.oddFooter.right.text='Página &P de &N'
    if extensions:
        extra=wb.create_sheet('Ampliaciones')
        extra.sheet_view.showGridLines=False
        extra.append([f'ALONSO · NOTA {rental_id:06d} · AMPLIACIONES INCLUIDAS EN EL TOTAL'])
        extra.merge_cells('A1:F1')
        extra['A1'].font=Font(name='Calibri',bold=True,size=14,color=NAVY)
        extra.row_dimensions[1].height=32
        extra.append(['Registro','Devolución anterior','Nueva devolución','Días agregados','Ajuste MXN','Fecha de registro'])
        for cell in extra[2]:
            cell.font=Font(name='Calibri',bold=True,color='FFFFFF')
            cell.fill=PatternFill('solid',fgColor=NAVY)
        for index,extension in enumerate(extensions,1):
            adjustment=extension['adjustment_cents'] if extension['adjustment_cents'] is not None else extension['added_cents']
            extra.append([index,date.fromisoformat(extension['previous_due']),date.fromisoformat(extension['new_due']),extension['added_days'],adjustment/100,extension['created_at']])
            extra.cell(index+2,2).number_format='dd/mm/yyyy'
            extra.cell(index+2,3).number_format='dd/mm/yyyy'
            extra.cell(index+2,5).number_format=MONEY
        for col,width in [('A',12),('B',25),('C',25),('D',18),('E',22),('F',26)]:
            extra.column_dimensions[col].width=width
        extra.freeze_panes=None
        extra.auto_filter.ref=f'A2:F{extra.max_row}'
        extra.sheet_properties.pageSetUpPr.fitToPage=True
        extra.page_setup.orientation='landscape'
        extra.page_setup.paperSize=extra.PAPERSIZE_LETTER
        extra.page_setup.fitToWidth=1
        extra.page_setup.fitToHeight=0
        extra.print_title_rows='1:2'
        extra.print_area=f'A1:F{extra.max_row}'
    if payments:
        ledger=wb.create_sheet('Pagos')
        ledger.sheet_view.showGridLines=False
        ledger.append([f'ALONSO · NOTA {rental_id:06d} · HISTORIAL DE PAGOS'])
        ledger.merge_cells('A1:I1')
        ledger['A1'].font=Font(name='Calibri',size=14,bold=True,color=NAVY)
        ledger.row_dimensions[1].height=32
        ledger.append(['ID','Fecha','Tipo','Método','Importe MXN','Referencia','Estado','Fecha de anulación','Motivo de anulación'])
        for cell in ledger[2]:
            cell.font=Font(name='Calibri',bold=True,color='FFFFFF')
            cell.fill=PatternFill('solid',fgColor=NAVY)
        for payment in payments:
            ledger.append([payment['id'],date.fromisoformat(payment['paid_on']),payment['kind'],payment['method'],payment['amount_cents']/100,
                payment['reference'],'Anulado' if payment['cancelled_at'] else 'Registrado',payment['cancelled_at'],payment['cancellation_reason']])
            for cell in ledger[ledger.max_row]:
                if isinstance(cell.value,str):
                    cell.data_type='s'
                cell.font=Font(name='Calibri',size=10,color=NAVY)
                cell.alignment=Alignment(vertical='center',wrap_text=True)
            ledger.cell(ledger.max_row,2).number_format='dd/mm/yyyy'
            ledger.cell(ledger.max_row,5).number_format=MONEY
            ledger.row_dimensions[ledger.max_row].height=34
        for col,width in [('A',9),('B',15),('C',17),('D',19),('E',18),('F',30),('G',16),('H',24),('I',32)]:
            ledger.column_dimensions[col].width=width
        ledger.auto_filter.ref=f'A2:I{ledger.max_row}'
        ledger.freeze_panes=None
        ledger.sheet_properties.pageSetUpPr.fitToPage=True
        ledger.page_setup.orientation='landscape'
        ledger.page_setup.paperSize=ledger.PAPERSIZE_LETTER
        ledger.page_setup.fitToWidth=1
        ledger.page_setup.fitToHeight=0
        ledger.print_title_rows='1:2'
        ledger.print_area=f'A1:I{ledger.max_row}'
    states=wb.create_sheet('Estado y devoluciones')
    states.sheet_view.showGridLines=False
    states.append([f'ALONSO · NOTA {rental_id:06d} · ESTADO DE LOS EQUIPOS'])
    states.merge_cells('A1:G1')
    states.append(['Equipo','Entregadas','Devueltas','Pendientes','Estado al entregar','Notas de entrega',''])
    for line in lines:
        states.append([line['item_name'],line['quantity'],line['returned_qty'],line['quantity']-line['returned_qty'],line['delivery_condition'],line['delivery_notes'],''])
    states.append([])
    states.append(['DEVOLUCIONES REGISTRADAS'])
    states.append(['Fecha','Equipo','Piezas recibidas','Estado al recibir','Notas (opcional)','Precio por pieza al recibir',''])
    for event in received:
        states.append([date.fromisoformat(event['returned_on']),event['item_name'],event['quantity'],event['condition'],event['notes'],event['unit_cents']/100,''])
        states.cell(states.max_row,1).number_format='dd/mm/yyyy'
        states.cell(states.max_row,6).number_format=MONEY
    for cells in states:
        for cell in cells:
            if isinstance(cell.value,str):
                cell.data_type='s'
            cell.font=Font(name='Calibri',size=10,color=NAVY)
            cell.alignment=Alignment(vertical='center',wrap_text=True)
        states.row_dimensions[cells[0].row].height=32
    for header in (1,2,4+len(lines),5+len(lines)):
        for cell in states[header]:
            cell.font=Font(name='Calibri',bold=True,color='FFFFFF')
            cell.fill=PatternFill('solid',fgColor=NAVY)
    for col,width in [('A',27),('B',27),('C',18),('D',20),('E',30),('F',32),('G',4)]:
        states.column_dimensions[col].width=width
    states.freeze_panes=None
    states.sheet_properties.pageSetUpPr.fitToPage=True
    states.page_setup.orientation='landscape'
    states.page_setup.paperSize=states.PAPERSIZE_LETTER
    states.page_setup.fitToWidth=1
    states.page_setup.fitToHeight=0
    states.print_area=f'A1:F{states.max_row}'
    return wb
