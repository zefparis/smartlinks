#!/usr/bin/env python3
"""
Script to bulk import affiliate offers from various networks into SmartLinks database.

This script fetches active offers from affiliate networks like MaxBounty, Mobidea, etc.
and imports them into the SmartLinks offers table via either SQL INSERT or backend API POST.

Features:
- Fetches offers from multiple affiliate networks
- Maps network offer fields to SmartLinks database schema
- Generates SQL INSERT statements or POST JSON requests
- Logs import success/failure for each offer
- Bonus: Checks if destination URLs are active (200 OK)
"""

import requests
import json
import sqlite3
import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
import urllib3

# Disable SSL warnings for networks that might have certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('affiliate_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# SmartLinks database path
SMARTLINKS_DB_PATH = 'smartlinks.db'

# Affiliate network configurations
AFFILIATE_NETWORKS = {
    'maxbounty': {
        'name': 'MaxBounty',
        'api_base_url': 'https://api.maxbounty.com',
        'offers_endpoint': '/offers',
        'auth_required': True,
        'auth_method': 'api_key_header',  # or 'api_key_param', 'oauth', etc.
        'api_key_header': 'X-API-Key',
        'partner_id_prefix': 'MB_'
    },
    'mobidea': {
        'name': 'Mobidea',
        'api_base_url': 'https://api.mobidea.com',
        'offers_endpoint': '/offers',
        'auth_required': True,
        'auth_method': 'api_key_header',
        'api_key_header': 'X-API-Key',
        'partner_id_prefix': 'MO_'
    },
    'performcb': {
        'name': 'Performcb (Clickbooth)',
        'api_base_url': 'https://api.performcb.com',
        'offers_endpoint': '/campaigns',
        'auth_required': True,
        'auth_method': 'api_key_header',
        'api_key_header': 'Authorization',
        'partner_id_prefix': 'PCB_'
    },
    'adcombo': {
        'name': 'AdCombo',
        'api_base_url': 'https://api.adcombo.com',
        'offers_endpoint': '/api/v2/offers',
        'auth_required': True,
        'auth_method': 'api_key_param',
        'api_key_param': 'api_key',
        'partner_id_prefix': 'AC_'
    }
}

class AffiliateOfferImporter:
    def __init__(self, db_path: str = SMARTLINKS_DB_PATH):
        self.db_path = db_path
        self.import_stats = {
            'total_offers': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'active_urls': 0,
            'inactive_urls': 0
        }
        
    def get_db_connection(self):
        """Create and return a database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def check_url_status(self, url: str) -> bool:
        """
        Check if a URL returns 200 OK status
        
        Args:
            url (str): The URL to check
            
        Returns:
            bool: True if URL is active, False otherwise
        """
        try:
            response = requests.get(url, timeout=10, verify=False)
            is_active = response.status_code == 200
            if is_active:
                self.import_stats['active_urls'] += 1
                logger.info(f"URL active: {url}")
            else:
                self.import_stats['inactive_urls'] += 1
                logger.warning(f"URL inactive ({response.status_code}): {url}")
            return is_active
        except Exception as e:
            self.import_stats['inactive_urls'] += 1
            logger.error(f"Failed to check URL {url}: {e}")
            return False

    def map_offer_fields(self, network_offer: Dict, network_name: str) -> Dict:
        """
        Map affiliate network offer fields to SmartLinks database schema
        
        Args:
            network_offer (Dict): Raw offer data from affiliate network
            network_name (str): Name of the affiliate network
            
        Returns:
            Dict: Mapped offer data compatible with SmartLinks schema
        """
        # Default mapping - should be customized per network
        mapped_offer = {
            'offer_id': f"{AFFILIATE_NETWORKS[network_name]['partner_id_prefix']}{network_offer.get('id', network_offer.get('offer_id', 'unknown'))}",
            'name': network_offer.get('title', network_offer.get('name', 'Untitled Offer')),
            'url': network_offer.get('url_destination', network_offer.get('url', network_offer.get('destination_url', ''))),
            'incent_ok': 1,  # Default value
            'cap_day': network_offer.get('cap_day', 10000),  # Default value
            'geo_allow': network_offer.get('geo', network_offer.get('country', 'ALL')),
            'status': network_offer.get('status', 'on'),
            'commission_rate': network_offer.get('commission_rate', network_offer.get('payout', 0.0)),
            'partner_id': network_offer.get('id', network_offer.get('offer_id', ''))
        }
        
        return mapped_offer

    def generate_sql_insert(self, offer: Dict) -> str:
        """
        Generate SQL INSERT statement for an offer
        
        Args:
            offer (Dict): Mapped offer data
            
        Returns:
            str: SQL INSERT statement
        """
        # Escape single quotes in string values
        name = offer['name'].replace("'", "''")
        url = offer['url'].replace("'", "''")
        geo_allow = offer['geo_allow'].replace("'", "''")
        status = offer['status'].replace("'", "''")
        
        sql = f"""
INSERT OR REPLACE INTO offers (offer_id, name, url, incent_ok, cap_day, geo_allow, status)
VALUES ('{offer['offer_id']}', '{name}', '{url}', {offer['incent_ok']}, {offer['cap_day']}, '{geo_allow}', '{status}');
"""
        return sql.strip()

    def import_offer_via_sql(self, offer: Dict) -> bool:
        """
        Import an offer directly via SQL INSERT
        
        Args:
            offer (Dict): Mapped offer data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            sql = self.generate_sql_insert(offer)
            cursor.execute(sql)
            conn.commit()
            
            logger.info(f"Successfully imported offer {offer['offer_id']} via SQL")
            return True
        except Exception as e:
            logger.error(f"Failed to import offer {offer['offer_id']} via SQL: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def import_offer_via_api(self, offer: Dict, api_url: str = "http://localhost:8000/api/offers") -> bool:
        """
        Import an offer via backend API POST request
        
        Args:
            offer (Dict): Mapped offer data
            api_url (str): SmartLinks backend API endpoint
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert to JSON compatible with backend
            api_offer = {
                'offer_id': offer['offer_id'],
                'name': offer['name'],
                'url': offer['url'],
                'incent_ok': offer['incent_ok'],
                'cap_day': offer['cap_day'],
                'geo_allow': offer['geo_allow'],
                'status': offer['status']
            }
            
            response = requests.post(api_url, json=api_offer, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully imported offer {offer['offer_id']} via API")
                return True
            else:
                logger.error(f"API import failed for offer {offer['offer_id']}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to import offer {offer['offer_id']} via API: {e}")
            return False

    def fetch_offers_from_network(self, network_name: str, api_key: Optional[str] = None) -> List[Dict]:
        """
        Fetch active offers from an affiliate network
        
        Args:
            network_name (str): Name of the affiliate network
            api_key (Optional[str]): API key for authentication
            
        Returns:
            List[Dict]: List of offers from the network
        """
        network_config = AFFILIATE_NETWORKS[network_name]
        url = urljoin(network_config['api_base_url'], network_config['offers_endpoint'])
        
        headers = {}
        params = {}
        
        # Handle authentication
        if network_config['auth_required']:
            if not api_key:
                logger.warning(f"No API key provided for {network_name}, skipping...")
                return []
                
            if network_config['auth_method'] == 'api_key_header':
                headers[network_config['api_key_header']] = api_key
            elif network_config['auth_method'] == 'api_key_param':
                params[network_config['api_key_param']] = api_key
        
        try:
            logger.info(f"Fetching offers from {network_name}...")
            response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
            
            if response.status_code == 200:
                offers = response.json()
                logger.info(f"Retrieved {len(offers)} offers from {network_name}")
                return offers
            else:
                logger.error(f"Failed to fetch offers from {network_name}: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error fetching offers from {network_name}: {e}")
            return []

    def import_offers_from_network(self, network_name: str, api_key: Optional[str] = None, 
                                 use_api: bool = False, check_urls: bool = True) -> None:
        """
        Import all offers from a specific affiliate network
        
        Args:
            network_name (str): Name of the affiliate network
            api_key (Optional[str]): API key for authentication
            use_api (bool): Whether to import via API or SQL
            check_urls (bool): Whether to verify destination URLs are active
        """
        offers = self.fetch_offers_from_network(network_name, api_key)
        
        if not offers:
            logger.warning(f"No offers retrieved from {network_name}")
            return
            
        for offer in offers:
            self.import_stats['total_offers'] += 1
            
            # Map fields to SmartLinks schema
            mapped_offer = self.map_offer_fields(offer, network_name)
            
            # Check URL status if requested
            if check_urls and mapped_offer['url']:
                url_active = self.check_url_status(mapped_offer['url'])
                if not url_active:
                    logger.warning(f"Skipping inactive offer: {mapped_offer['offer_id']}")
                    self.import_stats['failed_imports'] += 1
                    continue
            
            # Import via API or SQL
            success = False
            if use_api:
                success = self.import_offer_via_api(mapped_offer)
            else:
                success = self.import_offer_via_sql(mapped_offer)
            
            if success:
                self.import_stats['successful_imports'] += 1
            else:
                self.import_stats['failed_imports'] += 1
            
            # Add a small delay to avoid overwhelming the network
            time.sleep(0.1)

    def run_import(self, networks: List[str], api_keys: Dict[str, str], 
                  use_api: bool = False, check_urls: bool = True) -> None:
        """
        Run the import process for specified networks
        
        Args:
            networks (List[str]): List of network names to import from
            api_keys (Dict[str, str]): Dictionary of API keys for each network
            use_api (bool): Whether to import via API or SQL
            check_urls (bool): Whether to verify destination URLs are active
        """
        logger.info("Starting affiliate offer import process...")
        
        for network in networks:
            if network in AFFILIATE_NETWORKS:
                api_key = api_keys.get(network)
                self.import_offers_from_network(network, api_key, use_api, check_urls)
            else:
                logger.warning(f"Unknown network: {network}")
        
        # Log final statistics
        logger.info("Import process completed. Statistics:")
        logger.info(f"  Total offers processed: {self.import_stats['total_offers']}")
        logger.info(f"  Successful imports: {self.import_stats['successful_imports']}")
        logger.info(f"  Failed imports: {self.import_stats['failed_imports']}")
        if check_urls:
            logger.info(f"  Active URLs: {self.import_stats['active_urls']}")
            logger.info(f"  Inactive URLs: {self.import_stats['inactive_urls']}")

def main():
    """
    Main function to run the affiliate offer import
    
    Usage:
    - Modify the networks list to include desired affiliate networks
    - Add API keys in the api_keys dictionary
    - Set use_api=True to import via backend API, False to use SQL directly
    - Set check_urls=True to verify destination URLs are active
    """
    importer = AffiliateOfferImporter()
    
    # Specify which networks to import from
    networks_to_import = ['maxbounty', 'mobidea', 'performcb', 'adcombo']
    
    # Add your API keys here
    api_keys = {
        # 'maxbounty': 'your_maxbounty_api_key',
        # 'mobidea': 'your_mobidea_api_key',
        # 'performcb': 'your_performcb_api_key',
        # 'adcombo': 'your_adcombo_api_key'
    }
    
    # Import settings
    use_api = False  # Set to True to use backend API instead of direct SQL
    check_urls = True  # Set to False to skip URL validation
    
    importer.run_import(networks_to_import, api_keys, use_api, check_urls)

if __name__ == "__main__":
    main()
