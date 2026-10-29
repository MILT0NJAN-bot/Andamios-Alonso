# Alonso · Guía rápida de operación

## Antes de comenzar

Abre **Andamios Alonso** desde el acceso del escritorio o el menú Inicio. Si usas la versión portátil, abre `dist\AndamiosAlonso.exe` desde el Explorador de Windows. En **Inventario y precios**, verifica las existencias reales. **Disponible** son piezas listas para entregar; **En revisión** son piezas que se recibieron en mal estado y todavía no se pueden rentar.

## Registrar una renta

1. En **Registrar renta**, escribe nombre o teléfono. Si aparece una coincidencia, selecciónala; si no, sigue llenando los datos normalmente.
2. Confirma la dirección de la obra. Usa el calendario para salida y devolución.
3. Pulsa la tarjeta del equipo, indica cantidad y estado de entrega **Bueno** o **Malo**. Al elegir Malo aparecen notas opcionales. Pulsa **Agregar equipo**. Repite para otros materiales.
4. Revisa piezas, tarifas, fechas y total. Marca **Requiere factura** únicamente cuando el cliente la solicite: agregará IVA del 16%. Sin marcar, no se cobra IVA. No se cobra ISR. Para andamios el mínimo es una semana; usa los botones de duración rápida si te ayudan.
5. Si recibiste dinero, captura el pago inicial y su método. Si no, déjalo en cero.
6. Pulsa **Guardar renta y generar nota**. En la nota puedes pulsar **PDF** o **Pagos y saldo**.

## Guardar documentos de un cliente y enviarlos a la contadora

1. En **Clientes**, registra al cliente si aún no existe. Selecciona su fila y pulsa **Expediente para facturación** o haz doble clic en ella.
2. En **Documentos**, elige **Constancia de situación fiscal**, **Comprobante de domicilio**, **INE · frente**, **INE · reverso**, **INE · ambos lados** u **Otros documentos**. Pulsa **Agregar archivos…** y selecciona las fotos o PDF recibidos (máximo 20 MB por archivo). Se guardan en ese momento, sin depender del archivo original.
3. Si te dieron los datos por escrito, abre **Datos para factura** y captura lo disponible. Pulsa **Guardar datos para factura**. Puedes dejar campos y documentos pendientes.
4. Pulsa **Exportar expediente ZIP** y elige dónde guardarlo. Incluye los documentos y una ficha de datos; también guarda los cambios que hayas escrito en la ficha. Envía ese ZIP a la contadora por tu medio habitual.
5. Cuando el cliente vuelva, abre el mismo expediente y vuelve a exportarlo. Para renovar un documento, agrega el nuevo y usa **Quitar documento** en el anterior cuando ya no deba incluirse. Usa **Guardar copia…** para recuperar un solo archivo.

Los respaldos habituales incluyen estos expedientes y sus documentos. Los ZIP contienen todos los documentos adjuntos del cliente, incluidos los INE si se agregaron, y no tienen contraseña. No se emite ninguna factura desde este apartado.

## Recibir una parte o todos los equipos

1. En **Rentas activas**, selecciona la renta y pulsa **Registrar devolución**. También puedes hacer doble clic en una renta del panel principal para localizarla.
2. Escribe únicamente las piezas que estás recibiendo. Deja cero en los equipos que no regresaron.
3. Selecciona **Bueno** o **Malo** por tipo de equipo. Si eliges Malo puedes escribir una nota, pero no es obligatorio.
4. Pulsa **Guardar devolución** y confirma. Si regresó todo, la renta se cierra; si falta algo, continúa activa con la cantidad pendiente.

**Ejemplo:** se rentaron 10 andamios y hoy regresan 6 en buen estado. Recibe 6: esas piezas vuelven a disponibles y quedan 4 pendientes. Si en una misma entrega hay piezas buenas y malas del mismo tipo, registra primero las buenas y después las malas, en dos recepciones.

Las piezas malas quedan **En revisión**. Cuando estén reparadas, selecciónalas en Inventario y pulsa **Liberar piezas revisadas / reparadas**. Nunca liberes piezas que todavía no se pueden entregar.

La devolución no cancela lo contratado ni paga la deuda. Si se amplía una renta parcial, los días extra se cobran solo a las piezas que siguen pendientes. Las piezas ya recibidas conservan el periodo que tenían al devolverse.

## Mostrar el valor completo del equipo

En **Inventario y precios**, selecciona un producto y edítalo. Captura **Valor completo del equipo por pieza**. La nota lo mostrará para que el cliente conozca el valor del material y lo cuide. No se suma al total de renta. Si todavía no tienes ese costo, deja el campo vacío; aparecerá Por definir.

## Registrar un abono o liquidar

En **Pagos y saldos**, selecciona la renta y pulsa **Ver pagos / registrar abono**. Escribe importe, fecha y método; confirma con **Registrar pago**. Para liquidar usa **Completar importe para liquidar** y después **Registrar pago**. Devolver el equipo y liquidar el saldo son acciones distintas.

## Apartar equipo para otra fecha

1. En **Reservaciones**, pulsa **Nueva reservación**.
2. Se abre la captura de renta: llena cliente y obra, fechas futuras, equipos y cantidades.
3. Deja el pago inicial en cero y pulsa **Guardar reservación para estas fechas**. El programa valida que no se hayan apartado más piezas de las disponibles.
4. El día de entrega, selecciona el apartado en **Reservaciones** y pulsa **Entregar e iniciar renta**. Confirma solo cuando se entregue físicamente el material. Se revisa el stock otra vez y se abre la nota.
5. Registra el anticipo desde **Pagos y saldo** de esa nota.

Si el cliente cancela, usa **Cancelar reservación**. Si recogió después de la fecha acordada, el periodo completo comienza el día en que confirmas la entrega y se valida de nuevo la disponibilidad. **Revisar disponibilidad** indica un conflicto que debes resolver, por ejemplo porque otro cliente devolvió equipo dañado.

## Vencimientos

La ventana de alertas muestra quién tiene material vencido y su teléfono. **Aceptar** permite continuar trabajando. Si pidió más tiempo, pulsa **Agregar días / recalcular importe** y revisa la fecha y el total antes de guardar.

## Respaldos y cierre

Los respaldos se crean al abrir el sistema y también al cerrar si hubo cambios. Si el programa sigue abierto al cambiar de día, crea la copia diaria durante su revisión automática. Se conservan las últimas 30 copias. Puedes verlas en **Respaldos** y crear otra con **Crear respaldo ahora**.

Al terminar la jornada, usa **Guardar copia en otra ubicación** y guarda una copia en otra unidad. Las copias de la misma computadora no protegen contra una falla del disco. Para restaurar, cierra el programa y sigue el procedimiento del README; conserva primero la base actual.

## Comprobación para entregar el turno

- Revisa **Rentas activas** para saber qué piezas siguen fuera.
- Revisa **Pagos y saldos** para saber qué falta cobrar, incluso en rentas devueltas.
- Revisa **Reservaciones** para preparar las próximas entregas.
- Revisa **En revisión** antes de ofrecer equipo que regresó dañado.
- Vuelve a exportar el **PDF** si hubo pagos, ampliaciones o devoluciones después de la nota anterior.
# Flete, tablones extra y tablas

Al guardar una renta o entregar una reservación que consume las últimas unidades disponibles, aparece **Producto agotado**, con los nombres de los equipos y disponibilidad cero. La renta ya está guardada; pulsa Aceptar para continuar. En Inventario, los equipos con stock registrado y sin unidades disponibles se resaltan en rojo. Al recibir devoluciones en buen estado o aumentar existencias, se actualiza el indicador. Una reservación pendiente no dispara esta alerta porque todavía no entrega material.

En **Nueva Renta**, el bloque **Flete y tablones extra (opcionales)** permite capturar el importe de traslado acordado por la secretaria y la cantidad de tablones adicionales. Deja cero cuando no apliquen. Cada tablón extra cuesta $50 por pedido; estos cargos no se multiplican por días ni se cobran otra vez al ampliar. El tablón extra es un cargo adicional, no un movimiento del inventario de tablas para cimbra.

El PDF desglosa ambos cargos antes del subtotal. Si se solicita factura, el IVA del 16% se aplica al subtotal completo, incluidos estos cargos. Las reservaciones conservan los importes al iniciar la renta.

Las **Tablas para cimbra** tienen precio inicial de ejemplo de $250 por pieza por los primeros 7 días y $10 por día adicional. Por ejemplo, 10 días cuestan $280 por pieza. El mínimo es de 7 días y no tienen descuento mensual. En Inventario se puede cambiar el precio con tarifa **Semanal / mensual**, dejando el mes en cero. Los cambios afectan las nuevas rentas; las notas anteriores conservan su tarifa.

