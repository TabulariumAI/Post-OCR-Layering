from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "Post-OCR-Layering-Spec.md"


def validate_local_links() -> None:
    pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for document in ROOT.rglob("*.md"):
        for target in pattern.findall(document.read_text(encoding="utf-8")):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_text = target.split("#", 1)[0]
            if path_text and not (document.parent / path_text).resolve().exists():
                raise ValueError(f"Broken local link in {document.relative_to(ROOT)}: {target}")


def validate_vectors() -> None:
    vectors = sorted((ROOT / "conformance").glob("*.json"))
    if not vectors:
        raise ValueError("No conformance vectors found")
    for vector in vectors:
        data = json.loads(vector.read_text(encoding="utf-8"))
        if data.get("specification_version") != "1.0":
            raise ValueError(f"Unexpected specification version in {vector.name}")
        cases = data.get("cases")
        if not isinstance(cases, list) or not cases:
            raise ValueError(f"No cases in {vector.name}")
        identifiers = [case.get("id") for case in cases]
        if None in identifiers or len(identifiers) != len(set(identifiers)):
            raise ValueError(f"Missing or duplicate case id in {vector.name}")


def validate_metadata() -> None:
    spec_text = SPEC.read_text(encoding="utf-8")
    for marker in ("**Version:** 1.0", "**Status:** Published", "## Conformance and Normative Scope"):
        if marker not in spec_text:
            raise ValueError(f"Missing specification marker: {marker}")

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    for marker in ('cff-version: 1.2.0', 'version: "1.0"', "license: Apache-2.0"):
        if marker not in citation:
            raise ValueError(f"Missing citation marker: {marker}")


if __name__ == "__main__":
    validate_local_links()
    validate_vectors()
    validate_metadata()
    print("Specification repository validation passed.")
