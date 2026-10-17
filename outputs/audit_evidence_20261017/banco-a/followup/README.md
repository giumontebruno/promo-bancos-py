# Segunda revisión de pendientes

## Atlas

Se consultaron otra vez las páginas oficiales 2, 3 y 4 y los dos documentos enlazados. Siete registros revisados: uno resuelto, seis pendientes; ninguna fuente inaccesible.

**Miércoles Plus**: la página indica explícitamente 21/10/2026. El PDF de una página, leído visualmente, confirma 21 de octubre y muestra excepciones: Nike, Academy y Verónica Torre tienen 10% en caja +10% de reintegro con QR, hasta tres cuotas; Prüne y Nueva Americana tienen 20% +10%, hasta doce cuotas; el grupo principal enumerado tiene 20% +10%, hasta tres cuotas. La ficha conserva «Hasta20%» y las excepciones sin extender la campaña a todos los locales del shopping. Fecha y detalles corregidos, protegidos por hash del texto y PDF en `data/atlas_document_reviews.json`.

Alias adicional: `fd8cedfb36f09b95` → `57b016cd047fb17d`. Lista completa actualizada en `../atlas-id-aliases.json`.

**Pendientes:** delSol, SUEÑOLAR, Cecconello, Di Valentini, BOX Mayorista y Supermercados. Las fuentes oficiales no aportan fecha final completa con año. Cinco no enlazan bases adicionales; Supermercados enlaza una imagen de tarjetas, locales adheridos y compras online, sin vigencia. No se dedujo un año ni se declaró la renovación. IDs, URLs y motivos: `atlas-results.json`. Respuestas y hashes de documentos: `atlas-evidence.json`.

Dos pruebas nuevas de revisión documental aprobadas; cinco pruebas anteriores también aprobadas, incluida la fecha numérica21/10/2026. No se ejecutó normalización ni publicación.

## Itaú

La revisión terminó: 14 fichas se separaron en 30 variantes legítimas por tipo de tarjeta y tope. El CSV pasó de 532 a 548 filas. Las tres fichas b=16359 (Benditta Collection, Benditta Style For Men y Dudalina) presentan contradicción entre el resumen de 5% de reintegro y el detalle de 10%; se conservaron como no confirmadas hasta que el banco aclare la fuente. No corresponde seleccionar arbitrariamente uno de esos porcentajes.

BROTZEIT aplica martes a viernes; los otros nueve gastronómicos de esa campaña, martes a sábados. Salemma conserva descuento en caja y reintegro separados. Se preservaron la identidad histórica, fuente íntegra y revisión protegida por hash. Seis pruebas nuevas aprobadas; las 30 variantes no tienen fechas finales desconocidas, conflictos de fecha ni múltiples topes de compra. Detalles exactos en `../itau-followup.json`.

Miércoles Plus conserva explícitamente un reintegro bancario efectivo de 10% pagando con QR. El descuento en caja de 10% o 20%, según el local, permanece separado y no se suma a una tasa única de reintegro. No se publicaron cambios.
