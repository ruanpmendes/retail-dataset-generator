-- ############################################################################
-- PROJETO: Empório E-commerce - Automações de Banco de Dados
-- DESCRIÇÃO: Conjunto de 6 Triggers para gestão de estoque, auditoria de preços,
--            padronização de dados e segurança de registros.
-- AUTOR: Ruan Pereira Mendes
-- ############################################################################

-- Trigger para registar na tabela de log, alterações de preços
CREATE TRIGGER trg_log_product
AFTER UPDATE OF product_price ON product
FOR EACH ROW
BEGIN
	INSERT INTO log_product(id_product, old_product_price, new_product_price, command) VALUES
	(OLD.id_product, OLD.product_price, NEW.product_price, 'U');
END;

-- ##############################################################################################
-- Trigger subtrair o estoque do item ao ser vendido
CREATE TRIGGER trg_stock_control_rem
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
	UPDATE product
	SET product_stock = product_stock - NEW.quantity 
	WHERE id_product = NEW.id_product;
END;

-- ##############################################################################################
-- Trigger estornar o estoque do item se a comprar for cancelada
CREATE TRIGGER trg_control_add
AFTER DELETE ON order_items
FOR EACH ROW
BEGIN
	UPDATE product
	SET product_stock = product_stock + OLD.quantity
	WHERE id_product = OLD.id_product;
END;

-- ##############################################################################################
-- Trigger padronizar os emails para caixa baixa
CREATE TRIGGER trg_lower_email
AFTER INSERT ON customer
FOR EACH ROW
BEGIN
	UPDATE customer
	SET customer_email = LOWER(TRIM(NEW.customer_email))
	WHERE id_customer = NEW.id_customer;
END;

-- ##############################################################################################
-- Trigger para impedir exclusão, altera o status para canceled(cancelado)
CREATE TRIGGER trg_order_delete
BEFORE DELETE ON orders
FOR EACH ROW
BEGIN
	UPDATE orders
	SET status = 'Canceled'
	WHERE id_order = OLD.id_order;
	SELECT RAISE(IGNORE);
END;

-- ##############################################################################################
-- Trigger para estornar a quantidade de um produto, quanto o pedido todo for excluido
CREATE TRIGGER trg_restore_stock_on_cancel
AFTER UPDATE OF status ON orders
FOR EACH ROW
WHEN NEW.status = 'Canceled' AND OLD.status != 'Canceled'
BEGIN
	UPDATE product
	SET product_stock = product_stock + (
		SELECT quantity
		FROM order_items
		WHERE order_items.id_order = NEW.id_order
		AND order_items.id_product = product.id_product 
	)
	WHERE id_product IN (
		SELECT id_product
		FROM order_items
		WHERE id_order = NEW.id_order
	);
END;