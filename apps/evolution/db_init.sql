-- EvolutionGo Database Initialization for PostgreSQL 18
-- Segregates authentication/Noise protocol keys from application messaging

SELECT 'CREATE DATABASE evogo_auth'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evogo_auth')\gexec

SELECT 'CREATE DATABASE evogo_users'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'evogo_users')\gexec

-- Anti-Starvation Shield: Hard-caps & Idle Session Reaping (Issue #106 / #118)
ALTER DATABASE evogo_auth WITH CONNECTION LIMIT 15;
ALTER DATABASE evogo_users WITH CONNECTION LIMIT 15;
ALTER DATABASE evogo_auth SET idle_session_timeout = '2min';
ALTER DATABASE evogo_users SET idle_session_timeout = '2min';
ALTER DATABASE evogo_auth SET idle_in_transaction_session_timeout = '30s';
ALTER DATABASE evogo_users SET idle_in_transaction_session_timeout = '30s';

\c evogo_auth;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c evogo_users;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
