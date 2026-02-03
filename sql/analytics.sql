-- sql/analytics.sql
-- Queries analíticas exigidas pelo teste

-------------------------------------------------------------
-- Query 1:
-- Top 5 operadoras com maior crescimento percentual de despesas
-- entre o primeiro e o último trimestre analisado.
-------------------------------------------------------------

WITH despesas_por_operadora_tri AS (
    SELECT
        d.registro_ans,
        o.razao_social,
        o.uf,
        d.ano,
        d.trimestre,
        d.valor_despesas
    FROM despesas_consolidadas d
    LEFT JOIN operadoras o
        ON d.registro_ans = o.registro_ans
),
primeiro_ultimo_tri AS (
    SELECT
        registro_ans,
        MIN(ano * 10 + trimestre) AS inicio_ref,   -- "chave" do primeiro período
        MAX(ano * 10 + trimestre) AS fim_ref       -- "chave" do último período
    FROM despesas_por_operadora_tri
    GROUP BY registro_ans
),
valores AS (
    SELECT
        p.registro_ans,
        d_ini.razao_social,
        d_ini.uf,
        d_ini.valor_despesas AS valor_inicial,
        d_fim.valor_despesas AS valor_final
    FROM primeiro_ultimo_tri p
    JOIN despesas_por_operadora_tri d_ini
        ON d_ini.registro_ans = p.registro_ans
       AND (d_ini.ano * 10 + d_ini.trimestre) = p.inicio_ref
    JOIN despesas_por_operadora_tri d_fim
        ON d_fim.registro_ans = p.registro_ans
       AND (d_fim.ano * 10 + d_fim.trimestre) = p.fim_ref
    WHERE d_ini.valor_despesas IS NOT NULL
      AND d_ini.valor_despesas > 0
      AND d_fim.valor_despesas IS NOT NULL
)
SELECT
    registro_ans,
    razao_social,
    uf,
    valor_inicial,
    valor_final,
    ((valor_final - valor_inicial) / valor_inicial) * 100 AS crescimento_percentual
FROM valores
ORDER BY crescimento_percentual DESC
LIMIT 5;


-------------------------------------------------------------
-- Query 2:
-- Distribuição de despesas por UF + média por operadora na UF
-------------------------------------------------------------

WITH despesas_por_uf AS (
    SELECT
        o.uf,
        SUM(d.valor_despesas) AS total_despesas_uf,
        COUNT(DISTINCT d.registro_ans) AS qtd_operadoras_uf
    FROM despesas_consolidadas d
    LEFT JOIN operadoras o
        ON d.registro_ans = o.registro_ans
    WHERE d.valor_despesas IS NOT NULL
    GROUP BY o.uf
)
SELECT
    uf,
    total_despesas_uf,
    qtd_operadoras_uf,
    total_despesas_uf / NULLIF(qtd_operadoras_uf, 0) AS media_por_operadora
FROM despesas_por_uf
ORDER BY total_despesas_uf DESC
LIMIT 5;


-------------------------------------------------------------
-- Query 3:
-- Quantas operadoras tiveram despesas acima da média geral
-- em pelo menos 2 dos 3 trimestres analisados.
-------------------------------------------------------------

WITH media_global AS (
    SELECT AVG(valor_despesas) AS media_geral
    FROM despesas_consolidadas
    WHERE valor_despesas IS NOT NULL
),
despesas_flag_acima AS (
    SELECT
        d.registro_ans,
        d.ano,
        d.trimestre,
        d.valor_despesas,
        CASE
            WHEN d.valor_despesas > (SELECT media_geral FROM media_global)
            THEN 1
            ELSE 0
        END AS acima_media
    FROM despesas_consolidadas d
    WHERE d.valor_despesas IS NOT NULL
),
contador AS (
    SELECT
        registro_ans,
        SUM(acima_media) AS qtd_trimestres_acima
    FROM despesas_flag_acima
    GROUP BY registro_ans
)
SELECT
    COUNT(*) AS operadoras_com_pelo_menos_dois_trimestres_acima
FROM contador
WHERE qtd_trimestres_acima >= 2;
