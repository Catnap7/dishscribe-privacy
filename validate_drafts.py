#!/usr/bin/env python3
"""Static validation for the DishScribe privacy site and Play draft packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.external_assets: list[str] = []
        self.panels: list[str] = []
        self.buttons: list[str] = []
        self.text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value for key, value in attrs}
        if values.get("id"):
            self.ids.append(values["id"] or "")
        if values.get("href"):
            self.hrefs.append(values["href"] or "")
        if tag in {"script", "img", "iframe", "video", "audio", "source"} and values.get("src"):
            self.external_assets.append(values["src"] or "")
        if tag == "link" and values.get("href"):
            self.external_assets.append(values["href"] or "")
        if values.get("data-panel"):
            self.panels.append(values["data-panel"] or "")
        if values.get("data-lang"):
            self.buttons.append(values["data-lang"] or "")

    def handle_data(self, data: str) -> None:
        normalized = " ".join(data.split())
        if normalized:
            self.text_parts.append(normalized)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(markdown: str, heading: str, following_headings: list[str]) -> str:
    marker = f"## {heading}\n"
    if marker not in markdown:
        raise ValueError(f"missing heading: {heading}")
    value = markdown.split(marker, 1)[1]
    end_positions = [value.find(f"\n## {candidate}\n") for candidate in following_headings]
    end_positions = [position for position in end_positions if position >= 0]
    if end_positions:
        value = value[: min(end_positions)]
    return value.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--drafts-dir", type=Path, required=True)
    args = parser.parse_args()

    site_dir = args.site_dir.resolve()
    drafts_dir = args.drafts_dir.resolve()
    html_path = site_dir / "index.html"
    html = html_path.read_text(encoding="utf-8")
    parsed = SiteParser()
    parsed.feed(html)
    parsed.close()

    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    check("html_declares_english_default", '<html lang="en">' in html, "html lang=en")
    check("locale_panels", sorted(parsed.panels) == ["en", "es", "ko"], parsed.panels)
    check("locale_buttons", sorted(parsed.buttons) == ["en", "es", "ko"], parsed.buttons)
    check("unique_ids", len(parsed.ids) == len(set(parsed.ids)), len(parsed.ids))
    missing_anchors = sorted({href[1:] for href in parsed.hrefs if href.startswith("#") and href[1:] not in parsed.ids})
    check("internal_links_resolve", not missing_anchors, missing_anchors)
    invalid_links = sorted(
        href for href in parsed.hrefs
        if not (href.startswith("#") or href.startswith("mailto:devjang.apps@gmail.com"))
    )
    check("links_allowlisted", not invalid_links, invalid_links)
    check("no_external_assets", not parsed.external_assets, parsed.external_assets)
    check("support_email", html.count("devjang.apps@gmail.com") >= 7, html.count("devjang.apps@gmail.com"))
    check("effective_dates", all(value in html for value in ["July 17, 2026", "2026년 7월 17일", "17 de julio de 2026"]), "en/ko/es")
    check(
        "signed_release_identity",
        all(value in html for value in ["com.evmodu.dishscribe", "version 1.0.0 (1)", "버전 1.0.0 (1)", "versión 1.0.0 (1)"]),
        "package and version in en/ko/es",
    )
    check(
        "backup_is_confirmed",
        all(value in html for value in ["Release verification:", "출시 검증:", "Verificación de la versión:"]),
        "confirmed signed-release backup statement in en/ko/es",
    )
    provisional_terms = ["point is provisional", "잠정 사항", "punto es provisional", "final signed manifest is not yet available"]
    provisional_hits = [value for value in provisional_terms if value in html]
    check("provisional_release_copy_absent", not provisional_hits, provisional_hits)
    check("no_insecure_urls", "http://" not in html, "http:// absent")

    listing_specs = {
        "listing_en-US.md": ("Title", "Short description", "Full description"),
        "listing_ko.md": ("제목", "간단한 설명", "자세한 설명"),
        "listing_es-ES.md": ("Título", "Descripción breve", "Descripción completa"),
    }
    listing_lengths: dict[str, dict[str, object]] = {}
    listing_release_copy: list[str] = []
    for filename, headings in listing_specs.items():
        path = drafts_dir / filename
        markdown = path.read_text(encoding="utf-8")
        title = section(markdown, headings[0], [headings[1], headings[2]])
        short = section(markdown, headings[1], [headings[2]])
        full = section(markdown, headings[2], [])
        listing_lengths[filename] = {
            "title": {"characters": len(title), "limit": 30, "valid": len(title) <= 30},
            "short": {"characters": len(short), "limit": 80, "valid": len(short) <= 80},
            "full": {"characters": len(full), "limit": 4000, "valid": len(full) <= 4000},
        }
        listing_release_copy.extend([title, short, full])

    check(
        "listing_character_limits",
        all(field["valid"] for locale in listing_lengths.values() for field in locale.values()),
        listing_lengths,
    )

    required_drafts = [
        drafts_dir / "listing_en-US.md",
        drafts_dir / "listing_ko.md",
        drafts_dir / "listing_es-ES.md",
        drafts_dir / "play_policy_declarations.md",
        drafts_dir / "store_asset_design_brief.md",
    ]
    all_paths = [html_path, site_dir / "README.md", site_dir / "validate_drafts.py", *required_drafts]
    missing_files = [str(path) for path in all_paths if not path.is_file()]
    check("required_files_exist", not missing_files, missing_files)

    content_paths = [path for path in all_paths if path.name != "validate_drafts.py"]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in content_paths if path.is_file())
    excluded_exact = [
        "Qui" + "ck",
        "TO" + "DO",
        "T" + "BD",
        "lorem" + " ipsum",
        "example" + ".com",
        "your" + "@email",
    ]
    excluded_hits = {term: combined.count(term) for term in excluded_exact if term in combined}
    check("excluded_terms_absent", not excluded_hits, excluded_hits)

    release_copy = "\n".join(listing_release_copy + parsed.text_parts)
    risky_patterns = {
        "ranking": r"(?i)(?:#\s*1|\bnumber\s+one\b|\bbest\b|\btop[- ]rated\b)",
        "install_cta": r"(?i)\b(?:download|install)\s+(?:now|today)\b",
        "guarantee": r"(?i)\bguaranteed?\b",
        "price_promotion": r"(?i)\b(?:discount|limited[- ]time|sale price)\b",
    }
    risky_hits = {
        name: sorted(set(match.group(0) for match in re.finditer(pattern, release_copy)))
        for name, pattern in risky_patterns.items()
    }
    risky_hits = {name: hits for name, hits in risky_hits.items() if hits}
    check("risky_release_copy_absent", not risky_hits, risky_hits)

    hashes = {str(path.relative_to(site_dir.parent.parent)): sha256(path) for path in all_paths if path.is_file()}
    passed = all(bool(item["passed"]) for item in checks)
    report = {
        "schema_version": 1,
        "result": "pass" if passed else "fail",
        "checks_passed": sum(bool(item["passed"]) for item in checks),
        "checks_total": len(checks),
        "checks": checks,
        "listing_lengths": listing_lengths,
        "sha256": hashes,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
