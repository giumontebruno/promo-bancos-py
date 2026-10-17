# Auditoría B — corte 16/10/2026 Paraguay

Se revisó el catálogo actualizado, inventarios y reportes de extracción de Familiar, GNB, Universitaria y ueno. Descarga exitosa no equivale a revisión manual completa. Las cifras siguientes corresponden al catálogo de 2.489 promociones antes de integrar las correcciones de esta auditoría.

| Banco | Publicadas | Dentro de fechas del catálogo | Fin pasado en catálogo | Futuras | Sin fin / conflicto |
|---|---:|---:|---:|---:|---:|
| Familiar | 416 | 415 | 0 | 1 | 0 |
| GNB | 477 | 470 | 6 | 1 | 0 |
| Universitaria | 71 | 54 | 11 | 0 | 6 sin fin |
| ueno | 355 | 347 | 7 | 0 | 1 conflicto |

Estas categorías son diagnósticos de fechas; no prueban vigencia oficial. `inventory.json` contiene los IDs, URLs y fechas de cada caso fuera del rango corriente.

## Correcciones ejecutadas

Universitaria: cuatro documentos oficiales actuales (PDFs de caché de la extracción, con texto completo y SHA256 en `verified-pdfs.json`) contradicen los topes reutilizados por el generador. Burger King, Subway y Popeyes tienen límite de compra mensual por cuenta Gs. 200.000, reintegro QR 30% hasta Gs. 60.000 o físico 10% hasta Gs. 20.000. Estaciones ENERGY tiene límite Gs. 300.000, QR 20% hasta Gs. 60.000 o físico 10% hasta Gs. 30.000. Vigencia 01/10–31/12/2026, miércoles, crédito Panal/Cabal/Mastercard. El PDF de Burger King y Subway fue leído además mediante web oficial; la descarga directa nueva recibió 403 y no se insistió ni sorteó esa denegación. ENERGY y Popeyes se leyeron desde los PDF oficiales ya descargados por el pipeline.

`review_universitaria.py` ahora obtiene el límite explícito del documento corriente; si falta o resulta ambiguo, retiene para revisión en lugar de aplicar el importe anterior. Conserva el texto original con exclusiones. Su ejecución repetida toma la captura actual y no el snapshot de septiembre. Cinco pruebas pasaron. Regenerados únicamente CSV/MD/reporte Universitaria: 52 tarjetas, 71 variantes, 3 retenidas.

La reducción de tarjetas de 63 a 52 se reconcilia como 14 nombres ausentes y 3 nuevos. Ausencia de la web no prueba vencimiento. `universitaria-reconciliation.json` detalla ambos conjuntos. La prueba obsoleta de mínimo 80 variantes se sustituyó por cobertura completa fuente = publicadas o retenidas con motivo, sin intersección.

ueno: quince campañas Día U confundían período de depósito/mantenimiento de saldo con fecha de compra. Nueve se aplican a compras del 15/10, cuatro al 10/10 y dos al 18/10. `ueno-verified-window-changes.json` detalla IDs, URLs, evidencia y SHA256 del PDF. `extract_ueno_tables.py` detecta únicamente frases que restringen expresamente compras; preserva los términos completos, añade vigencia de compras verificada y horario. Cuatro pruebas pasaron, incluyendo rechazo de fechas conflictivas y de plazos de saldo aislados. El padre integra el campo explícito en normalización/calidad. Se regenera desde PDFs/HTML ya descargados mediante `--cached`.

## Cobertura y pendientes exactos

Familiar: extracción oficial 329 tarjetas en 22 páginas, 326 con términos, 416 variantes publicadas. 88 entradas pendientes: 43 comercio no encontrado en términos, 19 fechas ambiguas, 8 calendario sin confirmar, 6 términos vencidos, 4 campañas por expandir a comercios, 3 sin términos, 2 tarjetas sin confirmar, 1 variante monetaria/cuotas compleja retenida sin dividir, 1 año ausente y 1 fechas invertidas. El detalle exacto comercio/URL/motivo se conserva en `pending-sources.json`, copiado del reporte actual. LA BADEÑA inicia 01/12/2026, por lo que no corresponde mostrarla como disponible el 16/10. No se comprobó manualmente cada una de las 416 variantes.

GNB: 250 tarjetas oficiales con 250 enlaces a términos, 477 variantes. Excluidas 20 (compras exterior con intereses), 157 (adelanto con comisión) y 297 (tarjeta declara 31/12 frente a términos 30/06); discrepancia 377 Jullito mantiene fin anterior 28/11 frente a 28/12 en términos. Las seis variantes con fin pasado son cinco Farmacenter (28/09) y Día GNB Casa Rica (14/10). Casa Yasy empieza 19/10. Se inspeccionaron datos oficiales y metadatos; no se releíeron manualmente los 250 documentos, por lo que no se declara auditoría documental completa.

Universitaria: las fechas históricas de Las Hortensias, Malian, Biogenic, AUTOPAR, Materassi, Migone y Meister incluyen renovación automática; no deben rotularse como vencimiento confirmado sólo por el primer término. Sin prueba de continuidad, quedan pendientes de revisión. Ferrex y JOSE A. CARRON tienen fechas pasadas sin esa cláusula en el campo capturado. PUNTOFARMA y ÓPTICA LUCE retenidos por beneficio no cuantificado en título, La Ponde por precio preferencial sin referencia; revisar PDF puede permitir incorporarlos en una siguiente pasada.

ueno: 355 beneficios, 747 registros de sucursales. Tres documentos pendientes: enlace de Raio Bemba lleva a La Guarida Barberos (se retiene por desajuste); bonificación upys ahorro a plazo y ahorro suma cupón umarket no producen beneficio extraído. URLs exactas en `pending-sources.json`. Además las tablas dirigidas Día U tienen escalones de saldo/topes, no completamente estructurados; se conserva el PDF íntegro y no se inventa un tope general.

No se ejecutaron push, despliegues, pagos ni cambios de credenciales. No se modificó el mapa.
