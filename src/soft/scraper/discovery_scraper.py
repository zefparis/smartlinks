"""
Discovery Scraper Module for SmartLinks Autopilot
Autonomous exploration of affiliate sources, marketplaces, and CPA networks
"""

import asyncio
import aiohttp
import json
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
from pathlib import Path
import sqlite3
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
import random

logger = logging.getLogger(__name__)

@dataclass
class DiscoveredSource:
    """Represents a discovered affiliate source"""
    url: str
    title: str
    description: str
    source_type: str  # 'marketplace', 'network', 'directory', 'forum'
    confidence_score: float  # 0.0 to 1.0
    last_scraped: Optional[datetime] = None
    status: str = 'discovered'  # 'discovered', 'validated', 'scraped', 'failed'
    offers_count: int = 0
    parsing_template: Optional[Dict[str, Any]] = None
    discovered_at: datetime = None
    
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now()

@dataclass
class DiscoveredOffer:
    """Represents a discovered affiliate offer"""
    title: str
    url: str
    source_url: str
    payout: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    vertical: Optional[str] = None
    geo: Optional[str] = None
    network: Optional[str] = None
    confidence_score: float = 0.0
    discovered_at: datetime = None
    raw_data: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = datetime.now()

class SearchEngineScanner:
    """Scans search engines for affiliate sources"""
    
    SEARCH_QUERIES = [
        "affiliate offers 2025",
        "CPA network list",
        "high payout affiliate",
        "affiliate marketplace",
        "performance marketing network",
        "affiliate program directory",
        "CPA offers high converting",
        "affiliate network signup",
        "performance marketing offers",
        "affiliate program list 2025"
    ]
    
    SEARCH_ENGINES = {
        'google': 'https://www.google.com/search?q={query}&num=20',
        'bing': 'https://www.bing.com/search?q={query}&count=20',
        'duckduckgo': 'https://duckduckgo.com/html/?q={query}'
    }
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
    
    async def scan_search_engines(self) -> List[DiscoveredSource]:
        """Scan all search engines for affiliate sources"""
        discovered_sources = []
        
        for engine, url_template in self.SEARCH_ENGINES.items():
            logger.info(f"[DISCOVERY] Scanning {engine}")
            
            for query in self.SEARCH_QUERIES:
                try:
                    sources = await self._scan_engine(engine, url_template, query)
                    discovered_sources.extend(sources)
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"[DISCOVERY] Error scanning {engine} with query '{query}': {e}")
        
        return self._deduplicate_sources(discovered_sources)
    
    async def _scan_engine(self, engine: str, url_template: str, query: str) -> List[DiscoveredSource]:
        """Scan a specific search engine"""
        sources = []
        
        try:
            url = url_template.format(query=query.replace(' ', '+'))
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    sources = self._parse_search_results(html, engine, query)
                else:
                    logger.warning(f"[DISCOVERY] {engine} returned status {response.status}")
                    
        except Exception as e:
            logger.error(f"[DISCOVERY] Error scanning {engine}: {e}")
        
        return sources
    
    def _parse_search_results(self, html: str, engine: str, query: str) -> List[DiscoveredSource]:
        """Parse search results HTML"""
        sources = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Engine-specific selectors
        selectors = {
            'google': {'link': 'h3 a', 'title': 'h3', 'snippet': '.VwiC3b'},
            'bing': {'link': 'h2 a', 'title': 'h2', 'snippet': '.b_caption p'},
            'duckduckgo': {'link': '.result__a', 'title': '.result__a', 'snippet': '.result__snippet'}
        }
        
        if engine not in selectors:
            return sources
        
        sel = selectors[engine]
        
        # Find result links
        links = soup.select(sel['link'])
        
        for link in links[:10]:  # Limit to top 10 results
            try:
                href = link.get('href', '')
                
                # Clean Google redirect URLs
                if engine == 'google' and href.startswith('/url?'):
                    parsed = parse_qs(href[5:])
                    href = parsed.get('q', [''])[0]
                
                if not href or not href.startswith('http'):
                    continue
                
                # Extract title and description
                title = link.get_text(strip=True)
                
                # Get snippet/description
                description = ""
                snippet_elem = link.find_next(sel['snippet'])
                if snippet_elem:
                    description = snippet_elem.get_text(strip=True)
                
                # Score the source based on relevance
                confidence = self._score_source(href, title, description, query)
                
                if confidence > 0.3:  # Only keep promising sources
                    source_type = self._classify_source_type(href, title, description)
                    
                    source = DiscoveredSource(
                        url=href,
                        title=title,
                        description=description,
                        source_type=source_type,
                        confidence_score=confidence
                    )
                    sources.append(source)
                    
            except Exception as e:
                logger.warning(f"[DISCOVERY] Error parsing search result: {e}")
        
        return sources
    
    def _score_source(self, url: str, title: str, description: str, query: str) -> float:
        """Score a source based on relevance to affiliate marketing"""
        score = 0.0
        text = f"{url} {title} {description}".lower()
        
        # High-value keywords
        high_value_keywords = [
            'affiliate', 'cpa', 'performance', 'network', 'offers', 'marketplace',
            'commission', 'payout', 'advertiser', 'publisher', 'conversion'
        ]
        
        # Medium-value keywords
        medium_value_keywords = [
            'marketing', 'advertising', 'promotion', 'campaign', 'lead',
            'revenue', 'monetize', 'traffic', 'click', 'impression'
        ]
        
        # Negative keywords (reduce score)
        negative_keywords = [
            'blog', 'tutorial', 'course', 'guide', 'news', 'article',
            'wikipedia', 'definition', 'what is', 'how to'
        ]
        
        # Score based on keyword presence
        for keyword in high_value_keywords:
            if keyword in text:
                score += 0.2
        
        for keyword in medium_value_keywords:
            if keyword in text:
                score += 0.1
        
        for keyword in negative_keywords:
            if keyword in text:
                score -= 0.15
        
        # Bonus for known affiliate domains
        known_domains = [
            'clickbank', 'commission', 'shareasale', 'cj.com', 'impact',
            'partnerize', 'awin', 'rakuten', 'maxbounty', 'clickfunnels'
        ]
        
        for domain in known_domains:
            if domain in url.lower():
                score += 0.3
        
        return min(max(score, 0.0), 1.0)
    
    def _classify_source_type(self, url: str, title: str, description: str) -> str:
        """Classify the type of affiliate source"""
        text = f"{url} {title} {description}".lower()
        
        if any(word in text for word in ['marketplace', 'directory', 'list']):
            return 'marketplace'
        elif any(word in text for word in ['network', 'cpa', 'affiliate program']):
            return 'network'
        elif any(word in text for word in ['forum', 'community', 'discussion']):
            return 'forum'
        else:
            return 'directory'
    
    def _deduplicate_sources(self, sources: List[DiscoveredSource]) -> List[DiscoveredSource]:
        """Remove duplicate sources"""
        seen_urls = set()
        unique_sources = []
        
        for source in sources:
            # Normalize URL for deduplication
            normalized_url = urlparse(source.url).netloc.lower()
            
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_sources.append(source)
        
        return unique_sources

class OfferPatternDetector:
    """Detects patterns in offer listings on web pages"""
    
    OFFER_PATTERNS = [
        # Common offer listing patterns
        r'(?i)payout[:\s]*\$?(\d+(?:\.\d{2})?)',
        r'(?i)commission[:\s]*\$?(\d+(?:\.\d{2})?)',
        r'(?i)cpa[:\s]*\$?(\d+(?:\.\d{2})?)',
        r'(?i)epc[:\s]*\$?(\d+(?:\.\d{2})?)',
        r'(?i)conversion rate[:\s]*(\d+(?:\.\d+)?%)',
    ]
    
    def __init__(self):
        self.offer_selectors = [
            '.offer', '.listing', '.campaign', '.product',
            '[class*="offer"]', '[class*="listing"]', '[class*="campaign"]',
            'tr', 'li', '.row', '.item'
        ]
    
    async def detect_offers(self, html: str, url: str) -> Tuple[List[DiscoveredOffer], Dict[str, Any]]:
        """Detect offers and extract parsing template"""
        soup = BeautifulSoup(html, 'html.parser')
        offers = []
        template = {}
        
        # Try different selectors to find offer containers
        offer_containers = []
        
        for selector in self.offer_selectors:
            containers = soup.select(selector)
            if len(containers) > 3:  # Likely contains multiple offers
                offer_containers = containers
                template['container_selector'] = selector
                break
        
        if not offer_containers:
            return offers, template
        
        # Analyze first few containers to build template
        sample_containers = offer_containers[:5]
        template = self._build_parsing_template(sample_containers)
        
        # Extract offers using the template
        for container in offer_containers[:50]:  # Limit to 50 offers
            try:
                offer = self._extract_offer_from_container(container, url, template)
                if offer and offer.title:
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"[DISCOVERY] Error extracting offer: {e}")
        
        return offers, template
    
    def _build_parsing_template(self, containers: List) -> Dict[str, Any]:
        """Build a parsing template from sample containers"""
        template = {
            'title_selectors': [],
            'url_selectors': [],
            'payout_selectors': [],
            'description_selectors': [],
            'category_selectors': []
        }
        
        # Analyze containers to find common patterns
        for container in containers:
            # Find potential title elements
            title_candidates = container.select('h1, h2, h3, h4, h5, h6, .title, .name, a[href]')
            for candidate in title_candidates:
                selector = self._get_element_selector(candidate)
                if selector and selector not in template['title_selectors']:
                    template['title_selectors'].append(selector)
            
            # Find potential URL elements
            url_candidates = container.select('a[href]')
            for candidate in url_candidates:
                selector = self._get_element_selector(candidate)
                if selector and selector not in template['url_selectors']:
                    template['url_selectors'].append(selector)
            
            # Find potential payout elements
            payout_candidates = container.select('*')
            for candidate in payout_candidates:
                text = candidate.get_text(strip=True)
                if re.search(r'\$\d+|\d+\.\d{2}|payout|commission|cpa', text, re.I):
                    selector = self._get_element_selector(candidate)
                    if selector and selector not in template['payout_selectors']:
                        template['payout_selectors'].append(selector)
        
        return template
    
    def _get_element_selector(self, element) -> str:
        """Generate a CSS selector for an element"""
        if not element:
            return ""
        
        # Try class-based selector first
        if element.get('class'):
            classes = ' '.join(element['class'])
            return f".{classes.replace(' ', '.')}"
        
        # Fall back to tag name
        return element.name
    
    def _extract_offer_from_container(self, container, source_url: str, template: Dict[str, Any]) -> Optional[DiscoveredOffer]:
        """Extract an offer from a container using the template"""
        title = ""
        url = ""
        payout = ""
        description = ""
        
        # Extract title
        for selector in template.get('title_selectors', []):
            element = container.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                break
        
        # Extract URL
        for selector in template.get('url_selectors', []):
            element = container.select_one(selector)
            if element and element.get('href'):
                url = urljoin(source_url, element['href'])
                break
        
        # Extract payout
        for selector in template.get('payout_selectors', []):
            element = container.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                payout_match = re.search(r'\$?(\d+(?:\.\d{2})?)', text)
                if payout_match:
                    payout = payout_match.group(1)
                    break
        
        # Extract description
        description_elem = container.select_one('p, .description, .desc')
        if description_elem:
            description = description_elem.get_text(strip=True)[:200]
        
        if not title:
            return None
        
        # Score the offer
        confidence = self._score_offer(title, description, payout)
        
        return DiscoveredOffer(
            title=title,
            url=url or source_url,
            source_url=source_url,
            payout=payout,
            description=description,
            confidence_score=confidence,
            raw_data={
                'container_html': str(container)[:1000]  # Store sample HTML
            }
        )
    
    def _score_offer(self, title: str, description: str, payout: str) -> float:
        """Score an offer based on quality indicators"""
        score = 0.5  # Base score
        
        text = f"{title} {description}".lower()
        
        # Positive indicators
        if payout and re.search(r'\d+', payout):
            score += 0.2
        
        if any(word in text for word in ['high converting', 'top offer', 'exclusive', 'premium']):
            score += 0.15
        
        if len(title) > 10 and len(title) < 100:
            score += 0.1
        
        # Negative indicators
        if any(word in text for word in ['test', 'demo', 'sample', 'placeholder']):
            score -= 0.2
        
        return min(max(score, 0.0), 1.0)

class DiscoveryDatabase:
    """Database for storing discovery results"""
    
    def __init__(self, db_path: str = "discovery.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the discovery database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovered_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                source_type TEXT,
                confidence_score REAL,
                status TEXT DEFAULT 'discovered',
                offers_count INTEGER DEFAULT 0,
                parsing_template TEXT,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_scraped TIMESTAMP
            )
        ''')
        
        # Offers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovered_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT,
                source_url TEXT,
                payout TEXT,
                description TEXT,
                category TEXT,
                vertical TEXT,
                geo TEXT,
                network TEXT,
                confidence_score REAL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data TEXT,
                imported BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Discovery sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovery_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status TEXT DEFAULT 'running',
                sources_found INTEGER DEFAULT 0,
                offers_found INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                logs TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_source(self, source: DiscoveredSource) -> int:
        """Save a discovered source"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO discovered_sources 
                (url, title, description, source_type, confidence_score, status, 
                 offers_count, parsing_template, discovered_at, last_scraped)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                source.url, source.title, source.description, source.source_type,
                source.confidence_score, source.status, source.offers_count,
                json.dumps(source.parsing_template) if source.parsing_template else None,
                source.discovered_at, source.last_scraped
            ))
            
            source_id = cursor.lastrowid
            conn.commit()
            return source_id
            
        except Exception as e:
            logger.error(f"[DISCOVERY] Error saving source: {e}")
            return 0
        finally:
            conn.close()
    
    def save_offers(self, offers: List[DiscoveredOffer]) -> int:
        """Save discovered offers"""
        if not offers:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        
        try:
            for offer in offers:
                cursor.execute('''
                    INSERT OR IGNORE INTO discovered_offers 
                    (title, url, source_url, payout, description, category, vertical, 
                     geo, network, confidence_score, discovered_at, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    offer.title, offer.url, offer.source_url, offer.payout,
                    offer.description, offer.category, offer.vertical, offer.geo,
                    offer.network, offer.confidence_score, offer.discovered_at,
                    json.dumps(offer.raw_data) if offer.raw_data else None
                ))
                
                if cursor.rowcount > 0:
                    saved_count += 1
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"[DISCOVERY] Error saving offers: {e}")
        finally:
            conn.close()
        
        return saved_count
    
    def get_recent_sources(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recently discovered sources"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM discovered_sources 
            ORDER BY discovered_at DESC 
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        sources = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return sources
    
    def get_recent_offers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recently discovered offers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM discovered_offers 
            WHERE imported = FALSE
            ORDER BY confidence_score DESC, discovered_at DESC 
            LIMIT ?
        ''', (limit,))
        
        columns = [desc[0] for desc in cursor.description]
        offers = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return offers

class DiscoveryScraper:
    """Main Discovery Scraper class"""
    
    def __init__(self):
        self.db = DiscoveryDatabase()
        self.scanner = None
        self.detector = OfferPatternDetector()
        self.session = None
        self.is_running = False
        self.current_session_id = None
        self.logs = []
    
    async def start_discovery(self) -> Dict[str, Any]:
        """Start the discovery process"""
        if self.is_running:
            return {"success": False, "message": "Discovery already running"}
        
        self.is_running = True
        self.logs = []
        
        try:
            # Create session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            self.scanner = SearchEngineScanner(self.session)
            
            # Start discovery session in database
            self.current_session_id = self._start_session()
            
            self._log("🚀 Starting discovery process...")
            
            # Phase 1: Search engine scanning
            self._log("📡 Phase 1: Scanning search engines...")
            sources = await self.scanner.scan_search_engines()
            
            self._log(f"✅ Found {len(sources)} potential sources")
            
            # Save sources to database
            sources_saved = 0
            for source in sources:
                if self.db.save_source(source):
                    sources_saved += 1
            
            self._log(f"💾 Saved {sources_saved} new sources")
            
            # Phase 2: Crawl promising sources
            self._log("🕷️ Phase 2: Crawling promising sources...")
            total_offers = 0
            
            high_confidence_sources = [s for s in sources if s.confidence_score > 0.6]
            
            for source in high_confidence_sources[:10]:  # Limit to top 10
                try:
                    self._log(f"🔍 Crawling: {source.title}")
                    offers = await self._crawl_source(source)
                    
                    if offers:
                        saved_offers = self.db.save_offers(offers)
                        total_offers += saved_offers
                        self._log(f"  📦 Found {len(offers)} offers, saved {saved_offers}")
                        
                        # Update source with offers count
                        source.offers_count = len(offers)
                        source.status = 'scraped'
                        source.last_scraped = datetime.now()
                        self.db.save_source(source)
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    self._log(f"  ❌ Error crawling {source.url}: {e}")
                    source.status = 'failed'
                    self.db.save_source(source)
            
            self._log(f"🎯 Discovery completed! Total offers found: {total_offers}")
            
            # Complete session
            self._complete_session(len(sources), total_offers, 0)
            
            return {
                "success": True,
                "message": "Discovery completed successfully",
                "sources_found": len(sources),
                "offers_found": total_offers,
                "logs": self.logs
            }
            
        except Exception as e:
            self._log(f"❌ Discovery failed: {e}")
            logger.error(f"[DISCOVERY] Discovery failed: {e}", exc_info=True)
            
            if self.current_session_id:
                self._complete_session(0, 0, 1)
            
            return {
                "success": False,
                "message": f"Discovery failed: {str(e)}",
                "logs": self.logs
            }
            
        finally:
            self.is_running = False
            if self.session:
                await self.session.close()
    
    async def _crawl_source(self, source: DiscoveredSource) -> List[DiscoveredOffer]:
        """Crawl a specific source for offers"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(source.url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    offers, template = await self.detector.detect_offers(html, source.url)
                    
                    # Save the parsing template
                    source.parsing_template = template
                    
                    return offers
                else:
                    self._log(f"  ⚠️ HTTP {response.status} for {source.url}")
                    
        except Exception as e:
            logger.warning(f"[DISCOVERY] Error crawling {source.url}: {e}")
        
        return []
    
    def _start_session(self) -> int:
        """Start a discovery session"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO discovery_sessions (started_at, status)
            VALUES (?, ?)
        ''', (datetime.now(), 'running'))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    def _complete_session(self, sources_found: int, offers_found: int, errors_count: int):
        """Complete a discovery session"""
        if not self.current_session_id:
            return
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE discovery_sessions 
            SET completed_at = ?, status = ?, sources_found = ?, 
                offers_found = ?, errors_count = ?, logs = ?
            WHERE id = ?
        ''', (
            datetime.now(), 'completed', sources_found, offers_found, 
            errors_count, '\n'.join(self.logs), self.current_session_id
        ))
        
        conn.commit()
        conn.close()
    
    def _log(self, message: str):
        """Add a log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        logger.info(f"[DISCOVERY] {message}")
        print(log_entry)  # Also print to console
    
    def get_status(self) -> Dict[str, Any]:
        """Get current discovery status"""
        return {
            "is_running": self.is_running,
            "current_session_id": self.current_session_id,
            "logs": self.logs[-20:] if self.logs else [],  # Last 20 logs
            "recent_sources": self.db.get_recent_sources(10),
            "recent_offers": self.db.get_recent_offers(20)
        }
    
    def get_recent_findings(self) -> Dict[str, Any]:
        """Get recent discovery findings"""
        return {
            "sources": self.db.get_recent_sources(50),
            "offers": self.db.get_recent_offers(100)
        }
