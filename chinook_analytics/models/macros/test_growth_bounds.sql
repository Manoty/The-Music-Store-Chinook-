{% test growth_bounds(model, column_name) %}

SELECT *
FROM {{ model }}
WHERE {{ column_name }} > 2
   OR {{ column_name }} < -1

{% endtest %}
