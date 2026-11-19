from html import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape,letter
from .service import money


def export_cash(report, path):
    styles=getSampleStyleSheet()
    body=styles['BodyText'];body.fontSize=8;body.leading=11
    p=lambda text:Paragraph(escape(str(text)),body)
    story=[Paragraph('ALONSO · CAJA Y GASTOS',styles['Title']),p(f"Periodo: {report['start']} al {report['end']} · MXN"),Spacer(1,10)]
    if 'counted' in report:
        story.extend([p(f"CORTE CERRADO · Responsable: {report['responsible']}"),p(f"Fondo inicial: {money(report['opening'])} · Esperado: {money(report['expected'])} · Contado: {money(report['counted'])} · Diferencia: {money(report['difference'])}"),p('Observaciones: '+report['notes']),Spacer(1,8)])
    else:
        story.append(p('REPORTE DE CONSULTA · No sustituye un corte cerrado.'))
        if 'expected' in report:
            story.append(p(f"Estado de caja: {report['status']} · Fondo inicial: {money(report['opening'])} · Efectivo que debe haber en caja: {money(report['expected'])}"))
    story.append(p(f"Ingresos operativos: {money(report['operating_income'])} · Gastos: {money(report['expenses'])} · Flujo operativo: {money(report['net'])}"))
    for method in report['incoming']:
        story.append(p(f"{method}: entradas {money(report['incoming'][method])} · salidas {money(report['outgoing'][method])}"))
    for category,value in report.get('by_category',{}).items():
        if value:story.append(p(f'{category}: {money(value)}'))
    story.extend([p('Fondo inicial y aportaciones no son ventas. Los retiros del dueño se separan del gasto operativo. Flujo de efectivo no equivale a utilidad contable.'),Spacer(1,12)])
    data=[[p(x) for x in ('Fecha / ID','Categoría / método','Concepto / referencia','Responsable','Entrada','Salida','Estado')]]
    for e in report['entries']:
        reason=(' · Anulación: '+e.get('cancel_reason','')+' · '+e.get('cancel_by','')) if e['cancelled'] else ''
        data.append([p(e['day']+' / '+e['id']),p(e['category']+' / '+e['method']),p(e['description']+' '+e['reference']+reason),p(e['responsible']),p(money(e['amount']) if e['direction']==1 else ''),p(money(e['amount']) if e['direction']==-1 else ''),p('Anulado' if e['cancelled'] else 'Vigente')])
    table=Table(data,colWidths=[90,110,220,80,70,70,65],repeatRows=1,splitInRow=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF0F7')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.lightgrey),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(table)
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawRightString(755,20,f'Alonso · Página {doc.page}')
    SimpleDocTemplate(str(path),pagesize=landscape(letter),leftMargin=36,rightMargin=36,topMargin=30,bottomMargin=36).build(story,onFirstPage=footer,onLaterPages=footer)
