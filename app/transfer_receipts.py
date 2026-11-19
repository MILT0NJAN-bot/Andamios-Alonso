"""Comprobantes vinculados al pago y al expediente del cliente."""
import csv
import hashlib
import io
from datetime import date
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from .client_files import DOCUMENT_EXTENSIONS,MAX_DOCUMENT_BYTES,_matches_format,safe_filename

RECEIPT_CATEGORY='Comprobantes de transferencia'


class TransferReceipts:
    def _attach_transfer_receipt(self,payment_id,source):
        rows=self.db.rows('SELECT * FROM financial_payments WHERE id=?',(payment_id,))
        if not rows or rows[0]['method']!='Transferencia' or rows[0]['cancelled_at']:
            raise ValueError('Selecciona una transferencia vigente para adjuntar el comprobante.')
        payment=rows[0];path=Path(source);extension=path.suffix.lower()
        if extension not in DOCUMENT_EXTENSIONS or not path.is_file():
            raise ValueError('Selecciona un comprobante PDF o una imagen compatible.')
        with path.open('rb') as stream:data=stream.read(MAX_DOCUMENT_BYTES+1)
        if not data or len(data)>MAX_DOCUMENT_BYTES or not _matches_format(data,extension):
            raise ValueError('El comprobante debe ser un PDF o imagen válida, de hasta 20 MB.')
        digest=hashlib.sha256(data).hexdigest()
        self.db.conn.execute('''INSERT INTO client_documents(client_id,category,filename,content,size_bytes,sha256)
            VALUES (?,?,?,?,?,?) ON CONFLICT(client_id,category,sha256) DO NOTHING''',
            (payment['client_id'],RECEIPT_CATEGORY,path.name,data,len(data),digest))
        document=self.db.rows('SELECT id FROM client_documents WHERE client_id=? AND category=? AND sha256=?',
            (payment['client_id'],RECEIPT_CATEGORY,digest))[0][0]
        table='reservation_payment_receipts' if payment_id<0 else 'transfer_receipts'
        self.db.conn.execute(f'INSERT OR IGNORE INTO {table}(payment_id,document_id) VALUES (?,?)',(abs(payment_id),document))
        return document

    def attach_transfer_receipt(self,payment_id,source):
        # Adjuntar evidencia no modifica importes ni reabre una caja cerrada.
        with self.db.conn:return self._attach_transfer_receipt(payment_id,source)

    def transfer_payments(self,start=None,end=None,invoice_only=True,client_id=None):
        clauses=["p.method='Transferencia'"];params=[]
        if start:
            start=date.fromisoformat(start).isoformat();clauses.append('p.paid_on>=?');params.append(start)
        if end:
            end=date.fromisoformat(end).isoformat();clauses.append('p.paid_on<=?');params.append(end)
        if start and end and start>end:raise ValueError('El inicio debe ser anterior al final.')
        if invoice_only:clauses.append('p.vat_bp>0')
        if client_id is not None:clauses.append('p.client_id=?');params.append(client_id)
        return self.db.rows('''SELECT p.*,
            CASE WHEN p.id>0 THEN (SELECT COUNT(*) FROM transfer_receipts t WHERE t.payment_id=p.id)
            ELSE (SELECT COUNT(*) FROM reservation_payment_receipts t WHERE t.payment_id=-p.id) END AS receipt_count
            FROM financial_payments p WHERE '''+' AND '.join(clauses)+' ORDER BY p.paid_on DESC,p.id DESC',params)

    def transfer_documents(self,payment_id):
        table='reservation_payment_receipts' if payment_id<0 else 'transfer_receipts'
        return self.db.rows(f'''SELECT d.id,d.filename,d.size_bytes,d.client_id FROM {table} t
            JOIN client_documents d ON d.id=t.document_id WHERE t.payment_id=? ORDER BY t.id''',(abs(payment_id),))

    def export_accountant_receipts(self,start,end,destination):
        rows=self.transfer_payments(start,end,invoice_only=True)
        if not rows:raise ValueError('No hay transferencias con factura en este periodo.')
        manifest=io.StringIO(newline='');writer=csv.writer(manifest)
        # La relación se abre con frecuencia en Excel: conservar texto literal.
        raw_writer=writer
        class TextWriter:
            def writerow(self,values):
                raw_writer.writerow(["'"+v if isinstance(v,str) and v.lstrip().startswith(('=','+','-','@')) else v for v in values])
        writer=TextWriter()
        writer.writerow(['Pago','Renta','Reservación','Cliente','Fecha pago','Importe MXN','Referencia','Estado','Archivo','SHA256'])
        count=0;pending=0
        with self._document_output(destination,'.zip') as temporary:
            with ZipFile(temporary,'w',ZIP_DEFLATED) as archive:
                for payment in rows:
                    documents=self.transfer_documents(payment['id'])
                    state='ANULADO' if payment['cancelled_at'] else ('RESERVACION CANCELADA: COBRO CONSERVADO' if payment['reservation_status']=='Cancelada' else 'VIGENTE')
                    operation=f"Renta_{payment['rental_id']:06d}" if payment['rental_id'] else f"Reservacion_{payment['reservation_id']:06d}"
                    payment_label=f"A{abs(payment['id'])}" if payment['id']<0 else str(payment['id'])
                    if not documents:
                        if not payment['cancelled_at']:pending+=1
                        writer.writerow([payment_label,payment['rental_id'],payment['reservation_id'],payment['client_name'],payment['paid_on'],f"{payment['amount_cents']/100:.2f}",payment['reference'],state,'PENDIENTE DE COMPROBANTE',''])
                    for document in documents:
                        row=self._client_document(payment['client_id'],document['id'])
                        prefix='Anulados' if payment['cancelled_at'] else 'Comprobantes'
                        filename=f"{prefix}/Cliente_{payment['client_id']}_{safe_filename(payment['client_name'])}/{operation}/Pago_{payment_label}/{document['id']}_{safe_filename(row['filename'])}"
                        archive.writestr(filename,row['content']);count+=1
                        writer.writerow([payment_label,payment['rental_id'],payment['reservation_id'],payment['client_name'],payment['paid_on'],f"{payment['amount_cents']/100:.2f}",payment['reference'],state,filename,row['sha256']])
                archive.writestr('Relacion_de_transferencias.csv',manifest.getvalue().encode('utf-8-sig'))
                archive.writestr('LEEME.txt',f'Transferencias de rentas con factura. Periodo de pago: {start} a {end}.\nComprobantes: {count}. Pagos vigentes pendientes de comprobante: {pending}.\nLos pagos anulados se conservan separados en Anulados; no son ingresos vigentes.\nLos comprobantes son evidencia recibida; no confirman por si mismos el abono bancario ni son facturas emitidas.\n'.encode('utf-8'))
        return dict(documents=count,pending=pending)
