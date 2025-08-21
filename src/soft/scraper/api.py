"""FastAPI router for scraper endpoints."""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging
import os
import subprocess
import json
import sys
from pathlib import Path
import asyncio
import tempfile
from datetime import datetime

from .offervault_scraper import OffervaultScraper
from .scraper_discovery import ScraperDiscovery
from .scraper_runner import ScraperRunner
from .discovery_scraper import DiscoveryScraper
from .discovery_scheduler import discovery_scheduler

# SQLAlchemy Core for lightweight table creation/inserts
try:
    from sqlalchemy import Table, Column, Integer, String, Float, Text, MetaData
    from sqlalchemy.exc import SQLAlchemyError
    from backend.database import engine
    _sqlalchemy_available = True
except Exception:
    _sqlalchemy_available = False

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/scraper", tags=["scraper"])

# Initialize modules
discovery = ScraperDiscovery()
runner = ScraperRunner()
discovery_scraper = DiscoveryScraper()

class ScrapeRequest(BaseModel):
    """Request model for scraping offers."""
    network: str = "offervault"
    pages: int = 2

class RunScraperRequest(BaseModel):
    """Request model for running dynamic scrapers."""
    repo: str
    params: Optional[Dict[str, Any]] = {}
    timeout: Optional[int] = 300  # 5 minutes default

class ScrapeResponse(BaseModel):
    """Response model for scraping offers."""
    success: bool
    offers: List[Dict[str, Any]]
    count: int
    message: str

class ScraperInfo(BaseModel):
    """Information about a discovered scraper."""
    name: str
    description: Optional[str] = None
    entry_point: str
    requirements: Optional[List[str]] = []
    params_schema: Optional[Dict[str, Any]] = {}
    status: str = "available"  # available, error, missing_deps

class ListScrapersResponse(BaseModel):
    """Response model for listing scrapers."""
    scrapers: List[ScraperInfo]
    count: int

class ImportOfferRequest(BaseModel):
    """Request model for importing offers."""
    title: str
    url: str
    description: Optional[str] = None
    payout: Optional[float] = None
    category: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None

class DiscoveryStatusResponse(BaseModel):
    """Response model for discovery status."""
    is_running: bool
    current_session_id: Optional[int] = None
    logs: List[str] = []
    recent_sources: List[Dict[str, Any]] = []
    recent_offers: List[Dict[str, Any]] = []

class DiscoveryStartResponse(BaseModel):
    """Response model for starting discovery."""
    success: bool
    message: str
    sources_found: Optional[int] = None
    offers_found: Optional[int] = None
    logs: List[str] = []

class DiscoveryFindingsResponse(BaseModel):
    """Response model for discovery findings."""
    sources: List[Dict[str, Any]] = []
    offers: List[Dict[str, Any]] = []

class HealthResponse(BaseModel):
    """Health response for scraper dependencies."""
    ok: bool
    dependencies: Dict[str, bool]
    message: str

class ImportOfferResponse(BaseModel):
    """Response for importing a single offer."""
    success: bool
    message: str

@router.post("/offers", response_model=ScrapeResponse)
async def scrape_affiliate_offers(
    request: ScrapeRequest
):
    """
    Scrape affiliate offers from specified network.
    
    This endpoint is public (no admin required).
    
    Args:
        request: Scrape request with network and pages parameters
        
    Returns:
        ScrapeResponse with offers data
    """
    print(f"[SCRAPER] POST /offers called - network={request.network}, pages={request.pages}")
    logger.info(f"[SCRAPER] Start: network={request.network}, pages={request.pages}")
    
    try:
        if request.network == "offervault":
            scraper = OffervaultScraper()
            offers = scraper.scrape_offers(request.pages)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported network: {request.network}"
            )

        print(f"[SCRAPER] Success: scraped {len(offers)} offers")
        logger.info(f"[SCRAPER] Success: network={request.network}, count={len(offers)}")
        return ScrapeResponse(
            success=True,
            offers=offers,
            count=len(offers),
            message=f"Successfully scraped {len(offers)} offers from {request.network}"
        )

    except ImportError as e:
        error_msg = "BeautifulSoup4 n'est pas installé. Installez-le avec: pip install beautifulsoup4==4.12.3"
        print(f"[SCRAPER] ImportError: {e}")
        logger.error(f"[SCRAPER] Dependency missing: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except HTTPException:
        # Re-raise HTTPExceptions untouched
        raise
    except Exception as e:
        print(f"[SCRAPER] Exception: {e}")
        logger.error(f"[SCRAPER] Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping offers: {str(e)}"
        )

@router.get("/health", response_model=HealthResponse)
async def scraper_health():
    """Return comprehensive health status for scraper system."""
    print("[SCRAPER] GET /health called")
    deps = {"bs4": False, "requests": False, "subprocess": False, "json": False}
    versions = {}
    
    # Check basic Python modules
    try:
        import subprocess
        deps["subprocess"] = True
        versions["subprocess"] = "built-in"
    except Exception as e:
        print(f"[SCRAPER] subprocess import failed: {e}")
        deps["subprocess"] = False
    
    try:
        import json
        deps["json"] = True
        versions["json"] = "built-in"
    except Exception as e:
        print(f"[SCRAPER] json import failed: {e}")
        deps["json"] = False
    
    try:
        import requests
        deps["requests"] = True
        versions["requests"] = getattr(requests, '__version__', 'unknown')
    except Exception as e:
        print(f"[SCRAPER] requests import failed: {e}")
        deps["requests"] = False
        
    try:
        from bs4 import BeautifulSoup
        deps["bs4"] = True
        import bs4
        versions["bs4"] = getattr(bs4, '__version__', 'unknown')
    except Exception as e:
        print(f"[SCRAPER] bs4 import failed: {e}")
        deps["bs4"] = False
    
    # Check external scrapers directory
    try:
        scrapers = discovery.discover_scrapers()
        deps["external_scrapers"] = len(scrapers) > 0
        versions["external_scrapers"] = f"{len(scrapers)} scrapers found"
    except Exception as e:
        print(f"[SCRAPER] external scrapers check failed: {e}")
        deps["external_scrapers"] = False
        versions["external_scrapers"] = f"Error: {str(e)}"
    
    ok = all(deps.values())
    message = "OK" if ok else "Missing dependencies: " + ", ".join([k for k, v in deps.items() if not v])
    
    print(f"[SCRAPER] Health check result: ok={ok}, deps={deps}, versions={versions}")
    
    response = HealthResponse(ok=ok, dependencies=deps, message=message)
    # Add versions to response for debugging
    response.versions = versions
    return response

@router.get("/list", response_model=ListScrapersResponse)
async def list_scrapers():
    """
    List all available scrapers in external_scrapers directory.
    
    This endpoint is public (no admin required).
    
    Returns:
        ListScrapersResponse with discovered scrapers
    """
    print("[SCRAPER] GET /list called")
    logger.info("[SCRAPER] Discovering scrapers")
    
    try:
        scrapers_data = discovery.discover_scrapers()
        scrapers = []
        
        for scraper in scrapers_data:
            try:
                scraper_info = ScraperInfo(
                    name=scraper["name"],
                    description=scraper.get("description"),
                    entry_point=scraper["entry_point"],
                    requirements=scraper.get("requirements", []),
                    params_schema=scraper.get("params_schema", {}),
                    status=scraper.get("status", "available")
                )
                scrapers.append(scraper_info)
            except Exception as scraper_error:
                logger.warning(f"[SCRAPER] Failed to process scraper {scraper.get('name', 'unknown')}: {str(scraper_error)}")
                # Add a broken scraper entry
                scrapers.append(ScraperInfo(
                    name=scraper.get("name", "unknown"),
                    description=f"Error: {str(scraper_error)}",
                    entry_point="",
                    requirements=[],
                    params_schema={},
                    status="error"
                ))
        
        print(f"[SCRAPER] Found {len(scrapers)} scrapers")
        logger.info(f"[SCRAPER] Successfully discovered {len(scrapers)} scrapers")
        
        return ListScrapersResponse(scrapers=scrapers, count=len(scrapers))
        
    except Exception as e:
        error_msg = f"Failed to discover scrapers: {str(e)}"
        print(f"[SCRAPER] Error discovering scrapers: {str(e)}")
        logger.error(f"[SCRAPER] Error discovering scrapers: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/run", response_model=RunScraperResponse)
async def run_scraper(request: RunScraperRequest):
    """
    Run a specific scraper with parameters.
    
    This endpoint is public (no admin required).
    
    Args:
        request: RunScraperRequest with repo name and parameters
    
    Returns:
        RunScraperResponse with execution results
    """
    print(f"[SCRAPER] POST /run called for repo: {request.repo}")
    logger.info(f"[SCRAPER] Running scraper: {request.repo} with params: {request.params}")
    
    # Validate repo name
    if not request.repo or not request.repo.strip():
        error_msg = "Repo name is required"
        logger.error(f"[SCRAPER] {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Validate timeout
    if request.timeout and (request.timeout < 10 or request.timeout > 3600):
        error_msg = "Timeout must be between 10 and 3600 seconds"
        logger.error(f"[SCRAPER] {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)
    
    try:
        result = await runner.run_scraper(request.repo, request.params or {}, request.timeout or 300)
        
        success = result.get("success", False)
        offer_count = len(result.get("offers", []))
        execution_time = result.get("execution_time", 0.0)
        
        print(f"[SCRAPER] Scraper execution completed: success={success}, offers={offer_count}, time={execution_time:.2f}s")
        logger.info(f"[SCRAPER] Scraper execution completed for {request.repo}: success={success}, offers={offer_count}, time={execution_time:.2f}s")
        
        return RunScraperResponse(
            success=success,
            message=result.get("message", "Execution completed"),
            logs=result.get("logs", []),
            offers=result.get("offers", []),
            count=offer_count,
            execution_time=execution_time
        )
        
    except HTTPException:
        # Re-raise HTTPExceptions untouched
        raise
    except Exception as e:
        print(f"[SCRAPER] Error running scraper: {e}")
        logger.error(f"[SCRAPER] Error running scraper {request.repo}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running scraper: {str(e)}"
        )

@router.post("/import")
async def import_offer(payload: ImportOfferRequest):
    """
    Import a single offer into the database.
    """
    print(f"[SCRAPER] POST /import called for offer: {payload.offer.get('name', 'unknown')}")
    logger.info(f"[SCRAPER] Import request for offer: {payload.offer.get('name', 'unknown')}")

    try:
        if not _sqlalchemy_available:
            print("[SCRAPER] SQLAlchemy not available - simulating import")
            logger.warning("SQLAlchemy not available; echoing import without DB insert")
            return {
                "success": True,
                "message": "Offer import simulated (SQLAlchemy not available)",
                "offer": payload.offer,
            }

        # Define table on the fly
        metadata = MetaData()
        offers_table = Table(
            "affiliate_offers",
            metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("name", String(512)),
            Column("network", String(128)),
            Column("payout", Float),
            Column("payout_type", String(64)),
            Column("category", String(256)),
            Column("countries", Text),  # comma-separated
            Column("epc", Float),
            Column("approval_rate", Float),
            Column("preview_url", Text),
            Column("tracking_url", Text),
        )

        # Create table if not exists
        metadata.create_all(bind=engine)

        # Prepare row
        o = payload.offer or {}
        countries = o.get("countries")
        if isinstance(countries, list):
            countries_str = ",".join([str(c) for c in countries])
        else:
            countries_str = str(countries or "")

        row = {
            "name": o.get("name"),
            "network": o.get("network"),
            "payout": (o.get("payout") if isinstance(o.get("payout"), (int, float)) else None),
            "payout_type": o.get("payout_type"),
            "category": o.get("category"),
            "countries": countries_str,
            "epc": (o.get("epc") if isinstance(o.get("epc"), (int, float)) else None),
            "approval_rate": (o.get("approval_rate") if isinstance(o.get("approval_rate"), (int, float)) else None),
            "preview_url": o.get("preview_url"),
            "tracking_url": o.get("tracking_url"),
        }

        # Insert
        with engine.begin() as conn:
            result = conn.execute(offers_table.insert().values(**row))
            inserted_id = result.inserted_primary_key[0] if result.inserted_primary_key else None

        msg = "Offer imported" + (f" (id={inserted_id})" if inserted_id else "")
        print(f"[SCRAPER] Import success: {msg}")
        return {"success": True, "message": msg, "offer": {**o, "id": inserted_id}}

    except SQLAlchemyError as e:
        print(f"[SCRAPER] Import SQL error: {e}")
        logger.error(f"[SCRAPER] Import SQL error: {e}")
        raise HTTPException(status_code=500, detail=f"Import SQL error: {str(e)}")
    except Exception as e:
        print(f"[SCRAPER] Import error: {e}")
        logger.error(f"[SCRAPER] Import error: {e}")
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")

# Discovery Scraper Endpoints

@router.get("/discovery/status", response_model=DiscoveryStatusResponse)
async def get_discovery_status():
    """
    Get current discovery scraper status.
    
    Returns current status, logs, and recent findings.
    """
    print("[DISCOVERY] GET /discovery/status called")
    logger.info("[DISCOVERY] Getting discovery status")
    
    try:
        status = discovery_scraper.get_status()
        
        return DiscoveryStatusResponse(
            is_running=status["is_running"],
            current_session_id=status["current_session_id"],
            logs=status["logs"],
            recent_sources=status["recent_sources"],
            recent_offers=status["recent_offers"]
        )
        
    except Exception as e:
        error_msg = f"Failed to get discovery status: {str(e)}"
        logger.error(f"[DISCOVERY] {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/discovery/start", response_model=DiscoveryStartResponse)
async def start_discovery():
    """
    Start the autonomous discovery process.
    
    Launches search engine scanning and marketplace crawling.
    """
    print("[DISCOVERY] POST /discovery/start called")
    logger.info("[DISCOVERY] Starting discovery process")
    
    try:
        result = await discovery_scraper.start_discovery()
        
        return DiscoveryStartResponse(
            success=result["success"],
            message=result["message"],
            sources_found=result.get("sources_found"),
            offers_found=result.get("offers_found"),
            logs=result.get("logs", [])
        )
        
    except Exception as e:
        error_msg = f"Failed to start discovery: {str(e)}"
        logger.error(f"[DISCOVERY] {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/discovery/findings", response_model=DiscoveryFindingsResponse)
async def get_discovery_findings():
    """
    Get recent discovery findings.
    
    Returns discovered sources and offers for review.
    """
    print("[DISCOVERY] GET /discovery/findings called")
    logger.info("[DISCOVERY] Getting discovery findings")
    
    try:
        findings = discovery_scraper.get_recent_findings()
        
        return DiscoveryFindingsResponse(
            sources=findings["sources"],
            offers=findings["offers"]
        )
        
    except Exception as e:
        error_msg = f"Failed to get discovery findings: {str(e)}"
        logger.error(f"[DISCOVERY] {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/discovery/import-offer")
async def import_discovered_offer(offer_id: int):
    """
    Import a discovered offer into the main database.
    
    Args:
        offer_id: ID of the discovered offer to import
    """
    print(f"[DISCOVERY] POST /discovery/import-offer called for offer {offer_id}")
    logger.info(f"[DISCOVERY] Importing discovered offer {offer_id}")
    
    try:
        # Get the offer from discovery database
        conn = sqlite3.connect(discovery_scraper.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM discovered_offers WHERE id = ? AND imported = FALSE
        ''', (offer_id,))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Offer not found or already imported")
        
        # Convert to offer format
        columns = [desc[0] for desc in cursor.description]
        offer_data = dict(zip(columns, row))
        
        # Import using existing import endpoint logic
        import_request = ImportOfferRequest(
            title=offer_data["title"],
            url=offer_data["url"] or "",
            description=offer_data["description"],
            payout=float(offer_data["payout"]) if offer_data["payout"] else None,
            category=offer_data["category"],
            company=offer_data["network"],
            location=offer_data["geo"]
        )
        
        # Mark as imported in discovery database
        cursor.execute('''
            UPDATE discovered_offers SET imported = TRUE WHERE id = ?
        ''', (offer_id,))
        conn.commit()
        conn.close()
        
        # Import to main database (reuse existing logic)
        result = await import_offer(import_request)
        
        logger.info(f"[DISCOVERY] Successfully imported discovered offer {offer_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Failed to import discovered offer: {str(e)}"
        logger.error(f"[DISCOVERY] {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.get("/discovery/scheduler/status")
async def get_discovery_scheduler_status():
    """
    Get discovery scheduler status and configuration.
    """
    print("[DISCOVERY] GET /discovery/scheduler/status called")
    logger.info("[DISCOVERY] Getting scheduler status")
    
    try:
        status = discovery_scheduler.get_status()
        stats = discovery_scheduler.get_stats()
        
        return {
            "scheduler": status,
            "stats": stats
        }
        
    except Exception as e:
        error_msg = f"Failed to get scheduler status: {str(e)}"
        logger.error(f"[DISCOVERY] {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/discovery/scheduler/start")
async def start_discovery_scheduler():
    """
    Start the discovery scheduler.
    """
    print("[DISCOVERY] POST /discovery/scheduler/start called")
    logger.info("[DISCOVERY] Starting scheduler")
    
    try:
        success = discovery_scheduler.start()
        
        return {
            "success": success,
            "message": "Scheduler started successfully" if success else "Failed to start scheduler"
        }
        
    except Exception as e:
        error_msg = f"Failed to start scheduler: {str(e)}"
        logger.error(f"[DISCOVERY] {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/discovery/scheduler/stop")
async def stop_discovery_scheduler():
    """
    Stop the discovery scheduler.
    """
    print("[DISCOVERY] POST /discovery/scheduler/stop called")
    logger.info("[DISCOVERY] Stopping scheduler")
    
    try:
        success = discovery_scheduler.stop()
        
        return {
            "success": success,
            "message": "Scheduler stopped successfully" if success else "Failed to stop scheduler"
        }
        
    except Exception as e:
        error_msg = f"Failed to stop scheduler: {str(e)}"
        logger.error(f"[DISCOVERY] {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/discovery/scheduler/run-now")
async def run_discovery_now():
    """
    Run discovery immediately (manual trigger).
    """
    print("[DISCOVERY] POST /discovery/scheduler/run-now called")
    logger.info("[DISCOVERY] Manual discovery trigger")
    
    try:
        result = discovery_scheduler.run_now()
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Discovery completed"),
            "sources_found": result.get("sources_found", 0),
            "offers_found": result.get("offers_found", 0)
        }
        
    except Exception as e:
        error_msg = f"Failed to run discovery now: {str(e)}"
        logger.error(f"[DISCOVERY] {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/discovery/scheduler/config")
async def update_discovery_scheduler_config(config: Dict[str, Any]):
    """
    Update discovery scheduler configuration.
    """
    print("[DISCOVERY] POST /discovery/scheduler/config called")
    logger.info("[DISCOVERY] Updating scheduler config")
    
    try:
        success = discovery_scheduler.update_config(config)
        
        return {
            "success": success,
            "message": "Configuration updated successfully" if success else "Failed to update configuration"
        }
        
    except Exception as e:
        error_msg = f"Failed to update scheduler config: {str(e)}"
        logger.error(f"[DISCOVERY] {error_msg}", exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)
