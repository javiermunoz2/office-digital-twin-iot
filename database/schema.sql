-- Esquema de la base de datos historica del gemelo digital.
-- n8n inserta una lectura por minuto en lecturas_sensores; las vistas
-- agregadas alimentan al asistente virtual (chatbot).

DROP VIEW IF EXISTS vista_resumen_diario;
DROP VIEW IF EXISTS vista_media_30min;
DROP TABLE IF EXISTS lecturas_sensores;

-- NIVEL 1: tabla real (para Machine Learning), un dato cada minuto
CREATE TABLE lecturas_sensores (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP NOT NULL,
    dispositivo VARCHAR(50),
    temperatura NUMERIC(5, 2),
    humedad NUMERIC(5, 2),
    co2 NUMERIC(6, 2),
    ruido NUMERIC(5, 2),
    gas NUMERIC(6, 2),
    raw_data JSONB
);

-- NIVEL 2: medias en bloques de 30 minutos (chatbot, datos recientes)
CREATE VIEW vista_media_30min AS
SELECT
    to_timestamp(floor(extract(epoch from fecha) / 1800) * 1800) AT TIME ZONE 'UTC' as tramo_30min,
    ROUND(AVG(temperatura), 2) as media_temp,
    ROUND(AVG(humedad), 2) as media_humedad,
    ROUND(AVG(co2), 2) as media_co2
FROM lecturas_sensores
GROUP BY tramo_30min
ORDER BY tramo_30min DESC;

-- NIVEL 3: resumen diario (chatbot, historico)
CREATE VIEW vista_resumen_diario AS
SELECT
    DATE(fecha) as dia,
    ROUND(AVG(temperatura), 2) as media_temp,
    MAX(temperatura) as max_temp,
    MIN(temperatura) as min_temp,
    ROUND(AVG(humedad), 2) as media_humedad,
    ROUND(AVG(co2), 2) as media_co2
FROM lecturas_sensores
GROUP BY DATE(fecha)
ORDER BY dia DESC;
