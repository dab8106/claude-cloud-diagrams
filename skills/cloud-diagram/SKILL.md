---
description: Generate Lucidchart-quality architecture diagrams for AWS, Azure, GCP, Kubernetes, DevOps/CI-CD pipelines, AI/ML systems, and HashiCorp (Terraform/Vault/Consul/Nomad) using each vendor's real, official icon set. Use whenever the user asks to draw, sketch, or generate a cloud architecture diagram, infrastructure diagram, system diagram, deployment diagram, Kubernetes diagram, DevOps pipeline diagram, AI/ML architecture diagram, or a reference architecture for AWS/Azure/GCP/Kubernetes/Terraform/Vault/Consul/Nomad. Also covers requests like "diagram this architecture", "draw our infra", or "make this look like a Lucidchart diagram".
---

# Cloud / infra architecture diagrams

You generate real, rendered PNG/SVG architecture diagrams by writing and running a short
Python script against the `diagrams` library (mingrammer/diagrams — used here purely for
its graph layout engine: `Diagram`, `Cluster`, `Edge`, Graphviz rendering). Every node icon
comes from this plugin's own bundled, official icon library in `assets/icons/` — never
from `diagrams`' own bundled icon images, and never invented or guessed.

## Step 1 — Gather requirements

From the user's request, identify:
- **Provider/domain(s)** involved: AWS, Azure, GCP, Kubernetes, DevOps/CI-CD, AI/ML,
  HashiCorp — a single request can span more than one (e.g. "Terraform provisioning an
  AWS EKS cluster running a RAG pipeline" spans HashiCorp + AWS + Kubernetes + AI/ML).
- **Components**: the actual named services/tools (e.g. "EC2", "Lambda", "Vault",
  "Kubernetes ingress", "Postgres", "an LLM").
- **Logical groupings**: VPC, subnet, region, availability zone, Kubernetes namespace,
  environment (prod/staging), or a vendor "stack" grouping (e.g. HashiCorp tools grouped
  together). Infer sensible groupings from context if the user doesn't spell them out.
- **Connections/data flow**: what talks to what, and whether it's worth labeling the
  connection type (data flow, control plane, secrets, service mesh, provisioning).

Keep this step fast for straightforward requests — don't interrogate the user over a
simple "draw a 3-tier AWS app" ask. Only pause to ask a clarifying question when the
request is genuinely ambiguous (e.g. spans multiple clouds with no clear boundary, or
names a component with no obvious icon match).

## Step 2 — Check the environment (once per session)

Run this once per session, skip on repeat invocations within the same session:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_env.py
```

If it reports `ENVIRONMENT NOT READY`, relay its exact remediation commands to the user
and stop — don't attempt to render without a working `diagrams` + Graphviz install.

## Step 3 — Map components to icon assets (static lookup only, no searching)

For each component, read the matching catalog(s) under `references/`:
`aws.md`, `azure.md`, `gcp.md`, `kubernetes.md`, `devops.md`, `hashicorp.md`, `ai-ml.md`.
Each is a plain markdown table of `Name → assets/icons/<provider>/<file>.png`. This is a
pure file read — do not grep the installed `diagrams` package, do not fetch anything from
the internet, and do not guess a path that "looks right."

Notes baked into the catalogs, worth remembering:
- A component can be cloud-native (e.g. an LLM served via AWS Bedrock → check `aws.md`)
  or third-party app-layer (e.g. LangChain → check `ai-ml.md`). Check the most specific
  catalog first, then the provider catalog, then `ai-ml.md`/`devops.md` for cross-cutting
  tools.
- `hashicorp.md` and `ai-ml.md` both explicitly list a few components with **no available
  icon** (HashiCorp Boundary; OpenAI, Pinecone, Weaviate, Cohere, Chroma, LlamaIndex for
  AI/ML) — for these, use the plain-box fallback described in `style-guide.md`, don't
  substitute an unofficial or unlicensed logo.
- If a component genuinely isn't in any catalog, use the plain-box fallback and tell the
  user which node(s) fell back, rather than inventing a path.

## Step 4 — Load the style guide

Read `references/style-guide.md` before writing the script. It has copy-pasteable
`graph_attr`/`Cluster`/`Edge` settings, the per-provider color palette, and the
title/legend conventions — apply them so output looks consistent across requests instead
of reinventing styling choices each time.

## Step 5 — Write and run the script

Write a short Python script using the `diagrams` DSL, e.g.:

```python
from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom

ICONS = "${CLAUDE_PLUGIN_ROOT}/assets/icons"

with Diagram("Title", show=False, direction="LR",
             graph_attr={...}, node_attr={...}, edge_attr={...},
             filename="<output-path-without-extension>", outformat="png"):
    ec2 = Custom("Amazon EC2", f"{ICONS}/aws/amazon-ec2.png")
    vault = Custom("Vault", f"{ICONS}/hashicorp/vault.png")
    ec2 >> Edge(color="#000000", style="dashed", label="secrets") >> vault
```

Default output location: a `diagrams-output/` folder in the user's current working
directory (create it if missing), unless the user specifies a path. Run the script via
Bash: `python3 <script>.py`.

## Step 6 — Self-correction

- **`graphviz.backend.execute.ExecutableNotFound`**: don't retry — this means Graphviz
  itself isn't installed. Surface `check_env.py`'s remediation message.
- **A referenced icon path doesn't exist** (typo while transcribing from the catalog):
  re-read the relevant `references/*.md` table once, correct the path, and retry. If it
  still fails, fall back to a plain labeled box for that node and mention it to the user.
- Cap retries at 3 total attempts before reporting the specific failure to the user.

## Step 7 — Return the result

Confirm the output file path and give a one-line description of what was drawn, including
a note on any components that fell back to a plain box for lack of an available icon.
