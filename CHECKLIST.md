# Project & Architecture Intake Checklist

This checklist acts as the durable record of requirements, decisions, and capabilities for the **Zerops AstroBranding Sovereign Platform**.

## 1. Project Identity & Scope
- **Repository**: `baiosfera/zerops-astrobranding`
- **Platform**: Zerops Incus LXC Cloud Platform
- **Audience**: Modern vibe-coders, AI agents, enterprise founders, and coaches deploying high-performance astrological, AI, and messaging solutions.
- **Topology Model**: Sovereign 10-Service Mesh (5 runtimes + 5 stateful managed services).

## 2. Monorepo Surface Split
- **`apps/website` (Astro 5 SSG)**: Public pages, landing page, SEO metadata, documentation, high-speed static delivery.
- **`apps/webapp` (React 19 + Vite CSR)**: Authenticated dashboard, client cockpit, astrological dossier inspection, real-time service health.
- **`apps/astrobranding` (Bun + Hono.dev)**: Core API gateway, typed RPC endpoints with Zod OpenAPI, BullMQ queues, and cluster orchestrator.
- **`packages/contracts`**: Universal Zod 4 schemas and TypeScript interfaces (SSoT).
- **`packages/database`**: PostgreSQL 18 schemas with Drizzle ORM, `uuidv7()` and `pgvector` HNSW index.
- **`packages/engine`**: Microservice drivers for Bifrost, FreeLLMAPI, EvolutionGo, and NATS JetStream.

## 3. Microservices Mesh
- [x] **Maxim AI Bifrost (`apps/bifrost`)**: Go v2.0.0 gateway, port `:8080`, CEL adaptive routing, semantic caching in Valkey 7.2.
- [x] **FreeLLMAPI (`apps/freellmapi`)**: Node.js 22 proxy, port `:3001`, aggregating 34+ free inference providers with persistent SQLite.
- [x] **EvolutionGo (`apps/evolution`)**: Go WhatsApp engine (`whatsmeow`), port `:8085`, double opt-in, OTP, and NATS event stream.
- [x] **Nous Research Hermes-Agent (`apps/hermes`)**: Python 3.12 (Ubuntu invariant) copilot, port `:8000`, Telegram API 22.8, and NATS JetStream bridge.

## 4. Managed Services on Zerops
- [x] **`database`**: `postgresql:single@18` (profile `oltp-hobby`) with `vector` extension.
- [x] **`valkey`**: `valkey:single@7.2` (profile `hobby`) for BullMQ and semantic cache.
- [x] **`nats`**: `nats:single@2.12` with JetStream persistence.
- [x] **`objectstorage`**: S3-compatible bucket for media and generated PDFs.
- [x] **`localstorage`**: POSIX volume for SQLite databases and WhatsApp session keys.

## 5. Deployment & Delivery
- **Manisfest**: `zerops.yaml` with 5 multi-setup lifecycle configurations.
- **Provisioning**: `import.yaml` validated with `zcp-validate yaml`.
- **CI/CD**: GitHub Actions workflow with `zeropsio/actions@v1.0.2`.
