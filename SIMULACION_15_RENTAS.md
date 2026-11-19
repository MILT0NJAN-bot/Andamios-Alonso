# Simulación de 15 rentas
Fecha: 2026-11-09. Datos ficticios y base aislada; no se modificaron registros reales.
Base de prueba: `data\simulacion_15_20261109_092647_440869\simulacion.sqlite3`

| Renta | Escenario | Total final | Cobrado | Pendiente | Estado |
|---|---|---:|---:|---:|---|
| 01 | Chico: semana, pago completo y devolución | $400.00 | $400.00 | $0.00 | Pagado |
| 02 | Grande: 10 días, pago parcial | $870.00 | $300.00 | $570.00 | Pendiente |
| 03 | Banquetero: mes con factura y comprobante | $522.00 | $522.00 | $0.00 | Pagado |
| 04 | Revolvedora: tarjeta y devolución | $900.00 | $900.00 | $0.00 | Pagado |
| 05 | Tablas: semana y tres días extra | $2,800.00 | $0.00 | $2,800.00 | Pendiente |
| 06 | Grande con flete y dos tablones extra | $700.00 | $700.00 | $0.00 | Pagado |
| 07 | Revolvedora con factura: anticipo y restante | $522.00 | $522.00 | $0.00 | Pagado |
| 08 | Chico y tablas: transferencia sin factura | $1,600.00 | $1,600.00 | $0.00 | Pagado |
| 09 | Bailarina: pago equivocado, anulación y corrección | $750.00 | $250.00 | $500.00 | Pendiente |
| 10 | Rotomartillo: devolución en mal estado | $700.00 | $700.00 | $0.00 | Pagado |
| 11 | Dos generadores: devolución parcial | $1,600.00 | $1,000.00 | $600.00 | Pendiente |
| 12 | Vibrador vencido sin devolver ni pagar | $180.00 | $0.00 | $180.00 | Pendiente |
| 13 | Chico: ampliación de 29 a 30 días, ya cobrado | $450.00 | $860.00 | $0.00 | Pagado |
| 14 | Reservación de hoy convertida en renta | $400.00 | $0.00 | $400.00 | Pendiente |
| 15 | Salida futura registrada como renta normal | $200.00 | $100.00 | $100.00 | Pendiente |

## Conciliación
- Total contratado final: $12,594.00
- Cobros vigentes: $7,854.00
- Pendiente: $5,150.00
- Efectivo esperado y contado: $2,060.00
- Diferencia del corte: $0.00
- Comprobantes exportados para contador: 3. Pendientes con factura: 0.
- El pendiente se suma por renta. Los $410 cobrados por encima del total final de la renta 13 no compensan las deudas de otras notas; por eso el pendiente global no equivale a restar todos los cobros del total contratado.

## Hallazgos y mejoras propuestas
1. Al ampliar de 29 a 30 días, el andamio baja de $860 a $450. Ya se cobraron $860: queda Pagado y no hay gestión de devolución. Es la tarifa configurada, pero exige acordar la regla comercial.
2. Se aceptó una renta con salida dentro de tres días y se descontó una pieza disponible desde hoy. Conviene ofrecer convertirla en reservación para no confundir material apartado con material entregado.
3. Se pudieron registrar dos transferencias de $10 para la misma renta, fecha y referencia. No hay advertencia de posible pago duplicado. Se anularon ambas al terminar esta comprobación.
4. El comprobante se puede recibir después del pago. Esto permite seguir trabajando, pero conviene revisar periódicamente los pendientes de comprobante en el apartado Comprobantes.

## Verificaciones (213 correctas)
- Renta 1: total inicial independiente: OK
- Renta 1: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 2: total inicial independiente: OK
- Renta 2: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 3: total inicial independiente: OK
- Renta 3: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 4: total inicial independiente: OK
- Renta 4: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 5: total inicial independiente: OK
- Renta 5: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 6: total inicial independiente: OK
- Renta 6: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 7: total inicial independiente: OK
- Renta 7: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 8: total inicial independiente: OK
- Renta 8: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 9: total inicial independiente: OK
- Renta 9: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 10: total inicial independiente: OK
- Renta 10: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 11: total inicial independiente: OK
- Renta 11: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 12: total inicial independiente: OK
- Renta 12: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 13: total inicial independiente: OK
- Renta 13: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 14: total inicial independiente: OK
- Renta 14: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Renta 15: total inicial independiente: OK
- Renta 15: total final: OK
- Conservación de stock: Andamios: OK
- Conservación de stock: Revolvedoras: OK
- Conservación de stock: Bailarinas: OK
- Conservación de stock: Rotomartillos de 30 kg: OK
- Conservación de stock: Generadores: OK
- Conservación de stock: Vibradores para concreto: OK
- Conservación de stock: Tablas para cimbra: OK
- Conservación de stock: Andamio chico · 1.50 m de altura: OK
- Conservación de stock: Andamio grande · 2 m de altura: OK
- Conservación de stock: Andamio banquetero · 0.90 m de ancho × 2 m de altura: OK
- Exactamente 15 rentas reales en la prueba: OK
- Factura rechaza efectivo: OK
- Factura rechaza tarjeta: OK
- No permite cobrar de más: OK
- No permite rentar el vibrador agotado: OK
- No permite eliminar equipo pendiente de devolución: OK
- No permite eliminar equipo en revisión: OK
- La renta vencida aparece en alertas: OK
- La referencia repetida fue aceptada dos veces: OK
- Renta 1: cobros reales: OK
- Renta 2: cobros reales: OK
- Renta 3: cobros reales: OK
- Renta 4: cobros reales: OK
- Renta 5: cobros reales: OK
- Renta 6: cobros reales: OK
- Renta 7: cobros reales: OK
- Renta 8: cobros reales: OK
- Renta 9: cobros reales: OK
- Renta 10: cobros reales: OK
- Renta 11: cobros reales: OK
- Renta 12: cobros reales: OK
- Renta 13: cobros reales: OK
- Renta 14: cobros reales: OK
- Renta 15: cobros reales: OK
- Comprobantes del contador solo con factura: OK
- Comprobante sin factura también en perfil: OK
- Caja concilia efectivo con cobros y salidas: OK
- Ingresos de caja coinciden con cobros, sin duplicar comprobantes: OK
- Corte sin faltante ni sobrante: OK
- Caja cerrada rechaza nuevos cobros: OK
- Respaldo de simulación generado: OK
- Integridad final de SQLite: OK
- Claves foráneas íntegras: OK

Se probaron las operaciones de negocio, la persistencia y el respaldo. No se probaron aquí impresoras físicas ni todas las interacciones de Windows. Los precios de maquinaria sin tarifa confirmada son valores ficticios exclusivos de esta prueba. No se modificó el programa ni su ejecutable.
