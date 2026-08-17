"""Ableton Live project scanning and metadata extraction.

Ableton `.als` files are gzip-compressed XML documents. We decompress and
parse the XML tree to extract tempo, time signature and arrangement length.
"""

from __future__ import annotations

import gzip
import hashlib
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

NAMESPACE = "{http://www.ableton.com/ns/liveset/10.0}"


@dataclass(frozen=True)
class Project:
    """Metadata for a single Ableton project file."""

    path: Path
    name: str
    tempo: float | None
    time_signature: str | None
    arrangement_length: float | None  # seconds
    sha256: str


def find_projects(root: Path) -> list[Path]:
    """Return all `.als` files under root, sorted by path."""
    if not root.exists():
        return []
    return sorted(root.rglob("*.als"))


def parse_project_xml(data: bytes) -> tuple[float | None, str | None, float | None]:
    """Parse gzip-compressed .als XML; return (tempo, time_signature, length_s)."""
    try:
        xml = gzip.decompress(data)
    except OSError:
        return None, None, None
    root = ET.fromstring(xml)

    tempo: float | None = None
    ts: str | None = None
    length: float | None = None

    for elem in root.iter():
        tag = elem.tag.removeprefix(NAMESPACE)
        if tag == "Tempo":
            val = elem.attrib.get("Value")
            if val is not None:
                tempo = float(val)
        elif tag == "TimeSignature":
            numerator = elem.attrib.get("Numerator")
            denominator = elem.attrib.get("Denominator")
            if numerator and denominator:
                ts = f"{numerator}/{denominator}"
        elif tag == "ArrangementLength" or tag == "LomIdProvider":
            val = elem.attrib.get("Value")
            if tag == "ArrangementLength" and val is not None:
                length = float(val)

    return tempo, ts, length


def read_als_metadata(path: Path) -> tuple[float | None, str | None, float | None]:
    """Read metadata from a single .als file on disk."""
    return parse_project_xml(path.read_bytes())


def sha256_of(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def inspect_project(path: Path) -> Project:
    """Collect metadata for one .als file."""
    tempo, ts, length = read_als_metadata(path)
    return Project(
        path=path,
        name=path.stem,
        tempo=tempo,
        time_signature=ts,
        arrangement_length=length,
        sha256=sha256_of(path),
    )
