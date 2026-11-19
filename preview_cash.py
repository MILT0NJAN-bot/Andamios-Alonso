"""Entrada exclusiva del ejecutable de comparación; no altera la base habitual."""
import sqlite3
import sys
from app.database import default_path


def preview_path():
    source=default_path()
    target=source.parent/'prueba_caja'/'inventario.sqlite3'
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists() and source.exists():
        temporary=target.with_suffix('.tmp')
        origin=sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)
        destination=sqlite3.connect(temporary)
        try:
            origin.backup(destination)
        finally:
            destination.close();origin.close()
        temporary.replace(target)
    return target


if __name__=='__main__':
    if '--db' not in sys.argv and not any(a.startswith('--db=') for a in sys.argv):
        sys.argv.extend(['--db',str(preview_path())])
    from main import main
    main()
