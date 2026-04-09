import sqlite3, random, os
from datetime import datetime, timedelta
from time import sleep

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
            FOREIGN KEY (id_category) REFERENCES category(id_category)
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
            PRIMARY KEY (id_product, id_supplier),
            FOREIGN KEY (id_product) REFERENCES product(id_product),
            FOREIGN KEY (id_supplier) REFERENCES supplier(id_supplier)
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
            customer_email VARCHAR(100) UNIQUE,
            customer_phone VARCHAR(15),
            gender CHAR(1) NOT NULL CHECK(gender IN ('M', 'F', 'O'))
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
            FOREIGN KEY (id_customer) REFERENCES customer(id_customer)
        );
    ''')

# Tabela de pedidos
# Cada pedido pertence a um cliente e tem a data/hora registrada automaticamente
def create_pedidos():
    cursor.execute('''
        CREATE TABLE orders (
            id_order INTEGER PRIMARY KEY AUTOINCREMENT,
            id_customer INTEGER,
            order_date DATETIME DEFAULT (CURRENT_TIMESTAMP),
            FOREIGN KEY (id_customer) REFERENCES customer(id_customer)
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
            FOREIGN KEY (id_order) REFERENCES orders(id_order),
            FOREIGN KEY (id_product) REFERENCES product(id_product)
        );
    ''')

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
    print('Dados inserindos na tabela "category" com sucesso!\n')

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
    print('Dados inserindos na tabela "product" com sucesso!\n')

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
    print('Dados inserindos na tabela "supplier" com sucesso!\n')

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
    print('Dados inserindos na tabela "product_supplier" com sucesso!\n')

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
    print('Dados inserindos na tabela "customer" com sucesso!\n')

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
    print('Dados inserindos na tabela "address" com sucesso!\n')

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

                # Insiro o pedido e pego o id gerado pra usar nos itens
                cursor.execute("INSERT INTO orders (id_customer, order_date) VALUES (?, ?)", 
                               (cliente_id, data_str))
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
    ('Vinho Branco Chardonnay', 75.00, 30, 1),
    ('Espumante Brut Premium', 120.00, 20, 1),
    ('Vinho Rosé Provence', 95.00, 25, 1),
    ('Vinho do Porto Tawny', 150.00, 15, 1),
    ('Vinho Tinto Cabernet', 65.00, 60, 1),
    ('Vinho Merlot Suave', 45.00, 80, 1),
    ('Vinho Carménère Chileno', 78.00, 40, 1),
    ('Espumante Moscatel Doce', 55.00, 50, 1),
    ('Vinho Pinot Noir Classic', 110.00, 18, 1),
    ('Queijo Canastra Curado (kg)', 85.00, 12.5, 2),
    ('Queijo Brie Francês (un)', 45.00, 20, 2),
    ('Gorgonzola Cremoso (kg)', 95.00, 8.0, 2),
    ('Parmesão 12 Meses (kg)', 110.00, 15.0, 2),
    ('Queijo Meia Cura (kg)', 55.00, 25.0, 2),
    ('Queijo de Cabra com Ervas', 38.00, 15, 2),
    ('Provolone Defumado (kg)', 72.00, 10.0, 2),
    ('Queijo Coalho Premium', 32.00, 40, 2),
    ('Ricota Temperada (un)', 18.00, 12, 2),
    ('Queijo Camembert (un)', 42.00, 10, 2),
    ('Presunto de Parma (100g)', 28.00, 5.0, 3),
    ('Salame Italiano Fatiado', 15.00, 10.0, 3),
    ('Copa Lombo Defumada', 22.00, 8.0, 3),
    ('Bacon Artesanal (kg)', 48.00, 20.0, 3),
    ('Linguiça de Cuiabá (kg)', 35.00, 15.0, 3),
    ('Pastrami Bovino (100g)', 32.00, 4.5, 3),
    ('Chouriço Espanhol', 45.00, 12, 3),
    ('Pepperoni Premium', 19.00, 15, 3),
    ('Lombo Canadense (kg)', 58.00, 10.0, 3),
    ('Salame com Pimenta (un)', 25.00, 20, 3),
    ('Café em Grãos Arábica (500g)', 45.00, 50, 4),
    ('Café Moído Intenso (250g)', 22.00, 100, 4),
    ('Chá Earl Grey Imperial', 35.00, 30, 4),
    ('Cápsulas Café Espresso (10un)', 28.00, 200, 4),
    ('Chá de Hibisco e Frutas', 18.00, 45, 4),
    ('Café Bourbon Amarelo', 55.00, 25, 4),
    ('Chá Verde Matcha (50g)', 65.00, 15, 4),
    ('Café Descafeinado Premium', 32.00, 30, 4),
    ('Infusão de Hortelã e Mel', 15.00, 60, 4),
    ('Café Especial de Altitude', 72.00, 12, 4),
    ('Azeite Extra Virgem (500ml)', 68.00, 40, 5),
    ('Vinagre Balsâmico Modena', 45.00, 25, 5),
    ('Sal Rosa do Himalaia (kg)', 15.00, 100, 5),
    ('Pimenta do Reino em Grãos', 12.00, 80, 5),
    ('Flor de Sal Francesa', 38.00, 20, 5),
    ('Azeite Trufado (250ml)', 125.00, 10, 5),
    ('Molho Pesto Artesanal', 24.00, 35, 5),
    ('Chimichurri Argentino', 14.00, 50, 5),
    ('Orégano Chileno (100g)', 8.00, 70, 5),
    ('Mel de Abelha Silvestre', 35.00, 40, 5),
    ('Geleia de Morango (250g)', 24.00, 40, 6),
    ('Doce de Leite Mineiro (400g)', 32.00, 35, 6),
    ('Chocolate Amargo 70% (100g)', 18.50, 60, 6),
    ('Mel de Flor de Laranjeira', 42.00, 20, 6),
    ('Geleia de Pimenta Defumada', 26.00, 30, 6),
    ('Goiabada Cascão Artesanal', 22.00, 45, 6),
    ('Pasta de Amendoim Integral', 19.90, 50, 6),
    ('Trufas de Avelã (cx 12un)', 55.00, 15, 6),
    ('Compota de Figo Ramy', 38.00, 12, 6),
    ('Alfajor Artesanal (un)', 9.50, 100, 6),
    ('Cerveja IPA Extra Lúpulo', 28.00, 120, 7),
    ('Cerveja Weiss de Trigo', 24.50, 80, 7),
    ('Cerveja Stout Chocolate', 32.00, 40, 7),
    ('Cerveja Pilsen Premium', 18.00, 200, 7),
    ('Cerveja Belgian Tripel', 45.00, 30, 7),
    ('Cerveja Red Ale Defumada', 29.00, 55, 7),
    ('Cerveja APA Refrescante', 26.00, 90, 7),
    ('Cerveja Sour de Frutas', 35.00, 25, 7),
    ('Cerveja Witbier Laranja', 22.00, 70, 7),
    ('Kit Degustação (4 rótulos)', 110.00, 15, 7),
    ('Macarrão Fettuccine de Ovos', 18.00, 60, 8),
    ('Massa de Lasanha Artesanal', 22.00, 40, 8),
    ('Molho de Tomate Rústico', 26.00, 50, 8),
    ('Ravioli de Queijo (500g)', 35.00, 20, 8),
    ('Espaguete com Tinta de Lula', 42.00, 15, 8),
    ('Molho Funghi Porcini', 38.00, 25, 8),
    ('Nhoque de Batata Caseiro', 24.00, 30, 8),
    ('Molho Quatro Queijos', 29.00, 40, 8),
    ('Capeletti de Carne', 32.00, 25, 8),
    ('Massa Integral com Grãos', 21.00, 55, 8),
    ('Pão de Fermentação Natural', 18.00, 20, 9),
    ('Baguete Francesa (un)', 8.50, 50, 9),
    ('Ciabatta com Azeitonas', 12.00, 30, 9),
    ('Pão de Queijo Especial (kg)', 45.00, 15, 9),
    ('Croissant de Manteiga', 9.00, 40, 9),
    ('Pão Italiano Redondo', 15.00, 25, 9),
    ('Focaccia de Alecrim', 14.50, 15, 9),
    ('Pão de Grãos e Castanhas', 22.00, 18, 9),
    ('Pão de Hamburguer Brioche', 16.00, 30, 9),
    ('Torradas Finas com Ervas', 12.50, 60, 9),
    ('Cesta Café da Manhã Luxo', 180.00, 10, 10),
    ('Cesta Queijos & Vinhos', 250.00, 8, 10),
    ('Kit Churrasco Premium', 220.00, 5, 10),
    ('Cesta Doce Deleite', 135.00, 12, 10),
    ('Cesta Cervejeiro Gourmet', 160.00, 15, 10),
    ('Cesta Boas Vindas', 190.00, 6, 10),
    ('Baú de Vinhos Reservas', 450.00, 3, 10),
    ('Cesta Chá e Relaxamento', 145.00, 10, 10),
    ('Kit Azeites do Mundo', 210.00, 7, 10),
    ('Cesta PicNic Completa', 280.00, 4, 10)
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

# 100 clientes: cada tupla é (nome, email, telefone, genero)
# Gênero: 'M' = masculino, 'F' = feminino, 'O' = outro
clientes = [
    ('Ricardo Silva', 'ricardo.silva@email.com', '16991112233', 'M'),
    ('Ana Paula Oliveira', 'ana.oliveira@gmail.com', '16992223344', 'F'),
    ('Marcos Paulo Mendes', 'marcos.mendes@outlook.com', '16993334455', 'M'),
    ('Juliana Ferreira', 'ju.ferreira@uol.com.br', '11994445566', 'F'),
    ('Roberto Carlos Santos', 'rc.santos@bol.com.br', '16995556677', 'M'),
    ('Fernanda Costa', 'fer.costa@hotmail.com', '16996667788', 'F'),
    ('Carlos Eduardo Lima', 'cadu.lima@yahoo.com', '11997778899', 'M'),
    ('Beatriz Souza', 'bia.souza@email.com', '16998889900', 'F'),
    ('Lucas Gabriel Rocha', 'lucas.rocha@gmail.com', '16999990011', 'M'),
    ('Camila Rodrigues', 'camila.rod@outlook.com', '16991110022', 'F'),
    ('Alexandre Pires', 'alex.pires@uol.com.br', '11992220033', 'M'),
    ('Amanda Martins', 'amanda.m@gmail.com', '16993330044', 'F'),
    ('Bruno Henrique Vaz', 'bruno.vaz@hotmail.com', '16994440055', 'M'),
    ('Daniela Albuquerque', 'dani.albu@yahoo.com', '16995550066', 'F'),
    ('Eduardo Spohr', 'edu.spohr@email.com', '11996660077', 'M'),
    ('Fabiana Karla', 'fabi.karla@gmail.com', '16997770088', 'F'),
    ('Gabriel Pensador', 'gabriel.p@outlook.com', '16998880099', 'M'),
    ('Heloísa Perissé', 'helo.per@uol.com.br', '16999991100', 'F'),
    ('Ítalo Ferreira', 'italo.f@gmail.com', '11991111122', 'M'),
    ('Jéssica Ellen', 'jessica.e@hotmail.com', '16992222233', 'F'),
    ('Kleber Gladiador', 'kleber.g@yahoo.com', '16993333344', 'M'),
    ('Larissa Manoela', 'lari.m@email.com', '16994444455', 'F'),
    ('Murilo Benício', 'murilo.b@gmail.com', '11995555566', 'M'),
    ('Natália Guimarães', 'nat.guimaraes@outlook.com', '16996665577', 'F'),
    ('Otávio Mesquita', 'otavio.m@uol.com.br', '16997775588', 'M'),
    ('Patrícia Poeta', 'patricia.p@gmail.com', '16998885599', 'F'),
    ('Quiteria Chagas', 'quiteria.c@hotmail.com', '11999996600', 'F'),
    ('Rafael Portugal', 'rafa.portugal@yahoo.com', '16991116611', 'M'),
    ('Sabrina Sato', 'sabrina.sato@email.com', '16992226622', 'F'),
    ('Tiago Leifert', 'tiago.l@gmail.com', '16993336633', 'M'),
    ('Ursula Corbero', 'ursula.c@outlook.com', '11994446644', 'F'),
    ('Vitor Kley', 'vitor.kley@uol.com.br', '16995556655', 'M'),
    ('Wanessa Camargo', 'wanessa.c@gmail.com', '16996666677', 'F'),
    ('Xande de Pilares', 'xande.p@hotmail.com', '16997776688', 'M'),
    ('Yasmin Brunet', 'yasmin.b@yahoo.com', '11998886699', 'F'),
    ('Zeca Pagodinho', 'zeca.p@email.com', '16999997700', 'M'),
    ('Adriana Esteves', 'adriana.e@gmail.com', '16991117711', 'F'),
    ('Bento Ribeiro', 'bento.r@outlook.com', '16992227722', 'M'),
    ('Cris Vianna', 'cris.v@uol.com.br', '11993337733', 'F'),
    ('Danton Mello', 'danton.m@gmail.com', '16994447744', 'M'),
    ('Eliana Michaelichen', 'eliana.m@hotmail.com', '16995557755', 'F'),
    ('Felipe Titto', 'felipe.t@yahoo.com', '16996667766', 'M'),
    ('Giovanna Antonelli', 'gio.anto@email.com', '11997777788', 'F'),
    ('Hugo Gloss', 'hugo.g@gmail.com', '16998887799', 'O'),
    ('Isis Valverde', 'isis.v@outlook.com', '16999998800', 'F'),
    ('João Vicente', 'joao.v@uol.com.br', '16991118811', 'M'),
    ('Karol Conka', 'karol.c@gmail.com', '11992228822', 'F'),
    ('Lázaro Ramos', 'lazaro.r@hotmail.com', '16993338833', 'M'),
    ('Maju Coutinho', 'maju.c@yahoo.com', '16994448844', 'F'),
    ('Neymar Junior', 'ney.j@email.com', '13995558855', 'M'),
    ('Fábio Assunção', 'fabio.assun@email.com', '16991119900', 'M'),
    ('Grazi Massafera', 'grazi.m@gmail.com', '16992228811', 'F'),
    ('Lázaro Ramos', 'lazaro.ramos@outlook.com', '11993337722', 'M'),
    ('Taís Araújo', 'tais.araujo@uol.com.br', '11994446633', 'F'),
    ('Selton Mello', 'selton.mello@bol.com.br', '16995555544', 'M'),
    ('Paolla Oliveira', 'paolla.o@hotmail.com', '16996664455', 'F'),
    ('Rodrigo Lombardi', 'rodrigo.lomb@yahoo.com', '11997773366', 'M'),
    ('Alinne Moraes', 'alinne.moraes@email.com', '16998882277', 'F'),
    ('Mateus Solano', 'mateus.s@gmail.com', '16999991188', 'M'),
    ('Débora Falabella', 'debora.f@outlook.com', '16991110099', 'F'),
    ('Vladimir Brichta', 'vlad.b@uol.com.br', '11992229911', 'M'),
    ('Adriana Esteves', 'adri.esteves@gmail.com', '16993338822', 'F'),
    ('Murilo Benício', 'murilo.ben@hotmail.com', '16994447733', 'M'),
    ('Cauã Reymond', 'caua.r@yahoo.com', '16995556644', 'M'),
    ('Ísis Valverde', 'isis.valv@email.com', '11996665555', 'F'),
    ('Bruno Gagliasso', 'bruno.g@gmail.com', '16997774466', 'M'),
    ('Marina Ruy Barbosa', 'marina.rb@outlook.com', '16998883377', 'F'),
    ('Chay Suede', 'chay.s@uol.com.br', '16999992288', 'M'),
    ('Alice Wegmann', 'alice.w@gmail.com', '11991111199', 'F'),
    ('Emílio Dantas', 'emilio.d@hotmail.com', '16992220011', 'M'),
    ('Sophie Charlotte', 'sophie.c@yahoo.com', '16993339922', 'F'),
    ('Daniel de Oliveira', 'daniel.o@email.com', '16994448833', 'M'),
    ('Letícia Colin', 'leticia.c@gmail.com', '11995557744', 'F'),
    ('Renato Góes', 'renato.g@outlook.com', '16996666655', 'M'),
    ('Thaila Ayala', 'thaila.a@uol.com.br', '16997775566', 'F'),
    ('Ícaro Silva', 'icaro.s@gmail.com', '16998884477', 'M'),
    ('Luísa Arraes', 'luisa.a@hotmail.com', '11999993388', 'F'),
    ('Caio Blat', 'caio.b@yahoo.com', '16991112299', 'M'),
    ('Maria Ribeiro', 'maria.r@email.com', '16992221100', 'F'),
    ('Eduardo Moscovis', 'edu.mosc@gmail.com', '16993330011', 'M'),
    ('Carolina Dieckmann', 'carol.d@outlook.com', '11994449922', 'F'),
    ('Reynaldo Gianecchini', 'reynaldo.g@uol.com.br', '16995558833', 'M'),
    ('Giovanna Ewbank', 'gio.ew@gmail.com', '16996667744', 'F'),
    ('Felipe Simas', 'felipe.s@hotmail.com', '16997776655', 'M'),
    ('Agatha Moreira', 'agatha.m@yahoo.com', '11998885566', 'F'),
    ('Rodrigo Simas', 'rodrigo.s@email.com', '16999994477', 'M'),
    ('Dira Paes', 'dira.paes@gmail.com', '16991113388', 'F'),
    ('Marcos Palmeira', 'marcos.p@outlook.com', '16992222299', 'M'),
    ('Juliette Freire', 'juliette.f@uol.com.br', '83993331100', 'F'),
    ('Gil do Vigor', 'gil.vigor@gmail.com', '11994440011', 'M'),
    ('Camilla de Lucas', 'camilla.l@hotmail.com', '21995559922', 'F'),
    ('João Luiz Pedrosa', 'joao.l@yahoo.com', '16996668833', 'M'),
    ('Viih Tube', 'viih.tube@email.com', '15997777744', 'F'),
    ('Eliezer Netto', 'eliezer.n@gmail.com', '24998886655', 'M'),
    ('Jade Picon', 'jade.p@outlook.com', '11999995566', 'F'),
    ('Paulo André', 'paulo.a@uol.com.br', '27991114477', 'M'),
    ('Douglas Silva', 'douglas.s@gmail.com', '21992223388', 'M'),
    ('Arthur Aguiar', 'arthur.a@hotmail.com', '11993332299', 'M'),
    ('Liniker de Barros', 'liniker.b@yahoo.com', '16994441100', 'O'),
    ('Pabllo Vittar', 'pabllo.v@email.com', '11995550011', 'O')
]

# 100 endereços: cada tupla é (id_cliente, rua, numero, bairro, cidade, estado)
# Maioria em Ribeirão Preto e cidades da região, alguns em São Paulo
enderecos = [
    (1, 'Rua General Osório', '450', 'Centro', 'Ribeirão Preto', 'SP'),
    (2, 'Avenida João Fiúsa', '1200', 'Jardim Olhos d Água', 'Ribeirão Preto', 'SP'),
    (3, 'Rua Tibiriçá', '88', 'Centro', 'Ribeirão Preto', 'SP'),
    (4, 'Avenida Paulista', '1500', 'Bela Vista', 'São Paulo', 'SP'),
    (5, 'Rua Capitão Adelmário Facca', '32', 'Vila Virgínia', 'Ribeirão Preto', 'SP'),
    (6, 'Rua Professor João Salles Puppo', '155', 'City Ribeirão', 'Ribeirão Preto', 'SP'),
    (7, 'Rua Oscar Freire', '200', 'Jardins', 'São Paulo', 'SP'),
    (8, 'Avenida Presidente Vargas', '2100', 'Jardim Sumaré', 'Ribeirão Preto', 'SP'),
    (9, 'Rua Florêncio de Abreu', '670', 'Centro', 'Ribeirão Preto', 'SP'),
    (10, 'Rua Altino Arantes', '1020', 'Boulevard', 'Ribeirão Preto', 'SP'),
    (11, 'Rua Augusta', '900', 'Consolação', 'São Paulo', 'SP'),
    (12, 'Rua Chile', '45', 'Iraja', 'Ribeirão Preto', 'SP'),
    (13, 'Avenida Independência', '3800', 'Jardim Independência', 'Ribeirão Preto', 'SP'),
    (14, 'Rua Quintino Bocaiúva', '120', 'Vila Seixas', 'Ribeirão Preto', 'SP'),
    (15, 'Alameda Santos', '400', 'Cerqueira César', 'São Paulo', 'SP'),
    (16, 'Rua Mariana Junqueira', '330', 'Centro', 'Ribeirão Preto', 'SP'),
    (17, 'Avenida Braz Olaia Acosta', '720', 'Jardim Califórnia', 'Ribeirão Preto', 'SP'),
    (18, 'Rua Alice Além Saadi', '250', 'Nova Ribeirânia', 'Ribeirão Preto', 'SP'),
    (19, 'Avenida Faria Lima', '3500', 'Itaim Bibi', 'São Paulo', 'SP'),
    (20, 'Rua Inácio Luiz Pinto', '440', 'Alto da Boa Vista', 'Ribeirão Preto', 'SP'),
    (21, 'Rua Silveira Martins', '1100', 'Campos Elíseos', 'Ribeirão Preto', 'SP'),
    (22, 'Rua Lafaiete', '890', 'Centro', 'Ribeirão Preto', 'SP'),
    (23, 'Rua Haddock Lobo', '100', 'Cerqueira César', 'São Paulo', 'SP'),
    (24, 'Avenida Caramuru', '2500', 'República', 'Ribeirão Preto', 'SP'),
    (25, 'Rua Visconde de Inhaúma', '580', 'Centro', 'Ribeirão Preto', 'SP'),
    (26, 'Rua Marechal Deodoro', '140', 'Vila Seixas', 'Ribeirão Preto', 'SP'),
    (27, 'Avenida Rebouças', '2200', 'Pinheiros', 'São Paulo', 'SP'),
    (28, 'Rua São José', '1600', 'Boulevard', 'Ribeirão Preto', 'SP'),
    (29, 'Rua Garibaldi', '1300', 'Centro', 'Ribeirão Preto', 'SP'),
    (30, 'Rua Bernardino de Campos', '920', 'Centro', 'Ribeirão Preto', 'SP'),
    (31, 'Avenida 9 de Julho', '1100', 'Jardim Sumaré', 'Ribeirão Preto', 'SP'),
    (32, 'Rua Otto Benz', '550', 'Nova Ribeirânia', 'Ribeirão Preto', 'SP'),
    (33, 'Rua Sete de Setembro', '400', 'Centro', 'Ribeirão Preto', 'SP'),
    (34, 'Rua Amador Bueno', '220', 'Centro', 'Ribeirão Preto', 'SP'),
    (35, 'Avenida Ipiranga', '200', 'República', 'São Paulo', 'SP'),
    (36, 'Rua Couto Magalhães', '150', 'Alto da Boa Vista', 'Ribeirão Preto', 'SP'),
    (37, 'Avenida Costabile Romano', '2200', 'Ribeirânia', 'Ribeirão Preto', 'SP'),
    (38, 'Rua Nélio Guimarães', '350', 'Alto da Boa Vista', 'Ribeirão Preto', 'SP'),
    (39, 'Rua Buri', '12', 'Jardim Paulistano', 'Ribeirão Preto', 'SP'),
    (40, 'Avenida Maurílio Biagi', '1800', 'Santa Cruz', 'Ribeirão Preto', 'SP'),
    (41, 'Rua Itacolomi', '450', 'Alto da Boa Vista', 'Ribeirão Preto', 'SP'),
    (42, 'Rua Arnaldo Victaliano', '600', 'Jardim Palma Travassos', 'Ribeirão Preto', 'SP'),
    (43, 'Rua João Penteado', '1100', 'Jardim Sumaré', 'Ribeirão Preto', 'SP'),
    (44, 'Avenida Portugal', '950', 'Santa Cruz', 'Ribeirão Preto', 'SP'),
    (45, 'Rua Eliseu Guilherme', '300', 'Jardim Sumaré', 'Ribeirão Preto', 'SP'),
    (46, 'Avenida Luiz Maggioni', '45', 'Distrito Industrial', 'Ribeirão Preto', 'SP'),
    (47, 'Rua Guiana Inglesa', '220', 'Jardim Independência', 'Ribeirão Preto', 'SP'),
    (48, 'Rua Javari', '1500', 'Ipiranga', 'Ribeirão Preto', 'SP'),
    (49, 'Avenida do Café', '800', 'Vila Tibério', 'Ribeirão Preto', 'SP'),
    (50, 'Avenida Professor João Fiúsa', '2500', 'Jardim Olhos d Água', 'Ribeirão Preto', 'SP'),
    (51, 'Rua Barão do Rio Branco', '120', 'Centro', 'Sertãozinho', 'SP'),
    (52, 'Avenida Egisto Sicchieri', '800', 'Jardim Alvorada', 'Sertãozinho', 'SP'),
    (53, 'Rua XV de Novembro', '450', 'Centro', 'Cravinhos', 'SP'),
    (54, 'Avenida Rita Cândida Nogueira', '110', 'Jardim Itamarati', 'Cravinhos', 'SP'),
    (55, 'Rua Santos Dumont', '33', 'Centro', 'Dumont', 'SP'),
    (56, 'Avenida Dr. Pio Dufles', '900', 'Centro', 'Pontal', 'SP'),
    (57, 'Rua Prudente de Moraes', '1500', 'Centro', 'Ribeirão Preto', 'SP'),
    (58, 'Avenida Costábile Romano', '1200', 'Ribeirânia', 'Ribeirão Preto', 'SP'),
    (59, 'Rua José Bonifácio', '600', 'Centro', 'Ribeirão Preto', 'SP'),
    (60, 'Avenida Senador César Vergueiro', '450', 'Jardim Irajá', 'Ribeirão Preto', 'SP'),
    (61, 'Rua Professor João Salles Puppo', '300', 'City Ribeirão', 'Ribeirão Preto', 'SP'),
    (62, 'Avenida Santa Luzia', '150', 'Jardim Sumaré', 'Ribeirão Preto', 'SP'),
    (63, 'Rua João Penteado', '800', 'Boulevard', 'Ribeirão Preto', 'SP'),
    (64, 'Avenida do Café', '1200', 'Vila Tibério', 'Ribeirão Preto', 'SP'),
    (65, 'Rua Javaé', '45', 'Ipiranga', 'Ribeirão Preto', 'SP'),
    (66, 'Avenida Dom Pedro I', '1100', 'Ipiranga', 'Ribeirão Preto', 'SP'),
    (67, 'Rua General Glicério', '300', 'Vila Virgínia', 'Ribeirão Preto', 'SP'),
    (68, 'Avenida Luzitana', '900', 'Parque Ribeirão', 'Ribeirão Preto', 'SP'),
    (69, 'Rua Manoel de Macedo', '120', 'Vila Albertina', 'Ribeirão Preto', 'SP'),
    (70, 'Avenida General Euclides de Figueiredo', '1500', 'Adelino Simioni', 'Ribeirão Preto', 'SP'),
    (71, 'Rua Dr. Romeu Pereira', '44', 'Alto da Boa Vista', 'Ribeirão Preto', 'SP'),
    (72, 'Avenida Professor João Fiúsa', '3100', 'Jardim Olhos d Água', 'Ribeirão Preto', 'SP'),
    (73, 'Rua Chile', '780', 'Irajá', 'Ribeirão Preto', 'SP'),
    (74, 'Rua Platina', '15', 'Vila Recreio', 'Ribeirão Preto', 'SP'),
    (75, 'Avenida Jerônimo Gonçalves', '500', 'Centro', 'Ribeirão Preto', 'SP'),
    (76, 'Rua Américo Brasiliense', '400', 'Centro', 'Ribeirão Preto', 'SP'),
    (77, 'Rua Visconde de Inhaúma', '1100', 'Centro', 'Ribeirão Preto', 'SP'),
    (78, 'Avenida Francisco Junqueira', '2500', 'Jardim Paulista', 'Ribeirão Preto', 'SP'),
    (79, 'Rua Henrique Dumont', '800', 'Jardim Paulista', 'Ribeirão Preto', 'SP'),
    (80, 'Avenida Treze de Maio', '1400', 'Jardim Paulista', 'Ribeirão Preto', 'SP'),
    (81, 'Rua Camilo de Mattos', '300', 'Jardim Paulista', 'Ribeirão Preto', 'SP'),
    (82, 'Avenida Meira Júnior', '1100', 'Jardim Mosteiro', 'Ribeirão Preto', 'SP'),
    (83, 'Rua Capitão Salomão', '600', 'Campos Elíseos', 'Ribeirão Preto', 'SP'),
    (84, 'Rua Tamandaré', '900', 'Campos Elíseos', 'Ribeirão Preto', 'SP'),
    (85, 'Avenida Saudade', '1200', 'Campos Elíseos', 'Ribeirão Preto', 'SP'),
    (86, 'Rua Fernão Sales', '450', 'Campos Elíseos', 'Ribeirão Preto', 'SP'),
    (87, 'Avenida Brasil', '2200', 'Vila Elisa', 'Ribeirão Preto', 'SP'),
    (88, 'Rua Guiana Inglesa', '400', 'Vila Mariana', 'Ribeirão Preto', 'SP'),
    (89, 'Avenida Mogiana', '1500', 'Vila Mariana', 'Ribeirão Preto', 'SP'),
    (90, 'Rua Pernambuco', '600', 'Ipiranga', 'Ribeirão Preto', 'SP'),
    (91, 'Avenida Rio Branco', '1100', 'Centro', 'Brodowski', 'SP'),
    (92, 'Rua General Carneiro', '45', 'Centro', 'Brodowski', 'SP'),
    (93, 'Avenida das Castanheiras', '200', 'Condomínio Guaporé', 'Ribeirão Preto', 'SP'),
    (94, 'Rua Inácio Luiz Pinto', '800', 'Nova Aliança', 'Ribeirão Preto', 'SP'),
    (95, 'Avenida Laranjeiras', '150', 'Bonfim Paulista', 'Ribeirão Preto', 'SP'),
    (96, 'Rua Izabel da Silva', '33', 'Bonfim Paulista', 'Ribeirão Preto', 'SP'),
    (97, 'Alameda dos Ipês', '90', 'San Marco', 'Ribeirão Preto', 'SP'),
    (98, 'Rua Abrahão Issa Halack', '450', 'Ribeirânia', 'Ribeirão Preto', 'SP'),
    (99, 'Avenida Leais Paulista', '800', 'Jardim Irajá', 'Ribeirão Preto', 'SP'),
    (100, 'Rua Galileu Galilei', '1500', 'Irajá', 'Ribeirão Preto', 'SP')
]

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
popular_vendas()  # Essa é a mais demorada — gera mais de um ano de histórico de vendas!

print('/* DADOS INSERIDOS COM SUCESSO! */\n')

# Fechando a conexão com o banco — boa prática sempre fazer isso no final!
conn.close()