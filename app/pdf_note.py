"""PDF generado directamente desde la misma plantilla de la nota Excel."""
from datetime import date,datetime
from decimal import Decimal,ROUND_HALF_UP
from html import escape
from pathlib import Path
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT,TA_CENTER,TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,PageBreak
from .excel_note import build_workbook
from .service import money
from .rental_document import main_note


def rgb(color,default):
    if color is not None and color.type=='rgb' and isinstance(color.rgb,str):
        return colors.HexColor('#'+color.rgb[-6:])
    return colors.HexColor('#'+default.lstrip('#'))


def display(cell):
    value=cell.value
    if value is None:
        return ''
    if isinstance(value,(date,datetime)):
        return value.strftime('%d/%m/%Y')
    if isinstance(value,(int,float)) and '$' in cell.number_format:
        amount=int((Decimal(str(value))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        return '-'+money(-amount) if amount<0 else money(amount)
    return str(value)


def export_pdf(db,rental_id,destination):
    path=Path(destination)
    if path.suffix.lower()!='.pdf':
        raise ValueError('Guarda la nota con extensión .pdf.')
    if path.resolve()==db.path.resolve():
        raise ValueError('Elige un archivo distinto de la base de datos.')
    workbook=build_workbook(db,rental_id)
    # Cada hoja usa la misma estructura, combinaciones, colores y datos que Excel.
    document=SimpleDocTemplate(str(path),pagesize=letter,rightMargin=28,leftMargin=28,topMargin=24,bottomMargin=28,
        title=f'Alonso · Nota de renta {rental_id:06d}',author='Miguel Ángel Alonso Justo')
    story=main_note(db,rental_id,document.width)
    try:
        for index,sheet in enumerate(workbook.worksheets):
            if index==0:
                continue
            long_notes=[]
            if index:
                story.append(PageBreak())
                story.append(Paragraph(escape(sheet.title),ParagraphStyle('Section',fontName='Helvetica-Bold',fontSize=13,leading=18,spaceAfter=12,textColor=colors.HexColor('#203F78'))))
            max_col=sheet.max_column
            widths=[(sheet.column_dimensions[get_column_letter(c)].width or 13)*5.25 for c in range(1,max_col+1)]
            scale=document.width/sum(widths)
            widths=[w*scale for w in widths]
            merged={}
            spans=[]
            for region in sheet.merged_cells.ranges:
                spans.append(('SPAN',(region.min_col-1,region.min_row-1),(region.max_col-1,region.max_row-1)))
                merged[(region.min_row,region.min_col)]=region.max_col
            data=[];heights=[];commands=spans[:]
            for r in range(1,sheet.max_row+1):
                row=[]
                height=(sheet.row_dimensions[r].height or 15)*min(scale,.65)
                for c in range(1,max_col+1):
                    cell=sheet.cell(r,c)
                    value=display(cell)
                    if len(value)>350:
                        long_notes.append((f'{sheet.title} · Registro {r}',value))
                        value=value[:220]+'... (continúa en notas ampliadas)'
                    font_size=max(7.5,(cell.font.sz or 10)*min(scale,1))
                    font='Helvetica-Bold' if cell.font.bold else 'Helvetica'
                    align={'left':TA_LEFT,'center':TA_CENTER,'right':TA_RIGHT}.get(cell.alignment.horizontal,TA_LEFT)
                    paragraph=Paragraph(escape(value).replace('\n','<br/>').replace('→',' a '),
                        ParagraphStyle(f'cell{index}-{r}-{c}',fontName=font,fontSize=font_size,leading=font_size*1.15,textColor=rgb(cell.font.color,'203F78'),alignment=align,
                                       splitLongWords=True))
                    span_end=merged.get((r,c),c)
                    if value:
                        _,required=paragraph.wrap(max(5,sum(widths[c-1:span_end])-8),10000)
                        height=max(height,required+5)
                    row.append(paragraph)
                    if cell.fill.patternType=='solid':
                        commands.append(('BACKGROUND',(c-1,r-1),(c-1,r-1),rgb(cell.fill.fgColor,'FFFFFF')))
                    if cell.border.bottom.style:
                        commands.append(('LINEBELOW',(c-1,r-1),(c-1,r-1),.35,colors.HexColor('#D4DEEC')))
                data.append(row);heights.append(height)
            commands.extend([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
                ('TOPPADDING',(0,0),(-1,-1),2.5),('BOTTOMPADDING',(0,0),(-1,-1),2.5)])
            table=Table(data,colWidths=widths,rowHeights=heights,repeatRows=11 if index==0 else 2,splitByRow=1,hAlign='LEFT')
            table.setStyle(TableStyle(commands))
            story.append(table)
            if long_notes:
                story.append(PageBreak())
                for label,value in long_notes:
                    story.append(Paragraph(escape(label)+' · Notas ampliadas',ParagraphStyle('LongHeading',fontName='Helvetica-Bold',fontSize=11,leading=15,spaceAfter=10)))
                    story.append(Paragraph(escape(value).replace('\n','<br/>'),ParagraphStyle('LongNote',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=16)))
        def footer(canvas,doc):
            canvas.saveState()
            canvas.setFont('Helvetica',8)
            canvas.setFillColor(colors.HexColor('#64748B'))
            canvas.drawString(28,14,f'Alonso · Nota {rental_id:06d}')
            canvas.drawRightString(letter[0]-28,14,f'Página {doc.page}')
            canvas.restoreState()
        document.build(story,onFirstPage=footer,onLaterPages=footer)
    finally:
        workbook.close()
    return path
