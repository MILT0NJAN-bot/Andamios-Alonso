"""Expedientes locales: los adjuntos viajan con la base y sus respaldos."""
import hashlib
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


DOCUMENT_CATEGORIES = (
    'Constancia de situación fiscal', 'Comprobante de domicilio',
    'INE · frente', 'INE · reverso', 'INE · ambos lados', 'Otros documentos',
)
DOCUMENT_EXTENSIONS = ('.pdf', '.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.tif', '.tiff', '.bmp')
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
BILLING_FIELDS = {
    'legal_name': 'Nombre o razón social', 'rfc': 'RFC',
    'postal_code': 'Código postal fiscal', 'tax_regime': 'Régimen fiscal',
    'cfdi_use': 'Uso de CFDI', 'email': 'Correo para facturas',
    'fiscal_address': 'Domicilio fiscal', 'notes': 'Notas para la contadora',
}


def safe_filename(value):
    """Un componente de nombre, compatible con Windows y sin rutas internas."""
    return re.sub(r'[^\w .()-]', '_', value, flags=re.UNICODE).strip(' .')[:100] or 'documento'


def _matches_format(data, extension):
    if extension == '.pdf':
        return data.startswith(b'%PDF-')
    if extension in ('.jpg', '.jpeg'):
        return data.startswith(b'\xff\xd8\xff')
    if extension == '.png':
        return data.startswith(b'\x89PNG\r\n\x1a\n')
    if extension == '.webp':
        return data.startswith(b'RIFF') and data[8:12] == b'WEBP'
    if extension in ('.heic', '.heif'):
        return data[4:8] == b'ftyp' and data[8:12] in (b'heic', b'heix', b'hevc', b'hevx', b'mif1', b'msf1')
    if extension in ('.tif', '.tiff'):
        return data.startswith((b'II*\x00', b'MM\x00*'))
    return extension == '.bmp' and data.startswith(b'BM')


class ClientFiles:
    def _billing_client(self, client_id):
        row = self.db.conn.execute('SELECT id,name,phone FROM clients WHERE id=?', (client_id,)).fetchone()
        if row is None:
            raise ValueError('Selecciona un cliente registrado para abrir su expediente.')
        return row

    def billing_details(self, client_id):
        self._billing_client(client_id)
        row = self.db.conn.execute('SELECT * FROM client_billing WHERE client_id=?', (client_id,)).fetchone()
        return {field: row[field] if row else '' for field in BILLING_FIELDS}

    def save_billing_details(self, client_id, values):
        self._billing_client(client_id)
        clean = {field: str(values.get(field, '')).strip() for field in BILLING_FIELDS}
        clean['rfc'] = clean['rfc'].upper()
        if any(len(value) > 4000 for value in clean.values()):
            raise ValueError('Cada dato fiscal admite hasta 4,000 caracteres.')
        # Se permite un expediente parcial; la contadora revisa los datos recibidos.
        fields = ','.join(BILLING_FIELDS)
        updates = ','.join(f'{field}=excluded.{field}' for field in BILLING_FIELDS)
        with self.db.conn:
            self.db.conn.execute(
                f'INSERT INTO client_billing(client_id,{fields}) VALUES ({",".join("?" for _ in range(len(BILLING_FIELDS) + 1))}) '
                f'ON CONFLICT(client_id) DO UPDATE SET {updates}', (client_id, *clean.values()))
        return clean

    def client_documents(self, client_id):
        self._billing_client(client_id)
        # No cargar los archivos binarios al consultar el directorio.
        return self.db.rows(
            'SELECT id,category,filename,size_bytes,sha256,created_at FROM client_documents '
            'WHERE client_id=? ORDER BY category,id', (client_id,))

    def add_client_documents(self, client_id, category, paths):
        self._billing_client(client_id)
        if category not in DOCUMENT_CATEGORIES:
            raise ValueError('Selecciona un tipo de documento de la lista.')
        added = skipped = 0
        with self.db.conn:
            for source in paths:
                path = Path(source)
                extension = path.suffix.lower()
                if extension not in DOCUMENT_EXTENSIONS:
                    raise ValueError(f'{path.name}: selecciona un PDF o una imagen compatible.')
                if not path.is_file():
                    raise ValueError(f'{path.name}: el archivo no está disponible.')
                if path.stat().st_size > MAX_DOCUMENT_BYTES:
                    raise ValueError(f'{path.name}: el tamaño máximo por archivo es 20 MB.')
                with path.open('rb') as stream:
                    data = stream.read(MAX_DOCUMENT_BYTES + 1)
                if not data or len(data) > MAX_DOCUMENT_BYTES:
                    raise ValueError(f'{path.name}: el archivo está vacío o supera los 20 MB.')
                if not _matches_format(data, extension):
                    raise ValueError(f'{path.name}: el contenido no corresponde al formato del archivo.')
                cursor = self.db.conn.execute(
                    'INSERT INTO client_documents(client_id,category,filename,content,size_bytes,sha256) '
                    'VALUES (?,?,?,?,?,?) ON CONFLICT(client_id,category,sha256) DO NOTHING',
                    (client_id, category, path.name, data, len(data), hashlib.sha256(data).hexdigest()))
                added += cursor.rowcount
                skipped += 1 - cursor.rowcount
        return {'added': added, 'skipped': skipped}

    def _client_document(self, client_id, document_id):
        row = self.db.conn.execute('SELECT * FROM client_documents WHERE client_id=? AND id=?',
                                   (client_id, document_id)).fetchone()
        if row is None:
            raise ValueError('El documento no pertenece a este cliente o ya fue eliminado.')
        if hashlib.sha256(row['content']).hexdigest() != row['sha256']:
            raise ValueError(f'No se pudo verificar {row["filename"]}. Recupera una copia del respaldo.')
        return row

    def delete_client_document(self, client_id, document_id):
        with self.db.conn:
            cursor = self.db.conn.execute('DELETE FROM client_documents WHERE client_id=? AND id=?',
                                          (client_id, document_id))
            if not cursor.rowcount:
                raise ValueError('El documento no pertenece a este cliente o ya fue eliminado.')

    @contextmanager
    def _document_output(self, destination, extension):
        target = Path(destination).absolute()
        if target.resolve() == self.db.path.resolve():
            raise ValueError('Elige un archivo distinto de la base de datos actual.')
        if target.suffix.lower() != extension:
            raise ValueError(f'El archivo de destino debe terminar en {extension}.')
        # Crear en la misma unidad y reemplazar solo después de terminar con éxito.
        descriptor, name = tempfile.mkstemp(prefix='.expediente-', suffix='.tmp', dir=target.parent)
        temporary = Path(name)
        try:
            os.close(descriptor)
            yield temporary
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)

    def export_client_document(self, client_id, document_id, destination):
        row = self._client_document(client_id, document_id)
        extension = Path(row['filename']).suffix.lower()
        with self._document_output(destination, extension) as temporary:
            temporary.write_bytes(row['content'])

    def billing_zip_name(self, client_id):
        client = self._billing_client(client_id)
        return f'Expediente_{client_id}_{safe_filename(client["name"])}_{date.today().isoformat()}.zip'

    def export_client_billing(self, client_id, destination):
        client = self._billing_client(client_id)
        details = self.billing_details(client_id)
        documents = self.client_documents(client_id)
        if not documents and not any(details.values()):
            raise ValueError('Agrega documentos o datos para facturación antes de exportar el expediente.')
        summary = ['EXPEDIENTE PARA FACTURACIÓN', f'Cliente: {client["name"]}',
                   f'ID de cliente: {client_id}', f'Teléfono: {client["phone"]}',
                   f'Fecha de exportación: {date.today().isoformat()}', '',
                   *[f'{label}: {details[field] or "Sin capturar"}' for field, label in BILLING_FIELDS.items()],
                   '', 'ARCHIVOS INCLUIDOS']
        with self._document_output(destination, '.zip') as temporary:
            with ZipFile(temporary, 'w', compression=ZIP_DEFLATED) as archive:
                for metadata in documents:
                    row = self._client_document(client_id, metadata['id'])
                    original = Path(row['filename'])
                    filename = f'{row["id"]:04d}_{safe_filename(original.stem)}{original.suffix.lower()}'
                    member = f'Documentos/{safe_filename(row["category"])}/{filename}'
                    archive.writestr(member, row['content'])
                    summary.append(f'- {row["category"]}: {filename}')
                if not documents:
                    summary.append('Sin documentos adjuntos.')
                archive.writestr('Datos_para_facturacion.txt', ('\n'.join(summary) + '\n').encode('utf-8-sig'))
        return len(documents)
