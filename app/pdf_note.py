"""Nota de renta principal en una sola hoja, sin anexos."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate,KeepInFrame
from .rental_document import main_note


def export_pdf(db,rental_id,destination):
    path=Path(destination)
    if path.suffix.lower()!='.pdf':
        raise ValueError('Guarda la nota con extension .pdf.')
    if path.resolve()==db.path.resolve():
        raise ValueError('Elige un archivo distinto de la base de datos.')
    document=SimpleDocTemplate(str(path),pagesize=letter,rightMargin=28,leftMargin=28,topMargin=24,bottomMargin=28,
        title=f'Alonso - Nota de renta {rental_id:06d}',author='Miguel Angel Alonso Justo')
    # Mantener todos los equipos y totales de la nota; ajustar si exceden una hoja.
    story=[KeepInFrame(document.width-12,document.height-12,main_note(db,rental_id,document.width-12),mode='shrink',hAlign='LEFT',vAlign='TOP')]
    def footer(canvas,doc):
        canvas.saveState()
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawString(28,14,f'Alonso - Nota {rental_id:06d}')
        canvas.drawRightString(letter[0]-28,14,'1 / 1')
        canvas.restoreState()
    document.build(story,onFirstPage=footer,onLaterPages=footer)
    return path
