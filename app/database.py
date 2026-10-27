import os
import sqlite3
from datetime import date, datetime
from pathlib import Path

SEEDS = ('Andamios', 'Revolvedoras', 'Bailarinas', 'Rotomartillos de 30 kg', 'Generadores',
         'Vibradores para concreto', 'Tablas para cimbra')


def default_path():
    return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'AndamiosAlonso' / 'inventario.sqlite3'


class Database:
    def __init__(self, path=None):
        self.path = Path(path) if path else default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, timeout=10)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.backup_error=''
        if self.path.stat().st_size:
            self.automatic_backup()
            for table in ('rentals','reservations'):
                before={r['name'] for r in self.conn.execute(f'PRAGMA table_info({table})')}
                if 'isr_cents' in before and self.conn.execute(f'SELECT 1 FROM {table} WHERE isr_cents<>0 LIMIT 1').fetchone():
                    self.automatic_backup(force=True)
                    break
        self.conn.executescript(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))
        with self.conn:
            for table in ('rentals','reservations'):
                existing={r['name'] for r in self.conn.execute(f'PRAGMA table_info({table})')}
                for field in ('freight_cents','extra_planks','plank_cents'):
                    if field not in existing:
                        self.conn.execute(f'ALTER TABLE {table} ADD COLUMN {field} INTEGER NOT NULL DEFAULT 0 CHECK({field}>=0)')
            for table in ('rentals','reservations'):
                fiscal_columns={r['name'] for r in self.conn.execute(f'PRAGMA table_info({table})')}
                for name in ('subtotal_cents','vat_bp','isr_bp','vat_cents','isr_cents'):
                    if name not in fiscal_columns:
                        self.conn.execute(f'ALTER TABLE {table} ADD COLUMN {name} INTEGER NOT NULL DEFAULT 0')
                        if name=='subtotal_cents':
                            self.conn.execute(f'UPDATE {table} SET subtotal_cents=total_cents')
            for table in ('items','rental_lines','reservation_lines'):
                columns={r['name'] for r in self.conn.execute(f'PRAGMA table_info({table})')}
                if 'replacement_cents' not in columns:
                    self.conn.execute(f'ALTER TABLE {table} ADD COLUMN replacement_cents INTEGER CHECK(replacement_cents>=0)')
            columns = {r['name'] for r in self.conn.execute('PRAGMA table_info(clients)')}
            if 'ratings_confirmed' not in columns:
                self.conn.execute('ALTER TABLE clients ADD COLUMN ratings_confirmed INTEGER NOT NULL DEFAULT 0 CHECK(ratings_confirmed IN (0,1))')
                # Los 3/5 automáticos de la versión anterior no son una evaluación.
                self.conn.execute('UPDATE clients SET ratings_confirmed=1 WHERE payment_rating<>3 OR return_rating<>3 OR care_rating<>3')
            self.conn.executemany('INSERT OR IGNORE INTO items(name) VALUES (?)', [(x,) for x in SEEDS])
            columns={r['name'] for r in self.conn.execute('PRAGMA table_info(items)')}
            if 'maintenance' not in columns:
                self.conn.execute('ALTER TABLE items ADD COLUMN maintenance INTEGER NOT NULL DEFAULT 0 CHECK(maintenance>=0)')
            columns={r['name'] for r in self.conn.execute('PRAGMA table_info(rental_lines)')}
            for name,declaration in [('returned_qty','INTEGER NOT NULL DEFAULT 0 CHECK(returned_qty>=0)'),
                                     ('delivery_condition',"TEXT NOT NULL DEFAULT 'Bueno'"),('delivery_notes',"TEXT NOT NULL DEFAULT ''")]:
                if name not in columns:
                    self.conn.execute(f'ALTER TABLE rental_lines ADD COLUMN {name} {declaration}')
                    if name=='returned_qty':
                        self.conn.execute('UPDATE rental_lines SET returned_qty=quantity WHERE rental_id IN (SELECT id FROM rentals WHERE returned_at IS NOT NULL)')
                    elif name=='delivery_condition':
                        self.conn.execute("UPDATE rental_lines SET delivery_condition='Sin registro previo'")
            for table in ('items','rental_lines'):
                columns = {r['name'] for r in self.conn.execute(f'PRAGMA table_info({table})')}
                for name, declaration in [('pricing_mode',"TEXT NOT NULL DEFAULT 'daily'"),
                                          ('week_cents','INTEGER NOT NULL DEFAULT 0'),
                                          ('month_cents','INTEGER NOT NULL DEFAULT 0')]:
                    if name not in columns:
                        self.conn.execute(f'ALTER TABLE {table} ADD COLUMN {name} {declaration}')
            columns = {r['name'] for r in self.conn.execute('PRAGMA table_info(rental_extensions)')}
            if 'adjustment_cents' not in columns:
                self.conn.execute('ALTER TABLE rental_extensions ADD COLUMN adjustment_cents INTEGER')
            self.conn.execute('CREATE TABLE IF NOT EXISTS migrations (name TEXT PRIMARY KEY)')
            self.conn.execute('CREATE TABLE IF NOT EXISTS tax_adjustments (id INTEGER PRIMARY KEY,record_type TEXT,record_id INTEGER,previous_total INTEGER,new_total INTEGER,reason TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
            if not self.conn.execute("SELECT 1 FROM migrations WHERE name='optional_vat_no_isr_v1'").fetchone():
                for table in ('rentals','reservations'):
                    for row in self.conn.execute(f'SELECT * FROM {table} WHERE isr_bp<>0 OR isr_cents<>0').fetchall():
                        total=row['subtotal_cents']+row['vat_cents']
                        self.conn.execute('INSERT INTO tax_adjustments(record_type,record_id,previous_total,new_total,reason) VALUES (?,?,?,?,?)',
                            (table,row['id'],row['total_cents'],total,'Eliminación de ISR solicitada por el negocio'))
                        self.conn.execute(f'UPDATE {table} SET isr_bp=0,isr_cents=0,total_cents=? WHERE id=?',(total,row['id']))
                self.conn.execute("INSERT INTO migrations VALUES ('optional_vat_no_isr_v1')")
            if not self.conn.execute("SELECT 1 FROM migrations WHERE name='alonso_tariffs_v1'").fetchone():
                self.conn.execute("UPDATE items SET pricing_mode='scaffold',price_cents=3000,week_cents=20000,month_cents=45000 WHERE name='Andamios'")
                self.conn.execute("UPDATE items SET price_cents=45000 WHERE name='Revolvedoras'")
                self.conn.execute("INSERT INTO migrations VALUES ('alonso_tariffs_v1')")
            if not self.conn.execute("SELECT 1 FROM migrations WHERE name='boards_weekly_v1'").fetchone():
                self.conn.execute("UPDATE items SET pricing_mode='scaffold',price_cents=1000,week_cents=25000,month_cents=0 WHERE name='Tablas para cimbra'")
                self.conn.execute("INSERT INTO migrations VALUES ('boards_weekly_v1')")
        self.automatic_backup()

    def automatic_backup(self,force=False,today=None):
        today=today or date.today()
        directory=self.path.parent/'respaldos'
        temporary=None
        try:
            directory.mkdir(parents=True,exist_ok=True)
            suffix=datetime.now().strftime('-%H%M%S-%f') if force else ''
            target=directory/f'automatico-{today.isoformat()}{suffix}.sqlite3'
            if not target.exists():
                temporary=target.with_suffix('.sqlite3.tmp')
                self.backup(temporary)
                temporary.replace(target)
            # Solo copias generadas por este mecanismo, en la carpeta de esta base.
            backups=sorted(directory.glob('automatico-*.sqlite3'),key=lambda p:p.stat().st_mtime,reverse=True)
            for old in backups[30:]:
                if old.parent.resolve()==directory.resolve():
                    old.unlink()
            self.backup_error=''
            return target
        except (OSError,sqlite3.Error) as exc:
            if temporary is not None and temporary.exists():
                try:
                    temporary.unlink()
                except OSError:
                    pass
            self.backup_error=str(exc)
            return None

    def rows(self, sql, params=()):
        return self.conn.execute(sql, params).fetchall()

    def backup(self, destination):
        if Path(destination).resolve() == self.path.resolve():
            raise ValueError('Elige un archivo distinto de la base de datos actual.')
        target = sqlite3.connect(destination)
        try:
            self.conn.backup(target)
        finally:
            target.close()
