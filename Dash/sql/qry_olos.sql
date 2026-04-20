WITH hist_tab AS (
    SELECT
        call_id,
        campaign_id,
        tablename,
        campaign,

        -- Mailing category simplificado
        CASE
            WHEN tablename ILIKE '%HUB%' OR campaign ILIKE '%HUB%' THEN 'REGUA'
            WHEN call_type LIKE '%R%' THEN 'RECEPTIVO'
            WHEN call_type LIKE '%M%' THEN 'MANUAL'
            ELSE 'MAILING'
        END AS mailing_category,

        -- Área sem regex (mais leve)
        CASE
            WHEN tablename ILIKE '%mental%' OR tablename ILIKE '%psicologia%' THEN 'Psicologia'
            WHEN tablename ILIKE '%multi%'       THEN 'Multi'
            WHEN tablename ILIKE '%fisio%'       THEN 'Fisioterapia'
            WHEN tablename ILIKE '%enf%'         THEN 'Enfermagem'
            WHEN tablename ILIKE '%medic%'       THEN 'Medicina'
            WHEN tablename ILIKE '%nutri%'       THEN 'Nutrição'
            WHEN tablename ILIKE '%vet%'         THEN 'Veterinária'
            WHEN tablename ILIKE '%ped%'         THEN 'Pediatria'
            WHEN tablename ILIKE '%psiquia%'     THEN 'Psiquiatria'
            ELSE 'Outras Áreas'
        END AS area,

        -- SEM cast no filtro
        start_agent_date::date AS data,

        -- Flags
        CASE WHEN disposition_nivel_1 = 'AbortCustomerOnQueue' THEN 1 ELSE 0 END AS drop,
        CASE WHEN disposition_nivel_1 = 'TransferModule' THEN 1 ELSE 0 END AS hangup,
        CASE WHEN wrap_duration > interval '0 seconds' THEN 1 ELSE 0 END AS answered

    FROM integration_operations.vw_call_center_calls cc

    WHERE campaign_id IN (1025, 1605, 1700, 1553, 1299, 1690)

    -- 🔥 ESSENCIAL: sem cast
    AND start_agent_date >= current_date - interval '3 months'
)

SELECT
    area,
    data,
    COUNT(*) AS tentativas,
    SUM(answered) AS atendidas,
    SUM(drop) AS drop,
    SUM(hangup) AS hangup
FROM hist_tab
GROUP BY area, data;