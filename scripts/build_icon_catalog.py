#!/usr/bin/env python3
"""Authoring-time only. Not a runtime dependency of the plugin.

Ingests officially-downloaded icon packs (AWS, Azure, GCP, Kubernetes,
HashiCorp, DevOps tools, AI/ML vendors) from a staging directory, normalizes
every icon to PNG, writes them into assets/icons/<provider>/, and generates
the static markdown reference catalogs under skills/cloud-diagram/references/.

Usage:
    .venv-build/bin/python3 scripts/build_icon_catalog.py --staging /path/to/icon-staging
"""
import argparse
import re
import shutil
from pathlib import Path

import cairosvg
from PIL import Image

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PLUGIN_ROOT / "assets" / "icons"
REFERENCES_DIR = PLUGIN_ROOT / "skills" / "cloud-diagram" / "references"
ICON_PX = 128
BADGE_PX = 28  # small badge size for boundary/cluster-label icons (see style-guide.md)


def slugify(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return re.sub(r"-+", "-", name)


def write_png_from_svg(svg_path: Path, out_path: Path, size: int = ICON_PX):
    cairosvg.svg2png(url=str(svg_path), write_to=str(out_path), output_width=size, output_height=size)


def copy_png(src: Path, out_path: Path):
    shutil.copyfile(src, out_path)


def resize_png(src: Path, out_path: Path, size: int = BADGE_PX):
    """Graphviz HTML-like labels ignore <img width=/height=> attributes, so badge
    icons used in Cluster label badges (see style-guide.md) must be pre-sized here
    rather than scaled at render time."""
    with Image.open(src) as im:
        im = im.convert("RGBA")
        im.thumbnail((size, size), Image.LANCZOS)
        im.save(out_path)


def write_catalog(name: str, header_note: str, rows: list[tuple[str, str, str]]):
    """rows: (display_name, relative_asset_path, notes)"""
    out = REFERENCES_DIR / f"{name}.md"
    lines = [f"# {name.upper()} icon catalog", "", header_note, "", "| Name | Asset path | Notes |", "|---|---|---|"]
    for display, path, notes in sorted(rows, key=lambda r: r[0].lower()):
        lines.append(f"| {display} | `{path}` | {notes} |")
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out} ({len(rows)} rows)")


def build_aws(staging: Path):
    out_dir = ASSETS_DIR / "aws"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    base = next((staging / "aws").glob("Architecture-Service-Icons_*"), None)
    if base is None:
        print("WARNING: AWS Architecture-Service-Icons folder not found, skipping AWS")
        return
    for png in sorted(base.glob("Arch_*/48/Arch_*_48.png")):
        category = png.parts[-3].replace("Arch_", "").replace("-", " ")
        raw_name = png.stem.replace("Arch_", "").rsplit("_48", 1)[0]
        display = raw_name.replace("-", " ")
        slug = slugify(raw_name)
        if slug in seen:
            continue
        seen.add(slug)
        out_path = out_dir / f"{slug}.png"
        copy_png(png, out_path)
        rows.append((display, f"assets/icons/aws/{slug}.png", category))
    write_catalog(
        "aws",
        "Source: official AWS Architecture Icons (aws.amazon.com/architecture/icons), "
        "Architecture-Service-Icons set, 48px PNG. Diagram/doc use permitted; do not "
        "modify the icons or use them to represent a non-AWS product (see ../../../NOTICE.md).",
        rows,
    )


def build_azure(staging: Path):
    out_dir = ASSETS_DIR / "azure"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    base = staging / "azure" / "Azure_Public_Service_Icons" / "Icons"
    if not base.exists():
        print("WARNING: Azure Icons folder not found, skipping Azure")
        return
    for svg in sorted(base.glob("*/*.svg")):
        category = svg.parent.name
        m = re.match(r"^[0-9]+-icon-service-(.+)$", svg.stem)
        raw_name = m.group(1) if m else svg.stem
        display = raw_name.replace("-", " ")
        slug = slugify(raw_name)
        if slug in seen:
            continue
        seen.add(slug)
        out_path = out_dir / f"{slug}.png"
        write_png_from_svg(svg, out_path)
        rows.append((display, f"assets/icons/azure/{slug}.png", category))
    write_catalog(
        "azure",
        "Source: official Azure Architecture Icons (learn.microsoft.com/azure/architecture/icons), "
        "SVGs pre-converted to 128px PNG. Diagram/training/doc use permitted; do not modify "
        "icons or use in marketing (see ../../../NOTICE.md).",
        rows,
    )


def build_gcp(staging: Path):
    out_dir = ASSETS_DIR / "gcp"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()

    # Newer flagship products first (core-products pack) so they win on slug collisions.
    core_base = staging / "gcp-core" / "Unique Icons"
    if core_base.exists():
        for png in sorted(core_base.glob("*/PNG/*.png")):
            raw_name = png.parent.parent.name
            display = raw_name
            slug = slugify(raw_name)
            if slug in seen:
                continue
            seen.add(slug)
            copy_png(png, out_dir / f"{slug}.png")
            rows.append((display, f"assets/icons/gcp/{slug}.png", "core product (current)"))

    legacy_base = staging / "gcp-legacy"
    if legacy_base.exists():
        for png in sorted(legacy_base.glob("*/*.png")):
            raw_name = png.parent.name
            display = raw_name.replace("_", " ")
            slug = slugify(raw_name)
            if slug in seen:
                continue
            seen.add(slug)
            copy_png(png, out_dir / f"{slug}.png")
            rows.append((display, f"assets/icons/gcp/{slug}.png", "legacy per-service set"))

    if not rows:
        print("WARNING: no GCP icons found, skipping GCP")
        return
    write_catalog(
        "gcp",
        "Source: official Google Cloud icon packs (cloud.google.com/icons) — 'core products' "
        "set (current) merged with the broader 'legacy' per-service set for coverage. Free use "
        "to accurately reference Google Cloud technology (see ../../../NOTICE.md).",
        rows,
    )


def build_kubernetes(staging: Path):
    out_dir = ASSETS_DIR / "kubernetes"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    seen = set()
    base = staging / "k8s-icons" / "png"
    if not base.exists():
        print("WARNING: k8s-icons/png not found, skipping Kubernetes")
        return
    for group in ["resources", "control_plane_components", "infrastructure_components"]:
        unlabeled = base / group / "unlabeled"
        if not unlabeled.exists():
            continue
        for png in sorted(unlabeled.glob("*-128.png")):
            raw_name = png.stem.rsplit("-128", 1)[0]
            display = raw_name.replace("-", " ")
            slug = slugify(raw_name)
            if slug in seen:
                continue
            seen.add(slug)
            copy_png(png, out_dir / f"{slug}.png")
            rows.append((display, f"assets/icons/kubernetes/{slug}.png", group.replace("_", " ")))
    write_catalog(
        "kubernetes",
        "Source: official Kubernetes icon set (github.com/kubernetes/community/tree/master/icons), "
        "unlabeled 128px color PNGs. CNCF trademark usage guidelines apply.",
        rows,
    )


def build_svg_set(staging_folder: Path, out_dir: Path, name: str, header_note: str, extra_rows: list[tuple[str, str, str]] = None):
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = list(extra_rows or [])
    if staging_folder.exists():
        for svg in sorted(staging_folder.glob("*.svg")):
            slug = slugify(svg.stem)
            out_path = out_dir / f"{slug}.png"
            write_png_from_svg(svg, out_path)
            rows.append((svg.stem, f"assets/icons/{out_dir.name}/{slug}.png", ""))
    write_catalog(name, header_note, rows)


def build_hashicorp(staging: Path):
    build_svg_set(
        staging / "hashicorp-svg",
        ASSETS_DIR / "hashicorp",
        "hashicorp",
        "Source: Simple Icons (simpleicons.org), CC0 1.0. Covers Terraform, Vault, Consul, "
        "Nomad, Packer, Vagrant, and the HashiCorp company mark. **Boundary has no CC0 icon "
        "available** — use a plain labeled box (see style-guide.md fallback convention) rather "
        "than an unofficial logo. CC0 covers the artwork only, not the HashiCorp trademarks — "
        "using these to label HashiCorp's own products in an architecture diagram is standard "
        "nominative use (see ../../../NOTICE.md).",
        extra_rows=[("Boundary (no icon available)", "", "fall back to a plain labeled box")],
    )


def build_devops(staging: Path):
    build_svg_set(
        staging / "devops-svg",
        ASSETS_DIR / "devops",
        "devops",
        "Source: Simple Icons (simpleicons.org), CC0 1.0. CI/CD, source control, "
        "observability, and IaC tooling logos for pipeline/DevOps diagrams.",
    )


def build_ai_ml(staging: Path):
    build_svg_set(
        staging / "ai-ml-svg",
        ASSETS_DIR / "ai-ml",
        "ai-ml",
        "Source: Simple Icons (simpleicons.org), CC0 1.0, for the third-party AI/ML app-layer "
        "stack not covered by any cloud provider's own icon pack (use aws.md/azure.md/gcp.md "
        "for Bedrock/SageMaker/Azure OpenAI/Vertex AI etc.). **No CC0 icon exists for OpenAI, "
        "Pinecone, Weaviate, Cohere, Chroma, or LlamaIndex** — fall back to a plain labeled box "
        "for these rather than an unlicensed logo (see style-guide.md).",
        extra_rows=[
            (v, "", "no CC0 icon available — fall back to a plain labeled box")
            for v in ["OpenAI", "Pinecone", "Weaviate", "Cohere", "Chroma", "LlamaIndex"]
        ],
    )


AWS_BOUNDARY_ICONS = {
    "aws-cloud": "AWS-Cloud_32.png",
    "vpc": "Virtual-private-cloud-VPC_32.png",
    "public-subnet": "Public-subnet_32.png",
    "private-subnet": "Private-subnet_32.png",
    "region": "Region_32.png",
    "auto-scaling-group": "Auto-Scaling-group_32.png",
    "corporate-data-center": "Corporate-data-center_32.png",
}


def build_aws_boundaries(staging: Path):
    """Small badge icons for AWS's own boundary/group-label convention (a tiny
    icon next to "VPC" / "Public Subnet" / "Availability Zone" etc. cluster
    labels), sourced from AWS's official Architecture-Group-Icons set — distinct
    from the per-service icons in build_aws(). See style-guide.md for how these
    are used in Graphviz HTML-like Cluster labels."""
    out_dir = ASSETS_DIR / "aws" / "boundaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = next((staging / "aws").glob("Architecture-Group-Icons_*"), None)
    if base is None:
        print("WARNING: AWS Architecture-Group-Icons folder not found, skipping AWS boundary badges")
        return
    rows = []
    for slug, filename in AWS_BOUNDARY_ICONS.items():
        src = base / filename
        if not src.exists():
            print(f"WARNING: {filename} not found in Architecture-Group-Icons, skipping")
            continue
        out_path = out_dir / f"{slug}.png"
        resize_png(src, out_path)
        rows.append((slug.replace("-", " "), f"assets/icons/aws/boundaries/{slug}.png", "cluster-label badge"))
    write_catalog(
        "aws-boundaries",
        f"Small ({BADGE_PX}px) badge icons for AWS's boundary/group-label convention — used inside "
        "Cluster labels (VPC, Public/Private Subnet, Region, Auto Scaling group, Corporate Data "
        "Center), not as node icons. See style-guide.md \"Boundary badge icons\" for the HTML-label "
        "recipe. Source: same AWS Architecture Icons pack as aws.md, Architecture-Group-Icons set.",
        rows,
    )


def build_kubernetes_boundaries(staging: Path):
    """Small badge icon for a Kubernetes Namespace cluster-label badge, matching
    the same convention as build_aws_boundaries()."""
    out_dir = ASSETS_DIR / "kubernetes" / "boundaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    src = staging / "k8s-icons" / "png" / "resources" / "unlabeled" / "ns-128.png"
    if not src.exists():
        print("WARNING: k8s namespace icon not found, skipping Kubernetes boundary badges")
        return
    out_path = out_dir / "namespace.png"
    resize_png(src, out_path)
    write_catalog(
        "kubernetes-boundaries",
        f"Small ({BADGE_PX}px) badge icon for a Kubernetes Namespace cluster-label badge, matching "
        "the AWS boundary-badge convention (see aws-boundaries.md and style-guide.md).",
        [("namespace", "assets/icons/kubernetes/boundaries/namespace.png", "cluster-label badge")],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", required=True, type=Path, help="Directory containing extracted icon packs")
    args = parser.parse_args()

    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    build_aws(args.staging)
    build_azure(args.staging)
    build_gcp(args.staging)
    build_kubernetes(args.staging)
    build_hashicorp(args.staging)
    build_devops(args.staging)
    build_ai_ml(args.staging)
    build_aws_boundaries(args.staging)
    build_kubernetes_boundaries(args.staging)


if __name__ == "__main__":
    main()
