with map_status (status_atual,stas_atend) as (
VALUES
('active','Descartar'),
('ClosedAttendant','Encerrado'),
('ClosedClient','Encerrado'),
('ClosedClientInactivity','Encerrado'),
('enrolled','Matriculado'),
('Open','Atendimento'),
('qualified','Atendimento'),
('Transferred','Descartar'),
('waiting','Fila'),
('Waiting','Fila')
),
atend_blip as  (
SELECT 
    rpch.system as sistema,
    CASE 
        WHEN rpch.queue = 'CESMAC' THEN 'GRADUAÇÃO STANDARD'
        WHEN rpch.queue = 'FAESA' THEN 'GRADUAÇÃO STANDARD'
        WHEN rpch.queue = 'PÓS FAESA' THEN 'GRADUAÇÃO STANDARD'
        WHEN rpch.queue = 'UCPEL' THEN 'GRADUAÇÃO STANDARD'
        WHEN rpch.queue = 'UCS' THEN 'GRADUAÇÃO STANDARD'
        WHEN rpch.queue = 'UCS PÓS' THEN 'GRADUAÇÃO STANDARD'
        WHEN rpch.queue = 'UNIVALI' THEN 'GRADUAÇÃO STANDARD'
        WHEN rpch.queue = 'UNICEP' THEN 'GRADUAÇÃO STANDARD'
        WHEN rpch.queue = 'UNISAGRADO' THEN 'GRADUAÇÃO STANDARD'
        WHEN rpch.queue = 'PUCPR' THEN 'GRADUAÇÃO PREMIUM'
        WHEN rpch.product = 'PUCPR' THEN 'GRADUAÇÃO PREMIUM'
        WHEN rpch.queue = 'UNISINOS' THEN 'GRADUAÇÃO PREMIUM'
        WHEN rpch.product = 'UNISINOS' THEN 'GRADUAÇÃO PREMIUM'
        ELSE rpch.product
    END AS Produto,        
    rpch.account_id,
    rpch.conversation_id as id,
    rpch.parent_ticket_id as fist_ticket_id,
    rpch.opened_at as data_abertura_ticket,
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
WHERE rpch.opened_at::date = current_date  AND
rpch.system = 'BLIP' AND
rpch.product != 'Artmed 360'
)

SELECT 
    produto as Ies,
    COUNT (*) FILTER (WHERE status = 'Fila') as Fila,
    COUNT (*) FILTER (WHERE status = 'Atendimento') as "Em Atendimento",
    COUNT (*) FILTER (WHERE status = 'Encerrado') as Encerrado
FROM atend_blip
WHERE status != 'Descartar'
GROUP BY produto