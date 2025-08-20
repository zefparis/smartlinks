"""Tests unitaires pour le générateur de rapports."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json
import pandas as pd

from src.soft.dg.algorithms.reporting import ReportGenerator
from src.soft.dg.models.decision import DecisionContext

@pytest.fixture
def report_generator():
    return ReportGenerator()

@pytest.fixture
def sample_context():
    return DecisionContext(
        request_id="test-123",
        timestamp=datetime.utcnow(),
        metadata={"test": "data"}
    )

@pytest.fixture
def sample_config():
    return {
        "report_types": ["daily"],
        "report_formats": ["html"],
        "sections": ["executive_summary"],
        "templates_dir": "templates"
    }

@pytest.mark.asyncio
async def test_execute(report_generator, sample_context, sample_config):
    """Teste l'exécution du générateur de rapports."""
    with patch.object(report_generator, '_generate_report') as mock_generate:
        mock_generate.return_value = {"test": "report"}
        
        result = await report_generator.execute(sample_context, sample_config)
        
        assert result is not None
        assert len(result.actions) > 0
        assert mock_generate.called

@pytest.mark.asyncio
async def test_generate_report(report_generator, sample_context, sample_config):
    """Teste la génération d'un rapport."""
    with patch.object(report_generator._sections, 'generate_executive_summary') as mock_section:
        mock_section.return_value = {"summary": "Test summary"}
        
        report = await report_generator._generate_report("daily", sample_context, sample_config)
        
        assert report is not None
        assert "sections" in report
        assert "executive_summary" in report["sections"]
        assert report["sections"]["executive_summary"] == {"summary": "Test summary"}

def test_get_report_period_daily(report_generator):
    """Teste le calcul de la période pour un rapport journalier."""
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2023, 1, 15, 12, 0, 0)
        
        period = report_generator._get_report_period("daily")
        
        assert period["start"] == "2023-01-14T00:00:00"
        assert period["end"] == "2023-01-14T23:59:59.999999"
        assert period["timezone"] == "UTC"

def test_update_report_history(report_generator):
    """Teste la mise à jour de l'historique des rapports."""
    report_data = {
        "daily": {
            "report_date": "2023-01-15 12:00:00",
            "period": {"start": "2023-01-14T00:00:00", "end": "2023-01-14T23:59:59.999999"},
            "sections": {}
        }
    }
    
    report_generator._update_report_history(report_data)
    
    assert len(report_generator._report_history) == 1
    assert report_generator._report_history[0]["type"] == "daily"
    assert report_generator._report_history[0]["timestamp"] == "2023-01-15 12:00:00"

@pytest.mark.parametrize("format_type", ["html", "json", "csv"])
def test_create_report_action(report_generator, format_type):
    """Teste la création d'actions pour différents formats de rapport."""
    report_data = {
        "report_date": "2023-01-15 12:00:00",
        "period": {"start": "2023-01-14T00:00:00", "end": "2023-01-14T23:59:59.999999"},
        "sections": {}
    }
    
    action = report_generator._create_report_action(
        report_data, "daily", format_type, {"templates_dir": "templates"}
    )
    
    assert action is not None
    assert action.action_type == "generate_report"
    assert action.params["format"] == format_type
    assert "content" in action.params
    assert "filename" in action.params
    assert "daily" in action.params["filename"]
    assert format_type in action.params["filename"]

def test_flatten_report_data(report_generator):
    """Teste l'aplatissement des données du rapport pour le format CSV."""
    data = {
        "section1": {"key1": "value1"},
        "section2": ["item1", "item2"],
        "key3": "value3"
    }
    
    flat_data = report_generator._flatten_report_data(data)
    
    assert "section1_key1" in flat_data
    assert flat_data["section1_key1"] == "value1"
    assert "section2" in flat_data
    assert flat_data["section2"] == '["item1", "item2"]'
    assert "key3" in flat_data
    assert flat_data["key3"] == "value3"

@pytest.mark.asyncio
async def test_error_handling(report_generator, sample_context, sample_config):
    """Teste la gestion des erreurs lors de la génération des sections."""
    with patch.object(report_generator._sections, 'generate_executive_summary') as mock_section:
        mock_section.side_effect = Exception("Test error")
        
        report = await report_generator._generate_report("daily", sample_context, sample_config)
        
        assert "sections" in report
        assert "executive_summary" in report["sections"]
        assert "error" in report["sections"]["executive_summary"]
        assert "Test error" in report["sections"]["executive_summary"]["error"]
