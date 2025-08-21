"""
Scraper Discovery Module for SmartLinks Autopilot
Automatically discovers and analyzes Python scrapers in external_scrapers directory.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import importlib.util
import sys
import subprocess

logger = logging.getLogger(__name__)

class ScraperDiscovery:
    """Discovers and analyzes external Python scrapers."""
    
    def __init__(self, external_scrapers_path: str = None):
        if external_scrapers_path is None:
            # Default to external_scrapers in project root
            project_root = Path(__file__).parent.parent.parent.parent
            self.external_scrapers_path = project_root / "external_scrapers"
        else:
            self.external_scrapers_path = Path(external_scrapers_path)
        
        logger.info(f"ScraperDiscovery initialized with path: {self.external_scrapers_path}")
    
    def discover_scrapers(self) -> List[Dict[str, Any]]:
        """
        Discover all available scrapers in external_scrapers directory.
        
        Returns:
            List of scraper information dictionaries
        """
        scrapers = []
        
        if not self.external_scrapers_path.exists():
            logger.warning(f"External scrapers directory not found: {self.external_scrapers_path}")
            return scrapers
        
        for item in self.external_scrapers_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                scraper_info = self._analyze_scraper_directory(item)
                if scraper_info:
                    scrapers.append(scraper_info)
        
        logger.info(f"Discovered {len(scrapers)} scrapers")
        return scrapers
    
    def _analyze_scraper_directory(self, scraper_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze a scraper directory to extract information.
        
        Args:
            scraper_dir: Path to scraper directory
            
        Returns:
            Scraper information dictionary or None if invalid
        """
        try:
            scraper_name = scraper_dir.name
            logger.debug(f"Analyzing scraper directory: {scraper_name}")
            
            # Look for entry points in order of preference
            entry_points = [
                "main.py",
                "scraper.py", 
                "run.py",
                "__main__.py"
            ]
            
            entry_point = None
            for ep in entry_points:
                if (scraper_dir / ep).exists():
                    entry_point = ep
                    break
            
            # Check for Python module structure
            if not entry_point and (scraper_dir / "__init__.py").exists():
                # This is a Python package, check for __main__.py
                main_files = list(scraper_dir.glob("*/__main__.py"))
                if main_files:
                    # Use the module name as entry point
                    module_dir = main_files[0].parent
                    entry_point = f"{module_dir.name}/__main__.py"
            
            if not entry_point:
                logger.warning(f"No valid entry point found for scraper: {scraper_name}")
                return None
            
            # Extract metadata
            description = self._extract_description(scraper_dir)
            requirements = self._extract_requirements(scraper_dir)
            params_schema = self._extract_params_schema(scraper_dir)
            status = self._check_scraper_status(scraper_dir, entry_point)
            
            scraper_info = {
                "name": scraper_name,
                "description": description,
                "entry_point": entry_point,
                "requirements": requirements,
                "params_schema": params_schema,
                "status": status,
                "path": str(scraper_dir)
            }
            
            logger.debug(f"Scraper analysis complete: {scraper_name} -> {status}")
            return scraper_info
            
        except Exception as e:
            logger.error(f"Error analyzing scraper directory {scraper_dir}: {e}")
            return None
    
    def _extract_description(self, scraper_dir: Path) -> Optional[str]:
        """Extract description from README or docstring."""
        try:
            # Try README files first
            readme_files = ["README.md", "readme.md", "README.txt", "readme.txt"]
            for readme_file in readme_files:
                readme_path = scraper_dir / readme_file
                if readme_path.exists():
                    content = readme_path.read_text(encoding='utf-8', errors='ignore')
                    # Extract first line or first paragraph
                    lines = content.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            return line[:200]  # Limit description length
                    
            # If no README, try to extract from main file docstring
            entry_points = ["main.py", "scraper.py", "run.py"]
            for ep in entry_points:
                entry_path = scraper_dir / ep
                if entry_path.exists():
                    try:
                        content = entry_path.read_text(encoding='utf-8', errors='ignore')
                        lines = content.split('\n')
                        in_docstring = False
                        docstring_lines = []
                        
                        for line in lines[:20]:  # Check first 20 lines
                            line = line.strip()
                            if line.startswith('"""') or line.startswith("'''"):
                                if in_docstring:
                                    break
                                in_docstring = True
                                docstring_lines.append(line[3:])
                            elif in_docstring:
                                if line.endswith('"""') or line.endswith("'''"):
                                    docstring_lines.append(line[:-3])
                                    break
                                docstring_lines.append(line)
                        
                        if docstring_lines:
                            desc = ' '.join(docstring_lines).strip()
                            return desc[:200] if desc else None
                    except Exception:
                        continue
                        
        except Exception as e:
            logger.debug(f"Could not extract description for {scraper_dir.name}: {e}")
        
        return None
    
    def _extract_requirements(self, scraper_dir: Path) -> List[str]:
        """Extract requirements from requirements.txt or setup.py."""
        requirements = []
        
        try:
            # Check requirements.txt
            req_file = scraper_dir / "requirements.txt"
            if req_file.exists():
                content = req_file.read_text(encoding='utf-8', errors='ignore')
                for line in content.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        requirements.append(line)
            
            # Check pyproject.toml for dependencies
            pyproject_file = scraper_dir / "pyproject.toml"
            if pyproject_file.exists() and not requirements:
                try:
                    import toml
                    content = toml.load(pyproject_file)
                    deps = content.get('project', {}).get('dependencies', [])
                    requirements.extend(deps)
                except ImportError:
                    pass  # toml not available
                except Exception as e:
                    logger.debug(f"Error parsing pyproject.toml: {e}")
                    
        except Exception as e:
            logger.debug(f"Could not extract requirements for {scraper_dir.name}: {e}")
        
        return requirements
    
    def _extract_params_schema(self, scraper_dir: Path) -> Dict[str, Any]:
        """Extract parameter schema if available."""
        try:
            # Look for schema.json
            schema_file = scraper_dir / "schema.json"
            if schema_file.exists():
                return json.loads(schema_file.read_text())
            
            # Look for config.json or similar
            config_files = ["config.json", "params.json", "settings.json"]
            for config_file in config_files:
                config_path = scraper_dir / config_file
                if config_path.exists():
                    try:
                        config_data = json.loads(config_path.read_text())
                        # Try to infer schema from config
                        if isinstance(config_data, dict):
                            return self._infer_schema_from_config(config_data)
                    except Exception:
                        continue
                        
        except Exception as e:
            logger.debug(f"Could not extract params schema for {scraper_dir.name}: {e}")
        
        # Default schema for common parameters
        return {
            "type": "object",
            "properties": {
                "pages": {
                    "type": "integer",
                    "description": "Number of pages to scrape",
                    "default": 1,
                    "minimum": 1,
                    "maximum": 10
                },
                "keywords": {
                    "type": "string",
                    "description": "Search keywords",
                    "default": ""
                },
                "limit": {
                    "type": "integer", 
                    "description": "Maximum number of results",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000
                }
            }
        }
    
    def _infer_schema_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Infer JSON schema from config dictionary."""
        properties = {}
        
        for key, value in config.items():
            if isinstance(value, int):
                properties[key] = {"type": "integer", "default": value}
            elif isinstance(value, float):
                properties[key] = {"type": "number", "default": value}
            elif isinstance(value, str):
                properties[key] = {"type": "string", "default": value}
            elif isinstance(value, bool):
                properties[key] = {"type": "boolean", "default": value}
            elif isinstance(value, list):
                properties[key] = {"type": "array", "default": value}
            elif isinstance(value, dict):
                properties[key] = {"type": "object", "default": value}
        
        return {
            "type": "object",
            "properties": properties
        }
    
    def _check_scraper_status(self, scraper_dir: Path, entry_point: str) -> str:
        """Check if scraper can be executed."""
        try:
            entry_path = scraper_dir / entry_point
            if not entry_path.exists():
                return "error"
            
            # Check if Python file is valid
            try:
                with open(entry_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Basic syntax check
                    compile(content, str(entry_path), 'exec')
            except SyntaxError:
                return "error"
            except Exception:
                pass  # Other errors are OK for now
            
            # Check basic requirements
            requirements = self._extract_requirements(scraper_dir)
            missing_deps = []
            
            for req in requirements[:5]:  # Check first 5 requirements only
                try:
                    # Extract package name (remove version specifiers)
                    pkg_name = req.split('>=')[0].split('==')[0].split('<=')[0].split('>')[0].split('<')[0].split('!=')[0].strip()
                    if pkg_name:
                        __import__(pkg_name)
                except ImportError:
                    missing_deps.append(pkg_name)
                except Exception:
                    continue
            
            if missing_deps:
                return "missing_deps"
            
            return "available"
            
        except Exception as e:
            logger.debug(f"Error checking scraper status for {scraper_dir.name}: {e}")
            return "error"
    
    def get_scraper_info(self, scraper_name: str) -> Optional[Dict[str, Any]]:
        """Get information for a specific scraper."""
        scrapers = self.discover_scrapers()
        for scraper in scrapers:
            if scraper["name"] == scraper_name:
                return scraper
        return None
