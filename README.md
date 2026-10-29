# Andamios Alonso

Aplicación de escritorio para Windows, en español, hecha con Python, CustomTkinter y SQLite. Una vez instaladas las dependencias o generado el ejecutable, funciona sin conexión a internet. La interfaz toma como referencia el HTML proporcionado: menú lateral, panel principal, tarjetas de resumen y formularios por secciones, con azul y naranja de Alonso.

Para capacitar al personal, consulta la [Guía rápida de operación](GUIA_OPERACION.md): incluye captura, devoluciones parciales, estados, pagos, reservaciones y cierre de jornada.

## Ejecutar desde el código

1. Instala Python 3.11 o posterior en Windows y habilita la opción de agregar Python al PATH.
2. Abre PowerShell en esta carpeta.
3. Crea el entorno e instala las dependencias (esta instalación inicial requiere internet):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Inicia la aplicación:

```powershell
.\.venv\Scripts\python.exe main.py
```

No es necesario activar el entorno ni modificar las políticas de PowerShell.

## Generar el ejecutable

En Windows, desde esta carpeta:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

El resultado es `dist\AndamiosAlonso.exe`. Se puede copiar a otro equipo Windows compatible sin instalar Python. El script incluye los recursos de CustomTkinter y el esquema SQL. La compilación debe realizarse en Windows para obtener un ejecutable de Windows, según la [documentación de PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html).

## Instalar en Windows

Después de generar el ejecutable, ejecuta desde esta carpeta:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Se instala para el usuario actual en `%LOCALAPPDATA%\Programs\AndamiosAlonso`, con accesos directos en el escritorio y el menú Inicio. Aparece como **Andamios Alonso** en las aplicaciones instaladas de Windows. El ejecutable incluye Python y sus dependencias; no necesita la carpeta del proyecto para funcionar.

Para actualizar, cierra la versión instalada, vuelve a compilar y ejecuta el mismo instalador. La base de datos y sus documentos continúan en `%LOCALAPPDATA%\AndamiosAlonso`; instalar, actualizar o desinstalar el programa conserva esos datos y sus respaldos.

## Primer uso

En **Inicio**, las tarjetas **Tipos de equipos** y **Unidades disponibles** abren Inventario; **Rentas activas** abre su listado y **Rentas vencidas** abre las alertas. El botón inferior **Consultar alertas** permanece disponible. Haz doble clic en una fila de **Próximas devoluciones y rentas vencidas** para abrir Rentas activas con esa renta seleccionada; también puedes seleccionar la fila y pulsar Enter.

1. En **Inventario/Precios**, configura las existencias reales. Se incluyen andamios y los seis equipos originales con stock inicial cero. Las tarifas de andamios y revolvedoras ya están configuradas; los demás precios quedan pendientes. También puedes agregar artículos y elegir su tipo de tarifa.
2. En **Registrar renta**, comienza directamente con **Nombre del cliente** y **Teléfono de contacto**, uno junto al otro. Al escribir en cualquiera aparecen sugerencias de clientes registrados, únicamente si hay coincidencias. Selecciona una para cargar nombre, teléfono, reputación y última dirección utilizada. El teléfono se busca ignorando espacios y separadores. Si no hay coincidencias no se muestra ningún aviso ni selector vacío; sigue llenando el formulario normalmente. Puedes elegir otra dirección registrada o **Agregar nueva dirección de obra**.
3. Para un cliente nuevo, llena nombre, teléfono y dirección en ese mismo formulario. No necesitas ir a Clientes: el cliente y la renta se guardan juntos al confirmar. Si falla la renta, tampoco se crea el cliente. Para un cliente seleccionado, **Limpiar datos del cliente** permite iniciar otra captura sin borrar los equipos. Cambiar el nombre o teléfono de la identidad seleccionada la desvincula de la captura para evitar sobrescribir a otro cliente; los cambios permanentes del directorio se realizan en Clientes. Un teléfono ya registrado requiere seleccionar al cliente existente para evitar duplicarlo.
4. Pulsa **Calendario** en salida o devolución y selecciona el día. Puedes cambiar de mes o pulsar **Hoy**. Los días son la diferencia entre devolución y salida: del 14 al 17 son **3 días**. Se cobra mínimo un día; para una renta de un día selecciona la devolución al día siguiente. El total se recalcula al elegir una fecha.
5. Filtra y pulsa una **tarjeta de equipo**, escribe la cantidad y pulsa **Agregar equipo**. Las tarjetas muestran disponibilidad y tarifa. Los artículos sin stock o precio no se pueden seleccionar. Al elegir andamios, si la duración era menor a 7 días se ajusta a una semana. También hay botones para 1 día, 1 semana y 30 días. Agregar un equipo otra vez acumula la cantidad; para corregirla quita la fila y vuelve a agregarla.
6. Confirma la renta. Se guardan la nota y la dirección y se descuentan las unidades. En la ventana de nota pulsa **PDF**; también se conserva la opción de texto.
7. En **Rentas activas**, busca por cliente, teléfono, material o dirección; consulta notas, agrega días o registra una devolución parcial o completa. El listado muestra cuántas piezas quedan pendientes. Una pieza ya recibida no puede recibirse dos veces. El **Historial de rentas** conserva todas las notas.
8. En **Clientes**, pulsa **Calificar cliente seleccionado**, o usa **Calificar al cliente** después de seleccionarlo en la nueva renta. Al registrar una devolución también se abre la evaluación; puedes cerrarla y calificar después. La secretaria elige pago, devolución y cuidado, de 1 (malo) a 5 (excelente), y pulsa **Guardar calificación**. Los clientes nuevos aparecen **Sin calificar** hasta que se evalúen. El conteo de devoluciones fuera de fecha se calcula con las fechas guardadas y no asigna ni cambia puntuaciones.

Al actualizar una base anterior se conservan sus datos. Como antes se asignaba 3/5 automáticamente sin distinguirlo de una evaluación manual de 3/5, los clientes con los tres valores en 3 aparecen **Sin calificar** hasta confirmar una evaluación. Si alguna puntuación anterior es diferente de 3 se conserva como calificación registrada. Los valores originales permanecen en la base de datos.

## Expediente de facturación por cliente

En **Clientes**, selecciona una persona y pulsa **Expediente para facturación** (también puedes hacer doble clic en su fila o pulsar Enter). El expediente permanece asociado al cliente para sus próximas rentas.

- En **Documentos**, elige el tipo: constancia de situación fiscal, comprobante de domicilio, INE de frente, reverso o ambos lados, u otros documentos. Pulsa **Agregar archivos…** y selecciona uno o varios PDF o imágenes JPG/JPEG, PNG, WEBP, HEIC/HEIF, TIFF o BMP, de hasta **20 MB por archivo**. Se guardan inmediatamente como una copia independiente; puedes mover o borrar el original. Un archivo idéntico del mismo tipo y cliente no se duplica. Si algún archivo de una selección es inválido, no se guarda ninguno de esa selección.
- En **Datos para factura**, captura opcionalmente nombre o razón social, RFC, código postal fiscal, régimen, uso de CFDI, correo, domicilio fiscal y notas para la contadora. Puedes guardar un expediente parcial. No se extraen datos automáticamente de las fotos ni se comprueba su validez fiscal.
- **Exportar expediente ZIP** guarda los datos capturados y genera un ZIP con todos los documentos de ese cliente, organizados por tipo, y `Datos_para_facturacion.txt`. Elige dónde guardarlo y envíalo a la contadora por el medio habitual. No incluye reputación, observaciones internas, rentas ni expedientes de otros clientes. No genera ni envía facturas.
- **Guardar copia…** recupera el documento seleccionado. **Quitar documento** pide confirmación y elimina únicamente la copia del expediente actual; los originales, ZIP ya exportados y respaldos anteriores se conservan. Para actualizar un comprobante, agrega la nueva versión y quita la anterior si ya no debe enviarse.

Los datos fiscales y los archivos se almacenan dentro de la misma base SQLite local y están incluidos en los respaldos automáticos y manuales. Al restaurar una copia se recupera el expediente tal como estaba en ella. El tamaño de la base y sus respaldos crece con los adjuntos. La base y los ZIP no están cifrados; contienen los documentos personales que se hayan adjuntado.

## Devoluciones parciales y estado

En **Registrar renta**, selecciona **Bueno/Malo** para el equipo que agregas. Si marcas Malo aparecen notas opcionales. Ese estado se guarda por tipo de equipo en la nota. Al agregar más piezas del mismo tipo se acumula la cantidad y se aplica el último estado seleccionado a la línea completa.

En **Rentas activas → Registrar devolución**, indica únicamente las piezas recibidas y el estado **Bueno/Malo** por equipo. Las notas aparecen al elegir Malo y son opcionales. Puedes pulsar **Recibir todas las piezas pendientes** para llenar las cantidades y después revisar cada estado antes de confirmar. Para recibir piezas buenas y malas del mismo tipo en una entrega, registra dos recepciones separadas.

Las piezas buenas vuelven a disponibles. Las malas se retiran de la renta y quedan **En revisión**, sin disponibilidad para volver a rentarse. Cuando estén listas, usa **Inventario → Liberar piezas revisadas / reparadas**. El stock total no puede reducirse por debajo de la suma de piezas rentadas y en revisión.

Mientras falten piezas, la renta sigue activa y sus alertas continúan. Al recibir la última se registra la devolución completa y se abre la evaluación del cliente. El importe del periodo ya contratado no se reduce automáticamente; tampoco se registra un pago. Las ampliaciones posteriores se calculan solo sobre las piezas pendientes. Las recibidas conservan el precio del periodo vigente al recibirse. El PDF incluye **Estado y devoluciones**, con cantidades entregadas, recibidas y pendientes, estados y notas; si hay piezas con periodos distintos se indica en la columna de precio.

## Reservaciones futuras

En **Reservaciones → Nueva reservación** se abre la misma captura utilizada para rentar. Completa cliente, dirección, fechas y equipos; deja el pago inicial en cero y pulsa **Guardar reservación para estas fechas**. No se modifica el stock físico ni se registra un ingreso; se aparta capacidad para esas fechas, con la tarifa del momento.

La disponibilidad considera reservaciones confirmadas, unidades en revisión y piezas pendientes de rentas activas. Se comprueba el máximo de ocupación simultánea dentro del periodo, no simplemente la suma de todos los apartados. El día de devolución se considera libre para otra entrega. Las devoluciones futuras se estiman según la fecha contratada: al entregar una reservación se vuelve a comprobar el stock físico. Una renta ya vencida sin devolución bloquea sus piezas para nuevas reservaciones hasta recibirlas o actualizar su fecha.

En la fecha de salida o después, selecciona el apartado y pulsa **Entregar e iniciar renta**. Solo hazlo cuando entregues físicamente el equipo: se descuenta el inventario una vez y se abre la nota para registrar el anticipo. Si la entrega se retrasa, el periodo reservado completo comienza hoy; la disponibilidad se valida otra vez para el periodo desplazado. Se respetan los precios reservados. No se puede entregar dos veces ni cancelar una reservación ya entregada.

**Cancelar reservación** libera el apartado. Para cambiar fechas o cantidades, cancela y captura una nueva. Las piezas dañadas o las rentas vencidas pueden dejar un apartado sin capacidad: el listado mostrará **Revisar disponibilidad** y no permitirá entregarlo sin stock. Las ampliaciones de rentas y las reducciones de stock también validan los apartados confirmados.

## Pagos y saldos

En **Registrar renta** puedes capturar un **Anticipo o pago inicial** opcional: importe, método y referencia. Deja $0.00 si todavía no recibiste dinero. La renta, el cliente nuevo y el pago inicial se guardan en una sola transacción; si algún dato falla, no se guarda ninguno de esos movimientos. Si el pago cubre el total se clasifica como liquidación.

En **Pagos y saldos**, busca por folio, cliente o teléfono. La tabla muestra total, pagado, pendiente, saldo a favor y estado de pago de cada renta, tanto activa como devuelta. Puedes filtrar solo rentas pendientes. Los totales de arriba corresponden a las rentas visibles. En **Clientes** también se muestra el saldo pendiente acumulado por cliente, sin compensar automáticamente saldos a favor de otras notas.

Selecciona una renta y pulsa **Ver pagos / registrar abono**, o usa **Pagos y saldo** desde Rentas activas, Historial o la ventana de nota. Registra importe, fecha mediante calendario, tipo (anticipo, abono o liquidación), método (efectivo, transferencia o tarjeta) y referencia opcional. **Completar importe para liquidar** llena el importe con el saldo pendiente; después confirma con **Registrar pago**. El sistema rechaza importes nulos, negativos, con más de dos decimales o mayores al saldo y fechas de pago futuras.

Los pagos se guardan como centavos enteros. Las ampliaciones pueden volver a abrir un saldo en una renta liquidada. Si una tarifa mensual reduce el total por debajo de lo pagado, se muestra **Saldo a favor** y se impiden pagos nuevos hasta que haya saldo pendiente. No se realizan compensaciones entre rentas ni devoluciones de dinero automáticamente. La entrega del equipo y el pago se controlan por separado: devolverlo no liquida la deuda, y se puede pagar después de devolverlo.

Para corregir una captura, elige el movimiento en el historial y pulsa **Anular pago seleccionado por error**. El motivo es obligatorio. El registro se conserva con fecha y motivo de anulación, y deja de descontarse del saldo. Esta acción corrige el registro; no representa una devolución de efectivo.

Las rentas anteriores a esta función aparecen **Sin pagos** hasta que registres los importes efectivamente recibidos. No se puede deducir si ya estaban pagadas a partir de su estado de devolución. La nueva tabla se crea automáticamente sin borrar inventario, clientes o notas.

## PDF, datos bancarios e impuestos

Desde una renta nueva o desde **Ver nota** en Rentas activas / Historial, pulsa **PDF** y elige dónde guardarla. Incluye el logo de Alonso, folio, cliente, dirección de obra, salida, devolución, días, estado, tabla de equipos y tarifas, valor completo del equipo, subtotal, IVA opcional, total en MXN, pagos, cuidado y firmas. La carátula está adaptada a las fotos de la nota de arrendamiento proporcionadas y conserva la identidad de Alonso. No se requiere Excel o LibreOffice instalado. El logo original se incluye en `assets/logo_alonso.png` y se empaqueta dentro del ejecutable para usarlo también en el encabezado del programa.

La estructura conserva el orden del ejemplo: encabezado, datos generales, partidas, totales, notas, banco y firmas. Por solicitud del propietario se incluyen los datos del PDF de referencia: **Miguel Ángel Alonso Justo**, RFC **AOJM740531IH9**, **Cuenta Maestra PYME BBVA**, cuenta **0159067418**, CLABE **012090001590674189** y número de cliente BBVA **77402582**. Están centralizados en `app/business.py`.

**IVA opcional:** en la captura está la casilla **Requiere factura · agregar IVA 16%**, desactivada de inicio. Sin marcar, total = subtotal. Si el cliente requiere factura, se suma IVA del 16% sobre el subtotal, redondeado a centavos. **No se cobra ni se muestra ISR**. Ejemplo: $1,000 de renta se cobran como $1,000 sin factura o $1,160 al solicitarla. El formulario, las reservaciones, ampliaciones, pagos y saldos respetan esa elección. El PDF sigue siendo una nota de renta, no un CFDI.

En la nota puedes cambiar **Requiere factura (agregar IVA 16%)** y pulsar **Guardar opción de factura**. Se muestra el nuevo total antes de confirmar; los pagos se conservan y el saldo se recalcula. Si al quitar IVA queda dinero pagado de más, aparece saldo a favor, sin reembolso automático.

**Actualización de registros anteriores:** se retira el ISR que hubiera quedado guardado en rentas y reservaciones, se recalcula el total como subtotal más el IVA que ya tenían y se conserva el historial de pagos. Se registra el cambio en `tax_adjustments` y se intenta crear una copia adicional antes de esta migración. No se desmarca el IVA de notas anteriores automáticamente: confirma con el cliente y usa la opción de factura de esa nota para cambiarlo si corresponde.

**Valor completo del equipo:** en Inventario, edita un producto y captura **Valor completo del equipo por pieza · MXN**. Se muestra en la nota como valor por pieza y valor de todas las piezas entregadas, con su total informativo. No se suma a la renta ni a los impuestos, no es un depósito y no genera cobros de daños automáticamente. Si no conoces el costo, deja el campo vacío: aparecerá **Por definir**. Las notas y reservaciones guardan ese valor; cambios posteriores no sustituyen valores ya registrados. Si una nota antigua todavía no tenía valor, al capturarlo por primera vez en el producto se completan esos valores faltantes. Los importes del PDF de ejemplo son ficticios y no se cargan al inventario real.

La columna **PIEZAS** muestra la cantidad de cada equipo; arriba aparece el **Total de piezas**. **Precio del periodo** es el precio de una unidad por todos los días contratados, e **Importe renta** es ese precio multiplicado por las piezas. **Valor equipo** es el costo completo de las piezas, separado de la renta. Se incluyen **Subtotal, IVA solo con factura, Total, Pagado, Saldo pendiente y Saldo a favor**. Los anexos de pagos conservan referencias y anulaciones; estas últimas no reducen el saldo.

El PDF contiene los valores guardados en la aplicación, sin macros ni fórmulas. Cuando cambies la renta o registres un pago, vuelve a exportarlo para que coincida con la base de datos.

Si hay ampliaciones, incluye una sección **Ampliaciones** con fecha anterior/nueva, días y ajuste del importe. Esos ajustes ya están incluidos en el total. También incluye estado de equipos y devoluciones. El PDF se genera en tamaño carta y repite los encabezados de tablas al continuar en otra página. Los textos extensos se conservan en notas ampliadas, sin recortarse. Los archivos anteriores deben volver a exportarse para recibir el nuevo formato.

La exportación es local y funciona sin internet. Puedes revisar [el PDF de ejemplo con cliente ficticio](examples/Nota_Alonso_Ejemplo.pdf) o regenerarlo:

```powershell
.\.venv\Scripts\python.exe examples\create_sample.py
```

## Tarifas y gráficas

Tarifas base por unidad, en MXN, antes de impuestos:

| Equipo / duración | Precio |
|---|---:|
| Andamio, mínimo 7 días | $200 |
| Andamio, día adicional antes de completar el mes | $30 |
| Andamio, mes completo de 30 días | $450 |
| Revolvedora, por día | $450 |

Ejemplos de un andamio: 7 días = $200; 8 = $230; 10 = $290; 30 = $450; 31 = $480; 60 = $900. No se permite confirmar andamios por menos de 7 días. Un mes se interpreta como **30 días**, no mes calendario. Para 7–29 días se cobra $200 más $30 por día posterior al séptimo; desde 30 días se cobran bloques completos de 30 a $450 más días sobrantes a $30. La cantidad de equipos multiplica el importe.

Al completar un bloque mensual, el precio puede **disminuir**: por ejemplo 29 días cuestan $860 y 30 días $450. La ampliación muestra ese ajuste negativo y pide confirmación antes de guardarlo. Es un cambio del importe contratado; no registra una devolución de dinero ni movimientos de caja. Cada línea de la nota conserva su tipo de tarifa y precios originales; los contratos anteriores a esta actualización mantienen su cálculo diario original.

En la primera apertura de esta versión se agregan andamios y se configuran las tarifas indicadas para los artículos llamados **Andamios** y **Revolvedoras**. El stock existente se conserva; después puedes editar sus tarifas en Inventario y no se restablecen al reiniciar.

En **Gráficas y resultados**, elige fechas o usa accesos de 7, 30 o 90 días y pulsa **Ver resultados**. Se muestran:

- Nuevas rentas por día (número de notas según fecha de salida).
- Productos más rentados (suma de unidades entregadas en las rentas que comenzaron durante el periodo).
- Unidades en renta por día y total de unidades actualmente fuera. Las rentas activas vencidas siguen ocupando unidades; una devolución termina la ocupación en su fecha real, con mínimo un día para devoluciones en el mismo día.
- Ingreso esperado por día: total contratado repartido entre los días de renta, incluyendo ampliaciones y tarifa mensual. El reparto es en centavos y conserva la suma exacta del contrato. Por ejemplo, $200 por siete días se distribuyen entre esos siete días; no se muestran $30 por día como si fuera el precio del paquete.

Las gráficas incluyen detalles al pasar el cursor y una tabla diaria. El periodo puede abarcar hasta 366 días. **No representan cobros recibidos ni utilidad neta**: muestran el importe contratado por día, independientemente del registro de pagos. No se registran gastos. Las ampliaciones recalculan la distribución del ingreso esperado; no se agregan dos veces al total. La devolución anticipada no reduce automáticamente el importe contratado.

## Alertas y ampliaciones

- Una renta activa está vencida cuando su fecha de devolución es anterior al día actual. Esta versión utiliza fechas, sin hora de vencimiento: la fecha programada completa se considera vigente.
- Al abrir el programa y cada minuto mientras sigue abierto, se revisan vencimientos. La ventana de alertas muestra folio, nombre, teléfono, materiales, dirección, fecha vencida y total registrado. Si hay otra ventana de captura abierta, el aviso espera a que termine.
- **Aceptar · continuar trabajando** cierra el aviso sin modificar la renta ni el formulario de trabajo. No vuelve a interrumpir por esa misma fecha de vencimiento durante la sesión. En Inicio permanecen el contador y el acceso **Consultar alertas**; al volver a abrir el programa se recuerdan las rentas que siguen vencidas.
- **Agregar días / recalcular importe** abre una vista previa. Por ejemplo, dos equipos de $200/día y tres días adicionales suman $1,200. Se muestra la fecha nueva y el total actualizado antes de confirmar.
- Los días adicionales se suman a la **fecha de devolución actual**, incluso si ya venció; no se suman a la fecha de la llamada. Si la nueva fecha continúa en el pasado, la renta permanece vencida.
- Se respeta la tarifa original de cada equipo y no se modifica el stock. Cada ampliación queda registrada con fecha anterior, fecha nueva, días y ajuste del importe. Las notas muestran el historial de ampliaciones y el total a cobrar, sin sumar dos veces esos ajustes.
- La revisión automática requiere que la aplicación esté abierta. No hay notificaciones del sistema cuando está cerrada ni recargos automáticos; el total corresponde al importe de renta acumulado y los pagos se registran por separado.

Los precios se almacenan como centavos enteros para evitar errores de redondeo. Cada nota conserva nombre del cliente, teléfono, dirección, nombre de equipos y precios del momento de la renta. Los cambios posteriores no alteran notas anteriores. Una renta descuenta piezas físicamente al registrarla. Para apartar sin entregar utiliza **Reservaciones**, en lugar de confirmar una renta futura.

## Base de datos y respaldos

Ubicación predeterminada: `%LOCALAPPDATA%\AndamiosAlonso\inventario.sqlite3`, fuera del ejecutable. Se conserva al cerrar o reemplazar el programa y es independiente para cada usuario de Windows. Para usar otra ubicación:

```powershell
.\.venv\Scripts\python.exe main.py --db "C:\ruta\inventario.sqlite3"
```

El botón **Respaldar base de datos** crea una copia consistente mediante la API de SQLite. Para restaurarla, cierra la aplicación, conserva una copia del archivo actual y reemplázalo por el respaldo en la ubicación indicada. Guarda respaldos frecuentes en otra unidad.

Se crea automáticamente una copia diaria en la carpeta `respaldos` situada junto a la base de datos. Si la base ya existe, se respalda antes de migrar el esquema al abrir el programa. También se crea una copia al cerrar cuando hubo cambios. Si continúa abierto durante el cambio de día, se revisa la copia diaria durante la comprobación periódica de vencimientos. Se conservan las últimas **30 copias automáticas**, no necesariamente 30 días. Las copias manuales en otras ubicaciones no se eliminan.

En **Respaldos** se muestra la ubicación, fecha y tamaño de las copias; puedes crear otra al momento o guardarla en otra unidad. Un error al respaldar se muestra en el panel principal y en Respaldos, sin borrar la base. Estas copias locales no protegen contra fallas del disco: guarda además una copia fuera de la computadora. Las copias contienen también pagos, devoluciones, estados y reservaciones.

El esquema completo está en [app/schema.sql](app/schema.sql). Relaciones:

| Tabla | Contenido y relaciones |
|---|---|
| `items` | ID, nombre, cantidad total, disponible y precio diario en centavos. Restricciones: `0 ≤ disponible ≤ total`. |
| `clients` | Nombre, teléfono, tres calificaciones entre 1 y 5 y observaciones. |
| `addresses` | Dirección y `client_id` → `clients.id`. Varias direcciones por cliente; no se duplica el mismo texto para ese cliente. |
| `rentals` | `client_id` → cliente, `address_id` → dirección, datos históricos, salida, devolución estimada, días, total y fecha de devolución real. |
| `rental_lines` | `rental_id` → renta, `item_id` → artículo, nombre histórico, cantidad y precio histórico. Un artículo por fila por renta. |
| `rental_extensions` | `rental_id` → renta, fecha anterior y nueva, días agregados, importe adicional y fecha de registro. |
| `payments` | `rental_id` → renta, importe en centavos, tipo, método, fecha de pago, referencia y datos de anulación. |
| `rental_returns` | Renta y línea, cantidad recibida, Bueno/Malo, notas, fecha y precio del periodo al recibirse. |
| `reservations` | Cliente, obra, fechas, importe, estado del apartado y renta generada al entregar. |
| `reservation_lines` | Equipo, cantidad y tarifa histórica del apartado. |
| `client_billing` | Datos opcionales para facturación por cliente. |
| `client_documents` | Copias de documentos, tipo, nombre original, contenido, tamaño, huella SHA-256 y fecha. |

Las claves foráneas están habilitadas. La creación, devolución y ampliación de rentas usan transacciones `BEGIN IMMEDIATE`: todas las operaciones se confirman juntas o se revierten. El stock total no puede reducirse por debajo de las unidades actualmente rentadas. Al abrir una base existente se agrega la tabla de ampliaciones automáticamente, sin borrar los datos.

## Organización y pruebas

```text
main.py                 Inicio y argumentos
app/database.py         Conexión, inicialización, artículos base y respaldo
app/schema.sql          Tablas y restricciones SQLite
app/service.py          Validaciones, dinero, rentas, devoluciones y notas
app/ui.py               Componentes compartidos, edición y exportación de notas
app/client_files.py     Expedientes por cliente, adjuntos locales y exportación ZIP
app/client_files_ui.py  Ventana de documentos y datos para factura
app/desktop.py          Diseño con menú lateral, nueva renta integrada y alertas
app/pricing.py          Tarifas diarias, semanales y mensuales
app/analytics.py        Métricas y distribución diaria de ingreso esperado
app/charts.py           Gráficas locales con detalles al pasar el cursor
tests/test_service.py   Pruebas con bases temporales
build.ps1               Compilación a .exe
```

Ejecuta las pruebas:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Comprobación de inicio de la interfaz con una base de prueba:

```powershell
.\.venv\Scripts\python.exe main.py --db .\data\prueba.sqlite3 --smoke-test
```

Prueba de la ventana de expedientes con datos ficticios y base temporal:

```powershell
.\.venv\Scripts\python.exe tests\gui_client_files_check.py
```

La nota es un comprobante operativo de renta. Esta versión no incluye facturación fiscal, fotos, identificación individual de cada máquina, reembolsos, recargos automáticos ni impresión directa. Las calificaciones se actualizan manualmente en Clientes. No se requiere ningún servicio remoto para operar.
