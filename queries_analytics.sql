/*******************************************************************************
   PROJETO: EMPÓRIO DAS GERAÇÕES - BUSINESS INTELLIGENCE (Q1 2026)
   AUTHOR: RUAN MENDES
   DATA: ABRIL / 2026
*******************************************************************************/

/* 1. RELATÓRIO DE SAZONALIDADE MENSAL
   PROBLEMA: O dono precisa entender a evolução das vendas mês a mês para planejar o fluxo de caixa.
   OBJETIVO: Agrupar o faturamento por mês, convertendo o código numérico para o nome do mês.
*/
WITH sold_by_month AS (
    SELECT
    	STRFTIME('%Y', o.order_date) AS year_number,
        STRFTIME('%m', o.order_date) AS month_number,
        ROUND(SUM(oi.quantity * oi.price), 0) AS total_sold
    FROM order_items oi
    JOIN orders o ON oi.id_order = o.id_order 
    GROUP BY year_number, month_number
)
SELECT
	year_number as year,
    CASE
        WHEN month_number = '01' THEN 'January'
        WHEN month_number = '02' THEN 'February'
        WHEN month_number = '03' THEN 'March'
        WHEN month_number = '04' THEN 'April'
        WHEN month_number = '05' THEN 'May'
        WHEN month_number = '06' THEN 'June'
        WHEN month_number = '07' THEN 'July'
        WHEN month_number = '08' THEN 'August'
        WHEN month_number = '09' THEN 'September'
        WHEN month_number = '10' THEN 'October'
        WHEN month_number = '11' THEN 'November'
        WHEN month_number = '12' THEN 'December'
    END AS month_name,
    total_sold
FROM sold_by_month
ORDER BY year_number ASC, month_number ASC;


/* 2. RANKING DE CLIENTES VIP (CURVA ABC)
   PROBLEMA: Identificar quais clientes são responsáveis pela maior fatia do faturamento.
   OBJETIVO: Listar os 10 clientes com maior gasto acumulado para ações de CRM e fidelidade.
*/
SELECT
    c.customer_name,
    SUM(oi.quantity * oi.price) AS total_gasto
FROM order_items oi
JOIN orders o ON oi.id_order = o.id_order
JOIN customer c ON o.id_customer = c.id_customer
WHERE o.id_status = 5
GROUP BY c.id_customer
ORDER BY total_gasto DESC
LIMIT 10;


/* 3. REPOSIÇÃO DE ESTOQUE E LOGÍSTICA
   PROBLEMA: Evitar a ruptura de estoque (produto faltante) e identificar quem deve ser acionado para entrega.
   OBJETIVO: Filtrar produtos com estoque crítico (<= 10) e mostrar o fornecedor com histórico de compra ativo.
*/
SELECT
    p.product_name,
    p.product_stock,
    s.supplier_name
FROM product p
JOIN product_supplier ps ON p.id_product = ps.id_product
JOIN supplier s ON ps.id_supplier = s.id_supplier 
WHERE p.product_stock <= 10 
  AND ps.last_purchase_date IS NOT NULL
GROUP BY p.id_product
ORDER BY p.product_stock ASC;


/* 4. PERFORMANCE DE CATEGORIAS E TICKET MÉDIO
   PROBLEMA: Entender quais departamentos da loja performam melhor financeiramente e no volume de vendas.
   OBJETIVO: Calcular o faturamento total e a média de gasto por pedido (Ticket Médio) em cada categoria.
*/
WITH category_metrics AS (
    SELECT
        c.category_name as category,
        COUNT(DISTINCT oi.id_order) as total_orders,
        ROUND(SUM(oi.quantity * oi.price), 2) as total_revenue
    FROM order_items oi
    JOIN product p ON oi.id_product = p.id_product 
    JOIN category c ON p.id_category = c.id_category
    JOIN orders o ON oi.id_order  = o.id_order
    WHERE o.id_status = 5
    GROUP BY c.category_name
)
SELECT
    category,
    total_orders,
    total_revenue,
    ROUND((total_revenue * 1.0 / total_orders), 2) as average_ticket
FROM category_metrics
ORDER BY average_ticket DESC;


/* 5. ANÁLISE DE RENTABILIDADE POR PRODUTO
   PROBLEMA: Um faturamento alto pode esconder margens baixas. É necessário saber o que realmente gera lucro.
   OBJETIVO: Comparar o preço médio de venda contra o custo médio de aquisição dos fornecedores.
*/
WITH product_costs AS (
    SELECT
        oi.id_product,
        AVG(ps.cost_price) as average_cost,
        AVG(oi.price) as average_price
    FROM order_items oi 
    JOIN product_supplier ps ON oi.id_product = ps.id_product
    JOIN orders o ON oi.id_order = o.id_order
    WHERE o.id_status  = 5
    GROUP BY oi.id_product 
)
SELECT
    p.product_name,
    pc.average_cost,
    pc.average_price,
    (pc.average_price - pc.average_cost) AS profit_margin_unit
FROM product p
JOIN product_costs pc ON p.id_product = pc.id_product
ORDER BY profit_margin_unit DESC
LIMIT 10;


/* 6. INDICADOR DE EFICIÊNCIA DE CARRINHO (CROSS-SELL)
   PROBLEMA: Entender se os clientes estão levando mais de um item ou se a loja está sendo usada para compras de conveniência única.
   OBJETIVO: Calcular o percentual de pedidos que possuem apenas 1 item em relação ao total.
*/
SELECT 
    COUNT(*) AS total_orders_general,
    SUM(CASE WHEN items_count = 1 THEN 1 ELSE 0 END) AS single_item_orders,
    ROUND((SUM(CASE WHEN items_count = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2) AS single_item_percentage
FROM (
    SELECT oi.id_order, COUNT(*) AS items_count 
    FROM order_items oi
    JOIN orders o ON oi.id_order = o.id_order 
    WHERE o.id_status  = 5
    GROUP BY oi.id_order
);


/* 7. CONCENTRAÇÃO E MIX DE FORNECEDORES
   PROBLEMA: Dependência excessiva de poucos fornecedores pode ser um risco operacional.
   OBJETIVO: Quantificar a variedade de itens (mix) atendida por cada parceiro comercial.
*/
SELECT
    s.supplier_name,
    COUNT(ps.id_product) as product_mix_count
FROM product_supplier ps
JOIN supplier s ON ps.id_supplier = s.id_supplier 
GROUP BY s.id_supplier
ORDER BY product_mix_count DESC;


/* 8. MONITORAMENTO DE RETENÇÃO (CHURN PREVENTIVO)
   PROBLEMA: Clientes que compram todos os meses são a base do negócio. Identificá-los é vital para prevenção de perda.
   OBJETIVO: Filtrar clientes que registraram atividade de compra em todos os meses de 2025.
*/
SELECT 
    c.id_customer,
    c.customer_name,
    c.customer_phone,
    c.customer_email 
FROM orders o
JOIN customer c ON o.id_customer = c.id_customer 
WHERE STRFTIME('%Y', o.order_date) = '2025' AND o.id_status = 5
GROUP BY c.id_customer
HAVING COUNT(DISTINCT STRFTIME('%m', o.order_date)) = 12
ORDER BY c.customer_name;


/* 9. ANÁLISE DE PRODUTOS OBSOLETOS (DORMANT PRODUCTS)
   PROBLEMA: Itens sem venda ocupam espaço físico e geram custo de oportunidade.
   OBJETIVO: Identificar produtos do catálogo que não registraram nenhuma saída no trimestre.
*/
SELECT
    p.product_name,
    COUNT(oi.id_order) as total_sold
FROM product p
LEFT JOIN order_items oi ON p.id_product = oi.id_product
GROUP BY p.id_product
HAVING total_sold = 0;


/* 10. MAPA DE CALOR DE ATENDIMENTO (OPERAÇÃO)
   PROBLEMA: Dimensionar a equipe de balcão e reposição conforme o fluxo de clientes.
   OBJETIVO: Agrupar o volume de pedidos por faixas horárias pré-definidas.
*/
SELECT
    CASE
        WHEN STRFTIME('%H', o.order_date) BETWEEN '08' AND '11' THEN 'Morning'
        WHEN STRFTIME('%H', o.order_date) BETWEEN '12' AND '17' THEN 'Afternoon'
        ELSE 'Evening'
    END AS day_period,
    COUNT(*) as orders_volume
FROM orders o
WHERE o.id_status = 5
GROUP BY day_period
ORDER BY day_period;

/* 11. MONITORAMENTO DE FUNIL LOGÍSTICO (SAÚDE DA OPERAÇÃO)
   PROBLEMA: Perda de visibilidade sobre gargalos na separação, atrasos de envio ou altas taxas de cancelamento no mês vigente.
   OBJETIVO: Calcular o volume e a representatividade percentual de cada status de pedido dentro do total de vendas do período.
*/
WITH qtd_orders AS (
    SELECT
        id_status,
        COUNT(*) as qtd
    FROM orders
    WHERE order_date >= '2026-03-01' AND order_date < '2026-04-01'
    GROUP BY id_status
)

SELECT
	s.status,
	qo.qtd as quantity,
	ROUND((qo.qtd * 100.0 / SUM(qo.qtd) OVER()),2) AS 'percentage(%)'
FROM qtd_orders qo
JOIN order_status s ON qo.id_status = s.id_status
ORDER BY qo.qtd DESC

/* 12. EVOLUÇÃO DA TAXA DE CANCELAMENTO (CANCEL RATE)
   PROBLEMA: Necessidade de monitorar se a perda de vendas por cancelamento está aumentando ou diminuindo ao longo dos meses.
   OBJETIVO: Calcular o volume total de pedidos, a quantidade de cancelamentos e a taxa percentual de perda (Cancel Rate) com agrupamento mensal.
*/
WITH cancel_by_month AS (
	SELECT
		STRFTIME('%Y', order_date) as year_number,
		STRFTIME('%m', order_date) as month_number,
		COUNT(*) as total_orders,
		SUM(CASE WHEN id_status = 2 THEN 1 ELSE 0 END) as qtd_canceled		
	FROM orders
	GROUP BY year_number, month_number
)

SELECT
	year_number,
	month_number,
	total_orders,
	qtd_canceled,
	ROUND((qtd_canceled * 100.0 / total_orders), 2) as 'cancel_rate(%)'
FROM cancel_by_month
ORDER BY year_number, month_number