# Third-party icon assets

This plugin bundles icon assets sourced directly from each vendor's official architecture
icon pack, converted to a consistent PNG format for use in generated diagrams. These
assets remain the property of their respective owners and are used here under each
vendor's stated terms for diagram/documentation use. This plugin's own code is MIT
licensed (see `LICENSE`); the bundled icon images below are **not** — they carry the terms
listed here regardless of this repo's overall license.

## AWS (`assets/icons/aws/`)
Source: [AWS Architecture Icons](https://aws.amazon.com/architecture/icons/), Amazon Web
Services, Inc. Free to use in architecture diagrams, whitepapers, and presentation
materials. **Do not** modify the icons or use them to represent a non-AWS product/service.
Icons remain the property of AWS; AWS reserves all other rights.

## Azure (`assets/icons/azure/`)
Source: [Azure Architecture Icons](https://learn.microsoft.com/en-us/azure/architecture/icons/),
Microsoft Corporation. Permitted for architectural diagrams, training materials, and
documentation, including naming the product near the icon. **Do not** modify (crop, flip,
rotate, distort) the icons, use Microsoft product icons to represent your own
product/service, or use them in marketing communications without Microsoft's permission.

## GCP (`assets/icons/gcp/`)
Source: [Google Cloud Icons](https://cloud.google.com/icons), Google LLC. Free to use to
accurately reference Google Cloud technology and tools, e.g. in architecture diagrams and
documentation. No separate formal license document is published by Google; use is
expected to stay within that reference-only purpose.

## IBM (`assets/icons/ibm/`)
Source: [IBM Cloud architecture icons](https://github.com/IBM-Cloud/architecture-icons),
IBM Corporation. The repository states it is published "to provide IBM Cloud Architecture
icons for external customers and business partners." Covers IBM Cloud platform services,
watsonx/AI, and general security concepts (IAM, Secrets Manager, Cloud Pak for Security).
**Does not cover the standalone IBM Security product line** (QRadar, Guardium,
Verify/Verify Access) — no public icon stencil kit was found for these; diagrams
referencing them use the generic-shape fallback (see
`skills/cloud-diagram/references/style-guide.md`).

## Kubernetes (`assets/icons/kubernetes/`)
Source: [Kubernetes community icon set](https://github.com/kubernetes/community/tree/master/icons),
a CNCF project. Subject to [CNCF trademark usage guidelines](https://www.linuxfoundation.org/trademarks).

## HashiCorp, DevOps tools, and AI/ML vendor logos (`assets/icons/hashicorp/`, `assets/icons/devops/`, `assets/icons/ai-ml/`)
Source: [Simple Icons](https://simpleicons.org/), artwork licensed **CC0 1.0** (public
domain dedication). CC0 covers the icon artwork itself, not the underlying trademarks of
each depicted company (HashiCorp, Docker, Anthropic, etc.). Using a vendor's icon to label
that vendor's own product in an architecture diagram — the only use this plugin makes of
them — is standard nominative use; this is not a license to use any mark for unrelated
purposes (e.g. as this plugin's own logo, or to imply endorsement).

## Generic AI agent icon (`assets/icons/ai-ml/agent.png`)
Source: [Lucide](https://lucide.dev/) `bot` icon, **ISC license** (permissive, similar to
MIT). Lucide is a generic UI icon set, not a company logo — used here for a vendor-neutral
"AI agent" node where using an actual cloud provider's own agent icon (AWS Bedrock
AgentCore, Azure Foundry Agent Service) would misleadingly brand an otherwise
cloud-agnostic diagram.

## Known gaps — no icon shipped
No CC0 or otherwise freely-redistributable icon was found for: **HashiCorp Boundary**,
**OpenAI**, **Pinecone**, **Weaviate**, **Cohere**, **Chroma**, **LlamaIndex**, **IBM
QRadar**, **IBM Guardium**, **IBM Verify/Verify Access**. Diagrams
referencing these use a plain generic labeled box instead (see
`skills/cloud-diagram/references/style-guide.md`). If you have a properly licensed icon
for any of these, `scripts/build_icon_catalog.py` can be extended to include it.

## Refreshing the icon packs
AWS refreshes its icon pack quarterly; Azure and GCP update on their own cadence. This
plugin's bundled copies are a point-in-time snapshot. To refresh: re-download each pack
from the official source URLs above, then re-run `scripts/build_icon_catalog.py` against
the new files.
