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
    "pad": "0.3",
    "nodesep": "0.5",
    "ranksep": "0.6",
}
node_attr = {"fontname": "Helvetica", "fontsize": "11"}
edge_attr = {"fontname": "Helvetica", "fontsize": "10"}
```

These are deliberately tight — an earlier version of this guide used `ranksep: "0.9"` /
`nodesep: "0.6"`, which reads fine for a single isolated diagram but compounds badly across
a long rank chain (e.g. client → LB → cluster → downstream service is 4 ranks deep) into
visibly excessive dead space, confirmed by user feedback on a real render. Only increase
these above the defaults when edges are still crossing after applying "Reduce the edge
count first" below — spacing is the second lever, not the first.

Use `"splines": "ortho"` instead only when the user explicitly wants a more rigid/technical
network-diagram look (e.g. network topology diagrams with strict L-shaped routing) — and
see the "When several edges converge" section below before reaching for it as a clutter
fix; it has real, confirmed label-placement problems with multiple labeled edges.

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

### Boundary badge icons (AWS only)

Official AWS reference diagrams put a small icon badge next to boundary labels — a padlock
glyph for "Public Subnet"/"Private Subnet", a cloud glyph for "VPC", etc. — not just plain
text. This plugin ships pre-sized 28px badges for exactly this in
`assets/icons/aws/boundaries/` (see `references/aws-boundaries.md`) and a matching
`assets/icons/kubernetes/boundaries/namespace.png` for Kubernetes namespaces. Use them via
a Graphviz HTML-like label (confirmed working with this library/Graphviz version):

```python
vpc_label = (
    '<<table border="0" cellborder="0" cellpadding="2">'
    '<tr><td><img src="{icon}"/></td><td><font point-size="12">VPC</font></td></tr>'
    '</table>>'
).format(icon=f"{ICONS}/aws/boundaries/vpc.png")

with Cluster(vpc_label, graph_attr={"bgcolor": "#FFF6E8", "style": "rounded"}):
    ...
```

Notes:
- The `<img>` tag's `width`/`height` attributes are **silently ignored** by Graphviz's
  HTML-label renderer — always point at one of the pre-sized 28px badge files, never the
  full-size 128px node icons, or the badge will render oversized.
- Only use this for **AWS** boundaries (VPC, Public/Private Subnet, Region, Auto Scaling
  group, Corporate Data Center) and **Kubernetes** namespaces — Azure/GCP reference
  architectures reviewed for this plugin consistently use plain text boundary labels with
  no icon badge, so keep those plain to match convention.
- This is purely for cluster/boundary titles, never for node icons — nodes always use the
  plain `Custom(name, icon_path)` form from the rest of this guide.

## Sibling clusters don't reliably keep declared left-to-right order

When several same-level peer clusters (e.g. 3+ Availability Zones each with their own
node(s)) are connected by `constraint="false"` peer edges (see below), Graphviz's
crossing-minimization can freely reorder the *clusters themselves* — tested repeatedly for
this plugin, and neither declaration order nor invisible constraint="false" ordering edges
between the clusters reliably held the order. The result: zones render out of sequence
(e.g. "AZ 2, AZ 3, AZ 1") and, worse, one cluster can drift away from the others with a
large empty gap, dragging its edges into long diagonal sprawls across unrelated parts of
the diagram.

**If several peer nodes must hold a specific left-to-right order, don't put each one in
its own sibling `Cluster` — use a flat row of plain nodes instead, with the grouping
information (AZ, shard, region, whatever) folded into each node's caption.** Plain nodes
in one rank hold declared order far more reliably than sibling cluster subgraphs do.
Invisible `constraint="false"` ordering edges between the nodes (not clusters) are a
reasonable extra nudge, but don't assume they guarantee exact order either — **always
visually check the rendered order**, and if a specific node lands somewhere unexpected
(this happened in testing — a "leader" node meant to render first ended up last), it's
still fine to ship as long as every node's role is unambiguous from its own caption; don't
burn excessive effort chasing exact positional order once the diagram is no longer
structurally misleading (that's the bar — see the hierarchy-misrepresentation issue below,
which does matter, vs. cosmetic left-right position, which usually doesn't once labeled).

If clusters must be used, group all peer nodes' *dependent* content (e.g. a shared
consensus/storage layer) into one place rather than splitting it per-cluster — short local
edges within one group beat long edges sprawling between separated sibling clusters.

## Peer relationships need `constraint="false"`, or they'll misrepresent a hierarchy

Graphviz ranks nodes by edge direction: `a >> Edge() >> b` places `b` one rank below `a`.
That's correct for genuine hierarchy (Terraform provisions infra, LB routes to a backend)
but **wrong for peer-to-peer relationships drawn as directed edges** — replication,
clustering, service mesh between equals. A 3-node Vault HA cluster with
`active >> Edge() >> standby1` and `active >> Edge() >> standby2` renders with Active
visually elevated above the two standbys, like a parent over children — that's not the
architecture; all three are peer nodes in a Raft cluster. This was caught by rendering the
diagram and looking at it, not by reasoning about the code — always do the same visual
check for any cluster/mesh/replication relationship before shipping.

Fix: add `constraint="false"` to peer-relationship edges so they're drawn but don't affect
ranking, and add the missing edge(s) to complete the peer set instead of leaving it
hub-and-spoke only:

```python
active >> Edge(color="#666666", style="dashed", label="Raft replication", constraint="false") >> standby1
active >> Edge(color="#666666", style="dashed", label="Raft replication", constraint="false") >> standby2
standby1 >> Edge(color="#666666", style="dashed", constraint="false") >> standby2
```

Applies to: HA cluster nodes, Raft/Consul replication, Kubernetes multi-master control
planes, multi-region active-active setups — anywhere the nodes are equals, not a flow.

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

### Inline lock/key glyphs on secure edges

Official reference diagrams (AWS, HashiCorp) commonly prefix an encrypted or
credential-bearing edge's label with a small lock or key glyph rather than relying on the
word "secure" alone. Use the Unicode glyphs directly in the edge label string — confirmed
rendering correctly (in color) via Graphviz/Pango on macOS:

```python
Edge(color="#000000", style="dashed", label="\U0001F512 HTTPS")        # 🔒 encrypted transport
Edge(color="#000000", style="dashed", label="\U0001F511 dynamic secret")  # 🔑 credential/secret retrieval
```

**Caveat**: this depends on the local Graphviz build having color-emoji font fallback
(confirmed working here via macOS's Apple Color Emoji through Pango/Cairo). If a rendered
diagram shows an empty box or missing-glyph placeholder instead of the lock/key, drop the
emoji and fall back to plain text (`"[encrypted] HTTPS"`) for that render.

### Cross-cutting services: don't wire every security/observability service individually

Services that apply broadly rather than to one specific data-flow edge — logging,
monitoring, secrets management, threat detection, cost/compliance tooling — shouldn't each
get their own edge back to every node that uses them; that's how the messiest real-world
reference diagrams end up with dozens of crossing lines. Instead, group them into an
unconnected (or lightly connected) horizontal strip, usually along the bottom:

```python
with Cluster("Security & Observability", graph_attr={"bgcolor": "#F5F5F5", "style": "rounded,dashed"}):
    kms = Custom("AWS KMS", f"{ICONS}/aws/aws-key-management-service.png")
    guardduty = Custom("Amazon GuardDuty", f"{ICONS}/aws/amazon-guardduty.png")
    cloudtrail = Custom("AWS CloudTrail", f"{ICONS}/aws/aws-cloudtrail.png")
    # ...no edges from these into the main flow unless the user specifically asks
    # to show one, e.g. "show CloudTrail auditing the API Gateway calls"
```

Only draw an explicit edge from a cross-cutting service to a specific node when the user's
request calls it out by name.

### When several edges converge near the same node or region

Multiple edges with similar labels crossing near each other (e.g. several "provisions"
arrows plus several "secrets"/"mesh" arrows all landing in the same corner) is the single
biggest cause of an unreadable diagram — worse than any icon or color choice. Before
shipping a diagram, check for this and fix it — **in this order**:

1. **Reduce the edge count first, before touching layout settings.** This is the fix that
   actually works reliably. Two concrete moves:
   - One representative edge per cluster instead of one edge per node inside it. If
     Terraform provisions five things spread across two clusters, draw two "provisions"
     edges (one into each cluster, landing on any one representative node inside it) —
     not five edges fanning out to every individual leaf node. The reader already
     understands "provisions" applies to the whole cluster from the label + the cluster
     boundary; five near-duplicate arrows add clutter without adding information.
   - Fewer nodes means fewer converging edges — see "Don't over-populate with
     near-identical nodes" below. A single "App Pods (×2)" node with one set of outgoing
     edges reads more clearly than two identical pod nodes each repeating the same three
     edges.
2. **Increase `ranksep`/`nodesep`** (e.g. to `"1.0"`/`"0.7"`) to give the remaining edges
   more room, *after* reducing count — spacing alone does not fix a genuinely overcrowded
   graph.
3. **Be cautious with `"splines": "ortho"` as a clutter fix — it is not reliably safe with
   labeled edges.** Graphviz emits `"Orthogonal edges do not currently handle edge
   labels"` for exactly this combination, and in testing for this plugin, `ortho` +
   multiple labeled edges + an HTML-labeled `Cluster` (the boundary-badge technique above)
   produced genuinely broken output — floating labels detached from their edges, and in
   one case Graphviz mis-computed the canvas bounding box and clipped the title/top node
   entirely. **`"spline"` (the default) does not have this problem** and correctly
   anchors labels to their edges even with several labeled edges present — prefer it, and
   treat `ortho` as an experimental option to visually verify on a case-by-case basis, not
   a dependable fix. Always visually inspect the rendered PNG after any layout change
   before calling a diagram done — an edge-count reduction is something you can reason
   about in the script; a layout engine's routing choice is not.
4. If a sequence of steps is being shown (e.g. "app asks Vault for a secret, then registers
   with Consul"), number the labels. For a short sequence (≤10 steps), circled Unicode
   digits read as a cleaner "step badge" than plain text numbers and are confirmed to
   render fine as regular glyphs (not color emoji, so no font-fallback risk):
   `"① requests dynamic secret"` (①), `"② registers with mesh"` (②) — circled 1–10
   are U+2460–U+2469. Beyond 10 steps, fall back to plain `"1."`, `"2."`, ...

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

## Two-line captions for role/context

When a node's role isn't obvious from its service name alone (especially with multiple
instances of the same service playing different roles), add a second caption line rather
than relying on the reader to infer it from position:

```python
Custom("Amazon RDS\n(Database — Primary)", f"{ICONS}/aws/amazon-rds.png")
Custom("Amazon RDS\n(Database — Secondary)", f"{ICONS}/aws/amazon-rds.png")
Custom("AWS WAF\nWeb Application Firewall", f"{ICONS}/aws/aws-waf.png")
```

Keep the first line the exact service name from the reference catalog and the second line
short (role, tier, or a one-word expansion of an acronym) — don't repeat information
already obvious from an adjacent Cluster label (e.g. skip "(App Tier)" on a node that's
already inside a Cluster named "App Tier").

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

**Add a legend whenever a diagram uses 4 or more distinct edge colors/styles.** This isn't
optional polish — a busy multi-color diagram with no legend (a real failure mode seen in
sprawling reference architectures with many concern-colored edges and no key) is
unreadable no matter how good the icons are. For 2-3 edge types, a legend usually isn't
worth the space — the labels on the edges themselves are enough.

**Render the legend as a separate image and composite it onto the main diagram — don't put
it inside the main graph.** An earlier version of this guide recommended an in-graph
`Cluster("Legend", ...)` with unconnected placeholder-node edges; in testing, that
approach let the legend's nodes compete for rank/position with the real architecture and
visibly distorted the main layout (edges that were clean without the legend started
sprawling once it was added). Two-step recipe that avoids this entirely:

```python
from diagrams import Diagram, Node
from PIL import Image

# 1. Render the main architecture as normal, then close that `with Diagram(...)` block.

# 2. Render the legend as its own tiny, completely separate diagram:
legend_rows = [("#7B42BC", "provisions (IaC)"), ("#000000", "\U0001F511 secrets/credentials")]
trs = "".join(
    f'<tr><td bgcolor="{color}" width="28" height="4"></td>'
    f'<td align="left"><font point-size="10">{label}</font></td></tr>'
    for color, label in legend_rows
)
legend_label = (
    '<<table border="1" color="#CCCCCC" cellborder="0" cellspacing="6" cellpadding="4" bgcolor="#FAFAFA">'
    '<tr><td colspan="2" align="left"><font point-size="11"><b>Legend</b></font></td></tr>'
    f'{trs}</table>>'
)
with Diagram("legend", show=False, filename="/tmp/_legend", outformat="png",
             graph_attr={"bgcolor": "white", "margin": "0"}):
    Node(legend_label, shape="plaintext")

# 3. Autocrop both renders first -- Graphviz pads its own canvas with whitespace beyond
#    what `pad` alone accounts for, and that padding stacks with whatever margin you add
#    next, which is a real contributor to the "too much dead space" failure mode (also
#    confirmed the hard way in testing):
from PIL import ImageChops

def autocrop(img, margin=16):
    rgb = img.convert("RGB")
    bg = Image.new("RGB", rgb.size, (255, 255, 255))
    bbox = ImageChops.difference(rgb, bg).getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    return img.crop((max(0, left - margin), max(0, top - margin),
                      min(img.width, right + margin), min(img.height, bottom + margin)))

main_img = autocrop(Image.open("<main-output>.png").convert("RGBA"))
legend_img = autocrop(Image.open("/tmp/_legend.png").convert("RGBA"), margin=4)

# 4. Composite by EXTENDING the canvas on whichever side wastes the LEAST space, not by
#    pasting into a guessed-empty corner of the existing image (a corner that looks empty
#    in one layout may not be in another, and overlapping real content with the legend is
#    worse than no legend at all -- also confirmed the hard way). A tall/narrow (portrait)
#    diagram should get the legend BELOW it; a wide/short (landscape) one should get it
#    to the SIDE -- padding a portrait diagram sideways (or a landscape one downward)
#    leaves a large empty block, which is exactly the failure mode being fixed here:
margin = 20
if main_img.height >= main_img.width:
    new_size = (max(main_img.width, legend_img.width), main_img.height + legend_img.height + margin * 2)
    legend_dest = ((new_size[0] - legend_img.width) // 2, main_img.height + margin)
else:
    new_size = (main_img.width + legend_img.width + margin * 2, max(main_img.height, legend_img.height))
    legend_dest = (main_img.width + margin, margin)

canvas = Image.new("RGBA", new_size, (255, 255, 255, 255))
canvas.alpha_composite(main_img, dest=(0, 0))
canvas.alpha_composite(legend_img, dest=legend_dest)
canvas.convert("RGB").save("<main-output>.png")
```

This makes `Pillow` a real runtime dependency whenever a diagram includes a legend —
`check_env.py` verifies it alongside `diagrams`/Graphviz.

## Excessive white space in general (even without a legend)

If a rendered diagram looks sparse relative to its canvas even with no legend involved,
before adding any manual fixes check, in order: (1) is `ranksep`/`nodesep` still at the
tightened defaults above, or was it bumped up earlier in this session without a reason
that still applies; (2) is the rank chain unnecessarily long — e.g. a client/actor node
that doesn't add information could be dropped, collapsing one rank; (3) for a
Pillow-composited output (legend or otherwise), was `autocrop()` applied to every image
before compositing. Always look at the actual rendered PNG's dimensions and content
density, not just whether the script ran — this class of issue, like the peer-relationship
ranking issue above, is only visible by looking.
