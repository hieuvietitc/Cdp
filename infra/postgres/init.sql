-- Create CDP schema (isolated from any existing loyalty/sales tables)
CREATE SCHEMA IF NOT EXISTS cdp;

-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
