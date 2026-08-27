SELECT column_name, data_type, is_nullable, COUNT()
FROM information_schema.columns 
WHERE table_name = 'telemetry_current';
