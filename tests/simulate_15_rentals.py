"""Simulación repetible y aislada. Nunca abre la base real del negocio."""
import sys
import json
from datetime import date,datetime,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.database import Database,SCAFFOLD_SIZES
from app.service import Service,money
from app.cash import Cash
from app.analytics import report
from app.recovery import journal_backup


def run():
    root=Path(__file__).resolve().parents[1]
    folder=root/'data'/('simulacion_15_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True)
    db=Database(folder/'simulacion.sqlite3')
    service=Service(db,require_cash_open=True);cash=Cash(db);today=date.today()
    checks=[];results=[];findings=[]
    def check(label,condition):
        checks.append(dict(check=label,passed=bool(condition)))
        if not condition:raise AssertionError(label)
    def stock():
        for item in db.rows('SELECT * FROM items'):
            pending=db.rows('''SELECT COALESCE(SUM(l.quantity-l.returned_qty),0) FROM rental_lines l
                JOIN rentals r ON r.id=l.rental_id WHERE l.item_id=? AND r.returned_at IS NULL''',(item['id'],))[0][0]
            check('Conservación de stock: '+item['name'],item['total']==item['available']+item['maintenance']+pending and item['available']>=0)
    def rejects(label,action):
        try:action()
        except (ValueError,__import__('sqlite3').Error):checks.append(dict(check=label,passed=True));return
        raise AssertionError('Se aceptó una operación que debía rechazarse: '+label)
    try:
        cash.open_day(today.isoformat(),'500','Secretaria de simulación')
        prices={'Revolvedoras':450,'Bailarinas':250,'Rotomartillos de 30 kg':350,'Generadores':400,'Vibradores para concreto':180}
        ids={r['name']:r['id'] for r in db.rows('SELECT * FROM items')}
        for name,price in prices.items():service.save_item(ids[name],name,1 if name=='Vibradores para concreto' else 10,str(price),'daily')
        for name in SCAFFOLD_SIZES:service.save_item(ids[name],name,30,'30','scaffold','200','450')
        service.save_item(ids['Tablas para cimbra'],'Tablas para cimbra',80,'10','scaffold','250','0')
        small,large,side=(ids[n] for n in SCAFFOLD_SIZES)
        receipt=folder/'Comprobante_FICTICIO.png';receipt.write_bytes((root/'assets'/'logo_alonso.png').read_bytes())
        clients=[service.save_client(None,f'Cliente ficticio {i:02d}',f'31290000{i:02d}',None,'Solo simulación') for i in range(1,16)]
        configs=[
            ('Chico: semana, pago completo y devolución',{small:2},7,40000,False,'400','Efectivo',{}),
            ('Grande: 10 días, pago parcial',{large:3},10,87000,False,'300','Efectivo',{}),
            ('Banquetero: mes con factura y comprobante',{side:1},30,52200,True,'522','Transferencia',{}),
            ('Revolvedora: tarjeta y devolución',{ids['Revolvedoras']:1},2,90000,False,'900','Tarjeta',{}),
            ('Tablas: semana y tres días extra',{ids['Tablas para cimbra']:10},10,280000,False,None,'Efectivo',{}),
            ('Grande con flete y dos tablones extra',{large:2},7,70000,False,'700','Efectivo',dict(freight='200',extra_planks=2)),
            ('Revolvedora con factura: anticipo y restante',{ids['Revolvedoras']:1},1,52200,True,'200','Transferencia',{}),
            ('Chico y tablas: transferencia sin factura',{small:1,ids['Tablas para cimbra']:5},7,160000,False,'500','Transferencia',dict(freight='150')),
            ('Bailarina: pago equivocado, anulación y corrección',{ids['Bailarinas']:1},3,75000,False,'200','Efectivo',{}),
            ('Rotomartillo: devolución en mal estado',{ids['Rotomartillos de 30 kg']:1},2,70000,False,'700','Efectivo',{}),
            ('Dos generadores: devolución parcial',{ids['Generadores']:2},2,160000,False,'1000','Transferencia',{}),
            ('Vibrador vencido sin devolver ni pagar',{ids['Vibradores para concreto']:1},1,18000,False,None,'Efectivo',{}),
            ('Chico: ampliación de 29 a 30 días, ya cobrado',{small:1},29,86000,False,'860','Efectivo',{}),
            ('Reservación de hoy convertida en renta',{small:2},7,40000,False,None,'Efectivo',{}),
            ('Salida futura registrada como renta normal',{side:1},7,20000,False,'100','Efectivo',{}),
        ]
        rentals=[];payments={}
        for i,(label,quantities,days,expected,invoice,amount,method,extras) in enumerate(configs,1):
            start=today-timedelta(days=3) if i==12 else today+timedelta(days=3) if i==15 else today
            if i==14:
                booking=service.create_reservation(clients[i-1],'Obra de prueba 14',start.isoformat(),(start+timedelta(days=days)).isoformat(),quantities)
                key=service.start_reservation(booking)
            else:
                key=service.create_rental(clients[i-1],f'Obra de prueba {i:02d}',start.isoformat(),(start+timedelta(days=days)).isoformat(),quantities,invoice_required=invoice,**extras)
            rentals.append(key)
            check(f'Renta {i}: total inicial independiente',service.payment_summary(key)['total_cents']==expected)
            if amount:
                payments[i]=service.record_payment(key,amount,method,reference=f'SIM-{i:02d}',receipt_path=receipt if i==3 else None)
            if i in (1,4):service.return_rental(key)
            if i==7:
                service.attach_transfer_receipt(payments[i],receipt)
                payments[i]=service.record_payment(key,'322','Transferencia',receipt_path=receipt)
            if i==8:service.record_payment(key,'1100','Transferencia',receipt_path=receipt)
            if i==9:
                service.cancel_payment(payments[i],'Importe incorrecto: simulación')
                payments[i]=service.record_payment(key,'250','Efectivo')
            if i==10:
                line=service.remaining_lines(key)[0]
                service.return_partial(key,[dict(line_id=line['id'],quantity=1,condition='Malo',notes='Revisión de prueba')])
            if i==11:
                line=service.remaining_lines(key)[0]
                service.return_partial(key,[dict(line_id=line['id'],quantity=1,condition='Bueno')])
                service.attach_transfer_receipt(payments[i],receipt)
            if i==13:
                service.extend_rental(key,1)
                expected=45000
                findings.append('Al ampliar de 29 a 30 días, el andamio baja de $860 a $450. Ya se cobraron $860: queda Pagado y no hay gestión de devolución. Es la tarifa configurada, pero exige acordar la regla comercial.')
            if i==15:
                findings.append('Se aceptó una renta con salida dentro de tres días y se descontó una pieza disponible desde hoy. Conviene ofrecer convertirla en reservación para no confundir material apartado con material entregado.')
            summary=service.payment_summary(key)
            check(f'Renta {i}: total final',summary['total_cents']==expected)
            results.append(dict(number=i,rental_id=key,scenario=label,**summary))
            stock()
        check('Exactamente 15 rentas reales en la prueba',len(db.rows('SELECT * FROM rentals'))==15)
        rejects('Factura rechaza efectivo',lambda:service.record_payment(rentals[2],'1','Efectivo'))
        rejects('Factura rechaza tarjeta',lambda:service.record_payment(rentals[6],'1','Tarjeta'))
        rejects('No permite cobrar de más',lambda:service.record_payment(rentals[1],'99999','Efectivo'))
        rejects('No permite rentar el vibrador agotado',lambda:service.create_rental(clients[0],'Obra',today.isoformat(),(today+timedelta(days=1)).isoformat(),{ids['Vibradores para concreto']:1}))
        rejects('No permite eliminar equipo pendiente de devolución',lambda:service.delete_item(ids['Generadores']))
        rejects('No permite eliminar equipo en revisión',lambda:service.delete_item(ids['Rotomartillos de 30 kg']))
        check('La renta vencida aparece en alertas',rentals[11] in [r['id'] for r in service.overdue()])
        # Doble referencia realista: diagnosticar sin dejar ingresos extra en el corte.
        a=service.record_payment(rentals[1],'10','Transferencia',reference='SIM-REFERENCIA-REPETIDA')
        b=service.record_payment(rentals[1],'10','Transferencia',reference='SIM-REFERENCIA-REPETIDA')
        check('La referencia repetida fue aceptada dos veces',a!=b)
        findings.append('Se pudieron registrar dos transferencias de $10 para la misma renta, fecha y referencia. No hay advertencia de posible pago duplicado. Se anularon ambas al terminar esta comprobación.')
        service.cancel_payment(a,'Diagnóstico de duplicados');service.cancel_payment(b,'Diagnóstico de duplicados')
        expected_paid=[40000,30000,52200,90000,0,70000,52200,160000,25000,70000,100000,0,86000,0,10000]
        for i,key in enumerate(rentals):
            summary=service.payment_summary(key)
            check(f'Renta {i+1}: cobros reales',summary['paid_cents']==expected_paid[i])
            results[i].update(summary)
        package=service.export_accountant_receipts(today.isoformat(),today.isoformat(),folder/'Comprobantes_contador.zip')
        check('Comprobantes del contador solo con factura',package['documents']==3 and package['pending']==0)
        check('Comprobante sin factura también en perfil',len(service.client_documents(clients[7]))==1)
        employee=cash.catalog('Empleado','Empleado ficticio');vehicle=cash.catalog('Vehículo','Camioneta ficticia')
        cash.add(today.isoformat(),'Gasolina','450','Efectivo','Reparto de prueba','Secretaria de simulación',vehicle)
        cash.add(today.isoformat(),'Sueldos','1200','Efectivo','Pago de prueba','Secretaria de simulación',employee,'Semana simulada')
        cash.add(today.isoformat(),'Retiro del dueño','300','Efectivo','Retiro de prueba','Secretaria de simulación')
        cash.add(today.isoformat(),'Aportación del dueño','200','Efectivo','Aportación de prueba','Secretaria de simulación')
        day=cash.day_report(today.isoformat())
        cash_paid=sum(expected_paid[i-1] for i in (1,2,6,9,10,13,15))
        check('Caja concilia efectivo con cobros y salidas',day['expected']==50000+cash_paid-45000-120000-30000+20000)
        check('Ingresos de caja coinciden con cobros, sin duplicar comprobantes',day['operating_income']==sum(expected_paid))
        close=cash.close(today.isoformat(),f"{day['expected']/100:.2f}",'Secretaria de simulación')
        snapshot=json.loads(db.rows('SELECT snapshot FROM cash_closings WHERE id=?',(close,))[0][0])
        check('Corte sin faltante ni sobrante',snapshot['difference']==0)
        rejects('Caja cerrada rechaza nuevos cobros',lambda:service.record_payment(rentals[1],'10','Efectivo'))
        backup=journal_backup(db.path)
        check('Respaldo de simulación generado',backup.exists())
        check('Integridad final de SQLite',db.rows('PRAGMA quick_check')[0][0]=='ok')
        check('Claves foráneas íntegras',not db.rows('PRAGMA foreign_key_check'))
        findings.append('El comprobante se puede recibir después del pago. Esto permite seguir trabajando, pero conviene revisar periódicamente los pendientes de comprobante en el apartado Comprobantes.')
        report_path=root/'SIMULACION_15_RENTAS.md'
        lines=['# Simulación de 15 rentas',f'Fecha: {today}. Datos ficticios y base aislada; no se modificaron registros reales.',
            f'Base de prueba: `{db.path.relative_to(root)}`','',
            '| Renta | Escenario | Total final | Cobrado | Pendiente | Estado |','|---|---|---:|---:|---:|---|']
        for r in results:lines.append(f"| {r['number']:02d} | {r['scenario']} | {money(r['total_cents'])} | {money(r['paid_cents'])} | {money(r['pending_cents'])} | {r['status']} |")
        lines.extend(['','## Conciliación',f"- Total contratado final: {money(sum(r['total_cents'] for r in results))}",f"- Cobros vigentes: {money(sum(expected_paid))}",f"- Pendiente: {money(sum(r['pending_cents'] for r in results))}",f"- Efectivo esperado y contado: {money(day['expected'])}",f"- Diferencia del corte: {money(snapshot['difference'])}",f'- Comprobantes exportados para contador: {package["documents"]}. Pendientes con factura: {package["pending"]}.',
            '- El pendiente se suma por renta. Los $410 cobrados por encima del total final de la renta 13 no compensan las deudas de otras notas; por eso el pendiente global no equivale a restar todos los cobros del total contratado.', '',
            '## Hallazgos y mejoras propuestas',*[f'{i}. {finding}' for i,finding in enumerate(findings,1)],'',
            f'## Verificaciones ({len(checks)} correctas)',*[f'- {c["check"]}: OK' for c in checks],
            '','Se probaron las operaciones de negocio, la persistencia y el respaldo. No se probaron aquí impresoras físicas ni todas las interacciones de Windows. Los precios de maquinaria sin tarifa confirmada son valores ficticios exclusivos de esta prueba. No se modificó el programa ni su ejecutable.'])
        report_path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
        (folder/'resultados.json').write_text(json.dumps(dict(results=results,checks=checks,findings=findings,cash=snapshot),ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(dict(rentals=len(results),checks=len(checks),total=sum(r['total_cents'] for r in results),paid=sum(expected_paid),pending=sum(r['pending_cents'] for r in results),cash_expected=day['expected'],findings=findings,report=str(report_path)),ensure_ascii=True))
    finally:db.conn.close()


if __name__=='__main__':run()
