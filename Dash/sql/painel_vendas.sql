with map_ies(id_produto,ies_name) as (
VALUES 
(53,'GRADUAÇÃO'),
(16,'GRADUAÇÃO'),
(7,'Observership'),
(33,'UNIACADEMIAEAD'),
(57,'CATÓLICA SC'),
(27,'UNIFACEX'),
(17,'UCPEL'),
(26,'PUCPR DIGITAL'),
(29,'GRADUAÇÃO'),
(37,'Pós UNIFSA'),
(41,'Pós PUCRJ'),
(30,'UNISANTOS'),
(22,'GRADUAÇÃO'),
(48,'GRADUAÇÃO'),
(14,'GRADUAÇÃO'),
(12,'URCAMP'),
(39,'UNICEP'),
(10,'UNIFEOB'),
(54,'Curta Duração PUCPR DIGITAL'),
(9,'UNIPAM'),
(35,'IMED'),
(2,'Pós Santa Casa'),
(8,'Pós HSL'),
(44,'Pós +Campus'),
(51,'Pós PUCCAMPINAS'),
(36,'Pós NEWTON PAIVA'),
(47,'Pós UDF'),
(20,'PUC GOIAS'),
(38,'Pós PUC GOIAS'),
(55,'Curta Duração PUCRJ'),
(28,'UNIVAP'),
(25,'UMC'),
(43,'GRADUAÇÃO'),
(32,'Pós UNISINOS'),
(31,'Pós UNIFACEX'),
(23,'UNIVILLE'),
(24,'UNOESC'),
(62,'PUCRJ Collab'),
(19,'GRADUAÇÃO'),
(59,'PSICOTERAPIA'),
(52,'Curso Online '),
(11,'GRADUAÇÃO'),
(49,'Curta Duração HSL'),
(64,'Cursos Artmed'),
(13,'UNIARP'),
(63,'ESPM'),
(34,'GRADUAÇÃO'),
(3,'HCOR'),
(18,'UNISC'),
(60,'DOM CABRAL'),
(58,'IMIP'),
(15,'UNIFSA'),
(56,'Curta Duração PUCCAMPINAS'),
(46,'Plataforma A'),
(1,'Pós Artmed'),
(21,'GRADUAÇÃO'),
(42,'PUCPR 4D')

), 
vendas_orbita as (

    SELECT 
        produtos.ies_name,
        vendas.*
    FROM mart_sales.ft_captacao_orbita vendas
    LEFT JOIN map_ies produtos on vendas.sk_produto = produtos.id_produto
    WHERE min_data_pagamento_matricula >= current_date AND 
        sales_origin = 'Call Center'
),
vendas_sispag AS (
    SELECT 
        vd_produto.nomeresumido,
        TO_CHAR(DATE_TRUNC('hour', vd_compra.datahora), 'HH24:MI') AS hr,
        CASE 
            WHEN vd_compra."codVendedor" = '91118' THEN 'mritzel'
            WHEN vd_compra."codVendedor" = '9326' THEN 'lsallaberry'
            WHEN vd_compra."codVendedor" = '9323' THEN 'lsoliveira'
            WHEN vd_compra."codVendedor" = '9185' THEN 'vcorreia'
            WHEN vd_compra."codVendedor" = '9167' THEN 'tcandia'
            WHEN vd_compra."codVendedor" = '91243' THEN 'cassilva'
            WHEN vd_compra."codVendedor" = '91238' THEN 'jcssilva'
            WHEN vd_compra."codVendedor" = '91244' THEN 'jrsantos'
            ELSE NULL
            END as operator_user,
        vd_compraitem.valor * vd_compra.valortotal / NULLIF(SUM(vd_compraitem.valor) OVER (PARTITION BY vd_compra.compraid), 0) AS value,
            CASE
        WHEN vd_compra."codVendedor" IS NULL THEN 'eCommerce'
        WHEN LEFT(vd_compra."codVendedor"::text, 1) = '8' THEN 'Representantes'
        WHEN LEFT(vd_compra."codVendedor"::text, 1) = 'R' THEN 'Renovacao'
        ELSE 'SECAD'
    END AS channel,
    
        CASE
        WHEN vd_compra."codVendedor" IS NULL THEN DATE(timezone('America/Sao_Paulo'::text, timezone('UTC'::text, vd_compra.datahora)))
        WHEN vd_compra."codVendedor"::text = '8000'::text THEN DATE(timezone('America/Sao_Paulo'::text, timezone('UTC'::text, vd_compra.datahora)))
        ELSE DATE(vd_compra.datahora)
        
    END AS data
    FROM app_sispag_pagamento.vd_compra
    LEFT JOIN app_sispag_pagamento.vd_compraitem ON vd_compra.compraid = vd_compraitem.compraid
    LEFT JOIN app_sispag_pagamento.vd_produto ON vd_compraitem.produtoid = vd_produto.produtoid
    LEFT JOIN app_sispag_pagamento.vd_request ON vd_compra.requestid = vd_request.requestid
    LEFT JOIN app_sispag_pagamento.vd_cliente ON vd_compra.clienteid = vd_cliente.clienteid
    LEFT JOIN bu_secad.programs ON vd_produto.nomeresumido::text = programs.program
    WHERE vd_compra.datahora::date = current_date
    AND vd_produto.tipoproduto::text IN ('P')
    AND vd_request.ambiente::text = 'P'
    AND LOWER(vd_cliente.nome::text) NOT LIKE '%teste%'
), 

vendas_agrup as (
select ies_name,
count(*) as vendas
from vendas_orbita
group by ies_name

UNION ALL

SELECT 
channel as ies_name,
count(*) as vendas
FROM vendas_sispag
WHERE channel = 'SECAD' and operator_user IS NOT NULL
GROUP BY channel
)

select * 
from vendas_agrup
ORDER BY
    CASE ies_name
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