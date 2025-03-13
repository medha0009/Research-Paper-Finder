"""
Tests for the core functionality of the Research Paper Finder.
"""

import pytest
from research_paper_finder.core import ResearchPaperFinder


def test_is_non_academic_affiliation():
    """Test the is_non_academic_affiliation method."""
    finder = ResearchPaperFinder()
    
    # Test academic affiliations
    assert not finder.is_non_academic_affiliation("University of California, San Francisco")
    assert not finder.is_non_academic_affiliation("Harvard Medical School")
    assert not finder.is_non_academic_affiliation("National Institute of Health")
    assert not finder.is_non_academic_affiliation("Memorial Sloan Kettering Cancer Center")
    
    # Test pharmaceutical/biotech affiliations
    assert finder.is_non_academic_affiliation("Pfizer Inc., New York, NY")
    assert finder.is_non_academic_affiliation("Novartis Pharmaceuticals, Basel, Switzerland")
    assert finder.is_non_academic_affiliation("Genentech, South San Francisco, CA")
    assert finder.is_non_academic_affiliation("Moderna Therapeutics")


def test_extract_company_name():
    """Test the extract_company_name method."""
    finder = ResearchPaperFinder()
    
    # Test company name extraction
    assert "Pfizer Inc" in finder.extract_company_name("Pfizer Inc., New York, NY")
    assert "Novartis Pharmaceuticals" in finder.extract_company_name("Novartis Pharmaceuticals, Basel, Switzerland")
    assert "Genentech" in finder.extract_company_name("Genentech, South San Francisco, CA")
    assert "Moderna Therapeutics" in finder.extract_company_name("Moderna Therapeutics, Cambridge, MA") 