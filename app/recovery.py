"""Borradores persistentes y copias de jornada publicadas de forma atómica."""
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path


class DraftStore:
    def __init__(self,db):self.db=db

    def load(self):
        rows=self.db.rows("SELECT payload,saved_at FROM app_drafts WHERE key='rental'")
        if not rows:return None
        payload=json.loads(rows[0]['payload'])
        if not isinstance(payload,dict) or payload.get('version')!=1:
            raise ValueError('Formato de borrador no reconocido.')
        return dict(payload=payload,saved_at=rows[0]['saved_at'])

    def save(self,payload):
        encoded=json.dumps(payload,ensure_ascii=False,sort_keys=True)
        row=self.db.rows("SELECT payload FROM app_drafts WHERE key='rental'")
        if row and row[0][0]==encoded:return False
        with self.db.conn:
            self.db.conn.execute("INSERT INTO app_drafts VALUES ('rental',?,?) ON CONFLICT(key) DO UPDATE SET payload=excluded.payload,saved_at=excluded.saved_at",
                (encoded,datetime.now().astimezone().isoformat(timespec='seconds')))
        return True

    def clear(self):
        with self.db.conn:self.db.conn.execute("DELETE FROM app_drafts WHERE key='rental'")


def journal_backup(source,keep=48):
    source=Path(source)
    directory=source.parent/'respaldos';directory.mkdir(parents=True,exist_ok=True)
    target=directory/f"jornada-{datetime.now():%Y-%m-%d-%H%M%S-%f}.sqlite3"
    temporary=target.with_suffix('.sqlite3.tmp')
    origin=destination=None
    try:
        origin=sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True,timeout=10)
        destination=sqlite3.connect(temporary)
        origin.backup(destination,pages=128,sleep=.05)
        result=destination.execute('PRAGMA quick_check').fetchall()
        if result!=[('ok',)]:raise sqlite3.DatabaseError('No se pudo verificar la integridad del respaldo.')
        destination.close();destination=None
        with temporary.open('r+b') as stream:
            stream.flush();os.fsync(stream.fileno())
        temporary.replace(target)
        for old in sorted(directory.glob('jornada-*.sqlite3'),key=lambda p:p.stat().st_mtime,reverse=True)[keep:]:old.unlink()
        return target
    finally:
        if destination:destination.close()
        if origin:origin.close()
        temporary.unlink(missing_ok=True)
