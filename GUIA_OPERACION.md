# Alonso · Guía rápida de operación

## Antes de comenzar

Abre **Andamios Alonso** desde el acceso del escritorio o el menú Inicio. Si usas la versión portátil, abre `dist\AndamiosAlonso.exe` desde el Explorador de Windows. En **Inventario y precios**, verifica las existencias reales. **Disponible** son piezas listas para entregar; **En revisión** son piezas que se recibieron en mal estado y todavía no se pueden rentar.

## Registrar una renta

1. En **Registrar renta**, escribe nombre o teléfono. Si aparece una coincidencia, selecciónala; si no, sigue llenando los datos normalmente.
2. Confirma la dirección de la obra y la devolución. Esta captura es para entregar hoy; para una salida futura usa Reservaciones.
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

En **Pagos y saldos**, selecciona la renta y pulsa **Cobrar / ver pagos**. Escribe importe recibido y método; confirma con **Registrar pago**. Para completar el saldo usa **Cobrar todo lo pendiente**. El anticipo de una reservación ya se aplica al saldo y no debe capturarse otra vez. Devolver el equipo y pagar son acciones distintas.

## Apartar equipo para otra fecha

1. En **Reservaciones**, pulsa **Nueva reservación**.
2. Se abre un formulario independiente de Nueva Renta: llena cliente, obra, fechas futuras, equipos y cantidades. La captura de renta que tengas iniciada se conserva.
3. Recibe como mínimo el **50% del total**, incluido IVA y cargos si aplican. El importe se calcula automáticamente. Si hay factura, solo permite transferencia. Puedes adjuntar comprobante. Pulsa **Confirmar reservación y recibir anticipo**; se registra en caja y se apartan las cantidades únicamente para esas fechas y su preparación.
4. El día de entrega, selecciona el apartado en **Reservaciones** y pulsa **Entregar e iniciar renta**. Confirma solo cuando se entregue físicamente el material. Se revisa el stock otra vez y se abre la nota.
5. La nota ya incluye el anticipo recibido. En **Pagos y saldo** cobra únicamente lo restante, sin registrar de nuevo el anticipo. Puede convertirse aunque la caja del día del anticipo ya esté cerrada; requiere abierta la caja del día de entrega.

Para una entrega el 25, otra renta puede terminar el 23 y deja el 24 completo para recoger y revisar. No se permite que termine el 24. Las piezas restantes del inventario siguen disponibles; no se descuenta físicamente lo reservado hasta entregarlo. Una devolución retrasada o dañada puede poner un apartado en riesgo: se señala en Inicio y Reservaciones. Se respeta el plazo mínimo de cada equipo.

Si el cliente cancela, usa **Cancelar reservación**: libera las fechas y conserva el anticipo recibido. No devuelve dinero automáticamente; la pantalla avisa de ello. Solo anula pagos si hubo una captura incorrecta, con motivo y respetando los cortes de caja. Si recogió después de la fecha acordada, el periodo completo comienza al confirmar la entrega y se valida otra vez. Las reservaciones anteriores a este cambio conservan su confirmación histórica sin exigir retroactivamente el 50%.

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

# Caja y gastos · versión oficial

**Al llegar:** en Inicio aparece el estado de la caja del día con el botón **Abrir caja**. Captura responsable y fondo inicial para iniciar la jornada. Este mismo bloque está arriba de Caja y gastos. Cuando está abierta, el botón cambia a **Realizar corte**; cuando está cerrada, muestra **Consultar / reabrir**. Las cajas anteriores pendientes de corte se señalan en el bloque.

Se requiere caja abierta antes de guardar una renta, confirmar una nueva reservación con anticipo, entregar una reservación o registrar cobros y gastos. Si falta apertura se muestra el formulario de inicio de jornada. El alta de empleados, vehículos o clientes no necesita apertura. Los pagos con fecha anterior exigen que la caja de esa fecha esté abierta; para corregir un día cerrado, usa Apertura / corte y reabre con motivo.

Abre **AndamiosAlonso.exe**. Caja y gastos ya está integrado en la versión oficial y usa la base habitual en `%LOCALAPPDATA%\AndamiosAlonso\inventario.sqlite3`, con los respaldos automáticos del sistema. Los movimientos capturados anteriormente en **PRUEBA DE CAJA** permanecen separados en `prueba_caja\inventario.sqlite3` y no se importan automáticamente. `build.ps1` genera el programa oficial; `build-preview.ps1` conserva la opción de construir una prueba independiente.

En Registrar movimiento, la categoría muestra **SALIDA DE DINERO · Egreso** en rojo o **ENTRADA DE DINERO · Ingreso** en verde. El campo indica **Importe pagado** o **Importe recibido** y la confirmación repite el tipo de movimiento. Captura siempre importes positivos.

1. En **Caja y gastos → Empleados / vehículos**, registra los nombres e identifica cada camioneta. Los sueldos son pagos registrados; no se calculan prestaciones, impuestos de nómina ni timbrado.
2. En **Apertura / corte**, consulta la fecha, captura el fondo real que queda en el cajón y el responsable. El fondo no se cuenta como ingreso; cada fecha tiene una sola apertura. No se arrastra automáticamente el efectivo del día anterior.
3. En **Registrar movimiento**, captura categoría, importe, método y concepto. Sueldos exige empleado y periodo; gasolina y mantenimiento exigen vehículo. La referencia del comprobante es opcional. Las aportaciones y retiros del dueño se separan del flujo operativo.
4. Los anticipos, abonos y liquidaciones se consultan automáticamente por su fecha real de pago. No vuelvas a registrarlos como otros ingresos. Transferencia y tarjeta no aumentan el efectivo esperado del cajón.
5. Al terminar, consulta **Apertura / corte**, cuenta el efectivo y confirma el cierre. Diferencia = contado − esperado: negativo es faltante y positivo es sobrante. Cualquier diferencia exige explicación. El cierre conserva detalle e importes del momento y bloquea movimientos y correcciones de pagos para esa fecha.
6. Para corregir, **Reabrir con motivo** exige responsable y explicación; conserva el corte anterior. Anula el movimiento equivocado y captura uno nuevo. Los cobros de renta se anulan en Pagos y saldos. Realiza otro cierre y consulta ambos en **Historial de cortes**.
7. Usa **Desde / Hasta → Consultar** para reportes diarios, semanales o mensuales. **Exportar reporte PDF** genera la consulta actual; desde Historial se exporta el corte histórico con su efectivo contado, diferencia y observaciones. Las filas anuladas se conservan, pero se excluyen de los totales.

El flujo operativo representa dinero recibido menos gastos pagados; no equivale a utilidad contable. Los responsables son nombres capturados: este módulo no agrega usuarios, contraseñas ni permisos por rol. Respalda y conserva la base junto con el acceso controlado a la computadora.

# Correo de facturación en Clientes

En Clientes, la columna **Correo** aparece junto al teléfono y utiliza el correo guardado en **Expediente para facturación → Datos para factura → Correo para facturas**. Haz clic directamente en el correo para copiarlo, o selecciona al cliente y pulsa **Copiar correo**. El sistema confirma debajo de la lista que el correo se copió. Si no hay correo, aparece **Sin correo** y el botón permanece deshabilitado. También puedes buscar clientes por correo. Al guardar cambios en el expediente, la lista se actualiza automáticamente.

# Transferencias, comprobantes y contador

- **Con factura:** los nuevos anticipos, abonos y liquidaciones solo permiten **Transferencia**. Se aplica al formulario de renta, pagos posteriores y reservaciones al entregarse. Una renta con pagos vigentes en efectivo o tarjeta no puede cambiarse a factura hasta corregir esos pagos; nunca se cambia el método de pagos anteriores automáticamente.
- **Comprobante:** al capturar una transferencia puedes adjuntar PDF o imagen (hasta 20 MB). También puedes agregarlo después desde **Pagos y saldos → pago seleccionado → Adjuntar comprobante** o en **Comprobantes → Adjuntar al pago**. Mientras no se reciba, figura **Pendiente**. Adjuntar evidencia a un pago existente no modifica el corte de caja ni vuelve a contar el ingreso.
- **Perfil del cliente:** se conserva en **Expediente para facturación → Documentos → Comprobantes de transferencia**, separado de INE, constancia fiscal y domicilio. El botón de comprobantes del expediente permite consultar y adjuntar al pago del cliente. Allí se incluyen transferencias con y sin factura. El ZIP del expediente del cliente incluye también estos archivos.
- **Para el contador:** el apartado **Comprobantes** muestra por defecto únicamente transferencias de rentas con factura. Ajusta fechas de pago y pulsa **Consultar**, luego **ZIP para contador**. El ZIP reúne carpetas por cliente, renta y pago; incluye una relación CSV y señala pagos pendientes de evidencia. Las transferencias sin factura no se incluyen en este paquete. Los comprobantes de pagos anulados se conservan en una carpeta separada, claramente identificados.
- Todo queda dentro de la base y sus respaldos. Los ZIP se generan donde tú elijas; no se envían automáticamente. Puedes guardar copias individuales. Los archivos vinculados a pagos se conservan como evidencia y no se eliminan desde el expediente. Un comprobante recibido no equivale a validación del abono en el banco ni a una factura fiscal emitida.

# Nota PDF en una hoja

El botón **PDF** exporta únicamente la nota principal en una sola hoja: equipos, cantidades, tarifas, cargos, impuestos aplicables, saldos, valor del equipo, datos bancarios y firmas. El contenido se ajusta al espacio cuando hay varios equipos. No se agregan anexos de pagos, ampliaciones ni devoluciones; esos registros y sus observaciones permanecen disponibles dentro del programa. Los reportes de Caja y gastos mantienen su propio formato.

# Direcciones desglosadas y estado de pago

En Nueva Renta y al agregar una dirección desde Clientes, captura **Calle y número**, **Colonia**, **Código postal**, **Municipio**, **Estado** y **Referencias de entrega (opcional)**. Si se captura código postal, debe tener cinco dígitos. Se pueden dejar datos desconocidos vacíos para obras sin dirección completa; es necesaria la calle o identificación de obra. Las direcciones nuevas conservan cada campo para reutilizarlas. Las antiguas se mantienen completas en Calle y número hasta que se desglosen manualmente; no se altera el historial de notas. Esta captura funciona sin internet y no consulta Maps.

El estado del cobro es únicamente **Pendiente** (queda dinero por cobrar) o **Pagado** (pendiente cero). Se muestran Total, Pagado y Pendiente, sin saldo a favor. Si una ampliación o ajuste de tarifa reduce el total por debajo de lo cobrado, los pagos históricos se conservan con sus importes reales y la nota queda Pagada. No se crea crédito para otras rentas ni se registra una devolución automática de dinero.

# Tamaños de andamios

El inventario incluye **Andamio chico · 1.50 m de altura**, **Andamio grande · 2 m de altura** y **Andamio banquetero · 0.90 m de ancho × 2 m de altura**, cada uno con existencias, tarifa y valor de equipo independientes. Al agregarse al sistema comienzan con stock cero y heredan la tarifa vigente de Andamios; confirma precios y valores de reposición en Inventario antes de operarlos.

Los registros anteriores de **Andamios** conservan sus existencias e historial. En **Inventario → Clasificar andamios por tamaño**, distribuye las piezas disponibles entre los tres tipos. La herramienta descuenta del registro genérico y suma a los tamaños sin duplicar stock; conserva un registro de clasificación. Las piezas ya rentadas o en revisión no se trasladan, y se valida que no se dejen reservaciones anteriores sin equipos. Cuando regresen piezas del registro genérico, podrás clasificarlas. Para compras nuevas, aumenta directamente el stock del tamaño correspondiente.

# Protección automática de la captura y respaldos de jornada

La captura de **Nueva Renta** se guarda como borrador cada cinco segundos mientras hay cambios y al cerrar normalmente. Incluye cliente, dirección (incluso campos incompletos), fechas, equipos, condiciones, flete, tablones extra, factura y anticipo en captura. Guardar un borrador no registra pagos, no descuenta inventario y no abre caja.

Si quedó una captura pendiente, al iniciar aparece un aviso en **Inicio** y **Nueva Renta**, con **Recuperar renta** y **Descartar**. Recupera y revisa disponibilidad, precios, fechas y el comprobante antes de confirmar. El archivo elegido para un comprobante debe seguir existiendo en su ubicación original; si se movió o eliminó, vuelve a adjuntarlo. Un borrador pendiente no se reemplaza automáticamente por el formulario vacío del inicio. Al registrar correctamente la renta o reservación, el borrador se elimina en la misma transacción para evitar recuperar una operación ya registrada.

Durante la jornada se crea un respaldo cada hora si hubo cambios. Se realiza en segundo plano mediante la copia segura de SQLite y se verifica su integridad antes de publicarlo. Se conservan las últimas **48 copias de jornada**, aparte de las **30 copias automáticas** diarias/al cerrar. En **Respaldos** se muestran la fecha del último respaldo correcto y los archivos disponibles. Un error de copia se muestra allí y se reintenta; las copias completas anteriores se conservan.

Ante un apagón podrían perderse los últimos segundos de captura anteriores al guardado del borrador. Estos respaldos siguen en la misma computadora: guarda además copias externas desde Respaldos para protegerte ante una falla del disco. No hay nuevos pasos obligatorios para la operación diaria; el aviso de recuperación solo aparece cuando quedó una captura pendiente.

# Impresión, eliminación de artículos y cobro simplificado

Para imprimir usa **Caja y gastos → Imprimir reporte**, **Apertura / corte → Imprimir corte / reporte** o **Historial de cortes → Imprimir corte seleccionado**. El reporte de un día abierto incluye fondo inicial y efectivo esperado; el corte cerrado conserva los importes del cierre, efectivo contado, diferencia e ingresos/egresos. Se entrega al lector PDF configurado en Windows; si no admite impresión directa, el programa abre el PDF y permite elegir impresora con Ctrl+P.

En Inventario, **Eliminar artículo** lo retira del catálogo activo conservando las notas anteriores. No se permite si tiene piezas rentadas, en revisión o reservaciones pendientes. Los productos eliminados no reaparecen al reiniciar el sistema.

El cobro solicita importe recibido y método. El botón **Cobrar todo lo pendiente** llena el restante y pide confirmar el pago. El estado Pendiente o Pagado se calcula automáticamente. Fecha y referencia son opciones secundarias, y el historial/correcciones se despliega cuando se necesita. La explicación completa está en el archivo externo **FLUJO_DE_PAGOS.md**; no se agregó una pantalla de capacitación al programa.

