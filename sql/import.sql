-- Limpa tabelas (ambiente de teste)
TRUNCATE TABLE operadoras;
TRUNCATE TABLE despesas_consolidadas;
TRUNCATE TABLE despesas_agregadas;

-- As instruções abaixo são exemplos de LOAD DATA para MySQL.
-- Antes de usar, ajuste o caminho dos arquivos CSV.

-- Cadastro de operadoras
-- LOAD DATA LOCAL INFILE '/caminho/para/cadastro_operadoras_normalizado.csv'
-- INTO TABLE operadoras
-- FIELDS TERMINATED BY ';'
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 LINES
-- (registro_ans, cnpj, razao_social, modalidade, uf);

-- Despesas consolidadas
-- LOAD DATA LOCAL INFILE '/caminho/para/consolidado_despesas.csv'
-- INTO TABLE despesas_consolidadas
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 LINES
-- (registro_ans, ano, trimestre, valor_despesas);

-- Despesas agregadas
-- LOAD DATA LOCAL INFILE '/caminho/para/despesas_agregadas.csv'
-- INTO TABLE despesas_agregadas
-- FIELDS TERMINATED BY ','
-- ENCLOSED BY '"'
-- LINES TERMINATED BY '\n'
-- IGNORE 1 LINES
-- (razao_social, uf, total_despesas, media_despesas, desvio_padrao_despesas);
