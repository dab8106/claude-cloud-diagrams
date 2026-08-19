# cloud-diagrams

A Claude Code plugin that generates **Lucidchart-quality architecture diagrams** for AWS,
Azure, GCP, Kubernetes, DevOps/CI-CD, AI/ML, and HashiCorp (Terraform, Vault, Consul,
Nomad) — using each vendor's real, official icon set, not generic boxes.

| | |
|---|---|
| ![AWS three-tier example](examples/aws_three_tier.png) | ![Kubernetes microservices example](examples/kubernetes_microservices.png) |
| ![Vault reference architecture example](examples/vault_rfp_reference_architecture.png) | |

## How it works

Ask Claude Code to draw an architecture diagram — e.g. *"draw a 3-tier AWS web app"*,
*"diagram a Kubernetes microservices setup with Vault for secrets"*, *"show a Terraform +
Vault + Consul reference architecture"* — and this plugin's `cloud-diagram` skill writes
and runs a short Python script using the [`diagrams`](https://diagrams.mingrammer.com/)
library's graph/layout engine, rendering every node with this plugin's own bundled,
official icon assets (`assets/icons/`) rather than generic shapes.

Icon sourcing: `AWS Architecture Icons`, `Azure Architecture Icons`, and `Google Cloud
Icons` downloaded directly from each vendor's official page; the Kubernetes community icon
set; and CC0 icons from Simple Icons for HashiCorp tools, common DevOps tooling, and
AI/ML vendors. See [`NOTICE.md`](NOTICE.md) for exact sources and usage terms per icon.

## Prerequisites

- Python 3
- [Graphviz](https://graphviz.org/) — provides the `dot` binary the `diagrams` library
  renders through:
  - macOS: `brew install graphviz`
  - Debian/Ubuntu: `sudo apt install graphviz`
  - Fedora/RHEL: `sudo dnf install graphviz`
- The `diagrams` Python package: `pip3 install diagrams`

The skill runs `scripts/check_env.py` automatically and tells you exactly what's missing
if either dependency isn't set up.

## Install

```
/plugin marketplace add <this-repo-url-or-path>
/plugin install cloud-diagrams@cloud-diagrams-marketplace
```

## Example prompts

- "Draw a 3-tier AWS web application with a load balancer, EC2, and RDS"
- "Diagram a Kubernetes microservices setup with an ingress, two services, and Vault for secrets"
- "Show a HashiCorp reference architecture: Terraform provisioning AWS infra, Vault for secrets, Consul for service mesh"
- "Draw an Azure architecture with App Service, Azure SQL, and Key Vault"
- "Diagram a RAG pipeline using Bedrock and a vector database"

## Repo layout

```
skills/cloud-diagram/           the skill: SKILL.md + reference icon catalogs + style guide
commands/cloud-diagram.md       explicit /cloud-diagram entry point
scripts/check_env.py            runtime dependency check
scripts/build_icon_catalog.py   authoring-time only: rebuilds assets/icons/ + references/*.md
                                 from freshly-downloaded vendor icon packs
assets/icons/                   the bundled, curated icon library (see NOTICE.md)
examples/                       sample rendered diagrams
```

## Refreshing the icon set

Vendor icon packs update periodically (AWS roughly quarterly). To refresh: download the
latest packs from the official sources listed in `NOTICE.md`, extract them into a staging
directory, and re-run:

```
python3 scripts/build_icon_catalog.py --staging /path/to/staging
```

## License

This repo's code is MIT licensed (see `LICENSE`). Bundled icon assets carry their own
vendor terms — see `NOTICE.md` before redistributing this repo further.
