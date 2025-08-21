"""Scraper for Offervault affiliate network."""

import requests
import logging
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import time

# Lazy import for BeautifulSoup to prevent module-level crash if bs4 isn't installed yet
_bs4_BeautifulSoup = None

def _get_beautifulsoup():
    global _bs4_BeautifulSoup
    if _bs4_BeautifulSoup is not None:
        return _bs4_BeautifulSoup
    try:
        from bs4 import BeautifulSoup as _BS
    except Exception as e:
        raise ImportError(
            "beautifulsoup4 is required for OffervaultScraper. Install with 'pip install beautifulsoup4==4.12.3'."
        ) from e
    _bs4_BeautifulSoup = _BS
    return _bs4_BeautifulSoup

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

class OffervaultScraper:
    """Scraper for Offervault affiliate network offers."""
    
    def __init__(self, base_url: str = "https://offervault.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
    
    def scrape_offers(self, pages: int = 2) -> List[Dict[str, Any]]:
        """
        Scrape affiliate offers from Offervault.
        
        Args:
            pages: Number of pages to scrape (default: 2)
            
        Returns:
            List of offer dictionaries with standardized fields
        """
        all_offers = []
        
        try:
            for page in range(1, pages + 1):
                logger.info(f"Scraping Offervault page {page}")
                
                # Construct URL for the page
                url = f"{self.base_url}/?page={page}"
                
                # Fetch page content
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse offers
                offers = self._parse_offers_page(response.text)
                all_offers.extend(offers)
                
                # Be respectful to the server
                time.sleep(1)
                
                logger.info(f"Found {len(offers)} offers on page {page}")
                
        except requests.exceptions.Timeout:
            logger.error("Timeout error while scraping Offervault")
            raise Exception("Timeout error while scraping Offervault")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while scraping Offervault: {e}")
            raise Exception(f"Request error while scraping Offervault: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scraping Offervault: {e}")
            raise Exception(f"Unexpected error scraping Offervault: {e}")
        
        logger.info(f"Total offers scraped: {len(all_offers)}")
        return all_offers
    
    def _parse_offers_page(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parse a single page of Offervault offers.
        
        Args:
            html_content: HTML content of the page
            
        Returns:
            List of parsed offer dictionaries
        """
        offers = []
        BeautifulSoup = _get_beautifulsoup()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find offer elements - this is a simplified example
        # The actual selectors would need to be adjusted based on Offervault's HTML structure
        offer_elements = soup.find_all('div', class_='offer-item')
        
        for element in offer_elements:
            try:
                offer = self._extract_offer_data(element)
                if offer:
                    offers.append(offer)
            except Exception as e:
                logger.warning(f"Error parsing individual offer: {e}")
                continue
        
        return offers
    
    def _extract_offer_data(self, element) -> Dict[str, Any]:
        """
        Extract data from a single offer element.
        
        Args:
            element: BeautifulSoup element containing offer data
            
        Returns:
            Dictionary with offer data
        """
        # This is a template - actual implementation would depend on Offervault's HTML structure
        # Here are the fields we want to extract:
        
        offer = {
            'name': '',           # Offer name/title
            'description': '',   # Offer description
            'payout': 0.0,       # Payout amount
            'payout_type': '',   # Payout type (CPA, CPL, etc.)
            'category': '',      # Offer category
            'preview_url': '',   # Landing page preview URL
            'tracking_url': '',  # Tracking URL template
            'network': 'offervault',  # Network name
            'status': 'active',  # Offer status
            'countries': [],     # Target countries
            'devices': [],       # Supported devices
            'conversion_flow': '', # Conversion flow description
            'epc': 0.0,          # Earnings per click
            'approval_rate': 0.0, # Approval rate percentage
            'conversion_time': '', # Average conversion time
            'restrictions': []   # Any restrictions
        }
        
        # Extract offer name
        name_element = element.find('h3', class_='offer-title')
        if name_element:
            offer['name'] = name_element.get_text(strip=True)
        
        # Extract description
        desc_element = element.find('p', class_='offer-description')
        if desc_element:
            offer['description'] = desc_element.get_text(strip=True)
        
        # Extract payout
        payout_element = element.find('span', class_='payout-amount')
        if payout_element:
            payout_text = payout_element.get_text(strip=True)
            # Extract numeric value from text like "$25.00 CPA"
            if '$' in payout_text:
                payout_value = payout_text.split('$')[1].split()[0]
                offer['payout'] = float(payout_value)
                offer['payout_type'] = payout_text.split()[-1] if payout_text.split() else 'CPA'
        
        # Extract category
        category_element = element.find('span', class_='offer-category')
        if category_element:
            offer['category'] = category_element.get_text(strip=True)
        
        # Extract preview URL
        preview_element = element.find('a', class_='preview-link')
        if preview_element and preview_element.get('href'):
            offer['preview_url'] = urljoin(self.base_url, preview_element.get('href'))
        
        # Extract tracking URL
        tracking_element = element.find('input', class_='tracking-url')
        if tracking_element and tracking_element.get('value'):
            offer['tracking_url'] = tracking_element.get('value')
        
        # Extract countries
        countries_element = element.find('span', class_='offer-countries')
        if countries_element:
            countries_text = countries_element.get_text(strip=True)
            offer['countries'] = [c.strip() for c in countries_text.split(',') if c.strip()]
        
        # Extract EPC
        epc_element = element.find('span', class_='epc-value')
        if epc_element:
            epc_text = epc_element.get_text(strip=True)
            if '$' in epc_text:
                epc_value = epc_text.split('$')[1]
                offer['epc'] = float(epc_value)
        
        # Extract approval rate
        approval_element = element.find('span', class_='approval-rate')
        if approval_element:
            approval_text = approval_element.get_text(strip=True)
            if '%' in approval_text:
                approval_value = approval_text.replace('%', '')
                offer['approval_rate'] = float(approval_value)
        
        return offer
