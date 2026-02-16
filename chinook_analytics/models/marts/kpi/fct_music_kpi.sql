{{ config(materialized='table') }}

WITH customer_spend AS (
    SELECT
        c.CustomerId,
        c.Country,
        SUM(i.Total) AS total_spent
    FROM {{ ref('stg_chinook__customer') }} c
    JOIN {{ ref('stg_chinook__invoice') }} i
      ON c.CustomerId = i.CustomerId
    GROUP BY c.CustomerId, c.Country
),

top_customer AS (
    SELECT
        Country,
        CustomerId AS top_customer_id,
        total_spent AS top_customer_ltv,
        total_spent / SUM(total_spent) OVER (PARTITION BY Country) AS top_customer_contribution_pct
    FROM customer_spend
    QUALIFY ROW_NUMBER() OVER (PARTITION BY Country ORDER BY total_spent DESC) = 1
),

country_revenue AS (
    SELECT
        c.Country,
        SUM(i.Total) AS country_revenue
    FROM {{ ref('stg_chinook__customer') }} c
    JOIN {{ ref('stg_chinook__invoice') }} i
      ON c.CustomerId = i.CustomerId
    GROUP BY c.Country
),

-- Optional YoY growth (mocked as 0 for single-year dataset)
country_yoy AS (
    SELECT
        Country,
        0.0 AS country_yoy_growth_pct
    FROM country_revenue
)

SELECT
    cr.Country,
    cr.country_revenue,
    tc.top_customer_id,
    tc.top_customer_ltv,
    tc.top_customer_contribution_pct,
    cy.country_yoy_growth_pct
FROM country_revenue cr
LEFT JOIN top_customer tc
    ON cr.Country = tc.Country
LEFT JOIN country_yoy cy
    ON cr.Country = cy.Country
