import sqlite3, random, os, unicodedata
from datetime import datetime, timedelta
from time import sleep
from faker import Faker


# Aqui descobrimos onde esse script está salvo no computador,
# assim o banco de dados sempre vai ser criado na mesma pasta do arquivo .py
# (independente de onde rodar o script!)
diretorio_atual = os.path.dirname(os.path.abspath(__file__))

# Montando o caminho completo do banco de dados
# Se quiser mudar o nome do arquivo, é só alterar o texto dentro das aspas simples ('')
database_path = os.path.join(diretorio_atual, 'emporium_geracoes.db')

# Conectando ao banco de dados
# Se o arquivo não existir ainda, o SQLite cria automaticamente pra gente!
conn = sqlite3.connect(database_path)
cursor = conn.cursor()

print(f"Banco de dados conectado/criado com sucesso na pasta:\n{database_path}\n")

# Isso aqui é IMPORTANTE: por padrão, o SQLite não verifica as chaves estrangeiras.
# Esse PRAGMA "liga" essa validação pra garantir que os relacionamentos entre tabelas funcionem certo.
cursor.execute('PRAGMA foreign_keys = ON;')

######################################################
# FUNCOES
######################################################

# ----------------------------------------------------
# Funcao para gravar no banco de dados
# ----------------------------------------------------
# Toda vez que eu inserir ou alterar dados, preciso "commitar" (confirmar) a transação.
# Criei essa função só pra não ter que ficar repetindo conn.commit() em todo lugar.
def grava_no_banco():
    conn.commit()

# ----------------------------------------------------
# Funcoes para criar as tabelas no banco
# ----------------------------------------------------

# Tabela de categorias dos produtos
# Simples: só um id (gerado automaticamente) e o nome da categoria
def create_categorias():
    cursor.execute('''
        CREATE TABLE category (
            id_category INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name VARCHAR(100));
    ''')

# Tabela de produtos
# Aqui já tem mais coisa: preço, estoque e a ligação com a categoria (chave estrangeira)
# O CHECK garante que preço e estoque nunca sejam negativos
def create_produtos():
    cursor.execute('''
        CREATE TABLE product (
            id_product INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name VARCHAR(100) NOT NULL,
            product_price DECIMAL(10,2) DEFAULT 0.00 CHECK(product_price >= 0.00),
            product_stock DECIMAL(10,2) DEFAULT 0.00 CHECK(product_stock >= 0.00),
            id_category INTEGER,
            CONSTRAINT fk_product_category FOREIGN KEY (id_category) REFERENCES category(id_category)
        );
    ''')

# Tabela de fornecedores
# Guarda nome, e-mail e telefone de cada fornecedor
def create_fornecedores():
    cursor.execute('''
        CREATE TABLE supplier (
            id_supplier INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name VARCHAR(100) NOT NULL,
            supplier_email VARCHAR(100),
            supplier_phone VARCHAR(15)
        );
    ''')

# Tabela auxiliar (muitos-para-muitos): produto <-> fornecedor
# Um produto pode ter vários fornecedores, e um fornecedor pode fornecer vários produtos.
# A chave primária aqui é COMPOSTA pelos dois ids juntos (sem duplicatas na combinação!)
# Também guarda o preço de custo e a data da última compra com esse fornecedor
def create_tabela_auxiliar():
    cursor.execute('''
        CREATE TABLE product_supplier (
            id_product INTEGER,
            id_supplier INTEGER,
            cost_price DECIMAL(10,2) DEFAULT 0.00 CHECK(cost_price >= 0.00),
            last_purchase_date DATETIME DEFAULT (CURRENT_TIMESTAMP),
            CONSTRAINT pk_product_supplier PRIMARY KEY (id_product, id_supplier),
            CONSTRAINT fk_productsupplier_product FOREIGN KEY (id_product) REFERENCES product(id_product),
            CONSTRAINT fk_productsupplier_supplier FOREIGN KEY (id_supplier) REFERENCES supplier(id_supplier)
        );
    ''')

# Tabela de clientes
# O e-mail é UNIQUE: dois clientes não podem ter o mesmo e-mail cadastrado
# O gênero aceita só 'M', 'F' ou 'O' (o CHECK garante isso)
def create_clientes():
    cursor.execute('''
        CREATE TABLE customer (
            id_customer INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name VARCHAR(100) NOT NULL,
            customer_email VARCHAR(100),
            customer_phone VARCHAR(15),
            gender CHAR(1) NOT NULL CHECK(gender IN ('M', 'F', 'O'))
        );
    ''')

# Tabela de status
def create_status():
    cursor.execute('''
        CREATE TABLE order_status (
            id_status INTEGER PRIMARY KEY AUTOINCREMENT,
            status VARCHAR(30) UNIQUE NOT NULL
        );
    ''')

# Tabela de endereços
# Separei dos clientes porque um cliente poderia ter mais de um endereço no futuro
def create_enderecos():
    cursor.execute('''
        CREATE TABLE address (
            id_address INTEGER PRIMARY KEY AUTOINCREMENT,
            id_customer INTEGER,
            street VARCHAR(100),
            num VARCHAR(10),
            neighborhood VARCHAR(100),
            city VARCHAR(100),
            state VARCHAR(50),
            CONSTRAINT fk_address_customer FOREIGN KEY (id_customer) REFERENCES customer(id_customer)
        );
    ''')

# Tabela de pedidos
# Cada pedido pertence a um cliente e tem a data/hora registrada automaticamente
# id_status do pedido, como padrão, se não for passado nenhum valor, será inserido o id_status de Pending(pendente)
def create_pedidos():
    cursor.execute('''
        CREATE TABLE orders (
            id_order INTEGER PRIMARY KEY AUTOINCREMENT,
            id_customer INTEGER,
            order_date DATETIME DEFAULT (CURRENT_TIMESTAMP),
            id_status INTEGER DEFAULT (1),
            CONSTRAINT fk_orders_customer FOREIGN KEY (id_customer) REFERENCES customer(id_customer),
            CONSTRAINT fk_orders_status FOREIGN KEY (id_status) REFERENCES order_status(id_status)
        );
    ''')

# Tabela de itens do pedido
# Aqui ficam os produtos de cada pedido: quantidade e preço no momento da compra
# (o preço pode mudar depois, por isso guardo ele aqui também)
def create_itens_pedidos():
    cursor.execute('''
        CREATE TABLE order_items (
            id_order_item INTEGER PRIMARY KEY AUTOINCREMENT,
            id_order INTEGER,
            id_product INTEGER,
            quantity DECIMAL(10,2) NOT NULL,
            price DECIMAL(10,2) NOT NULL CHECK(price >= 0.00),
            CONSTRAINT fk_orderitems_order FOREIGN KEY (id_order) REFERENCES orders(id_order),
            CONSTRAINT fk_orderitems_product FOREIGN KEY (id_product) REFERENCES product(id_product)
        );
    ''')

# Tabela de log para registrar as alterações nos preços dos itens
# Aqui ficam o id do produto, o valor antigo e o novo valor atualizado dele, para futuras consultas
def create_log_products():
    cursor.execute('''
        CREATE TABLE log_product (
            id_log INTEGER PRIMARY KEY AUTOINCREMENT,
            id_product INTEGER,
            old_product_price DECIMAL(10,2),
            new_product_price DECIMAL(10,2),
            command CHAR(1),
            last_updated DATETIME DEFAULT (CURRENT_TIMESTAMP),
            CONSTRAINT fk_logproduct_product FOREIGN KEY (id_product) REFERENCES product(id_product)
        );
    ''')

# ----------------------------------------------------
# Funcoes para gerar 5K de cliente fictícios
# e seus devidos enredeços ficitícios
# ----------------------------------------------------
fake = Faker('pt_BR')

def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def gerar_clientes_ficticios(quantidade):
    clientes_gerados = []
    
    # Pesos para distribuição de gênero
    opcoes_genero = ['M', 'F', 'O']
    pesos = [48, 48, 4] 
    
    for _ in range(quantidade):
        genero = random.choices(opcoes_genero, weights=pesos)[0]
        
        # Gerar nome compatível com o gênero
        if genero == 'M':
            nome = fake.name_male()
        elif genero == 'F':
            nome = fake.name_female()
        else:
            nome = fake.name_nonbinary()
            
        # Limpar o nome para o e-mail (sem acentos e em minúsculo)
        nome_limpo = remover_acentos(nome).lower().split()
        dominio = fake.free_email_domain()
        
        # Criação do email: primeiro_nome.ultimo_nome@dominio
        email = f"{nome_limpo[0]}.{nome_limpo[-1]}@{dominio}"
        
        # Gerar telefone (DDD 16 + 9 + 8 dígitos aleatórios)
        numero = fake.random_number(digits=8, fix_len=True)
        telefone = f"169{numero}"
        
        clientes_gerados.append((nome, email, telefone, genero))
        
    return clientes_gerados

def gerar_enderecos(quantidade):
    enderecos_gerados = []
    
    # Cidades para concentrar a maior parte da massa de dados
    cidades_paulistas = ['Ribeirão Preto', 'Sertãozinho', 'Cravinhos', 'Franca', 'Jardinópolis', 'Brodowski', 'Batatais', 'São Paulo']
    
    for id_cliente in range(1, quantidade + 1):
        # 95 de chance de cair no estado de SP para manter a consistência do seu modelo
        if random.random() < 0.95:
            cidade = random.choices(
                cidades_paulistas, 
                weights=[69, 6, 7, 3, 4, 8, 2, 1] # Maior peso para RP
            )[0]
            estado = 'SP'
            bairro = fake.bairro()
        else:
            # 5% de chance de gerar cidades de outros estados do Brasil
            cidade = fake.city()
            estado = fake.estado_sigla()
            bairro = fake.bairro()
            
        # Gera o restante do endereço
        # Algumas vezes o Faker coloca "Rua", "Avenida" no street_name
        logradouro = fake.street_name() 
        numero = fake.building_number()
        
        # Adiciona a tupla na lista
        enderecos_gerados.append((id_cliente, logradouro, numero, bairro, cidade, estado))
        
    return enderecos_gerados

# ----------------------------------------------------
# Funcoes para inserir dados nas tabelas do banco
# ----------------------------------------------------

# Percorre a lista 'categorias' e insere cada item no banco
# O ? é um placeholder — o SQLite substitui pelo valor real de forma segura (evita SQL Injection)
def insert_categorias():
    print('-- Inserindo dados na tabela "category"...')
    sleep(1)
    for categoria in categorias:
        cursor.execute('''
            INSERT INTO category (category_name) VALUES (?)
        ''', (categoria,))
    
    grava_no_banco()
    print('Dados inseridos na tabela "category" com sucesso!\n')

# Percorre a lista de status, e inseri na tabela order_status do banco
def insert_status():
    print('-- Inserindo dados na tabela "order_status"...')
    sleep(1)
    for stat in status:
        cursor.execute('''
            INSERT INTO order_status (status) VALUES (?)
        ''', (stat,))

    grava_no_banco()
    print('Dados inseridos na tabela "order_status" com sucesso!\n')

# Percorre a lista 'produtos' e insere cada um no banco
# Cada item da lista é uma tupla: (nome, preco, estoque, id_categoria)
def insert_produtos():
    print('-- Inserindo dados na tabela "product"...')
    sleep(1)
    for produto in produtos:
        nome_produto = produto[0]
        preco = produto[1]
        estoque = produto[2]
        id_categoria = produto[3]

        cursor.execute('''
            INSERT INTO product (product_name, product_price, product_stock, id_category)
            VALUES (?, ?, ?, ?)
        ''', (nome_produto, preco, estoque, id_categoria))

    grava_no_banco()
    print('Dados inseridos na tabela "product" com sucesso!\n')

# Atenção: na lista de fornecedores, o índice [1] é o telefone e o [2] é o e-mail
# (a ordem na lista não é a mesma que na tabela, por isso preciso mapear manualmente)
def insert_fornecedores():
    print('-- Inserindo dados na tabela "supplier"...')
    sleep(1)
    for fornecedor in fornecedores:
        nome_fornecedor = fornecedor[0]
        email_fornecedor = fornecedor[2]
        telefone_fornecedor = fornecedor[1]

        cursor.execute('''
            INSERT INTO supplier (supplier_name, supplier_email, supplier_phone)
            VALUES (?, ?, ?)
        ''', (nome_fornecedor, email_fornecedor, telefone_fornecedor))

    grava_no_banco()
    print('Dados inseridos na tabela "supplier" com sucesso!\n')

# Insere os relacionamentos entre produto e fornecedor
# Cada item da tabela_aux: (id_produto, id_fornecedor, custo, data_ultima_compra)
def insert_tabela_auxiliar():
    print('-- Inserindo dados na tabela "product_supplier"...')
    sleep(1)
    for reg in tabela_aux:
        id_produto = reg[0]
        id_fornecedor = reg[1]
        custo = reg[2]
        ultimo_pedido = reg[3]

        cursor.execute('''
            INSERT INTO product_supplier (id_product, id_supplier, cost_price, last_purchase_date)
            VALUES (?, ?, ?, ?)
        ''', (id_produto, id_fornecedor, custo, ultimo_pedido))

    grava_no_banco()
    print('Dados inseridos na tabela "product_supplier" com sucesso!\n')

# Cada cliente é uma tupla: (nome, email, telefone, genero)
def insert_clientes():
    print('-- Inserindo dados na tabela "customer"...')
    sleep(1)
    for cliente in clientes:
        nome_cliente = cliente[0]
        email_cliente = cliente[1]
        telefone_cliente = cliente[2]
        genero = cliente[3]

        cursor.execute('''
            INSERT INTO customer (customer_name, customer_email, customer_phone, gender)
            VALUES (?, ?, ?, ?)
        ''', (nome_cliente, email_cliente, telefone_cliente, genero))

    grava_no_banco()
    print('Dados inseridos na tabela "customer" com sucesso!\n')

# Cada endereço é uma tupla: (id_cliente, rua, numero, bairro, cidade, estado)
def insert_enderecos():
    print('-- Inserindo dados na tabela "address"...')
    sleep(1)
    for end in enderecos:
        id_cliente = end[0]
        rua = end[1]
        nro = end[2]
        bairro = end[3]
        cidade = end[4]
        estado = end[5]
        
        cursor.execute('''
            INSERT INTO address (id_customer, street, num, neighborhood, city, state)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (id_cliente, rua, nro, bairro, cidade, estado))

    grava_no_banco()
    print('Dados inseridos na tabela "address" com sucesso!\n')

# Essa função é a mais complexa do projeto — ela gera um histórico de vendas realista
# cobrindo o período de 01/01/2025 até 31/03/2026, com sazonalidade por mês
def popular_vendas():
    # Primeiro, busco todos os ids de clientes e produtos que já estão no banco
    cursor.execute("SELECT id_customer FROM customer")
    clientes = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT id_product, product_price FROM product")
    produtos = cursor.fetchall()

    # Tabela de sazonalidade: define quantos pedidos esperar por dia em cada mês
    # Quanto maior o número, mais movimentado é o mês
    # Ex: novembro (Black Friday) = 250, dezembro (Natal) = 300, janeiro (pós-festas) = 50
    pesos_mensais = {
        1: 50,   # Janeiro   - Fraco (pós-festas, pessoal sem dinheiro)
        2: 50,   # Fevereiro - Fraco
        3: 100,  # Março     - Moderado
        4: 100,  # Abril     - Moderado
        5: 150,  # Maio      - Forte (Dia das Mães!)
        6: 100,  # Junho     - Moderado
        7: 100,  # Julho     - Moderado
        8: 100,  # Agosto    - Moderado
        9: 150,  # Setembro  - Forte (Dia dos Pais!)
        10: 150, # Outubro   - Forte
        11: 250, # Novembro  - Muito Forte (Black Friday)
        12: 300, # Dezembro  - Muito Forte (Natal e Réveillon)
    }

    # Intervalo de datas que vou simular
    data_atual = datetime(2025, 1, 1)
    data_fim = datetime(2026, 3, 31)

    print(f"Gerando histórico de vendas (2025 - 2026)...")

    # Loop que avança dia a dia pelo período definido
    while data_atual <= data_fim:
        if data_atual.weekday() != 6:  # Pulando domingos (índice 6 = domingo no Python)
            
            # Quantos pedidos vão acontecer hoje?
            # Pego a meta do mês e adiciono uma variação de ±20% pra ficar mais natural
            mes_id = data_atual.month
            meta_pedidos = pesos_mensais[mes_id]
            pedidos_hoje = random.randint(int(meta_pedidos * 0.8), int(meta_pedidos * 1.2))

            for _ in range(pedidos_hoje):
                # Escolho um cliente aleatório pra fazer o pedido
                cliente_id = random.choice(clientes)
                
                # Gero um horário comercial aleatório (entre 8h e 21h)
                hora = random.randint(8, 21)
                minuto = random.randint(0, 59)
                data_com_hora = data_atual.replace(hour=hora, minute=minuto)
                data_str = data_com_hora.strftime('%Y-%m-%d %H:%M:%S')
                id_status = 0

                # Lógica para status realista
                # 1 = Pending, 2 = Canceled, 3 = Processing, 4 = In Transit, 5 = Delivered
                if data_atual.year == 2026 and data_atual.month == 3:
                    # Para pedidos de Março/2026 (Mês atual/vivo da operação)
                    # Ex: 10% Pendente, 10% Cancelado, 15% Processando, 25% Em Trânsito e 40% Entregue
                    opcoes_status = [1, 2, 3, 4, 5]
                    pesos = [0.075, 0.075, 0.15, 0.30, 0.40]
                    id_status = random.choices(opcoes_status, weights=pesos)[0]
                else:
                    # Para pedidos de fevereiro de 2026 para trás, o histórico já está fechado
                    # Ex: 95% dos pedidos foram entregues e 5 foram cancelados
                    opcoes_status = [2, 5]
                    pesos = [0.05, 0.95]
                    id_status = random.choices(opcoes_status, weights=pesos)[0]

                # Insiro o pedido e pego o id gerado pra usar nos itens
                cursor.execute("INSERT INTO orders (id_customer, order_date, id_status) VALUES (?, ?, ?)", 
                               (cliente_id, data_str, id_status))
                order_id = cursor.lastrowid

                # Cada pedido tem entre 1 e 5 produtos diferentes (sem repetir no mesmo pedido)
                num_itens = random.randint(1, 5)
                itens_escolhidos = random.sample(produtos, num_itens)

                # Insiro cada item do pedido com quantidade entre 1 e 3 unidades
                for prod_id, preco in itens_escolhidos:
                    qtd = random.randint(1, 3)
                    cursor.execute("""
                        INSERT INTO order_items (id_order, id_product, quantity, price) 
                        VALUES (?, ?, ?, ?)
                    """, (order_id, prod_id, qtd, preco))

        # Avança para o próximo dia
        data_atual += timedelta(days=1)

    grava_no_banco()
    print("Histórico populado com sucesso respeitando a sazonalidade!")

# ----------------------------------------------------
# Funcoes para criar os triggers
# ----------------------------------------------------
def create_triggers():
    print('-- Criando os Triggers (Automações) do banco...')
    sleep(1)
    
    cursor.executescript('''
        -- Trigger para registar na tabela de log, alterações de preços
        CREATE TRIGGER trg_log_product
        AFTER UPDATE OF product_price ON product
        FOR EACH ROW
        BEGIN
            INSERT INTO log_product(id_product, old_product_price, new_product_price, command) VALUES
            (OLD.id_product, OLD.product_price, NEW.product_price, 'U');
        END;

        -- Trigger subtrair o estoque do item ao ser vendido
        CREATE TRIGGER trg_stock_control_rem
        AFTER INSERT ON order_items
        FOR EACH ROW
        BEGIN
            UPDATE product
            SET product_stock = product_stock - NEW.quantity 
            WHERE id_product = NEW.id_product;
        END;
        
        -- Trigger estornar o estoque do item se a comprar for cancelada
        CREATE TRIGGER trg_control_add
        AFTER DELETE ON order_items
        FOR EACH ROW
        BEGIN
            UPDATE product
            SET product_stock = product_stock + OLD.quantity
            WHERE id_product = OLD.id_product;
        END;
                         
        -- Trigger padronizar os emails para caixa baixa
        CREATE TRIGGER trg_lower_email
        AFTER INSERT ON customer
        FOR EACH ROW
        BEGIN
            UPDATE customer
            SET customer_email = LOWER(TRIM(NEW.customer_email))
            WHERE id_customer = NEW.id_customer;
        END;        

        -- Trigger para impedir exclusão, altera o status para canceled(cancelado)
        CREATE TRIGGER trg_order_delete
        BEFORE DELETE ON orders
        FOR EACH ROW
        BEGIN
            UPDATE orders
            SET id_status = 2
            WHERE id_order = OLD.id_order;
            SELECT RAISE(IGNORE);
        END;                                  

        -- Trigger para estornar a quantidade de um produto, quanto o pedido todo for excluido      
        CREATE TRIGGER trg_restore_stock_on_cancel
        AFTER UPDATE OF id_status ON orders
        FOR EACH ROW
        WHEN NEW.id_status = 2 AND OLD.id_status != 2
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
                                      
    ''')
    
    grava_no_banco()
    print('Triggers criados com sucesso!\n')



######################################################
# Listas com os dados a serem inseridos no banco
######################################################

# 10 categorias de produtos da loja
categorias = [
    'Vinhos & Espumantes',
    'Queijos Artesanais',
    'Charcutaria & Defumados',
    'Cafes & Chas Gourmet',
    'Azeites & Temperos',
    'Doces & Geleias',
    'Cervejas Artesanais',
    'Massas & Molhos',
    'Paes & Padaria',
    'Cestas de Presente'
]

# 100 produtos: cada tupla é (nome, preco, estoque, id_categoria)
# Os ids de categoria seguem a ordem da lista acima: 1=Vinhos, 2=Queijos, etc.
produtos = [
    ('Vinho Tinto Malbec Reserva', 89.90, 45, 1),
    ('Vinho Branco Chardonnay', 59.90, 30, 1),
    ('Espumante Brut Premium', 119.90, 20, 1),
    ('Vinho Rosé Provence', 82.90, 25, 1),
    ('Vinho do Porto Tawny', 149.90, 15, 1),
    ('Vinho Tinto Cabernet', 56.90, 60, 1),
    ('Vinho Merlot Suave', 40.90, 80, 1),
    ('Vinho Carménère Chileno', 64.90, 40, 1),
    ('Espumante Moscatel Doce', 45.90, 50, 1),
    ('Vinho Pinot Noir Classic', 104.90, 18, 1),
    ('Queijo Canastra Curado (kg)', 89.90, 12.5, 2),
    ('Queijo Brie Francês (un)', 42.90, 20, 2),
    ('Gorgonzola Cremoso (kg)', 105.90, 8.0, 2),
    ('Parmesão 12 Meses (kg)', 99.90, 15.0, 2),
    ('Queijo Meia Cura (kg)', 52.90, 25.0, 2),
    ('Queijo de Cabra com Ervas', 36.90, 15, 2),
    ('Provolone Defumado (kg)', 79.90, 10.0, 2),
    ('Queijo Coalho Premium', 32.90, 40, 2),
    ('Ricota Temperada (un)', 18.90, 12, 2),
    ('Queijo Camembert (un)', 41.90, 10, 2),    
    ('Presunto de Parma (100g)', 29.90, 5.0, 3),
    ('Salame Italiano Fatiado', 14.90, 10.0, 3),
    ('Copa Lombo Defumada', 21.90, 8.0, 3),
    ('Bacon Artesanal (kg)', 47.90, 20.0, 3),
    ('Linguiça de Cuiabá (kg)', 34.90, 15.0, 3),
    ('Pastrami Bovino (100g)', 31.90, 4.5, 3),
    ('Chouriço Espanhol', 43.90, 12, 3),
    ('Pepperoni Premium', 19.90, 15, 3),
    ('Lombo Canadense (kg)', 56.90, 10.0, 3),
    ('Salame com Pimenta (un)', 24.90, 20, 3),
    ('Café em Grãos Arábica (500g)', 41.90, 50, 4),
    ('Café Moído Intenso (250g)', 20.90, 100, 4),
    ('Chá Earl Grey Imperial', 32.90, 30, 4),
    ('Cápsulas Café Espresso (10un)', 26.90, 200, 4),
    ('Chá de Hibisco e Frutas', 16.90, 45, 4),
    ('Café Bourbon Amarelo', 49.90, 25, 4),
    ('Chá Verde Matcha (50g)', 59.90, 15, 4),
    ('Café Descafeinado Premium', 29.90, 30, 4),
    ('Infusão de Hortelã e Mel', 13.90, 60, 4),
    ('Café Especial de Altitude', 63.90, 12, 4),
    ('Azeite Extra Virgem (500ml)', 56.90, 40, 5),
    ('Vinagre Balsâmico Modena', 34.90, 25, 5),
    ('Sal Rosa do Himalaia (kg)', 12.90, 100, 5),
    ('Pimenta do Reino em Grãos', 10.90, 80, 5),
    ('Flor de Sal Francesa', 29.90, 20, 5),
    ('Azeite Trufado (250ml)', 109.90, 10, 5),
    ('Molho Pesto Artesanal', 18.90, 35, 5),
    ('Chimichurri Argentino', 13.90, 50, 5),
    ('Orégano Chileno (100g)', 6.90, 70, 5),
    ('Mel de Abelha Silvestre', 29.90, 40, 5),
    ('Geleia de Morango (250g)', 22.90, 40, 6),
    ('Doce de Leite Mineiro (400g)', 26.90, 35, 6),
    ('Chocolate Amargo 70% (100g)', 18.90, 60, 6),
    ('Mel de Flor de Laranjeira', 38.90, 20, 6),
    ('Geleia de Pimenta Defumada', 23.90, 30, 6),
    ('Goiabada Cascão Artesanal', 20.90, 45, 6),
    ('Pasta de Amendoim Integral', 18.90, 50, 6),
    ('Trufas de Avelã (cx 12un)', 52.90, 15, 6),
    ('Compota de Figo Ramy', 38.90, 12, 6),
    ('Alfajor Artesanal (un)', 8.90, 100, 6),
    ('Cerveja IPA Extra Lúpulo', 22.90, 120, 7),
    ('Cerveja Weiss de Trigo', 17.90, 80, 7),
    ('Cerveja Stout Chocolate', 26.90, 40, 7),
    ('Cerveja Pilsen Premium', 12.90, 200, 7),
    ('Cerveja Belgian Tripel', 34.90, 30, 7),
    ('Cerveja Red Ale Defumada', 24.90, 55, 7),
    ('Cerveja APA Refrescante', 18.90, 90, 7),
    ('Cerveja Sour de Frutas', 29.90, 25, 7),
    ('Cerveja Witbier Laranja', 15.90, 70, 7),
    ('Kit Degustação (4 rótulos)', 89.90, 15, 7),
    ('Macarrão Fettuccine de Ovos', 14.90, 60, 8),
    ('Massa de Lasanha Artesanal', 15.90, 40, 8),
    ('Molho de Tomate Rústico', 22.90, 50, 8),
    ('Ravioli de Queijo (500g)', 29.90, 20, 8),
    ('Espaguete com Tinta de Lula', 32.90, 15, 8),
    ('Molho Funghi Porcini', 33.90, 25, 8),
    ('Nhoque de Batata Caseiro', 17.90, 30, 8),
    ('Molho Quatro Queijos', 24.90, 40, 8),
    ('Capeletti de Carne', 22.90, 25, 8),
    ('Massa Integral com Grãos', 17.90, 55, 8),
    ('Pão de Fermentação Natural', 22.90, 20, 9),
    ('Baguete Francesa (un)', 8.90, 50, 9),
    ('Ciabatta com Azeitonas', 14.90, 30, 9),
    ('Pão de Queijo Especial (kg)', 49.90, 15, 9),
    ('Croissant de Manteiga', 8.90, 40, 9),
    ('Pão Italiano Redondo', 16.90, 25, 9),
    ('Focaccia de Alecrim', 14.90, 15, 9),
    ('Pão de Grãos e Castanhas', 26.90, 18, 9),
    ('Pão de Hamburguer Brioche', 18.90, 30, 9),
    ('Torradas Finas com Ervas', 12.90, 60, 9),
    ('Cesta Café da Manhã Luxo', 289.90, 10, 10),
    ('Cesta Queijos & Vinhos', 379.90, 8, 10),
    ('Kit Churrasco Premium', 349.90, 5, 10),
    ('Cesta Doce Deleite', 219.90, 12, 10),
    ('Cesta Cervejeiro Gourmet', 239.90, 15, 10),
    ('Cesta Boas Vindas', 299.90, 6, 10),
    ('Baú de Vinhos Reservas', 699.90, 3, 10),
    ('Cesta Chá e Relaxamento', 219.90, 10, 10),
    ('Kit Azeites do Mundo', 339.90, 7, 10),
    ('Cesta PicNic Completa', 429.90, 4, 10)
]

# 50 fornecedores: cada tupla é (nome, telefone, email)
# Obs: repare que aqui o telefone vem ANTES do e-mail (índice 1 e 2)
# na função insert_fornecedores() eu faço o mapeamento correto pra não confundir
fornecedores = [
    ('Importadora Vinhedos do Sul', '11988881111', 'contato@vinhedosdosul.com.br'),
    ('Laticínios Serra da Canastra', '37999992222', 'vendas@canastra.com.br'),
    ('Fazenda Grãos de Ouro', '35988883333', 'pedidos@graosdeouro.com.br'),
    ('Charcutaria Italiana Original', '11977774444', 'comercial@charcutariaitaliana.com'),
    ('Azeites do Mundo Ltda', '21966665555', 'import@azeitesdomundo.com'),
    ('Doces da Vovó Maria', '19955556666', 'maria@docesvovo.com.br'),
    ('Cervejaria Artesanal Alpha', '16944447777', 'mestre@cervejaalpha.com.br'),
    ('Massas Nonna Bina', '11933338888', 'pedidos@nonnabina.com'),
    ('Padaria Central de Ribeirão', '16922229999', 'contato@padariacentral.com'),
    ('Cestas & Carinho Presentes', '11911110000', 'vendas@cestascarinho.com'),
    ('Distribuidora de Queijos MG', '31988881234', 'queijos@distribuidoramg.com'),
    ('Frigorífico Bovino Nobre', '62977775678', 'vendas@bovinonobre.com.br'),
    ('Torrefação Café Mineiro', '35966669012', 'contato@cafemineiro.com.br'),
    ('Hortifruti Orgânico Real', '11955553456', 'contato@organico.com.br'),
    ('Vinhos do Tejo Import', '21944447890', 'vendas@tejoimport.com'),
    ('Queijaria Artesanal do Vale', '12933332109', 'contato@queijariavalle.com'),
    ('Embutidos Selecionados PR', '41922226543', 'comercial@embutidospr.com'),
    ('Moinho de Trigo Premium', '51911110987', 'vendas@moinhopremium.com'),
    ('Mel e Cia Apicultura', '16999993344', 'contato@melecia.com.br'),
    ('Importadora Delícias da Europa', '11988885566', 'pedidos@deliciaseuropa.com'),
    ('Cervejaria Montanha Pura', '24977771122', 'vendas@montanhapura.com'),
    ('Laticínios Flor de Leite', '35966663344', 'financeiro@flordeleite.com'),
    ('Condimentos & Especiarias', '11955555577', 'vendas@condimentoseia.com'),
    ('Fazenda de Geleias do Sol', '19944449900', 'comercial@geleiadosol.com'),
    ('Vinhos Argentinos Express', '11933334455', 'contato@vinhosarg.com'),
    ('Massas Artesanais Di Roma', '11922228811', 'vendas@diroma.com'),
    ('Cooperativa de Cafés Especiais', '35911116677', 'pedidos@coopcafes.com'),
    ('Distribuidora de Bebidas Prime', '16999992211', 'comercial@bebidasprime.com'),
    ('Chás e Ervas do Oriente', '11988880099', 'contato@chasorientais.com'),
    ('Padaria Artesanal Rustique', '11977773322', 'pedidos@rustique.com'),
    ('Importadora Sabor do Mundo', '21966668877', 'vendas@sabormundo.com'),
    ('Queijaria Estrela do Sul', '34955554433', 'contato@estreladosul.com'),
    ('Charcutaria Regional Sul', '54944441122', 'comercial@regionalsul.com'),
    ('Fazenda Doce Vida', '16933337788', 'vendas@docevida.com.br'),
    ('Azeite & Cia Distribuidora', '11922220033', 'pedidos@azeitecia.com'),
    ('Cervejaria Noturna', '19911115566', 'vendas@noturna.cerveja.com'),
    ('Massa Gourmet S.A.', '11999994433', 'comercial@massagourmet.com'),
    ('Padaria Pão de Mel', '16988881122', 'contato@paodemel.com'),
    ('Artesanato em Cestas', '11977770099', 'vendas@artesanatocestas.com'),
    ('Laticínios Ouro Branco', '31966665544', 'vendas@ourobranco.com'),
    ('Frigorífico Angus Prime', '51955552211', 'comercial@angusprime.com'),
    ('Café de Montanha Ltda', '35944448877', 'contato@cafemontanha.com'),
    ('Importadora Lusitana', '21933330011', 'vendas@lusitana.com'),
    ('Geleias do Campo Artesanais', '19922225544', 'contato@geleiascampo.com'),
    ('Vinhos do Vale São Francisco', '87911119988', 'vendas@valesf.com.br'),
    ('Distribuidora de Frios VIP', '11999997766', 'pedidos@friosvip.com'),
    ('Chás da Terra Nativa', '41988883322', 'vendas@terranativa.com'),
    ('Moinho de Grãos Especiais', '16977770011', 'contato@moinhograos.com'),
    ('Doces Regionais MG', '35966661100', 'vendas@docesmg.com.br'),
    ('Logística de Alimentos Gourmet', '11955558899', 'comercial@alimentosgourmet.com')
]

# 5 status
status = [
    'Pending',
    'Canceled',
    'Processing',
    'In Transit',
    'Delivered'
]

# Tabela auxiliar produto <-> fornecedor
# Cada tupla: (id_produto, id_fornecedor, preco_custo, data_ultima_compra)
# Quando a data é None, o SQLite usa o CURRENT_TIMESTAMP definido na criação da tabela
tabela_aux = [
    (1, 1, 45.00, '2026-01-10'), (1, 15, 48.50, None),
    (2, 1, 35.00, '2026-01-12'), (2, 15, 33.00, None),
    (3, 1, 60.00, '2026-02-01'), (3, 25, 62.00, None),
    (4, 1, 47.50, None),           (4, 25, 45.00, '2026-02-05'),
    (5, 1, 75.00, '2026-01-20'), (5, 45, 70.00, None),
    (6, 15, 32.50, '2026-01-05'), (6, 45, 35.00, None),
    (7, 15, 22.50, None),           (7, 45, 21.00, '2026-02-10'),
    (8, 25, 39.00, '2026-01-15'), (8, 1, 41.00, None),
    (9, 25, 27.50, None),           (9, 15, 25.00, '2026-02-15'),
    (10, 45, 55.00, '2026-01-30'), (10, 1, 58.00, None),
    (11, 2, 42.50, '2026-01-08'), (11, 11, 45.00, None),
    (12, 2, 22.50, None),           (12, 16, 21.00, '2026-01-15'),
    (13, 2, 47.50, '2026-02-02'), (13, 32, 50.00, None),
    (14, 11, 55.00, '2026-01-20'), (14, 40, 58.00, None),
    (15, 11, 27.50, None),           (15, 16, 26.00, '2026-02-10'),
    (16, 16, 19.00, '2026-01-12'), (16, 32, 21.50, None),
    (17, 16, 36.00, None),           (17, 40, 34.50, '2026-02-18'),
    (18, 32, 16.00, '2026-01-05'), (18, 11, 17.50, None),
    (19, 32, 9.00, None),            (19, 2, 8.50, '2026-02-25'),
    (20, 40, 21.00, '2026-01-25'), (20, 16, 23.00, None),
    (21, 4, 14.00, '2026-01-10'), (21, 12, 16.50, None),
    (22, 4, 7.50, None),           (22, 17, 8.00, '2026-01-20'),
    (23, 12, 11.00, '2026-02-05'), (23, 33, 10.50, None),
    (24, 12, 24.00, '2026-01-15'), (24, 41, 26.00, None),
    (25, 17, 17.50, None),           (25, 4, 19.00, '2026-02-12'),
    (26, 17, 16.00, '2026-01-25'), (26, 33, 15.00, None),
    (27, 33, 22.50, None),           (27, 41, 20.00, '2026-02-20'),
    (28, 33, 9.50, '2026-01-05'),  (28, 12, 10.50, None),
    (29, 41, 29.00, '2026-01-30'), (29, 4, 31.00, None),
    (30, 41, 12.50, None),           (30, 17, 11.50, '2026-02-28'),
    (31, 3, 22.50, '2026-01-10'),  (31, 13, 24.00, None),
    (32, 13, 11.00, '2026-01-15'), (32, 27, 10.50, None),
    (33, 29, 17.50, '2026-02-05'), (33, 3, 19.00, None),
    (34, 13, 14.00, '2026-01-20'), (34, 42, 15.50, None),
    (35, 29, 9.00, None),           (35, 3, 8.50, '2026-02-10'),
    (36, 27, 27.50, '2026-01-12'), (36, 13, 29.00, None),
    (37, 29, 32.50, None),          (37, 47, 30.00, '2026-02-18'),
    (38, 3, 16.00, '2026-01-05'),  (38, 27, 17.50, None),
    (39, 29, 7.50, None),           (39, 47, 7.00, '2026-02-25'),
    (40, 42, 36.00, '2026-01-25'), (40, 13, 38.00, None),
    (41, 5, 34.00, '2026-01-08'),  (41, 35, 36.50, None),
    (42, 5, 22.50, None),           (42, 31, 21.00, '2026-01-15'),
    (43, 23, 7.50, '2026-02-02'),  (43, 48, 8.00, None),
    (44, 23, 6.00, '2026-01-20'),  (44, 5, 7.00, None),
    (45, 31, 19.00, None),          (45, 35, 18.00, '2026-02-10'),
    (46, 35, 62.50, '2026-01-12'), (46, 5, 65.00, None),
    (47, 23, 12.00, None),          (47, 31, 11.50, '2026-02-18'),
    (48, 48, 7.00, '2026-01-05'),  (48, 23, 8.50, None),
    (49, 48, 4.00, None),           (49, 5, 3.50, '2026-02-25'),
    (50, 31, 17.50, '2026-01-25'), (50, 23, 19.00, None),
    (51, 6, 12.00, '2026-01-10'),  (51, 24, 13.50, None),
    (52, 6, 16.00, None),           (52, 34, 15.00, '2026-01-20'),
    (53, 24, 9.25, '2026-02-05'),  (53, 49, 10.00, None),
    (54, 34, 21.00, '2026-01-15'), (54, 6, 23.00, None),
    (55, 24, 13.00, None),          (55, 49, 12.50, '2026-02-12'),
    (56, 34, 11.00, '2026-01-25'), (56, 24, 10.00, None),
    (57, 49, 9.95, None),           (57, 6, 11.00, '2026-02-20'),
    (58, 6, 27.50, '2026-01-05'),  (58, 34, 29.00, None),
    (59, 24, 19.00, '2026-01-30'), (59, 49, 21.00, None),
    (60, 49, 4.75, None),           (60, 34, 4.50, '2026-02-28'),
    (61, 7, 14.00, '2026-01-10'),  (61, 28, 15.50, None),
    (62, 7, 12.25, '2026-01-15'), (62, 36, 11.00, None),
    (63, 21, 16.00, '2026-02-05'), (63, 7, 17.50, None),
    (64, 28, 9.00, '2026-01-20'),  (64, 36, 8.50, None),
    (65, 21, 22.50, None),          (65, 28, 20.00, '2026-02-10'),
    (66, 36, 14.50, '2026-01-12'), (66, 7, 16.00, None),
    (67, 21, 13.00, None),          (67, 28, 12.50, '2026-02-18'),
    (68, 28, 17.50, '2026-01-05'), (68, 36, 19.00, None),
    (69, 36, 11.00, None),          (69, 7, 10.50, '2026-02-25'),
    (70, 28, 55.00, '2026-01-25'), (70, 21, 58.00, None),
    (71, 8, 9.00, '2026-01-08'),   (71, 18, 10.50, None),
    (72, 8, 11.00, None),           (72, 26, 10.00, '2026-01-15'),
    (73, 26, 13.00, '2026-02-02'), (73, 37, 14.50, None),
    (74, 37, 17.50, '2026-01-20'), (74, 8, 19.00, None),
    (75, 18, 21.00, None),          (75, 26, 19.50, '2026-02-10'),
    (76, 37, 19.00, '2026-01-12'), (76, 18, 22.00, None),
    (77, 8, 12.00, None),           (77, 26, 11.00, '2026-02-18'),
    (78, 26, 14.50, '2026-01-05'), (78, 37, 16.00, None),
    (79, 18, 16.00, None),          (79, 8, 15.00, '2026-02-25'),
    (80, 37, 10.50, '2026-01-25'), (80, 18, 12.00, None),
    (81, 9, 9.00, '2026-01-10'),   (81, 30, 11.50, None),
    (82, 9, 4.25, None),           (82, 38, 4.00, '2026-01-20'),
    (83, 30, 6.00, '2026-02-05'),  (83, 48, 7.50, None),
    (84, 38, 22.50, '2026-01-15'), (84, 9, 25.00, None),
    (85, 30, 4.50, None),           (85, 38, 4.00, '2026-02-12'),
    (86, 9, 7.50, '2026-01-25'),   (86, 48, 8.50, None),
    (87, 30, 7.25, None),           (87, 38, 6.50, '2026-02-20'),
    (88, 38, 11.00, '2026-01-05'), (88, 9, 13.50, None),
    (89, 48, 8.00, '2026-01-30'),  (89, 30, 9.50, None),
    (90, 30, 6.25, None),           (90, 48, 5.50, '2026-02-28'),
    (91, 10, 110.00, '2026-01-10'), (91, 39, 115.00, None),
    (92, 10, 150.00, '2026-01-15'), (92, 50, 145.00, None),
    (93, 39, 130.00, '2026-02-05'), (93, 10, 140.00, None),
    (94, 10, 85.00, '2026-01-20'),  (94, 50, 80.00, None),
    (95, 39, 95.00, None),           (95, 50, 92.00, '2026-02-10'),
    (96, 50, 115.00, '2026-01-12'), (96, 10, 120.00, None),
    (97, 10, 280.00, None),          (97, 39, 275.00, '2026-02-18'),
    (98, 39, 88.00, '2026-01-05'),  (98, 50, 85.00, None),
    (99, 50, 135.00, None),          (99, 10, 130.00, '2026-02-25'),
    (100, 39, 170.00, '2026-01-25'),(100, 50, 165.00, None)
]

# 5.000 clientes gerados através da função feita acima
clientes = gerar_clientes_ficticios(5000)

# 5.000 endereços: 1 endereço gerado para cada cliente
# Maioria em Ribeirão Preto e cidades da região, alguns em São Paulo
enderecos = gerar_enderecos(5000)

######################################################
# Main — aqui é onde tudo acontece de verdade!
######################################################

# --- ETAPA 1: Criando a estrutura do banco (as tabelas) ---
# Precisamos criar as tabelas na ordem certa por causa das chaves estrangeiras:
# category e supplier primeiro (não dependem de ninguém),
# depois product (depende de category), e assim por diante
create_categorias()
create_produtos()
create_fornecedores()
create_tabela_auxiliar()
create_clientes()
create_enderecos()
create_status()
create_log_products()
create_pedidos()
create_itens_pedidos()

print('/* TABELAS CRIADAS COM SUCESSO! */\n')


# --- ETAPA 2: Populando o banco com os dados das listas acima ---
# A mesma lógica de ordem se aplica aqui: inserir categorias antes dos produtos,
# clientes antes dos endereços, etc.
print('/* INSERINDO DADOS NO BANCO DE DADOS */\n')

insert_categorias()
insert_produtos()
insert_fornecedores()
insert_tabela_auxiliar()
insert_clientes()
insert_enderecos()
insert_status()
popular_vendas()  # Essa é a mais demorada — gera mais de um ano de histórico de vendas!

print('/* DADOS INSERIDOS COM SUCESSO! */\n')

create_triggers()

print('/* TRIGGERS CRIADOS COM SUCESSO! */\n')

# Fechando a conexão com o banco — boa prática sempre fazer isso no final!
conn.close()