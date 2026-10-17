# Revisión Sudameris bloque A — 17/10/2026

Alcance: filas 3 a 23 inclusive del CSV asignado (21 campañas). Descarga oficial exitosa de los 20 PDF enlazados; se leyeron visualmente todas las páginas renderizadas. Saspy Express no tiene PDF en el CSV y queda pendiente.

Entregables: reviews.json contiene 28 registros separados por prestación/comercio con SHA256 exacto; branches.json conserva 16 direcciones oficiales sin coordenadas inventadas; pending.json lista las limitaciones. Los PDF y PNG quedan junto a estos archivos como evidencia. No se modificó el repositorio.

Hallazgos que requieren tratamiento en la integración:
- Club Náutico: la fecha general 31/10/2026 NO debe extenderse a El Burguero, Asadito Aquino y La Casita Gourmet de Yudith (31/03/2026), ni Catas Nómadas (15/02/2026). Se conservan registros vencidos recuperables.
- Club Sajonia: PDF asignado verifica únicamente mesas/entradas Bierfest 13–30/10/2026 o hasta agotar stock. No respalda los beneficios recurrentes del texto de la ficha. Pie editorial 2025 contradice año2026 del cuerpo; documentado.
- DTA: documento verifica convenio hasta31/12/2028, no el evento Oktoberfest10/10/2026 que mezcla la ficha.
- Real: reintegro únicamente primer viernes mensual; financiación todos los días sólo electrodomésticos/jardín/decoración. Tope mensual1.500.000 no especifica alcance a financiación.
- CCU: reintegro primer jueves mensual,11 estaciones listadas. Dos filas tienen misma dirección Santa Rita: preservar nombres y revisar antes de fusionar pines.
- Kessel: sólo Malutín & Lilio y Sky Bar; San Bernardino excluido.
- Frigomas: sólo Paseo Miraflores, sin web, tope800.000 durante toda vigencia.
- Drugstore: cinco sucursales, tope800.000 durante promoción para reintegro. 100% corresponde al origen nacional del medicamento, no al descuento. No sumar descuento y reintegro como tasa única.
- Sin fecha inicial explícita en algunos beneficios de Encarnación, DTA, CNSB y Compras en Exterior: start vacío deliberadamente, fecha final sí consta.

Validación: JSON parseable,20 hashes contra bytes descargados,28 registros. Las categorías son clasificación editorial; días Todos los días en campañas sin restricción semanal significan intervalo general, no horario de apertura. Sin publicación ni pruebas de aplicación porque esta tarea sólo entrega evidencia para integración.
