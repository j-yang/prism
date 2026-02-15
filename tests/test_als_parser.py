"""
Tests for ALS Parser
"""

import pytest
from pathlib import Path

from prism.meta.als_parser import (
    get_domain_for_form,
    classify_forms,
    get_domain_field_mapping,
    parse_als,
)


class TestDomainMapping:
    def test_get_domain_for_form_ae(self):
        assert get_domain_for_form("AE") == "AE"
        assert get_domain_for_form("AE1") == "AE"
        assert get_domain_for_form("AE2") == "AE"
        assert get_domain_for_form("ae") == "AE"

    def test_get_domain_for_form_cm(self):
        assert get_domain_for_form("CM") == "CM"
        assert get_domain_for_form("CM1") == "CM"
        assert get_domain_for_form("CM2") == "CM"

    def test_get_domain_for_form_mh(self):
        assert get_domain_for_form("MH") == "MH"
        assert get_domain_for_form("MH1") == "MH"
        assert get_domain_for_form("MH2") == "MH"

    def test_get_domain_for_form_unknown(self):
        assert get_domain_for_form("DM") is None
        assert get_domain_for_form("VS") is None
        assert get_domain_for_form("LB") is None


class TestFormClassification:
    def test_classify_occurrence_forms(self):
        forms = [
            {"oid": "AE", "name": "Adverse Events"},
            {"oid": "CM1", "name": "Concomitant Medications"},
            {"oid": "MH", "name": "Medical History"},
        ]
        fields = []
        matrices = {}

        result = classify_forms(forms, fields, matrices)

        assert result["AE"]["schema"] == "occurrence"
        assert result["AE"]["domain"] == "AE"
        assert result["CM1"]["schema"] == "occurrence"
        assert result["CM1"]["domain"] == "CM"
        assert result["MH"]["schema"] == "occurrence"
        assert result["MH"]["domain"] == "MH"

    def test_classify_baseline_forms(self):
        forms = [
            {"oid": "DM", "name": "Demographics"},
        ]
        fields = []
        matrices = {"DM": ["SCR", "BASE"]}

        result = classify_forms(forms, fields, matrices)

        assert result["DM"]["schema"] == "baseline"

    def test_classify_longitudinal_forms(self):
        forms = [
            {"oid": "LB", "name": "Laboratory"},
        ]
        fields = []
        matrices = {"LB": ["SFU1", "SFU2", "SFU3"]}

        result = classify_forms(forms, fields, matrices)

        assert result["LB"]["schema"] == "longitudinal"


class TestDomainFieldMapping:
    def test_get_domain_field_mapping(self):
        mapping = get_domain_field_mapping()

        assert "AE" in mapping
        assert mapping["AE"]["term"] == "AETERM"
        assert mapping["AE"]["startdt"] == "AESTDTC"
        assert mapping["AE"]["coding_low"] == "AEDECOD"

        assert "CM" in mapping
        assert mapping["CM"]["term"] == "CMTRT"


class TestParseALS:
    @pytest.fixture
    def als_path(self):
        path = Path(
            "/Users/jimmyyang/projects/prism/examples/some_study/D8318N00001_ALS.xlsx"
        )
        if not path.exists():
            pytest.skip(f"ALS file not found: {path}")
        return str(path)

    def test_parse_als_structure(self, als_path):
        result = parse_als(als_path)

        assert "forms" in result
        assert "fields" in result
        assert "folders" in result
        assert "codelists" in result

        assert len(result["forms"]) > 0
        assert len(result["fields"]) > 0
        assert len(result["folders"]) > 0

    def test_parse_als_forms(self, als_path):
        result = parse_als(als_path)

        form_oids = [f["oid"] for f in result["forms"]]
        assert "AE" in form_oids
        assert "CM" in form_oids
        assert "MH" in form_oids

    def test_parse_als_codelists(self, als_path):
        result = parse_als(als_path)

        assert isinstance(result["codelists"], dict)
        assert len(result["codelists"]) > 0
