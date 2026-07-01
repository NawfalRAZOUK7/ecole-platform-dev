"""Unit tests for the teacher level-band parser (no DB required).

`_level_bands_from_class_label` is the *fallback* that derives Moroccan
``level_band`` codes from a class label/code (legacy French ``6eme-A`` / ``CP-A``
or native Moroccan ``1AC-A`` / ``2BAC-PC``) when ``Class.level_band`` is not set.
It drives the CMS library filter for teachers (D3 — a teacher only browses the
levels they teach).
"""

from __future__ import annotations

import pytest

from app.repositories.lms import _level_bands_from_class_label


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        # legacy French labels -> Moroccan bands
        ("6eme-A", {"1AC"}),
        ("6ème-A", {"1AC"}),
        ("CP-A", {"1AEP"}),
        ("CE2", {"3AEP"}),
        ("CM2-B", {"6AEP"}),
        ("3eme-B", {"3AC"}),
        ("Terminale S", {"2BAC"}),
        ("Term-A", {"2BAC"}),
        ("creche", {"GS"}),
        ("primaire", {"1AEP"}),
        # native Moroccan codes
        ("1AEP-A", {"1AEP"}),
        ("3AC-B", {"3AC"}),
        ("TC-S", {"TC"}),
    ],
)
def test_level_band_parsing(label, expected):
    assert _level_bands_from_class_label(label) == expected


@pytest.mark.parametrize("label", ["", None, "   ", "Section Inconnue"])
def test_unparseable_labels_return_empty(label):
    assert _level_bands_from_class_label(label) == set()


def test_moroccan_track_suffix_does_not_collide():
    # "2BAC-PC" (physique-chimie track) must resolve to 2BAC only — the "PC"
    # suffix must NOT collide with the "cp" primary token.
    assert _level_bands_from_class_label("2BAC-PC") == {"2BAC"}
