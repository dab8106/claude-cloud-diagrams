---
description: Generate Lucidchart-quality architecture diagrams for AWS, Azure, GCP, IBM Cloud/watsonx/Cloud Pak, Kubernetes, DevOps/CI-CD pipelines, AI/ML systems, and HashiCorp (Terraform/Vault/Consul/Nomad) using each vendor's real, official icon set. Use whenever the user asks to draw, sketch, or generate a cloud architecture diagram, infrastructure diagram, system diagram, deployment diagram, Kubernetes diagram, DevOps pipeline diagram, AI/ML architecture diagram, or a reference architecture for AWS/Azure/GCP/IBM/Kubernetes/Terraform/Vault/Consul/Nomad. Also covers requests like "diagram this architecture", "draw our infra", or "make this look like a Lucidchart diagram".
---

# Cloud / infra architecture diagrams

You generate real, rendered PNG/SVG architecture diagrams by writing and running a short
Python script against the `diagrams` library (mingrammer/diagrams — used here purely for
its graph layout engine: `Diagram`, `Cluster`, `Edge`, Graphviz rendering). Every node icon
comes from this plugin's own bundled, official icon library in `assets/icons/` — never
from `diagrams`' own bundled icon images, and never invented or guessed.

## Step 1 — Gather requirements, and ask before assuming on anything high-impact

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
- **Diagram framing**: most requests are network/deployment topology (clusters = VPC /
  subnet / AZ / namespace, per `style-guide.md`'s boundary conventions). Some are better
  framed as a **layered/columnar pipeline** instead — e.g. a data or ML pipeline described
  stage-by-stage ("ingest → process → store → serve") reads more clearly as clusters
  representing pipeline stages laid out left-to-right than as a network diagram with no
  real network boundaries to show. Pick whichever framing matches how the user actually
  described the system; don't force a VPC/subnet frame onto something that isn't about
  network topology.

### Ask, don't assume, on anything that would materially change the diagram

Before writing any script, check the request against this list. If something on it is
**both unspecified and would meaningfully change the diagram's structure**, ask about it
with the question tool (batch the questions that actually apply into one call, don't ask
one at a time) — don't silently pick a default and let the user discover it's wrong only
after seeing the render. This list exists because every item on it caused rework in
earlier sessions building this plugin:

1. **Cloud provider / platform.** Don't default to AWS (or any provider) when the request
   doesn't name one and it isn't clear from surrounding conversation — "draw a Vault HA
   architecture" doesn't imply AWS. If the conversation has an established provider context
   from recent turns, that counts as specified; a cold request does not.
2. **Scale / node count**, for anything HA, clustered, or replicated. "3 nodes" and "5
   nodes" are genuinely different diagrams (different quorum math, different layout), not
   a detail to fill in silently.
3. **Detail level**: a high-level overview (major components, one edge per relationship) or
   a detailed/low-level view (internal subsystems called out as their own nodes — e.g. a
   server's storage/consensus layer, specific ports/protocols on edge labels)? If the user
   says "detailed" or "low-level" (or, symmetrically, "simple"/"high-level"), that answers
   this — but if the request is bare ("draw a Vault architecture"), ask.
4. **Key technology forks** where the answer changes which nodes appear at all — e.g. for
   Vault: Integrated Storage (Raft) vs. a Consul storage backend; for Kubernetes: which
   ingress controller or service mesh, if any; for auto-unseal: which cloud KMS, or none.
   Don't silently pick HashiCorp's current default and hope it's what the user meant.
5. **Scope**: does the user want just the core architecture, or should adjacent concerns
   (auto-unseal, audit logging, monitoring, CI/CD) be included? For a bare request like
   "draw Vault HA," ask whether to include these rather than guessing a bundle of extras
   the user didn't ask for (or leaving out ones they wanted).

**Skip the questions and go straight to drawing when the request is already fully
specified** — e.g. "draw a 3-tier AWS web app with an ALB, EC2, and RDS" names the
provider, the components, and implies a standard level of detail; asking anyway would be
interrogating the user over something they already answered. The bar is: would a
reasonable default here have a real chance of being wrong in a way that costs the user a
regeneration cycle? If yes, ask; if the request already pins it down, don't.

Also ask (this was already true, still applies) when a request is ambiguous in other ways
— spans multiple clouds with no clear boundary, or names a component with no obvious icon
match.

## Step 2 — Check the environment (once per session)

Run this once per session, skip on repeat invocations within the same session:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_env.py
```

If it reports `ENVIRONMENT NOT READY`, relay its exact remediation commands to the user
and stop — don't attempt to render without a working `diagrams` + Graphviz install.

## Step 3 — Map components to icon assets (static lookup only, no searching)

For each component, read the matching catalog(s) under `references/`:
`aws.md`, `azure.md`, `gcp.md`, `ibm.md`, `kubernetes.md`, `devops.md`, `hashicorp.md`,
`ai-ml.md` for **node icons**, and `aws-boundaries.md`/`kubernetes-boundaries.md` for the
small badge icons used in **cluster/boundary labels** (VPC, Subnet, Region, Namespace —
see `style-guide.md`'s "Boundary badge icons" section; these are a different asset set
from node icons and are never used as a node's own icon). This is a pure file read — do
not grep the installed `diagrams` package, do not fetch anything from the internet, and do
not guess a path that "looks right."

Notes baked into the catalogs, worth remembering:
- A component can be cloud-native (e.g. an LLM served via AWS Bedrock → check `aws.md`)
  or third-party app-layer (e.g. LangChain → check `ai-ml.md`). Check the most specific
  catalog first, then the provider catalog, then `ai-ml.md`/`devops.md` for cross-cutting
  tools.
- `ibm.md` covers IBM Cloud platform services, watsonx/AI, and general security concepts
  (IAM, Secrets Manager, Cloud Pak for Security) — it does **not** cover the standalone IBM
  Security product line (QRadar, Guardium, Verify/Verify Access); no public icon stencil
  kit exists for these as of this writing, so they use the generic-icon fallback.
- `hashicorp.md` and `ai-ml.md` both explicitly list a few components with **no available
  icon** (HashiCorp Boundary; OpenAI, Pinecone, Weaviate, Cohere, Chroma, LlamaIndex for
  AI/ML) — for these, use the generic-icon fallback described in `style-guide.md`
  ("Missing-icon fallback" — a visible generic shape, never `diagrams.generic.blank.Blank`
  and never an unofficial/unlicensed logo).
- If a component genuinely isn't in any catalog, use that same generic-icon fallback and
  tell the user which node(s) got a generic icon instead of a branded one, rather than
  inventing a path.

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
  still fails, fall back to a generic shape icon per `style-guide.md` and mention it to
  the user.
- Cap retries at 3 total attempts before reporting the specific failure to the user.
- **Look at the rendered image before returning it**, not just at whether the script exited
  0. A clean exit doesn't mean a clean diagram — Graphviz layout bugs (edges crossing,
  labels floating away from their edges, peer nodes rendered as a hierarchy, a legend
  overlapping real content) only show up visually. Check specifically for: does the
  layout imply a relationship that isn't true (see `style-guide.md`'s `constraint="false"`
  section), do any labels look detached from their edge, does anything overlap.
- **Specifically check that every node has a visible icon, not just floating label text.**
  Graphviz silently drops a broken image reference and renders only the node's label — no
  exception, no warning, exit code 0. This is a real, confirmed failure mode (e.g. a stale
  absolute path in `${ICONS}` after the plugin directory moves) and is easy to miss on a
  quick glance, especially across a multi-diagram batch — a text label alone, with no icon
  above it, means that node's image path is broken and needs fixing, not a re-run.

## Step 7 — Return the result

Confirm the output file path and give a one-line description of what was drawn, including
a note on any components that fell back to a generic icon for lack of an available brand
icon.
