> Informe inicial. Los conteos y verificaciones posteriores están en [REVISION-FINAL-2026-10-16.md](REVISION-FINAL-2026-10-16.md), que prevalece para el estado actual.

# Auditoría Payback PY — 16/10/2026 Paraguay

Lecturas realizadas el 17/10 UTC (16/10 Paraguay). Rama local `codex/audit-promotions-20261017`, basada en `5d8c227`. No se publicó, hizo push ni desplegó. No se tocaron Growth, WhatsApp, credenciales o servicios.

## Kaiseki: confirmado por PDF oficial actual

La URL solicitada `https://www.sudameris.com.py/storage/app/uploads/public/6ab/eac/909/6abeac9098afc518629989.pdf` respondió 404. Se leyó el PDF enlazado por la nueva página oficial Gastronomía: https://www.sudameris.com.py/descargas/documentos/6ac7a93816c51982829209/gastronimia.pdf (V9, 01/10/2026), sus dos páginas completas. SHA256 `9bfce5b062d49ff1a300acadacac87a942a22d2e272fb48840b9a40638d788ab`.

KAISEKI: **03/08/2025–31/12/2026, lunes a viernes, 20% de reintegro y 5 puntos adicionales Black/Infinite (25%)**. Tope de compra Gs.1.000.000 mensual por comercio/cuenta. Crédito Visa/Mastercard; POS Bancard/Infonet, comercio electrónico habilitado/VPOS Bancard y QR crédito desde Sudameris App. Exclusiones: prepaga, débito, Bancard Check, Gourmet, Móvil, Productivas, Empresariales y otras procesadoras/plataformas. Si existe campaña especial simultánea del comercio, rigen sus condiciones. El viernes16/10 está dentro de esta vigencia. ID `adf5bc3eb1fc7e00` preservado. No se infirió del CSV.

## Resultado local y correcciones

- Catálogo: 2451 → **3080 registros**. 770 IDs nuevos incluyen renovaciones y desdoblamientos; no equivalen a ese número de comercios nuevos. 141 IDs sustituidos archivados en `data/promotion_history_20261017.json`; desaparición no equivale a vencimiento.
- Sudameris: corregida migración del sitio/API.46 campañas descubiertas;40 documentos de beneficios revisados,2 sorteos fuera del catálogo de ahorro y4 campañas sin PDF (Saspy y Zonas Sur/Este/Norte).158 registros derivados de bases verificadas;124 históricos/sin confirmación conservados y ocultos en vista vigente. Fechas particulares de CNSB, Patio Colonial y La Panera Rosa no heredan fin general.104 revisiones estructuradas con SHA y12 filas Gastronomía; Distrito expandido a58 comercios. Condiciones y topes separados por prestación.
- Itaú:32 categorías,532 fichas completas frente a126;531 tras deduplicación.406 URL antes omitidas.17 fichas tienen múltiples topes por tarjeta: se conserva su texto y no se calcula ahorro ilimitado cuando el límite no queda resuelto.
- Continental:44 fichas separadas en130 variantes con fechas/tarjetas/topes propios.827 filas fuente,828 registros normalizados. Identidad de campaña conservada para favoritos.
- BNF:77 beneficios derivados de5 PDF actuales, hashes contrastados. Restaurado alcance compartido de topes por cuenta/rubro/titular/adicionales. Caché se revalida aunque la URL no cambie; una respuesta no PDF no reemplaza el archivo anterior.
- Atlas:16 fechas explícitas recuperadas sin inventar años. Siete finales siguen desconocidos. Alias de cambios de identidad incluidos como evidencia.
- Universitaria:52 tarjetas actuales reconciliadas en71 variantes y3 retenidas. Burger King/Popeyes/Subway: compra200.000, reintegro QR60.000/física20.000; ENERGY compra300.000, QR60.000/física30.000. Se eliminó reutilización de topes antiguos.
- ueno:355 beneficios;15 ventanas Día U corregidas (4del10/10,9del15/10,2del18/10), con horarios. El plazo para mantener saldo no extiende el día de compra. Tres documentos pendientes exactos en reportes fuente.
- Familiar416 y GNB477 inventariados y actualizados. Corregido calendario GNB Cantina Salesianito para ventanas9–11 y16–18/10. No se afirma revisión manual completa de todos sus documentos.
- Vista vigente y notificaciones excluyen Sudameris sin confirmación, fechas desconocidas/contradictorias y ofertas fuera de fecha. Se conserva historial y procedencia.

## Cobertura temporal al 16/10

Estos conteos clasifican fechas del catálogo; **no son una certificación manual de cada registro**. Hay124 registros Sudameris pendientes que se ocultan, aunque una parte esté dentro de las fechas guardadas. Documentos inaccesibles y renovación automática requieren evidencia adicional.

| Banco | Total | Dentro de fechas | Fin anterior | Futuras | Sin fin/conflicto |
|---|---:|---:|---:|---:|---:|
| Atlas | 43 | 23 | 0 | 13 | 7 |
| BNF | 77 | 77 | 0 | 0 | 0 |
| Continental | 828 | 802 | 11 | 4 | 11 |
| Coop. Universitaria | 71 | 54 | 11 | 0 | 6 |
| Familiar | 416 | 415 | 0 | 1 | 0 |
| GNB | 477 | 470 | 6 | 1 | 0 |
| Itaú | 531 | 531 | 0 | 0 | 0 |
| Sudameris | 282 | 255 | 11 | 8 | 8 |
| ueno bank | 355 | 338 | 15 | 2 | 0 |

Inventario completo por ID/URL: `outputs/source_audit_inventory.csv`; cobertura y estado de extracción: `outputs/source_audit_coverage.json`. Los reportes de `outputs/audit_evidence_20261017` distinguen evidencia manual, procesamiento y pendientes. Los inventarios iniciales de agentes están etiquetados como snapshots; usar el inventario general para el estado final.

## Mapa

1.748 →1.841 ubicaciones, con93 entradas oficiales Sudameris (92 físicas y1online). Ningún registro previo, ID o coordenada se perdió.127 coordenadas existentes:58 elegibles,68 requieren revisión y1online.1.713 registros físicos aún carecen de coordenadas;2online en total. **Las93 direcciones nuevas no son93 pines nuevos**.

Eliminados recortes artificiales30/70 del conjunto,18/22 del mapa y14 de la lista. Se excluyen online, coordenadas fuera de rango y aproximaciones; comercios distintos no se fusionan sólo por compartir coordenadas. El constructor conserva candidatos pendientes y ofrece `--skip-geocoding`. No hubo geocodificación paga ni aproximada. Faltan incorporaciones específicas de sucursales de otros bancos; siete grupos de coordenadas compartidas no se eliminaron como duplicados sin prueba.

## Validación y publicación

88 pruebas Python y62 Node aprobadas; build correcto; diff de código sin errores de espacios. Navegador Chrome390px y1440px: sin desbordamiento ni errores JS, búsqueda Kaiseki/restablecimiento correctos, mapa completo del filtro con/sin GPS. Proveedor de mapa simulado para evitar llamadas pagas; esto no prueba disponibilidad del proveedor en producción. Resultado detallado en `outputs/audit_evidence_20261017/ui-results.json`.

Antes de publicar: revisar esta rama y el diff completo, actualizar contra main sin sobrescribir el refresco diario, revisar alias e historial y aprobar alcance. **Pages y backend Sites son despliegues separados**; cambio `server/schedule.js` requiere el backend existente. No se ejecutó ninguno. Pendientes sin solución oficial permanecen identificados; no se garantiza «cero errores» ni auditoría manual exhaustiva de miles de condiciones.
