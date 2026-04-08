WITH hist_tab AS (
    SELECT
        call_id, call_type, customer_id, phone_number, agent_id, agent,
        campaign_id, campaign, tablename,
        CASE
            WHEN tablename ILIKE '%HUB%' OR campaign ILIKE '%HUB%' THEN 'REGUA'
            WHEN call_type ILIKE '%R%'                              THEN 'RECEPTIVO'
            WHEN call_type ILIKE '%M%'                              THEN 'MANUAL'
            ELSE 'MAILING'
        END AS mailing_category,
        CASE
            WHEN tablename ~* 'mental|psicologia' THEN 'Psicologia'
            WHEN tablename ~* 'multi'             THEN 'Multi'
            WHEN tablename ~* 'fisio'             THEN 'Fisioterapia'
            WHEN tablename ~* 'enf'               THEN 'Enfermagem'
            WHEN tablename ~* 'medic'             THEN 'Medicina'
            WHEN tablename ~* 'nutri'             THEN 'Nutrição'
            WHEN tablename ~* 'vet'               THEN 'Veterinária'
            WHEN tablename ~* 'ped'               THEN 'Pediatria'
            WHEN tablename ~* 'psiquia'           THEN 'Psiquiatria'
            ELSE 'Outras Áreas'
        END AS area,
        start_agent_date::date AS data,
        EXTRACT(HOUR FROM start_agent_date) AS hour,
        CASE WHEN disposition_nivel_1 = 'AbortCustomerOnQueue' THEN 1 ELSE 0 END AS drop,
        CASE WHEN disposition_nivel_1 = 'TransferModule'       THEN 1 ELSE 0 END AS hangup,
        CASE WHEN EXTRACT(EPOCH FROM wrap_duration) > 0        THEN 1 ELSE 0 END AS answered,
        ROW_NUMBER() OVER (PARTITION BY call_id ORDER BY end_agent_date) AS rn
    FROM integration_operations.vw_call_center_calls cc
    WHERE campaign_id IN (1025, 1605, 1700, 1553, 1299, 1690)
    AND start_agent_date::date >= current_date - interval '5 months'
)
SELECT
    area, data,
    COUNT(*)      AS tentativas,
    SUM(answered) AS atendidas,
    SUM(drop)     AS drop,
    SUM(hangup)   AS hangup
FROM hist_tab
GROUP BY area, data
