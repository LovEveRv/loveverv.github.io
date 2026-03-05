#!/usr/bin/env python3
"""Build static pages from Markdown + frontmatter using Jinja2 templates."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape


FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
MARKDOWN_EXTENSIONS = [
    "markdown.extensions.extra",
    "markdown.extensions.codehilite",
    "markdown.extensions.toc",
]


def text_preview(md_text: str, max_len: int = 160) -> str:
    # Build a compact plain-text snippet for blog listing cards.
    plain = re.sub(r"\s+", " ", md_text).strip()
    if len(plain) <= max_len:
        return plain
    return plain[:max_len].rstrip() + "..."


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    meta_text = match.group(1)
    body = raw[match.end():]
    meta = yaml.safe_load(meta_text) or {}
    if not isinstance(meta, dict):
        raise ValueError("Frontmatter must be a key-value mapping")
    return meta, body


def choose_output_path(meta: dict, source_md: Path, src_root: Path, pages_root: Path) -> Path:
    rel = source_md.relative_to(src_root)
    if rel.parts and rel.parts[0] == "blogs":
        return pages_root / "blog" / f"{meta['id']}.html"
    return pages_root / rel.with_suffix(".html")


def markdown_to_html(md_text: str) -> tuple[str, str]:
    md = markdown.Markdown(extensions=MARKDOWN_EXTENSIONS)
    html = md.convert(md_text)
    return html, md.toc


def build(src_root: Path, pages_root: Path, templates_root: Path) -> None:
    env = Environment(
        loader=FileSystemLoader(str(templates_root)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("blog-page.html")

    markdown_files = sorted(
        p for p in src_root.rglob("*.md") if templates_root not in p.parents
    )
    posts_for_home = []

    for md_file in markdown_files:
        raw = md_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)

        html_text, toc_html = markdown_to_html(body)

        blog = dict(meta)
        blog["text"] = html_text
        blog["toc"] = toc_html

        context = {
            "title": blog["title"],
            "stylesheets": [
                "navbar&footer.css",
                "blog-page.css",
                "github-markdown.css",
                "github-codehilite.css",
            ],
            "scripts": [
                "blog-page.js"
            ],
            "blog": blog,
        }

        output_path = choose_output_path(meta, md_file, src_root, pages_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template.render(**context), encoding="utf-8")

        output_rel = output_path.relative_to(pages_root).as_posix()
        blog_id = blog["id"]
        posts_for_home.append(
            {
                "id": blog_id,
                "title": blog["title"],
                "publish_date": blog["publish_date"],
                "coverimg": blog.get("coverimg", ""),
                "preview": blog.get("preview", text_preview(body, 120)),
                "url": "/" + output_rel,
            }
        )

    posts_for_home.sort(
        key=lambda x: int(x["id"]),
        reverse=True,
    )

    home_context = {
        "title": "Imagasaikou - Blog",
        "stylesheets": ["navbar&footer.css", "blog-home.css"],
        "scripts": [],
        "blogs": posts_for_home,
    }

    home_template = env.get_template("blog-home.html")
    home_html = home_template.render(**home_context)
    # Temporarily use blog home as index page
    (pages_root / "index.html").write_text(home_html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build static pages for GitHub Pages.")
    parser.add_argument("--src", type=Path, default=Path("src"), help="Source directory")
    parser.add_argument("--pages", type=Path, default=Path("pages"), help="Output pages directory")
    parser.add_argument(
        "--templates",
        type=Path,
        default=Path("src/templates"),
        help="Template directory",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build(args.src.resolve(), args.pages.resolve(), args.templates.resolve())


if __name__ == "__main__":
    main()
