-- sql/schema.sql
-- Estrutura das tabelas para o teste da Intuitive Care
-- Compatível com MySQL 8 ou PostgreSQL (ajustando sintaxe de AUTO_INCREMENT/SERIAL se necessário)

-- Tabela de operadoras (cadastro)
CREATE TABLE operadoras (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    registro_ans    BIGINT NOT NULL,
    cnpj            VARCHAR(20) NOT NULL,
    razao_social    VARCHAR(255) NOT NULL,
    modalidade      VARCHAR(100),
    uf              CHAR(2),
    criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operadoras_registro_ans ON operadoras (registro_ans);
CREATE INDEX idx_operadoras_cnpj ON operadoras (cnpj);
CREATE INDEX idx_operadoras_uf ON operadoras (uf);

-- Tabela de despesas consolidadas por trimestre
CREATE TABLE despesas_consolidadas (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    registro_ans    BIGINT NOT NULL,
    ano             INT NOT NULL,
    trimestre       INT NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    valor_despesas  DECIMAL(18,2) NOT NULL,
    criado_em       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_despesas_registro_ans ON despesas_consolidadas (registro_ans);
CREATE INDEX idx_despesas_ano_tri ON despesas_consolidadas (ano, trimestre);

-- Tabela de despesas agregadas (por RazaoSocial + UF)
CREATE TABLE despesas_agregadas (
    id                      BIGINT AUTO_INCREMENT PRIMARY KEY,
    razao_social            VARCHAR(255) NOT NULL,
    uf                      CHAR(2) NOT NULL,
    total_despesas          DECIMAL(18,2) NOT NULL,
    media_despesas          DECIMAL(18,2),
    desvio_padrao_despesas  DECIMAL(18,2),
    criado_em               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agregadas_razao_uf ON despesas_agregadas (razao_social, uf);
