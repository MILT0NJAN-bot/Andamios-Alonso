# Cómo funcionan los pagos en Andamios Alonso

## 1. Al registrar una renta

El sistema calcula el total de los equipos, días y cargos elegidos. En **Pago recibido al registrar la renta**, captura únicamente el dinero que el cliente ya entregó. Si todavía no paga, deja cero. No elijas manualmente si está pagada o pendiente: eso se calcula solo.

Ejemplo: renta de **$1,000** y pago recibido de **$300**. Al guardar queda **Pagado: $300**, **Pendiente: $700**, estado **Pendiente**. Si entrega los $1,000 completos, queda **Pagado** y pendiente cero.

## 2. Cuando el cliente entrega otro pago

En **Pagos y saldos**, busca al cliente o el folio y pulsa **Cobrar / ver pagos**. También puedes abrir **Pagos y saldo** desde la renta.

Captura el **importe recibido**, elige **Efectivo**, **Transferencia** o **Tarjeta** y pulsa **Registrar pago**. La confirmación muestra cuánto se recibe y cuánto quedará pendiente. Si el cliente entrega exactamente lo que falta, puedes usar **Cobrar todo lo pendiente**, que completa el importe y pide confirmación.

No hay que decidir entre anticipo, abono o liquidación. El sistema conserva esa clasificación internamente para el historial, pero el flujo de trabajo es siempre registrar el dinero efectivamente recibido.

## 3. Solo dos estados

| Estado | Significado |
|---|---|
| Pendiente | Todavía queda dinero por cobrar, aunque el cliente ya haya pagado una parte. |
| Pagado | El total está cubierto y el pendiente es cero. |

**Pagado** es la suma de los pagos vigentes. **Pendiente** es lo que falta para cubrir el total. No son dos cantidades que deba capturar la secretaria.

## 4. Transferencias y factura

Si la renta requiere factura, solo se permite **Transferencia**. Puedes adjuntar el comprobante al registrar el pago o después en **Comprobantes**. Los comprobantes quedan en el pago y en el perfil del cliente; los de rentas con factura se pueden exportar en el ZIP para el contador.

Adjuntar un comprobante a un pago existente **no registra otro ingreso**. El comprobante debe asociarse al pago que ya está capturado. Si todavía falta el archivo, se muestra pendiente de comprobante; esto es distinto de tener dinero pendiente por cobrar.

El correo del cliente se registra en **Expediente para facturación → Datos para factura**, no en el formulario de renta.

## 5. Fecha, referencia y errores

Por defecto se registra la fecha de hoy. **Fecha y referencia** permite indicar otro día o agregar una referencia cuando haga falta. La caja de la fecha del pago debe estar abierta.

En **Ver historial / corregir pagos** puedes consultar movimientos y comprobantes. Si se capturó un pago equivocado, anúlalo con un motivo y registra el correcto. La anulación se conserva y deja de descontarse del pendiente; no es un reembolso de dinero. Si la caja está cerrada, primero se debe reabrir la fecha con un motivo.

## 6. Cómo se refleja en caja

Cada pago de renta aparece automáticamente en Caja y gastos: no se registra de nuevo como Otro ingreso. Solo los pagos en efectivo aumentan el dinero esperado en el cajón; transferencias y tarjeta se muestran por separado.

Puedes imprimir el reporte del día desde **Apertura / corte → Imprimir corte / reporte**, o un corte anterior desde **Historial de cortes → Imprimir corte seleccionado**. Antes de cerrar se muestra cuánto debería haber; el corte cerrado agrega cuánto se contó y la diferencia.

La devolución del equipo y el pago son independientes: devolverlo no significa que se pagó. Si se amplía una renta, el total puede cambiar y volver a quedar Pendiente. Si un ajuste reduce el total por debajo de lo cobrado, los pagos reales se conservan, el pendiente queda en cero y no se genera crédito para otras rentas.

## 7. Reservaciones con anticipo del 50%

Las salidas futuras se capturan en **Reservaciones → Nueva reservación**, en un formulario separado. Recibe al menos la mitad del total para confirmar; puede recibir más si el cliente lo desea. El total incluye los cargos e IVA aplicables. Con factura solo se acepta transferencia. El anticipo entra a caja en la fecha en que se recibe, con su comprobante si se adjunta.

Al entregar físicamente, pulsa **Entregar e iniciar renta**. El anticipo ya aparece como pagado y solo falta cobrar el restante. No registres el anticipo otra vez. La conversión no genera un segundo ingreso y puede hacerse aunque el corte del día del anticipo esté cerrado.

Un apartado no retira la maquinaria desde hoy: asegura cantidades para las fechas elegidas y un día de preparación. Ejemplo: reservación para el 25, devolución de una renta previa el 23, preparación el 24. Si no hay devolución a tiempo, Inicio y Reservaciones muestran el riesgo.

Al cancelar un apartado se liberan sus fechas, pero el dinero recibido se conserva. La cancelación del apartado no es una devolución bancaria ni una anulación automática del pago. Los pagos de reservaciones están en **Pagos de la reservación**; las correcciones exigen motivo y respetan los cortes. Las reservaciones históricas conservan sus condiciones anteriores.
