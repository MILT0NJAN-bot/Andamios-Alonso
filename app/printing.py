"""Entrega un PDF al manejador de impresión configurado en Windows."""
import os
from pathlib import Path


def print_pdf(path):
    path=Path(path).resolve()
    if not path.is_file() or path.suffix.lower()!='.pdf':raise ValueError('No se encontró el reporte PDF para imprimir.')
    try:
        os.startfile(str(path),'print')
        return 'print'
    except OSError:
        # Algunos lectores (por ejemplo ciertas instalaciones de Edge) no
        # registran la acción imprimir. Abrir la vista permite usar Ctrl+P.
        os.startfile(str(path),'open')
        return 'preview'
