# 📝 Documentation

Technical references for Prompt Polisher. Planning material (roadmap, task
tracker, walkthrough) lives in [`../project-docs/`](../project-docs/).

## Contents

| File | Description |
|---|---|
| [`final_demo_prep.md`](./final_demo_prep.md) | **Start here for a demo.** Setup checklist, run order, demo script and troubleshooting |
| [`architecture.md`](./architecture.md) | System design, component breakdown and diagrams |
| [`api-documentation.md`](./api-documentation.md) | REST/WebSocket endpoint reference with request/response examples |
| [`model-card.md`](./model-card.md) | AI model card — architecture, training data, evaluation, reproduction |
| [`frontend.md`](./frontend.md) | Next.js app structure, design system and component conventions |
| [`infrastructure.md`](./infrastructure.md) | Docker, Nginx, monitoring and multi-node deployment |
| [`network-setup.md`](./network-setup.md) | LAN addressing and firewall rules for the multi-laptop setup |

## Architecture Decision Records (ADRs)

ADRs document significant technical decisions. Create one whenever you make a
choice that:

- Affects multiple team members
- Is hard or expensive to reverse
- Involves trade-offs worth recording

Save them as `docs/adr/NNN-short-title.md`.

### Format

```markdown
# ADR-001: [Title]

## Status: Accepted / Proposed / Deprecated

## Context
What is the problem or situation?

## Decision
What did we decide?

## Consequences
What are the trade-offs? What becomes easier/harder?
```
