"""Tests unitaires pour les sections de rapport."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.soft.dg.algorithms.reporting.report_sections import ReportSections

@pytest.fixture
def report_sections():
    return ReportSections()

@pytest.fixture
def sample_context():
    return {
        "request_id": "test-123",
        "timestamp": datetime.utcnow(),
        "metadata": {
            "test": "data"
        },
        "metrics": {
            "conversion_rate": 0.05,
            "click_through_rate": 0.12,
            "revenue": 1250.75,
            "system_health": {
                "cpu_usage": 45.2,
                "memory_usage": 62.1,
                "disk_usage": 38.7
            },
            "anomalies": [
                {"type": "high_error_rate", "severity": "high", "timestamp": "2023-01-15T10:30:00"},
                {"type": "slow_response", "severity": "medium", "timestamp": "2023-01-15T11:15:00"}
            ]
        }
    }

@pytest.fixture
def sample_config():
    return {
        "kpi_targets": {
            "conversion_rate": {"target": 0.04, "min": 0.03},
            "click_through_rate": {"target": 0.10, "min": 0.08},
            "revenue": {"target": 1000.0, "min": 800.0}
        },
        "system_thresholds": {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0
        }
    }

@pytest.mark.asyncio
async def test_generate_executive_summary(report_sections, sample_context, sample_config):
    """Teste la génération du résumé exécutif."""
    result = await report_sections.generate_executive_summary("daily", sample_context, sample_config)
    
    assert isinstance(result, dict)
    assert "period_summary" in result
    assert "key_metrics" in result
    assert "highlights" in result
    assert "next_steps" in result
    
    # Vérifie que les KPI sont correctement formatés
    assert "conversion_rate" in result["key_metrics"]
    assert "click_through_rate" in result["key_metrics"]
    assert "revenue" in result["key_metrics"]

@pytest.mark.asyncio
async def test_generate_performance_metrics(report_sections, sample_context, sample_config):
    """Teste la génération des métriques de performance."""
    result = await report_sections.generate_performance_metrics("daily", sample_context, sample_config)
    
    assert isinstance(result, dict)
    assert "metrics" in result
    assert "trends" in result
    assert "comparison" in result
    
    # Vérifie la structure des données de tendance
    assert "conversion_rate" in result["trends"]
    assert "click_through_rate" in result["trends"]
    assert "revenue" in result["trends"]
    
    # Vérifie que les tendances contiennent des données simulées
    for metric in ["conversion_rate", "click_through_rate", "revenue"]:
        assert len(result["trends"][metric]) > 0
        for point in result["trends"][metric]:
            assert "timestamp" in point
            assert "value" in point

@pytest.mark.asyncio
async def test_generate_anomalies(report_sections, sample_context, sample_config):
    """Teste la génération des anomalies détectées."""
    result = await report_sections.generate_anomalies("daily", sample_context, sample_config)
    
    assert isinstance(result, dict)
    assert "anomalies" in result
    assert "summary" in result
    assert "trends" in result
    
    # Vérifie que les anomalies sont correctement formatées
    for anomaly in result["anomalies"]:
        assert "type" in anomaly
        assert "severity" in anomaly
        assert "timestamp" in anomaly
        assert "description" in anomaly

@pytest.mark.asyncio
async def test_generate_recommendations(report_sections, sample_context, sample_config):
    """Teste la génération des recommandations."""
    result = await report_sections.generate_recommendations("daily", sample_context, sample_config)
    
    assert isinstance(result, dict)
    assert "recommendations" in result
    assert "priority" in result
    
    # Vérifie que les recommandations sont correctement formatées
    for rec in result["recommendations"]:
        assert "title" in rec
        assert "description" in rec
        assert "priority" in rec
        assert "impact" in rec
        assert "effort" in rec

@pytest.mark.asyncio
async def test_generate_system_health(report_sections, sample_context, sample_config):
    """Teste la génération de l'état de santé du système."""
    result = await report_sections.generate_system_health("daily", sample_context, sample_config)
    
    assert isinstance(result, dict)
    assert "metrics" in result
    assert "alerts" in result
    assert "trends" in result
    
    # Vérifie les métriques système
    for metric in ["cpu_usage", "memory_usage", "disk_usage"]:
        assert metric in result["metrics"]
        assert "current" in result["metrics"][metric]
        assert "threshold" in result["metrics"][metric]
        assert "status" in result["metrics"][metric]
    
    # Vérifie les tendances
    for metric in ["cpu_usage", "memory_usage", "disk_usage"]:
        assert metric in result["trends"]
        assert len(result["trends"][metric]) > 0

@pytest.mark.asyncio
async def test_error_handling(report_sections, sample_context, sample_config):
    """Teste la gestion des erreurs dans les sections de rapport."""
    # Test avec un contexte vide
    empty_context = {}
    result = await report_sections.generate_executive_summary("daily", empty_context, sample_config)
    assert isinstance(result, dict)
    assert "error" not in result  # Doit gérer les contextes vides
    
    # Test avec une configuration invalide
    invalid_config = {}
    result = await report_sections.generate_executive_summary("daily", sample_context, invalid_config)
    assert isinstance(result, dict)
    assert "error" not in result  # Doit gérer les configurations invalides

def test_format_metric(report_sections):
    """Teste le formatage des métriques."""
    # Test avec une valeur numérique
    result = report_sections._format_metric(0.05432, "percentage")
    assert result == "5.43%"
    
    # Test avec une valeur monétaire
    result = report_sections._format_metric(1234.567, "currency")
    assert result == "$1,234.57"
    
    # Test avec un entier
    result = report_sections._format_metric(42, "count")
    assert result == "42"
    
    # Test avec une valeur None
    result = report_sections._format_metric(None, "percentage")
    assert result == "N/A"

def test_get_metric_status(report_sections):
    """Teste la détermination du statut d'une métrique."""
    # Test avec une valeur au-dessus du seuil
    status = report_sections._get_metric_status(0.05, {"target": 0.04, "min": 0.03})
    assert status == "good"
    
    # Test avec une valeur en dessous du seuil minimum
    status = report_sections._get_metric_status(0.02, {"target": 0.04, "min": 0.03})
    assert status == "critical"
    
    # Test avec une valeur entre le minimum et la cible
    status = report_sections._get_metric_status(0.035, {"target": 0.04, "min": 0.03})
    assert status == "warning"
    
    # Test sans seuil minimum
    status = report_sections._get_metric_status(0.05, {"target": 0.04})
    assert status == "good"
    
    # Test sans configuration
    status = report_sections._get_metric_status(0.05, {})
    assert status == "unknown"
