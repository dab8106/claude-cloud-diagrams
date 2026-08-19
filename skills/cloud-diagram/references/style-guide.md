# Style guide: making output look Lucidchart-quality, not default-Graphviz-plain

Every generated diagram script should follow these conventions. They are copy-pasteable
`diagrams` DSL settings, not abstract advice — reuse them verbatim unless the user asks
for something different.

## `graph_attr` defaults

```python
graph_attr = {
    "fontname": "Helvetica",
    "fontsize": "13",
    "bgcolor": "white",
    "splines": "spline",   # organic curved edges read more "Lucid" than "ortho" (boxy/technical)
    "pad": "0.4",
    "nodesep": "0.6",
    "ranksep": "0.9",
}
node_attr = {"fontname": "Helvetica", "fontsize": "11"}
edge_attr = {"fontname": "Helvetica", "fontsize": "10"}
```

Use `"splines": "ortho"` instead only when the user explicitly wants a more rigid/technical
network-diagram look (e.g. network topology diagrams with strict L-shaped routing).

### `direction` (rankdir) choice
- **`LR`** (left-to-right) — pipelines, data flow, CI/CD, request/response chains.
- **`TB`** (top-to-bottom, the `diagrams` default) — layered/tiered architectures (e.g.
  presentation → app → data tier), org-chart-like structures, Kubernetes resource
  hierarchies.

## Clusters (logical grouping)

Use `Cluster` for every logical boundary the user describes: VPC, subnet, region,
availability zone, Kubernetes namespace, environment (prod/staging), or a vendor "stack"
(e.g. "HashiCorp Stack" grouping Vault/Consul/Nomad). Give each cluster a light tint and
rounded corners so it reads as a labeled container, not a debug bounding box:

```python
with Cluster("AWS VPC", graph_attr={"bgcolor": "#FFF6E8", "style": "rounded", "fontsize": "12"}):
    ...
with Cluster("HashiCorp Stack", graph_attr={"bgcolor": "#F2EEFB", "style": "rounded", "fontsize": "12"}):
    ...
```

Nest clusters when the user describes nested scope (e.g. a subnet inside a VPC inside a
region) — `diagrams` supports nested `Cluster` blocks directly.

## Edges: color-code by connection type, don't leave everything default grey

```python
Edge(color="#232F3E", style="solid",  label="data flow")
Edge(color="#0078D4", style="solid",  label="control plane")
Edge(color="#000000", style="dashed", label="secrets")       # any credential/secret retrieval
Edge(color="#7B42BC", style="solid",  label="provisions")     # IaC / Terraform-applies-to
Edge(color="#DC477D", style="dashed", label="service mesh")   # Consul/Istio-style mesh links
```

Always label edges when the connection type isn't obvious from the node names alone.
Bidirectional/sync calls: plain solid line. Async/event-driven: dashed line. Secrets or
credential retrieval: always dashed black regardless of provider, so it reads consistently
as "sensitive" across every diagram this plugin produces.

### When several edges converge near the same node or region

Multiple edges with similar labels crossing near each other (e.g. several "provisions"
arrows plus several "secrets"/"mesh" arrows all landing in the same corner) is the single
biggest cause of an unreadable diagram — worse than any icon or color choice. Before
shipping a diagram, check for this and fix it:

- Switch that diagram's `splines` to `"ortho"` instead of `"spline"` — right-angle routing
  keeps parallel edges visually separated instead of curving through the same space.
  `"spline"` is the general default (see `graph_attr` above), but readability wins over the
  organic look whenever a diagram has 4+ edges converging on a shared area.
- Increase `ranksep`/`nodesep` (e.g. to `"1.2"`/`"0.9"`) to give converging edges more room.
- If a sequence of steps is being shown (e.g. "app asks Vault for a secret, then registers
  with Consul"), number the labels — `"1. requests dynamic secret"`, `"2. registers with
  mesh"` — so the reader can trace order even where lines pass close together.
- Fewer nodes means fewer converging edges — see "Don't over-populate with near-identical
  nodes" below before you reach for layout tweaks.

## Per-provider palettes

| Provider | Primary | Secondary |
|---|---|---|
| AWS | `#FF9900` (orange) | `#232F3E` (squid ink navy) |
| Azure | `#0078D4` (blue) | — |
| GCP | multicolor per Google's own palette (blue `#4285F4`, red `#EA4335`, yellow `#FBBC04`, green `#34A853`) | — |
| Kubernetes | `#326CE5` (k8s blue) | — |
| HashiCorp — Vault | `#000000` | `#FFEC6E` accent |
| HashiCorp — Terraform | `#7B42BC` | — |
| HashiCorp — Consul | `#DC477D` | — |
| HashiCorp — Nomad | `#00CA8E` | — |
| HashiCorp — Boundary | `#1563FF` | — |

Apply these to cluster tints (light desaturated version of the primary), edge colors when
the edge represents that provider's control/data plane, and any title/legend accents. Icon
colors themselves come from the bundled brand-accurate PNGs — don't recolor the icons.

## Node sizing consistency

Every icon in `assets/icons/` was normalized to a consistent size (128×128, or 48–64px for
the AWS set) during the authoring-time build, specifically so mixed-provider diagrams don't
have one oversized wordmark next to small square glyphs — this was a real problem with the
`diagrams` library's own bundled Terraform icon, which is why this plugin ships its own
curated icon set instead of relying on that package's images. Don't override `width`/
`height` per node; the shipped PNGs are already visually consistent.

## Missing-icon fallback

If a component has no entry in the relevant `references/*.md` catalog (and isn't found
after checking the sibling domain catalogs — e.g. an AI vendor might be cloud-native and
listed in `aws.md`/`azure.md`/`gcp.md` rather than `ai-ml.md`), don't invent or guess a
brand icon path — but **never fall back to `diagrams.generic.blank.Blank`**. `Blank` is a
layout spacer with no visible glyph at all; a node the reader can't identify at a glance is
exactly the "icon is missing" failure this plugin exists to avoid. Instead pick the closest
matching **generic shape** icon so the node is still visually legible, just unbranded:

```python
from diagrams.onprem.compute import Server      # unspecified app/compute instance
from diagrams.generic.database import SQL        # unspecified database
from diagrams.generic.network import Firewall, Router, Switch, VPN  # unspecified network gear
from diagrams.generic.storage import Storage      # unspecified storage
```

Tell the user in your response which components got a generic icon instead of a branded
one, and what the closest generic match was, so they know why those specific nodes look
different from the rest — and can tell you the real product if they want it swapped in.

## Don't over-populate with near-identical nodes

Two or three copies of the literal same unbranded node (e.g. "App Instance" ×2 with no
distinguishing detail) adds visual noise without adding information — it just multiplies
the number of edges converging on the same targets and makes the diagram harder to trace.
Draw **one** representative node for a tier/role unless the count itself is something the
user specifically asked about (e.g. "show 3 EC2 instances behind the load balancer") or is
architecturally meaningful (e.g. a multi-AZ pair). When in doubt, prefer fewer nodes with
clearer edges over more nodes that just repeat the same relationship.

## Title, subtitle, legend

```python
graph_attr["label"] = "Vault-secured AWS Application\n"  # trailing \n adds breathing room
graph_attr["labelloc"] = "t"
graph_attr["fontsize"] = "20"
```

For diagrams with more than ~3 edge colors in use, add a small legend cluster in a corner
(a `Cluster("Legend", ...)` containing a few unconnected labeled nodes) rather than relying
on the reader to infer what each edge color means — only do this when it earns its space
(4+ distinct edge types); skip it for simple 2-3 node diagrams.
