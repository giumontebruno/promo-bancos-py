# Revisión final previa a publicación

Estado: cambios locales en `codex/audit-promotions-20261017`, sin push ni despliegue. Este documento complementa y actualiza el informe inicial `AUDITORIA-2026-10-16.md`.

## Cierre de esta revisión

- Catálogo final: **3096 registros**; no equivale a promociones activas. Las sustituciones subieron de141 a**144** tras cerrar pendientes adicionales. Archivo histórico actualizado.
- Favoritos: **150 referencias comprobadas**, 74 conservadas directamente y 76 resueltas por alias; **0 huérfanas y0 ciclos**. Detalle por ID en `outputs/favorite_migration_audit.json`.
- Pruebas finales: **100 Python,64 Node**, build y diff-check correctos. Chrome390/1440 sin desbordamiento ni errores JS; proveedor de mapas simulado, sin cargos externos.
- Atlas:1 de7 pendientes resuelto; Miércoles Plus21/10/2026. Seis sin fecha completa: delSol, SUEÑOLAR, Cecconello, Di Valentini, BOX Mayorista y Supermercados. Fuentes accesibles pero insuficientes; sin inferir años. Véase `outputs/audit_evidence_20261017/banco-a/followup/atlas-results.json`.
- Itaú:14 de17 pendientes resueltos en30 variantes;548 filas fuente. Benditta Collection, Benditta Style For Men y Dudalina siguen ocultos por contradicción oficial5%/10%. URLs y evidencia en `outputs/audit_evidence_20261017/banco-a/itau-followup.json`.
- Sudameris: continúan124 registros sin confirmar, incluyendo fuentes históricas y campañas sin PDF. No se los declara vencidos por inaccesibilidad. Familiar/GNB y otros pendientes conservan el alcance de verificación del informe inicial y el inventario final por ID.
- Mapa:61 ubicaciones elegibles en total;3 candidatos existentes confirmados, **0 coordenadas nuevas inventadas o geocodificadas**. Las93 direcciones incorporadas siguen sin aportar coordenadas oficiales.8 rechazados,57 pendientes de los68 revisados;60 candidatos adicionales sin coordenadas documentados.
- Medición actual sin GPS: **18 pines con el recorte anterior frente a46 ahora**, con el mismo catálogo y filtro. De los3 candidatos confirmados, **1 aparecen en ese filtro**; el resto depende de los días y condiciones de sus promociones. La medición anterior aisló22 recuperados sólo por quitar el recorte (18→40). Además se corrigió el enlace de categorías Mayoristas/Frigoríficos al índice de Supermercados; no se atribuye ese efecto a coordenadas nuevas. Conteos por día en `ui-results.json`.

## Diff y riesgos

| Archivos | Cambio | Riesgo y control |
|---|---|---|
| `scrapers/extract_sudameris.py`, `sudameris_campaigns.py`, `build_sudameris_table.py`, `data/sudameris_document_reviews.json` | Nueva API, fuentes actuales, SHA por revisión, condiciones por variante y vencimiento por comercio | Un documento modificado invalida la revisión; zonas sin bases se conservan sin confirmación |
| `extract_itau.py`, `extract_continental.py` | Todas las categorías Itaú y separación Continental por tarjeta, prestación y fechas | Un título general no debe extender vigencias o topes; contradicciones quedan pendientes |
| `extract_bnf.py`, `extract_atlas.py`, `review_universitaria.py`, `extract_ueno_tables.py`, `build_gnb_live_offers.py` | Alcance de topes, fechas explícitas, importes actuales y ventanas reales de compra | Mantener saldo no equivale a poder comprar; no inferir años ni fechas faltantes |
| `promo_backend/normalize.py`, `quality.py` | Procedencia actual sin cambiar URL de identidad; límites revisados por variante; ventana de compra prioritaria; migración de favoritos | Los nuevos IDs no pueden dirigir un beneficio a otra tarjeta; auditoría exhaustiva de referencias archivadas |
| `promo_backend/run_all.py` | Estado parcial cuando quedan fuentes sin confirmar | Una extracción parcial no se comunica como verificación completa |
| `app-web/app.js` | Vigencia estricta, ahorro no calculado con topes ambiguos, mapa sin recortes, validación de coordenadas | Sin fecha final normalizada no se muestra vigente; más puntos pueden aumentar carga de interfaz |
| `server/schedule.js` | Una sola condición nueva: rechazar `source_verification === "unconfirmed"` en `isDue` | Despliegue independiente: publicar sólo web no actualiza este guard del servidor |
| `build_locations.py`, `location_reviews.py`, `data/location_candidate_reviews.json` | Preservación de metadata y revisión documentada de candidatos con hash | Sólo se habilitan coincidencias confirmadas; cambios de evidencia vuelven a revisión |
| `public/**`, `outputs/**`, `data/promotions.csv`, archivos de revisión e historial | Catálogo regenerado y auditorías trazables | No confundir registros totales con promociones activas ni direcciones con pines |

## Regla exacta de visibilidad

`shouldShowPromotion = isActivePromotion && isDisplayablePromotion`.

`isActivePromotion` usa el día de `America/Asuncion` y devuelve falso si:

1. `source_verification` es `unconfirmed`.
2. `terms.conflicting_dates` es verdadero.
3. Existe `terms.starts_on` y es posterior a hoy.
4. Falta `terms.ends_on`, o es anterior a hoy.

La fecha final es inclusiva. Se eliminó la alternativa que buscaba otra fecha dentro del texto crudo cuando faltaba la vigencia normalizada. La elegibilidad comercial y los filtros de día/mes/ordinal se aplican aparte. No tener una etiqueta de revisión manual no equivale por sí solo a una fuente fallida: las demás fuentes pasan por sus respectivos extractores y controles.

Las filas ocultas permanecen en el catálogo o archivo recuperable, con procedencia y motivo. No se borra historial. Una fecha de convenio con renovación automática se clasifica como pendiente de prueba, no como cancelación confirmada.

`server/schedule.js` ya rechazaba falta de fin, conflicto, inicio futuro y fin pasado. El diff añade únicamente el rechazo de fuente `unconfirmed`; después siguen reglas de día del mes, ordinal y día semanal. No se modificó ni ejecutó el envío, su frecuencia, credenciales o historial de entregas.

## Favoritos e identidad

`scripts/audit_favorite_migrations.py` comprueba cada ID archivado y cada `campaign_id` anterior contra IDs, campañas y aliases actuales, detectando destinos ausentes y ciclos. El resultado exacto está en `outputs/favorite_migration_audit.json`.

La revisión inicial encontró 58 referencias sin destino entre las 141 sustituciones. Se repararon:

- BNF: coincidencia exacta de fuente, comercio, vigencia, día, beneficio y tarjeta. El sufijo generado por colisión puede variar por una aclaración de topes; no debe cambiar la tarjeta favorita.
- Itaú: el mismo beneficio/fuente conserva su referencia aunque cambie su categoría de navegación.
- Sudameris: `data/reviewed_campaign_identities.json` conserva campañas revisadas al separar beneficios. El favorito de una campaña sigue esa campaña, sin elegir arbitrariamente una variante premium.
- Continental: la vigencia original de identidad conserva `campaign_id` al separar fechas de prestaciones.
- Atlas: las 16 referencias corregidas inicialmente resolvían por alias.

El registro de Kaiseki `adf5bc3eb1fc7e00` se mantiene. La prueba de regresión exige que todas las referencias archivadas resuelvan; una nueva sustitución sin destino hace fallar la prueba.

## Mapa: recuperación y pendientes

Se mantienen 1.841 registros y todas las coordenadas previas. Las 93 direcciones nuevas de Sudameris no aportan coordenadas verificadas.

De los 68 candidatos con coordenadas: 3 confirmados, 8 rechazados por corresponder a otra dirección/sucursal y 57 pendientes. Los 3 confirmados son Casa Grütter Fernando de la Mora, Casa Paraná Antequera 661 y Casa Paraná Av. San Antonio 273. Son coordenadas existentes contrastadas con dirección y fuentes; no coordenadas inventadas. Las ubicaciones elegibles pasan de 58 a 61. Además hay 60 candidatos sin coordenadas, fuera del lote de 68, que siguen pendientes.

La medición reproducible de interfaz está en `outputs/audit_evidence_20261017/ui-results.json`. Antes de validar estos tres puntos, quitar los recortes recuperó 22 pines en el filtro probado sin GPS (18 → 40). Los candidatos confirmados se cuentan aparte. Los conteos dependen del filtro y de la fecha, y no equivalen al total de lugares del catálogo.

## Publicación web, sólo después de revisión

1. Revisar diff, pendientes, hashes, aliases y pruebas. Guardar un commit revisable sin publicar todavía.
2. Antes de una publicación autorizada, hacer fetch de `origin/main` y reconciliar actualizaciones diarias; no sobrescribir datos nuevos ni forzar push. Revalidar los archivos afectados si hay conflictos.
3. El workflow existente `.github/workflows/deploy-pages.yml` publica GitHub Pages desde `dist/client`. Se activa con push a main de `app-web/**` o `public/**`, o ejecución manual; también por finalización de refresco/geocodificación. **Un merge/push a main puede desplegar automáticamente**.
4. El workflow ejecuta `npm ci`, `npm test`, `npm run build`, sube el artefacto y despliega. La validación Python debe haberse ejecutado previamente.
5. Confirmar resultado de Actions y URL de Pages; comprobar catálogo, fuentes, favoritos y mapa en el sitio publicado. No declarar éxito por el mero push.

## Publicación backend Sites, separada y todavía no ejecutada

1. Con autorización de despliegue, consultar el Site existente `appgprj_6a887ead2a2c8191ae07a63051cc0b18` y su versión/audiencia actuales. La identidad consta en `.openai/hosting.json`; conservar `DB`, audiencia y configuración. No crear ni recrear el servicio.
2. Obtener la credencial de escritura mediante la herramienta nativa correspondiente y abrir/sincronizar su fuente con el helper oficial de Sites. Comparar antes de aplicar el cambio revisado de `server/schedule.js`; no sustituir a ciegas un backend que haya avanzado. Credenciales sólo por stdin, nunca en archivos, argumentos o informes.
3. Ejecutar las pruebas afectadas y el build. El build existente genera `dist/server/index.js` y conserva metadata de hosting. No hay cambios de esquema ni migraciones DB solicitadas.
4. Empaquetar mediante el flujo oficial de Sites, conservando el `project_id`, commit y archivo verificados. Guardar versión y desplegar mediante las herramientas nativas que correspondan a la audiencia consultada. No asumir que el Site es privado.
5. Seguir el despliegue hasta resultado terminal y conservar versión anterior para reversión. Verificar un endpoint de lectura/estado sin disparar notificaciones reales. No ejecutar `dispatch_notifications.py` como prueba de despliegue.

Publicar Pages no despliega Sites, y viceversa. El guard nuevo de notificaciones sólo quedará activo tras el despliegue del backend.
