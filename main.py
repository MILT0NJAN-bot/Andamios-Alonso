import argparse
from app.database import Database


def main():
    import os
    if os.name == 'nt':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Alonso.ControlRentas.1')
    parser = argparse.ArgumentParser(description='Andamios Alonso: control local de rentas')
    parser.add_argument('--db', help='Ruta alternativa del archivo SQLite')
    parser.add_argument('--smoke-test', action='store_true', help='Validar inicio de GUI y cerrar')
    args = parser.parse_args()
    import customtkinter as ctk
    from app.desktop import Application
    ctk.set_appearance_mode('light')
    ctk.set_default_color_theme('blue')
    app = Application(Database(args.db))
    if args.smoke_test:
        app.after(600, app.close)
    app.mainloop()


if __name__ == '__main__':
    main()
