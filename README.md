# FinOps for Agentic-AI Architectures on Azure

[![CI](https://github.com/nubenetes/finops-agentic-ai-architectures/actions/workflows/ci.yml/badge.svg)](https://github.com/nubenetes/finops-agentic-ai-architectures/actions/workflows/ci.yml)
[![Report: Markdown + Mermaid](https://img.shields.io/badge/Report-Markdown_%2B_Mermaid-4338ca)](docs/finops-agentic-ai-architectures-study.md)
[![Generated with: Claude Opus 5.5 in Google Antigravity](https://img.shields.io/badge/Generated_with-Claude_Opus_5.5_(Antigravity)-D97757?logo=anthropic&logoColor=white)](#ai-generation--provenance)
[![Framework: FinOps Foundation](https://img.shields.io/badge/Framework-FinOps_Foundation-0f766e)](https://www.finops.org/framework/)
[![Currency: EUR + USD](https://img.shields.io/badge/Currency-EUR_%2B_USD-15803d)](calculator/assumptions.json)
[![Regions: EU + US](https://img.shields.io/badge/Regions-Spain_Central_·_EU_·_US-0078D4?logo=microsoftazure)](docs/finops-agentic-ai-architectures-study.md#13-regional-analysis-europe-and-the-united-states)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B_stdlib_only-3776AB?logo=python)](calculator/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A vendor-neutral, industry-agnostic **FinOps study and decision model** for enterprise **agentic-AI platforms** (assistants and agents with deterministic guardrails) on Microsoft Azure. It helps any organisation — from a start-up to a global corporation, from a 1,000-query pilot to a multi-million-query B2C app — decide **which architecture is the most cost-effective, and when to switch from one to another**.

> 📖 **Full study (Markdown with Mermaid diagrams, rendered natively by GitHub)**: [docs/finops-agentic-ai-architectures-study.md](docs/finops-agentic-ai-architectures-study.md)
>
> 🤖 **AI Generation & Provenance**: The study, parametric FinOps model, Python calculator, unit tests and Mermaid diagrams in this repository were generated in **Google Antigravity** using **Claude Opus 5.5 (High)**, with YouTube catalog verification assisted by **Gemini Flash** and final updates via the **Antigravity Orchestrator**.

## Table of Contents

- [What it compares](#what-it-compares)
- [Key findings](#key-findings)
  - [Reference scenario (P3 Regulated, Spain Central)](#reference-scenario-p3-regulated-spain-central)
  - [Guidance by organisation size](#guidance-by-organisation-size)
  - [Decision tree](#decision-tree)
- [Full Study Index (docs/finops-agentic-ai-architectures-study.md)](#full-study-index-docsfinops-agentic-ai-architectures-studymd)
- [Run the calculator](#run-the-calculator)
- [Official Video Series & Curated YouTube Playlists (@nubenetes)](#official-video-series--curated-youtube-playlists-nubenetes)
  - [Curated YouTube Playlists](#curated-youtube-playlists)
  - [Dedicated Video Series for This Study (12 Sessions)](#dedicated-video-series-for-this-study-12-sessions)
  - [Per-Video Architectural Summaries](#per-video-architectural-summaries)
  - [Companion @nubenetes Sessions on Individual Pillars](#companion-nubenetes-sessions-on-individual-pillars)
- [Repository structure](#repository-structure)
- [Disclaimer](#disclaimer)
  - [AI generation & provenance](#ai-generation--provenance)
- [License](#license)

## What it compares

| Option | Stack | In one sentence |
| :--- | :--- | :--- |
| **A · Pure serverless** | Azure Functions Flex Consumption + Durable Functions | Lowest fixed cost; best for 1–2 simple agents |
| **B · Managed agentic platform** | Microsoft Foundry (Agent Service, Model Router, Evaluations, Guardrails) + Functions | Best TCO from 3+ use cases thanks to native governance |
| **C · Managed Kubernetes** | AKS Automatic + Gateway API + Kafka/Event Hubs | Justified by GPUs, portability or millions of queries with an existing K8s team |
| **D · Container PaaS + enterprise integration** | Container Apps + Service Bus Premium + API Management Standard v2 | Only when APIM/Service Bus are already shared corporate services |
| **S · Per-seat SaaS** | Commercial assistant licensed per user | Benchmark for generic productivity |

Across **three security profiles** (P1 Essential, P2 Standard, P3 Regulated), **three query profiles** (light RAG, verified RAG, multi-step agentic), **sixteen Azure regions** (Spain Central, the main EU regions, UK, Switzerland and the major US regions) and any volume from 1,000 to 5 million queries per month. **Every figure is shown in EUR and USD.**

## Key findings

1. **Below ~5,000 queries/month the architecture is an infrastructure tax**: 97–99% of a regulated pilot's bill is fixed cost. Minimise fixed cost and add use cases.
2. **D is the most expensive way to start** (3.6–4× the fixed cost of serverless).
3. **A wins with 1–2 agents; B wins from 3 agents** — the number of use cases, not volume, decides between them.
4. **C rarely wins on cost alone**: the TCO crossover with B is ~<!-- val:bc-tco -->2.0 M<!-- /val --> queries/month, or ~<!-- val:bc-tco-team -->275 k<!-- /val --> with an amortised Kubernetes team.
5. **Above ~250 k queries/month, AI is 60–96% of the bill**: model routing and caching (−45–65% AI spend) matter more than architecture.
6. **US regions are ~<!-- val:us-vs-es-pct -->13<!-- /val -->% cheaper than Spain Central on infrastructure** (B pilot: <!-- val:b-pilot-us -->€966 / $1,111<!-- /val --> in East US 2 vs. <!-- val:b-pilot-es -->€1,107 / $1,273<!-- /val -->); the gap fades at high volume.
7. **An own platform beats per-seat SaaS from ~<!-- val:saas-breakeven-p1 -->88<!-- /val --> users (P1) or ~<!-- val:saas-breakeven-p3 -->251<!-- /val --> users (P3)** for specific, process-bound use cases.

### Reference scenario (P3 Regulated, Spain Central)

<!-- BEGIN:table-reference -->
| KPI (P3 Regulated, standard query, Spain Central) | A · Serverless (Functions) | B · Foundry + Functions | C · AKS Automatic | D · ACA + SB Premium + APIM |
| :--- | ---: | ---: | ---: | ---: |
| Monthly cloud bill @ 1,000 queries/month | €986 / $1,133 | €1,107 / $1,273 | €1,525 / $1,754 | €3,956 / $4,549 |
| Cost per query @ 1,000 queries/month | €0.986 / $1.13 | €1.11 / $1.27 | €1.52 / $1.75 | €3.96 / $4.55 |
| Fixed-cost share @ 1,000 queries/month | 97.1% | 97.4% | 98.2% | 99.3% |
| Monthly cloud bill @ 25,000 queries/month | €1,670 / $1,920 | €1,803 / $2,073 | €2,168 / $2,493 | €4,616 / $5,308 |
| Cost per query @ 25,000 queries/month | €0.0668 / $0.0768 | €0.0721 / $0.0829 | €0.0867 / $0.0997 | €0.185 / $0.212 |
| Annual saving vs. D @ 1,000 queries/month | €35,640 / $40,986 (−75.1%) | €34,182 / $39,309 (−72.0%) | €29,168 / $33,544 (−61.5%) | Baseline |
| Estimated operations effort (FTE, 1 agent) | 0.20 | 0.22 | 0.60 | 0.30 |
| Governance, CI/CD evaluation, multi-agent | Custom code | Native and unified | Self-managed on K8s | Manual + APIM |
<!-- END:table-reference -->

### Guidance by organisation size

<!-- BEGIN:table-segments -->
| Segment | Users | Queries/month | Profile · agents | Lowest TCO (model) | Cloud/month | Cloud/query | TCO/month | Equivalent per-seat SaaS | Economic verdict |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| XS · Start-up / micro | < 50 | 1 k | P1 · 1 agent | A · Serverless (Functions) | €166 / $191 | €0.166 / $0.191 | €2,216 / $2,549 | €840 / $966 (30 users) | SaaS / low-code |
| S · Small business | 50 – 250 | 5 k | P1 · 2 agents | B · Foundry + Functions | €298 / $343 | €0.0597 / $0.0686 | €2,766 / $3,180 | €4,200 / $4,830 (150 users) | Own platform |
| M · Mid-size company | 250 – 2,000 | 25 k | P2 · 3 agents | B · Foundry + Functions | €1,305 / $1,501 | €0.0522 / $0.0600 | €5,365 / $6,170 | €28,000 / $32,200 (1,000 users) | Own platform |
| L · Large enterprise | 2,000 – 20,000 | 120 k | P3 · 6 agents | B · Foundry + Functions | €4,558 / $5,242 | €0.0380 / $0.0437 | €11,452 / $13,170 | €224,000 / $257,600 (8,000 users) | Own platform |
| XL · Global corporation / B2C app | > 20,000 | 1.5 M | P3 · 10 agents · 3 regions | B · Foundry + Functions | €47,616 / $54,758 | €0.0317 / $0.0365 | €55,975 / $64,371 | €1,400,000 / $1,610,000 (50,000 users) | Own platform |
<!-- END:table-segments -->

### Decision tree

```mermaid
flowchart TD
    START(["New agentic-AI use case"]) --> Q0{"Generic productivity<br/>without own processes or data?"}
    Q0 -->|"Yes"| SAAS["S · Per-seat SaaS"]
    Q0 -->|"No"| Q1{"GPUs, self-hosted model,<br/>multi-cloud or on-premises?"}
    Q1 -->|"Yes"| C["C · Managed Kubernetes"]
    Q1 -->|"No"| Q2{"> 2 M queries/month, or K8s team<br/>already amortised and > 275 k/month?"}
    Q2 -->|"Yes"| C
    Q2 -->|"No"| Q3{"Shared APIM + Service Bus Premium<br/>and critical transactional messaging?"}
    Q3 -->|"Yes"| D["D · Container PaaS + integration"]
    Q3 -->|"No"| Q4{"3+ use cases in 12-18 months<br/>or native AI governance required?"}
    Q4 -->|"Yes"| B["B · Managed agentic platform"]
    Q4 -->|"No"| A["A · Pure serverless<br/>(designed to migrate to B)"]
```

## Full Study Index (docs/finops-agentic-ai-architectures-study.md)

Complete index of all sections and subsections in [docs/finops-agentic-ai-architectures-study.md](docs/finops-agentic-ai-architectures-study.md):

- [0. Using this study in five minutes](docs/finops-agentic-ai-architectures-study.md#0-using-this-study-in-five-minutes)
- [1. Executive summary](docs/finops-agentic-ai-architectures-study.md#1-executive-summary)
- [2. Reference functional pattern](docs/finops-agentic-ai-architectures-study.md#2-reference-functional-pattern)
- [3. The four candidate architectures and the SaaS benchmark](docs/finops-agentic-ai-architectures-study.md#3-the-four-candidate-architectures-and-the-saas-benchmark)
- [4. FinOps cost model](docs/finops-agentic-ai-architectures-study.md#4-finops-cost-model)
  - [4.1 Monthly cost equation](docs/finops-agentic-ai-architectures-study.md#41-monthly-cost-equation)
  - [4.2 Three thresholds that drive the decision](docs/finops-agentic-ai-architectures-study.md#42-three-thresholds-that-drive-the-decision)
- [5. The low-volume pilot paradox](docs/finops-agentic-ai-architectures-study.md#5-the-low-volume-pilot-paradox)
- [6. Cost by volume: the full matrix](docs/finops-agentic-ai-architectures-study.md#6-cost-by-volume-the-full-matrix)
- [7. Security profiles and efficiency thresholds](docs/finops-agentic-ai-architectures-study.md#7-security-profiles-and-efficiency-thresholds)
- [8. Crossovers between architectures and the effect of the number of agents](docs/finops-agentic-ai-architectures-study.md#8-crossovers-between-architectures-and-the-effect-of-the-number-of-agents)
  - [8.1 Crossover volumes (P3, one agent)](docs/finops-agentic-ai-architectures-study.md#81-crossover-volumes-p3-one-agent)
  - [8.2 The number of use cases decides between A and B](docs/finops-agentic-ai-architectures-study.md#82-the-number-of-use-cases-decides-between-a-and-b)
  - [8.3 The labour market shifts the thresholds](docs/finops-agentic-ai-architectures-study.md#83-the-labour-market-shifts-the-thresholds)
- [9. Sensitivity to query type and AI spend optimisation](docs/finops-agentic-ai-architectures-study.md#9-sensitivity-to-query-type-and-ai-spend-optimisation)
  - [9.1 When does a self-hosted small model pay off?](docs/finops-agentic-ai-architectures-study.md#91-when-does-a-self-hosted-small-model-pay-off)
  - [9.2 Provisioned capacity vs. pay-per-token](docs/finops-agentic-ai-architectures-study.md#92-provisioned-capacity-vs-pay-per-token)
- [10. Guidance by organisation size and comparison with SaaS](docs/finops-agentic-ai-architectures-study.md#10-guidance-by-organisation-size-and-comparison-with-saas)
  - [10.1 Indicative scenarios by segment](docs/finops-agentic-ai-architectures-study.md#101-indicative-scenarios-by-segment)
  - [10.2 Own platform vs. per-seat SaaS licences](docs/finops-agentic-ai-architectures-study.md#102-own-platform-vs-per-seat-saas-licences)
- [11. Business case, ROI and value levers](docs/finops-agentic-ai-architectures-study.md#11-business-case-roi-and-value-levers)
  - [11.1 Value model](docs/finops-agentic-ai-architectures-study.md#111-value-model)
  - [11.2 Value roadmap: build the foundation once, amortise it across N use cases](docs/finops-agentic-ai-architectures-study.md#112-value-roadmap-build-the-foundation-once-amortise-it-across-n-use-cases)
  - [11.3 Levers to improve TCO and ROI](docs/finops-agentic-ai-architectures-study.md#113-levers-to-improve-tco-and-roi)
- [12. DEV/PRE/PRO parity and network topology](docs/finops-agentic-ai-architectures-study.md#12-devprepro-parity-and-network-topology)
  - [12.1 Reference breakdown in P3 (1,000 queries/month, Spain Central)](docs/finops-agentic-ai-architectures-study.md#121-reference-breakdown-in-p3-1000-queriesmonth-spain-central)
  - [12.2 Private network topology](docs/finops-agentic-ai-architectures-study.md#122-private-network-topology)
- [13. Regional analysis: Europe and the United States](docs/finops-agentic-ai-architectures-study.md#13-regional-analysis-europe-and-the-united-states)
  - [13.1 Regional price index](docs/finops-agentic-ai-architectures-study.md#131-regional-price-index)
  - [13.2 Representative scenarios by region (cloud bill only)](docs/finops-agentic-ai-architectures-study.md#132-representative-scenarios-by-region-cloud-bill-only)
  - [13.3 How to choose the primary region](docs/finops-agentic-ai-architectures-study.md#133-how-to-choose-the-primary-region)
    - [Europe](docs/finops-agentic-ai-architectures-study.md#europe)
    - [United States](docs/finops-agentic-ai-architectures-study.md#united-states)
  - [13.4 What changes and what does not](docs/finops-agentic-ai-architectures-study.md#134-what-changes-and-what-does-not)
- [14. Multi-region scaling and data sovereignty](docs/finops-agentic-ai-architectures-study.md#14-multi-region-scaling-and-data-sovereignty)
- [15. Decision framework: when to use each option](docs/finops-agentic-ai-architectures-study.md#15-decision-framework-when-to-use-each-option)
  - [15.1 Decision tree](docs/finops-agentic-ai-architectures-study.md#151-decision-tree)
  - [15.2 When to use it and when not to](docs/finops-agentic-ai-architectures-study.md#152-when-to-use-it-and-when-not-to)
  - [15.3 Non-economic criteria that can reverse the decision](docs/finops-agentic-ai-architectures-study.md#153-non-economic-criteria-that-can-reverse-the-decision)
- [16. Operational FinOps practices for agentic AI](docs/finops-agentic-ai-architectures-study.md#16-operational-finops-practices-for-agentic-ai)
  - [16.1 Inform (visibility and allocation)](docs/finops-agentic-ai-architectures-study.md#161-inform-visibility-and-allocation)
  - [16.2 Optimize (unit economics)](docs/finops-agentic-ai-architectures-study.md#162-optimize-unit-economics)
  - [16.3 Operate (continuous control)](docs/finops-agentic-ai-architectures-study.md#163-operate-continuous-control)
- [17. Common cost anti-patterns](docs/finops-agentic-ai-architectures-study.md#17-common-cost-anti-patterns)
- [18. Methodology, assumptions and limitations](docs/finops-agentic-ai-architectures-study.md#18-methodology-assumptions-and-limitations)
- [19. References](docs/finops-agentic-ai-architectures-study.md#19-references)

## Run the calculator

No dependencies beyond Python 3.9+.

```bash
# Compare all architectures for your scenario (EUR and USD)
python calculator/finops_calculator.py --queries 25000 --profile P2 --agents 3 --region westeurope

# Large US deployment with an existing Kubernetes team and AI optimisation
python calculator/finops_calculator.py --queries 400000 --region eastus2 --agents 6 \
  --k8s-team --optimization routing_and_cache

# Regulated EU deployment with DR and a second sovereign cell
python calculator/finops_calculator.py --queries 150000 --region spaincentral --dr-regions 1 --extra-cells 1

# Machine-readable output, list of regions, regenerate every table in the docs
python calculator/finops_calculator.py --queries 5000 --profile P1 --json
python calculator/finops_calculator.py --list-regions
python calculator/finops_calculator.py --update-docs
```

All assumptions — fixed costs per profile, per-query AI costs, regional price indices, exchange rate, FTE cost, build cost, value model — live in [`calculator/assumptions.json`](calculator/assumptions.json). Edit them with your contract prices and run `--update-docs` to regenerate the report.

## Official Video Series & Curated YouTube Playlists (@nubenetes)

This repository is backed by a dedicated **12-video multimedia curriculum** on the official [@nubenetes](https://www.youtube.com/@nubenetes) YouTube channel (**5 long-form architectural & FinOps deep dives** and **7 focused technical Shorts**) alongside cross-referenced topic tracks and the [Nubenetes Video Hub (`nubenetes.com/videos/`)](https://nubenetes.com/videos/).

### Curated YouTube Playlists

| Track Type | Playlist | Scope & Cross-References |
| :--- | :--- | :--- |
| **Primary Flagship Series** | [**⭐ Nubenetes FinOps for Agentic AI Architectures: Azure TCO, Foundry, AKS & Serverless**](https://www.youtube.com/playlist?list=PLLvKIaVqVF78) | Official 12-part playlist (5 deep dives + 7 Shorts) walking end-to-end through this repository's 4-zone deterministic guardrail pattern, A/B/C/D/S topologies, P1–P3 profiles, TCO crossovers, model routing, and DEV/PRE/PRO private parity. Also featured at [nubenetes.com/videos/ai-agents/](https://nubenetes.com/videos/ai-agents/). |
| **Topic Track · FinOps** | [**004 - FinOps**](https://www.youtube.com/playlist?list=PLNo5gpY5DCO4Iw79NHNoLbuxfVIbrSx2J) | Cloud financial operations track housing all 12 videos from this study plus hybrid IaaS, container, and storage economics. |
| **Topic Track · AI** | [**141 - AI**](https://www.youtube.com/playlist?list=PLNo5gpY5DCO4G3GNUIqSMGEEZ1cJ6LkfD) | Enterprise AI & agentic architecture collection including all 12 videos from this repository. |
| **Topic Track · Azure** | [**083 - Azure**](https://www.youtube.com/playlist?list=PLNo5gpY5DCO7b6t0iBps8Y6oUrstV4tOa) | Microsoft Azure engineering catalog including all 12 videos from this study. |
| **Topic Track · Platform Engineering** | [**117 - Platform Engineering**](https://www.youtube.com/playlist?list=PLNo5gpY5DCO4zVdZPDn3EZ8HUt_VYJv5N) | Internal developer platforms and agentic landing zones (includes the 5 deep dives + 4 architecture Shorts). |
| **Topic Track · Serverless** | [**011 - NoOps Serverless**](https://www.youtube.com/playlist?list=PLNo5gpY5DCO4cUVxRtFsb-iKkFP16lwFR) | Azure Functions Flex Consumption & serverless agentic architectures (Options A & B sessions). |
| **Topic Track · Kubernetes** | [**013 - Kubernetes**](https://www.youtube.com/playlist?list=PLNo5gpY5DCO726yjYOilX649dyB3Z734y) & [**026 - Managed Kubernetes on Cloud**](https://www.youtube.com/playlist?list=PLNo5gpY5DCO4SlpKUA7B8RlufWlGCwRAx) | AKS Automatic tipping point, GPU self-hosting, and Kubernetes vs. managed PaaS deep dives (Option C sessions). |
| **Podcast Track** | [**⭐ Nubenetes Cloud Native Podcasts (English)**](https://www.youtube.com/playlist?list=PLBMAtCXWYfZA) | Long-form spoken engineering discussions including the 5 FinOps for Agentic AI deep-dive sessions. |
| **Companion Series** | [**Microsoft Foundry**](https://www.youtube.com/playlist?list=PLIHPlQVunY48) · [**Enterprise AI Platforms**](https://www.youtube.com/playlist?list=PLBZl7QsgYjrw) · [**Azure Container Strategy**](https://www.youtube.com/playlist?list=PLUlxI33bzjWQ) · [**Azure Hybrid IaaS FinOps**](https://www.youtube.com/playlist?list=PLaNxiRbEBYJ8) · [**AI SRE & Agentic Operations**](https://www.youtube.com/playlist?list=PLckcDbnSNdbE) · [**MCP SRE Agents & Security**](https://www.youtube.com/playlist?list=PLa99gsQrC--U) | Deep dives on individual architectural foundations (Foundry Agent Service, ACA vs. AKS, hybrid IaaS FinOps, agentic guardrails, and MCP execution safety). |

### Dedicated Video Series for This Study (12 Sessions)

| # | Format | Video Title & Link | Duration | Study Sections Covered |
| :-: | :---: | :--- | :---: | :--- |
| 1 | Deep Dive | [**Agentic AI on Azure TCO: Serverless, Foundry, AKS & Container Apps FinOps Guide**](https://www.youtube.com/watch?v=wbG4ZO3BF_U) | 9:44 | Sections 0–5 |
| 2 | Deep Dive | [**Azure Agentic AI Architectures Compared: Functions, Foundry, AKS & ACA Crossover**](https://www.youtube.com/watch?v=0SH6H5phFP4) | 7:23 | Sections 3, 6–8 |
| 3 | Deep Dive | [**FinOps for Agentic AI: Cost Equations, Model Routing, Caching & PTU Break-Even**](https://www.youtube.com/watch?v=10-s91vgbQs) | 7:10 | Sections 4, 6, 9 |
| 4 | Deep Dive | [**SaaS vs Build on Azure: Agentic AI Break-Even, Multi-Agent TCO & ROI Model**](https://www.youtube.com/watch?v=cKmt7jhtCAo) | 9:05 | Sections 8.2–8.3, 10–11 |
| 5 | Deep Dive | [**Agentic AI FinOps Operations: DEV/PRE/PRO Parity, EU/US Regions & Anti-Patterns**](https://www.youtube.com/watch?v=i5UzI-FrFfU) | 7:40 | Sections 12–17 |
| 6 | Short | [**Choosing the Most Cost-Effective Azure AI Architecture for Your Enterprise**](https://www.youtube.com/shorts/Dsv6AclJKik) | 1:28 | Sections 0, 15 |
| 7 | Short | [**How to Stop Overpaying for Azure AI Agents (Pilot Paradox)**](https://www.youtube.com/shorts/vAat9zOBBzI) | 1:28 | Sections 5, 17 |
| 8 | Short | [**Why Enterprise AI Architecture Scales by Agents, Not Volume**](https://www.youtube.com/shorts/8Lq9pNc7J7g) | 1:25 | Sections 8.2, 11.2 |
| 9 | Short | [**How Break-Even Analysis Dictates Your Enterprise AI Strategy**](https://www.youtube.com/shorts/Enu5sqiYstc) | 1:18 | Sections 4.2, 10.2, 11.1 |
| 10 | Short | [**FinOps for AI: The Kubernetes (AKS) Tipping Point on Azure**](https://www.youtube.com/shorts/g7LOltuhtx0) | 1:14 | Sections 8.1, 9.1, 15 |
| 11 | Short | [**How Model Routing & Semantic Caching Slash Agentic AI Costs**](https://www.youtube.com/shorts/iCGUTVuWwgY) | 1:26 | Sections 9, 16.2 |
| 12 | Short | [**How Decoupled Agentic AI Architecture Absorbs Traffic Spikes**](https://www.youtube.com/shorts/k8yBySfHSfE) | 1:11 | Sections 2, 9.2, 12.2 |

### Per-Video Architectural Summaries

#### 1. Agentic AI on Azure TCO: Serverless, Foundry, AKS & Container Apps FinOps Guide (9:44)

[Watch on YouTube (`wbG4ZO3BF_U`)](https://www.youtube.com/watch?v=wbG4ZO3BF_U) — Comprehensive walkthrough of the full FinOps decision model (Sections 0–5). Explains the **4-zone, 9-step deterministic guardrail pattern** separating non-AI controls (Zone 1 ingress masking, `usr_7K2` pseudonym vault, and prompt-injection admission; Zone 3 deterministic verifier, certainty threshold, and single-use permit hash; Zone 4 one-time egress re-identification and Merkle WORM audit sealing) from Zone 2's cognitive plane. Contrasts candidate topologies **A** (Functions Flex Consumption + Durable Functions), **B** (Microsoft Foundry Agent Service + Functions), **C** (AKS Automatic + Gateway API + Kafka), **D** (Container Apps + Service Bus Premium + APIM Standard v2), and **S** (Per-seat SaaS) across security profiles P1–P3, illustrating the **Low-Volume Pilot Paradox** in P3 Spain Central (1,000 queries/month): **97.1%–99.3% of the monthly cloud bill is fixed infrastructure cost** (`€986 / $1,133` on A, `€1,107 / $1,273` on B, `€1,525 / $1,754` on C, and `€3,956 / $4,549` on D).

#### 2. Azure Agentic AI Architectures Compared: Functions, Foundry, AKS & ACA Crossover (7:23)

[Watch on YouTube (`0SH6H5phFP4`)](https://www.youtube.com/watch?v=0SH6H5phFP4) — Deep-dive comparison of compute, orchestration, and integration planes across Options A, B, C, and D across security profiles **P1 Essential** (DEV + PRO, public endpoints + basic WAF, Global AI), **P2 Standard** (DEV + PRE + PRO, Private Endpoints in PRO, Data Zone EU/US), and **P3 Regulated** (full DEV/PRE/PRO private-network parity, HSM CMK, WORM sealing). Quantifies how fixed monthly infrastructure scales across P1/P2/P3 (`€140 / €520 / €957` on A; `€165 / €580 / €1,078` on B; `€620 / €1,050 / €1,498` on C; `€430 / €2,150 / €3,928` on D), maps the unit-efficiency thresholds `Q* = F / v` (`33,600` to `142,800` queries/month in P3), and walks through the exact **B vs. C crossovers**: `191k` queries/month on raw cloud bill, **`2.0 M` queries/month on full TCO** (including `0.60` vs. `0.22` base FTEs at `€6,500/mo` and `36`-month build amortisation), and **`275k` queries/month** when an existing Kubernetes platform team is already amortised.

#### 3. FinOps for Agentic AI: Cost Equations, Model Routing, Caching & PTU Break-Even (7:10)

[Watch on YouTube (`10-s91vgbQs`)](https://www.youtube.com/watch?v=10-s91vgbQs) — Dissects the parametric TCO equation across `1,000` to `5,000,000` queries/month (`cloud fixed + cloud variable + capacity steps E(Q) + operations FTE + build amortisation`, Sections 4, 6, and 9). Demonstrates sensitivity across three interaction profiles—**FAQ / Light RAG** (`€0.004/query`), **Verified RAG** (`€0.026/query`), and **Multi-Step Agentic** (`€0.120/query`, 5–15× higher variable cost)—and proves why AI spend reaches **60–96% of total cloud cost above `250k` queries/month** (`€31,628/mo` on B P3 at `1 M` standard queries; `€125,628/mo` for agentic). Shows how **model routing (`-45%`) combined with semantic caching (`-65%` total AI saving)** drops `1 M` standard queries on B P3 from `€31,628` to `€14,728/mo`, locates the **`~550k` queries/month break-even for self-hosting a small language model on two HA GPU nodes (`€2,200 / $2,530/mo`)**, and details when Provisioned Throughput Units (**PTUs at >60–70% sustained utilisation**) outperform pay-per-token.

#### 4. SaaS vs Build on Azure: Agentic AI Break-Even, Multi-Agent TCO & ROI Model (9:05)

[Watch on YouTube (`cKmt7jhtCAo`)](https://www.youtube.com/watch?v=cKmt7jhtCAo) — Strategic build-vs-buy, multi-agent scaling, and ROI business case analysis (Sections 8.2–8.3, 10, and 11). Evaluates five enterprise segments from **XS Start-up** (<50 users, 1k queries/mo on A P1) to **XL Global Corporation** (>20,000 users, 1.5M queries/mo on B P3 across 3 regions) against per-seat SaaS (`€28 / $32 per user/month`), pinpointing the **user break-even thresholds for Platform B at ~`88` users (P1), ~`153` users (P2), and ~`251` users (P3)**. Proves mathematically why **agent count—not volume—governs A vs. B** (`1–2` agents favour A Serverless, whereas from **`3+` agents** at `10k` queries/mo in P2, B's TCO `€4,930 / $5,670` beats A's `€5,292 / $6,085` and widens to `€6,765` vs. `€10,632` at 12 agents), examines US vs. European FTE labour sensitivity (`€4,500`–`€11,500/mo`), and tracks ROI payback under conservative **realised value (`€1.63 / $1.88` per query)** reaching **3.1× value/TCO (7.9-month payback)** at 3 use cases and **16.0× (1.1-month payback)** company-wide.

#### 5. Agentic AI FinOps Operations: DEV/PRE/PRO Parity, EU/US Regions & Anti-Patterns (7:40)

[Watch on YouTube (`i5UzI-FrFfU`)](https://www.youtube.com/watch?v=i5UzI-FrFfU) — Production FinOps engineering blueprint covering network parity, regional economics, FinOps Framework governance, and anti-patterns (Sections 12–17). Walks line-by-line through **DEV/PRE/PRO private-network parity** provisioned with Azure Verified Modules (AVM) in P3 Spain Central (`€1,106.80 / $1,272.82/mo` total on B: `€150.10` DEV + `€190.60` PRE + `€766.10` PRO covering Front Door Premium + WAF, Private Endpoints, PostgreSQL Flexible pseudonym vault, AI Search Basic, Key Vault Premium HSM, and Blob WORM vs. `€3,955.99` on D). Benchmarks **16 EU and US regions indexed to Spain Central (`1.00`)**—showing **Sweden Central (`0.94`, `€1,042` B pilot)** and **North Europe (`0.95`, `€1,053`)** as the lowest-cost EU options, **East US 2 (`0.87`, `€966`, `-13%`)** as lowest in the US, and **Switzerland North (`1.18`, `€1,302`)** as highest—maps **Inform → Optimize → Operate** KPIs (FOCUS billing, per-agent token attribution, basic/archive trace retention), and audits the **9 common cost anti-patterns** in Section 17.

#### 6. Choosing the Most Cost-Effective Azure AI Architecture for Your Enterprise (1:28 Short)

[Watch on YouTube (`Dsv6AclJKik`)](https://www.youtube.com/shorts/Dsv6AclJKik) — Concise 88-second walkthrough of the repository's 6-step decision tree comparing **S (Per-Seat SaaS)**, **A (Pure Serverless Functions)**, **B (Microsoft Foundry + Functions)**, **C (AKS Automatic)**, and **D (Container Apps + Service Bus Premium + APIM)** by use-case specificity, GPU/self-hosting needs, query volume (`275k`/`2.0M`), shared corporate integration, and expected agent count (`3+`).

#### 7. How to Stop Overpaying for Azure AI Agents (Pilot Paradox) (1:28 Short)

[Watch on YouTube (`vAat9zOBBzI`)](https://www.youtube.com/shorts/vAat9zOBBzI) — Explains why **97.1%–99.3%** of a 1,000-query/month regulated Azure AI pilot bill is fixed platform cost (`€3.96/query` on dedicated APIM + Service Bus Premium vs. `€0.99/query` on A Serverless and `€1.11/query` on B Microsoft Foundry) and highlights key anti-patterns: provisioning APIM/Service Bus Premium for pilots, full HA in DEV/PRE, and premature capacity reservations.

#### 8. Why Enterprise AI Architecture Scales by Agents, Not Volume (1:25 Short)

[Watch on YouTube (`8Lq9pNc7J7g`)](https://www.youtube.com/shorts/8Lq9pNc7J7g) — Summarises Section 8.2's core insight: with a single agent, Pure Serverless (A) stays cheapest on fixed cost, yet the **crossover to Microsoft Foundry (B) is triggered at 3+ agents** (`€4,930` vs. `€5,292` TCO/mo in P2 at `10k` queries/mo) because Foundry amortises evaluations, guardrails, model routing, and VNet plumbing across every new use case at near-zero marginal fixed cost.

#### 9. How Break-Even Analysis Dictates Your Enterprise AI Strategy (1:18 Short)

[Watch on YouTube (`Enu5sqiYstc`)](https://www.youtube.com/shorts/Enu5sqiYstc) — Breaks down the three parametric FinOps thresholds from Section 4.2 and Section 11—the **unit-efficiency threshold `Q* = F / v`** (when AI variable cost overtakes fixed infra), **architecture crossover volume**, and **ROI payback** (`€1.63 / $1.88` realised value per query)—alongside the per-seat SaaS user break-evens (`~88` users in P1, `~153` in P2, `~251` in P3).

#### 10. FinOps for AI: The Kubernetes (AKS) Tipping Point on Azure (1:14 Short)

[Watch on YouTube (`g7LOltuhtx0`)](https://www.youtube.com/shorts/g7LOltuhtx0) — Pinpoints exact economic tipping points for **AKS Automatic (C)** vs. **Microsoft Foundry (B)** in P3: **`191k` queries/month** on raw cloud bill only, **`2.0 M` queries/month** on full TCO (`0.60` FTE ops burden), or **`275k` queries/month** with an already-amortised Kubernetes team—plus **`~550k` queries/month** for self-hosted SLMs on HA GPU nodes (`€2,200/mo`).

#### 11. How Model Routing & Semantic Caching Slash Agentic AI Costs (1:26 Short)

[Watch on YouTube (`iCGUTVuWwgY`)](https://www.youtube.com/shorts/iCGUTVuWwgY) — Shows why optimizing token spend beats changing infrastructure above `250k` queries/month (where AI accounts for **60–96%** of the bill): routing `>60–70%` of routine queries to small models (`-45%`) and pairing **semantic caching (`-65%` combined)** cuts `1 M`-query verified RAG bills on B P3 from `€31,628` to `€14,728/month`.

#### 12. How Decoupled Agentic AI Architecture Absorbs Traffic Spikes (1:11 Short)

[Watch on YouTube (`k8yBySfHSfE`)](https://www.youtube.com/shorts/k8yBySfHSfE) — Illustrates Zone 1–4 separation from Sections 2 and 12.2: Front Door Premium + WAF terminates public channels over Private Link into Flex Consumption Functions and signed queues decoupled from the delegated agent subnet, smoothing burst traffic without paying for oversized always-on compute or tripping downstream PTU/TPM ceilings.

### Companion @nubenetes Sessions on Individual Pillars

In addition to the 12-video series dedicated directly to this study, the following existing sessions on [@nubenetes](https://www.youtube.com/@nubenetes) provide deep dives on its individual architectural and FinOps foundations:

1. [The Great Foundry Shift: Enterprise AI Operating Model & FinOps Governance](https://www.youtube.com/watch?v=CkFIcxzEnVw) — FinOps governance for GenAI on Microsoft Foundry, Pay-As-You-Go vs. Provisioned Throughput (PTU) break-even, TPM limits, and Azure data sovereignty.
2. [Cloud AI vs Kubernetes 2026: The Enterprise AI Control Plane Showdown](https://www.youtube.com/watch?v=9zosnOzQ90o) — Managed cloud AI control planes (Foundry, Bedrock, Vertex) vs. Kubernetes (AKS) for agentic platforms, "Zero Idle GPU Tax", MCP tool gateways, and data sovereignty.
3. [Azure Container Apps vs AKS: Networking, VNet Security & FinOps Economics](https://www.youtube.com/watch?v=BeOCYxr9uYE) — Mathematical FinOps modelling and break-even thresholds (scale-to-zero vs. steady-state on AKS) and VNet isolation.
4. [Azure Container Apps vs AKS: Azure Functions Integration & The 5-Lens Framework](https://www.youtube.com/watch?v=1hpnz3cz1Co) — Evaluating ACA vs. AKS including Azure Functions integration across five architectural lenses.
5. [Microsoft Foundry Deep Dive: Agent Service, Responses API & Observability](https://www.youtube.com/watch?v=STC4L1w2cPg) — Foundry Agent Service runtime, threads, tool calling, and tracing (Architecture B runtime).
6. [The 2026 Infrastructure Fork: Managed Cloud AI vs Disaggregated K8s Serving](https://www.youtube.com/watch?v=TUyX5PzEPGA) — Managed cloud AI platforms vs. disaggregated Kubernetes serving trade-offs.
7. [Azure Storage WORM Optimizado: Arquitectura y Cumplimiento Legal en Spain Central](https://www.youtube.com/watch?v=IZBAQg3kP7c) — Immutable WORM storage architecture and legal compliance in the Azure Spain Central region.
8. [Agentic SRE Defense in Depth: Zero-Trust Security for AI Agents](https://www.youtube.com/watch?v=XOrOjcgR_zg) — Zero-trust security guardrails, IAM, and prompt-injection defense for autonomous agents.
9. [Building an MCP SRE Agent: Kubernetes Tools & Production Guardrails](https://www.youtube.com/watch?v=bWBZR6rpm2s) — Deterministic execution guardrails for MCP-based agents on Kubernetes.
10. [AKS vs Azure Container Apps: The Cost of Control & Scale-to-Zero FinOps](https://www.youtube.com/shorts/NHeyQpW6i5s) — 1-minute comparison of scale-to-zero serverless economics vs. AKS fixed control planes.
11. [How the FinOps CLI Automates Break Even Math](https://www.youtube.com/shorts/-iJ65ex08dA) — Automating break-even calculations from the command line on Azure.
12. [Microsoft Foundry Production Readiness: Evaluations, SLAs & Safety](https://www.youtube.com/shorts/JDlkNqJIy9Q) — Continuous evaluation, safety guardrails, and production readiness in Microsoft Foundry.
13. [Microsoft Foundry Enterprise Controls: Security, VNet & Deadlines](https://www.youtube.com/shorts/i72ZvGizCEE) — VNet injection and enterprise security controls in Microsoft Foundry.

## Repository structure

```text
.
├── README.md
├── docs/
│   └── finops-agentic-ai-architectures-study.md   # Full study: Markdown + Mermaid (source of truth)
├── calculator/
│   ├── assumptions.json                           # Every price, index and parameter
│   ├── finops_calculator.py                       # Model, CLI and table generators
│   └── test_finops_calculator.py                  # Unit tests
└── .github/workflows/ci.yml                       # Tests, docs freshness, markdownlint
```

## Disclaimer

Figures are **indicative estimates** based on list prices (November 2026, no discounts or taxes), an indicative regional price index and expert-judgement effort assumptions. They are meant to compare options and locate thresholds, not to quote a project. Validate with the [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/), your agreement's prices and your own operational data. Service and model availability differs by region.

### AI generation & provenance

- **Authoring platform**: [Google Antigravity](https://antigravity.google/)
- **Primary model**: **Claude Opus 5.5 (High)** — authored the FinOps architecture study (`docs/finops-agentic-ai-architectures-study.md`), the parametric FinOps mathematical model (`calculator/assumptions.json`), the Python calculator and table generator (`calculator/finops_calculator.py`), unit tests (`calculator/test_finops_calculator.py`), and all Mermaid diagrams.
- **Catalog verification**: **Gemini Flash** (browser subagent) — audited the `@nubenetes` YouTube channel video and Shorts catalog to identify related sessions.
- **Repository updates**: **Antigravity Orchestrator** — integrated the related videos catalog, AI provenance metadata, and verified CI checks.

## License

[Apache License 2.0](LICENSE)
