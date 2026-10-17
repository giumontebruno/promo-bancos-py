# Auditoría Itaú, BNF, Continental y Atlas

Fecha objetivo: viernes 16 de octubre de 2026, Paraguay. Lecturas realizadas el 17 de octubre UTC. No hubo publicación ni despliegue.

## Alcance y evidencia

El inventario inicial se tomó del catálogo público local de 2489 registros. `coverage.json` cuenta todos los registros de los cuatro bancos; `pending-records.json` enumera IDs, fuentes, fechas y problemas del estado inicial. Es un inventario de calidad, no una certificación de vigencia de cada oferta.

| Banco | Registros iniciales | Dentro de fechas del catálogo | Fin desconocido | Fin anterior al 16/10 |
|---|---:|---:|---:|---:|
| Itaú | 126 | 126 | 0 | 0 |
| BNF | 77 | 77 | 0 | 0 |
| Continental | 742 | 718 | 13 | 11 |
| Atlas | 43 | 20 | 23 | 0 |

### BNF

Se volvieron a descargar los cinco PDF oficiales de octubre: mayoristas, farmacias, estaciones de servicio, supermercados y frigoríficos. Todos respondieron HTTP 200 y coincidieron byte a byte con los documentos usados por el extractor. URLs y SHA256 están en `fresh-source-checks.json`; textos de primeras páginas están junto a este informe. Se leyeron las condiciones, fechas, tarjetas, topes, medios y exclusiones de esos cinco documentos. Las sucursales provienen del extractor de tablas, no de una revisión visual manual de cada dirección.

Los 77 beneficios corresponden a cinco documentos, no a 77 verificaciones independientes. Se corrigió la pérdida del alcance de topes: el extractor antes reducía una cláusula completa a un importe mensual, omitiendo cuenta, titular/adicionales y conjunto de locales/rubro. Ahora conserva la cláusula oficial pertinente. Ejemplo: Cooperativa Chortitzer 30%, ID inicial `896de7bffb9bce58`, compra máxima de Gs. 1.000.000 compartida por cuenta y rubro frigoríficos. Los CSV se regeneraron sin acceder nuevamente al API, usando el texto original y las sucursales ya extraídas. La normalización en memoria no produjo alertas.

También se detectó que `download_pdf` reutilizaba una URL ya guardada sin volver a comprobarla. En esta auditoría se verificaron los cinco hashes contra red; el agente principal corrigió después el descargador para revalidar contenido en cada ejecución, comprobar la firma PDF y conservar el caché ante fallos.

### Atlas

El extractor usa atributos de las tarjetas oficiales que incluyen condiciones completas; no descarga automáticamente los PDF enlazados. Se recuperaron 16 fechas explícitas que el normalizador no interpretaba: formato `31/12 del 2026`, una fecha puntual, y dos fechas adyacentes como `30 y 31 de octubre de 2026`. No se dedujo ningún año ni se rellenaron intervalos entre fechas no consecutivas. Detalle y exclusiones originales permanecen completos.

Quedan siete registros con fin desconocido: Miércoles Plus, delSol, SUEÑOLAR, Cecconello, Di Valentini, BOX Mayorista y Supermercados. Nueve contienen topes no normalizados. `post-fix-preview.json` contiene IDs y fuentes exactas. No deben presentarse como vigentes confirmados.

Como la identidad actual incorpora el texto de vigencia, los 16 cambios de formato producen nuevos IDs. `atlas-id-aliases.json` contiene la correspondencia recuperable para integrar en el historial/alias sin perder referencias.

### Itaú

La página principal oficial enlaza 32 categorías. El extractor restringía la ingesta a una lista de 12 identificadores, de los cuales 11 aparecían en la página actual. La lectura de las otras 21 categorías encontró 406 URLs de detalle únicas ausentes del CSV de 126 filas. El inventario exacto está en `itau-omitted-links.json` y las categorías en `itau-live-categories.json`. Esos enlaces son candidatos oficiales; no deben contarse automáticamente como promociones vigentes.

Se eliminó la lista restrictiva, se agregaron comprobaciones de HTTP y de integridad de la ficha/categoría, y se guarda HTML individual para trazabilidad. Un error aborta antes de reemplazar los CSV. La ingesta terminó: 32 categorías, 566 tarjetas incluyendo duplicados y 532 fichas únicas completas, exactamente 406 URL nuevas. La comprobación de estructura de las 32 páginas no encontró errores. Las 532 tienen un rango de fecha que incluye el 16/10/2026; eso no significa que todas apliquen el viernes o a todas las tarjetas. Diecisiete fichas tienen varios topes y sus IDs/fuentes quedaron en `itau-complete-results.json`. No se afirma una revisión manual individual de las 532 condiciones. CSV y Markdown quedaron regenerados; el catálogo público espera la integración del agente principal.

### Continental

La fuente es el API oficial de comercios y sus descripciones completas. Se detectaron 42 filas con fechas diferentes dentro del texto, mientras el CSV sólo conservaba la primera. Ejemplo: 836 Cocina Internacional termina el 24/10/2026 para Privilege/Black/Infinite, pero el segmento Dinelco/Clásica/Oro tiene otra fecha. CREA tiene descuento vencido y financiación todavía dentro de plazo. No se debe extender toda la fila a la fecha mayor.

La corrección terminó: 44 fuentes se separaron en 130 variantes, cubriendo las 42 inicialmente detectadas más Biggie Farma y La Negrita. CSV/Markdown pasaron de 741 a 827 filas. Las variantes conservan texto original completo y vigencia original de identidad para que el normalizador preserve las referencias de campaña/favoritos. Los detalles de cada variante contienen sus propios beneficios, tarjetas, topes y fecha. Seis pruebas aprobadas y verificación en memoria de las 130 variantes sin fechas finales desconocidas ni conflictos. Informe exacto: `continental-segmentation-report.json`. No se ejecutó normalización ni publicación desde esta auditoría delegada.

## Validación de cambios propios

`python -X utf8 -m unittest discover -s tests -p test_bank_a_audit.py`: cinco pruebas aprobadas (formatos Atlas válidos, fechas inseguras intactas, alcance BNF y descubrimiento exhaustivo/fallo seguro Itaú). `git diff --check` acotado al código modificado: sin errores. La integración final, normalización, pruebas generales y publicación pertenecen al agente principal.
