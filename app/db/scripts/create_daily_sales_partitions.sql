DO $$
DECLARE
    start_date DATE := DATE '2019-01-01';
    end_date DATE := DATE '2031-01-01';
    current_date DATE;
    next_date DATE;
    partition_name TEXT;
BEGIN
    current_date := start_date;
    WHILE current_date < end_date LOOP
        next_date := current_date + INTERVAL '1 month';
        partition_name := format(
            'daily_sales_analytics_y%sm%s',
            to_char(current_date, 'YYYY'),
            to_char(current_date, 'MM')
        );

        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF daily_sales_analytics
             FOR VALUES FROM (%L) TO (%L);',
            partition_name,
            current_date,
            next_date
        );

        current_date := next_date;
    END LOOP;
END $$;
