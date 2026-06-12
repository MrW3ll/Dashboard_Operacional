with map_status (status_atual,stas_atend) as (
VALUES
('active','Atendimento'),
('ClosedAttendant','Encerrado'),
('ClosedClient','Encerrado'),
('ClosedClientInactivity','Encerrado'),
('enrolled','Matriculado'),
('Open','Atendimento'),
('qualified','Atendimento'),
('Transferred','Encerrado'),
('waiting','Fila'),
('Waiting','Fila')
),
atend_blip as  (
SELECT 
    rpch.system as sistema,
    CASE 
        WHEN rpch.queue = 'CESMAC' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'FAESA' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'PÓS FAESA' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'UCPEL' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'UCS' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'URI' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'UCS PÓS' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'UNIVALI' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'UNICEP' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'UNISAGRADO' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'PUCPR' THEN 'GRADUAÇÃO'
        WHEN rpch.product = 'PUCPR' THEN 'GRADUAÇÃO'
        WHEN rpch.queue = 'UNISINOS' THEN 'GRADUAÇÃO'
        WHEN rpch.product = 'UNISINOS' THEN 'GRADUAÇÃO'
        ELSE rpch.product
    END AS Produto,        
    rpch.account_id,
    rpch.conversation_id as id,
    rpch.parent_ticket_id as fist_ticket_id,
    rpch.opened_at::date as data_abertura_ticket,
    rpch.hour_opened_at as hora_abertura_ticket,
    rpch.closed_at as closed_date,
    rpch.status as status_old,
    ms.stas_atend as status,
    rpch.ticket_id,
    rpch.queue AS fila,
    rpch.tag,
    rpch.attendance as atendente,
    rpch.url_ticket_blip,
    rpch.conversation_id as last_id,
    rpch.router_account_id,
    rpch.template_name,
    rpch.ticket_origin, 
    rpch.contact_identifier as contact_id,
    rpch.is_sql as sql
FROM mart_sales.rpt_partner_conversations_hot rpch
JOIN map_status ms ON ms.status_atual = rpch.status
WHERE rpch.opened_at::date >= current_date - interval '1 week' AND
rpch.system = 'BLIP' AND
rpch.product != 'Artmed 360'
)


SELECT 
    produto as Ies,
    COUNT (*) FILTER (WHERE status = 'Fila') as Fila,
    COUNT (*) FILTER (WHERE status = 'Atendimento') as "Em Atendimento",
    COUNT (*) FILTER (WHERE status = 'Encerrado' AND closed_date IS NOT NULL and closed_date::date = current_date) as Encerrado,
    COUNT (*) FILTER (WHERE status = 'Encerrado' AND closed_date IS NOT NULL and closed_date::date = current_date - interval '7 days') as Encerrado_historico
FROM atend_blip
WHERE status != 'Descartar'
AND atendente IS NOT NULL
and tag not ilike '%FECHADO%'
GROUP BY produto
ORDER BY
    CASE produto
        WHEN 'PUCPR DIGITAL' THEN 1
        WHEN 'Pós PUCCAMPINAS' THEN 2
        WHEN 'PUCRJ Collab' THEN 3
        WHEN 'Pós PUCRJ' THEN 4
        WHEN 'GRADUAÇÃO' THEN 5
        WHEN 'Pós Artmed' THEN 6
        WHEN 'SECAD' THEN 7
        WHEN 'HCOR' THEN 8
        WHEN 'ESPM' THEN 9
        WHEN 'DOM CABRAL' THEN 10
        ELSE 999
    END    