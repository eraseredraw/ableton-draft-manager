import gzip
import hashlib
import xml.etree.ElementTree as ET

import pytest

from admanager.scanner import (
    find_projects,
    inspect_project,
    parse_project_xml,
    read_als_metadata,
    sha256_of,
)

XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<LiveSet Version="12.0">
  <Tempo Value="{tempo}"/>
  <TimeSignature Numerator="{num}" Denominator="{den}"/>
  <ArrangementLength Value="{length}"/>
</LiveSet>
"""


def make_als(path, tempo=120.0, num=4, den=4, length=180.0, content=None):
    if content is None:
        content = XML_TEMPLATE.format(tempo=tempo, num=num, den=den, length=length)
    path.write_bytes(gzip.compress(content.encode("utf-8")))
    return path


def test_parse_project_xml(tmp_path):
    als = make_als(tmp_path / "song.als", tempo=128.5, length=240.0)
    tempo, ts, length = read_als_metadata(als)
    assert tempo == 128.5
    assert ts == "4/4"
    assert length == 240.0


def test_parse_non_gzip_returns_none(tmp_path):
    f = tmp_path / "broken.als"
    f.write_text("not gzip", encoding="utf-8")
    assert parse_project_xml(f.read_bytes()) == (None, None, None)


def test_parse_bad_xml_raises(tmp_path):
    als = make_als(tmp_path / "bad.als")
    data = bytearray(gzip.decompress(als.read_bytes()))
    data[:10] = b"NOT XML at"  # corrupt the payload
    import gzip as gz

    corrupt = gz.compress(bytes(data))
    with pytest.raises(ET.ParseError):
        parse_project_xml(corrupt)


def test_find_projects_recursive(tmp_path):
    (tmp_path / "sub").mkdir()
    make_als(tmp_path / "a.als")
    make_als(tmp_path / "sub" / "b.als")
    (tmp_path / "c.txt").write_text("x")
    found = find_projects(tmp_path)
    assert len(found) == 2


def test_find_projects_missing_root():
    assert find_projects(__import__("pathlib").Path("Z:/does/not/exist")) == []


def test_inspect_project(tmp_path):
    als = make_als(tmp_path / "song.als")
    p = inspect_project(als)
    assert p.name == "song"
    assert p.tempo == 120.0
    assert p.path == als


def test_sha256_of(tmp_path):
    f = tmp_path / "f.bin"
    f.write_bytes(b"hello")
    expected = hashlib.sha256(b"hello").hexdigest()
    assert sha256_of(f) == expected


def test_duplicate_detection(tmp_path):
    content = XML_TEMPLATE.format(tempo=100, num=3, den=4, length=90)
    make_als(tmp_path / "one.als", content=content)
    make_als(tmp_path / "two.als", content=content)
    assert (
        inspect_project(tmp_path / "one.als").sha256
        == inspect_project(tmp_path / "two.als").sha256
    )