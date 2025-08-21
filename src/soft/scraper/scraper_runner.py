"""
Scraper Runner Module for SmartLinks Autopilot
Executes external Python scrapers in isolated subprocesses.
"""

import os
import json
import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import signal
import sys

logger = logging.getLogger(__name__)

class ScraperRunner:
    """Executes external Python scrapers safely in subprocesses."""
    
    def __init__(self, external_scrapers_path: str = None):
        if external_scrapers_path is None:
            # Default to external_scrapers in project root
            project_root = Path(__file__).parent.parent.parent.parent
            self.external_scrapers_path = project_root / "external_scrapers"
        else:
            self.external_scrapers_path = Path(external_scrapers_path)
        
        logger.info(f"ScraperRunner initialized with path: {self.external_scrapers_path}")
    
    async def run_scraper(self, repo_name: str, params: Dict[str, Any] = None, timeout: int = 300) -> Dict[str, Any]:
        """
        Run a scraper in an isolated subprocess.
        
        Args:
            repo_name: Name of the scraper repository
            params: Parameters to pass to the scraper
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        params = params or {}
        
        try:
            scraper_dir = self.external_scrapers_path / repo_name
            if not scraper_dir.exists():
                raise ValueError(f"Scraper directory not found: {repo_name}")
            
            # Find entry point
            entry_point = self._find_entry_point(scraper_dir)
            if not entry_point:
                raise ValueError(f"No valid entry point found for scraper: {repo_name}")
            
            # Prepare execution environment
            execution_result = await self._execute_scraper(scraper_dir, entry_point, params, timeout)
            
            execution_time = time.time() - start_time
            
            # Parse results
            offers = self._parse_scraper_output(execution_result["stdout"], execution_result["stderr"])
            
            return {
                "success": execution_result["returncode"] == 0,
                "repo": repo_name,
                "offers": offers,
                "count": len(offers),
                "message": execution_result["message"],
                "logs": execution_result["logs"],
                "execution_time": execution_time,
                "returncode": execution_result["returncode"]
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error running scraper {repo_name}: {e}")
            return {
                "success": False,
                "repo": repo_name,
                "offers": [],
                "count": 0,
                "message": f"Error executing scraper: {str(e)}",
                "logs": [f"ERROR: {str(e)}"],
                "execution_time": execution_time,
                "returncode": -1
            }
    
    def _find_entry_point(self, scraper_dir: Path) -> Optional[str]:
        """Find the entry point for a scraper."""
        entry_points = [
            "main.py",
            "scraper.py",
            "run.py",
            "__main__.py"
        ]
        
        for ep in entry_points:
            if (scraper_dir / ep).exists():
                return ep
        
        # Check for Python module structure
        if (scraper_dir / "__init__.py").exists():
            main_files = list(scraper_dir.glob("*/__main__.py"))
            if main_files:
                module_dir = main_files[0].parent
                return f"{module_dir.name}/__main__.py"
        
        return None
    
    async def _execute_scraper(self, scraper_dir: Path, entry_point: str, params: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute the scraper subprocess."""
        logs = []
        
        try:
            # Create temporary files for communication
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as params_file:
                json.dump(params, params_file)
                params_file_path = params_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as output_file:
                output_file_path = output_file.name
            
            # Prepare command
            entry_path = scraper_dir / entry_point
            
            # Create wrapper script to handle parameters and output
            wrapper_script = self._create_wrapper_script(entry_path, params_file_path, output_file_path)
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as wrapper_file:
                wrapper_file.write(wrapper_script)
                wrapper_file_path = wrapper_file.name
            
            # Execute the wrapper script
            cmd = [sys.executable, wrapper_file_path]
            
            logs.append(f"Executing: {' '.join(cmd)}")
            logs.append(f"Working directory: {scraper_dir}")
            logs.append(f"Parameters: {params}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(scraper_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._prepare_environment()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                
                stdout_text = stdout.decode('utf-8', errors='ignore') if stdout else ""
                stderr_text = stderr.decode('utf-8', errors='ignore') if stderr else ""
                
                # Try to read structured output
                structured_output = None
                try:
                    if os.path.exists(output_file_path):
                        with open(output_file_path, 'r') as f:
                            structured_output = json.load(f)
                except Exception as e:
                    logs.append(f"Could not read structured output: {e}")
                
                logs.extend([
                    f"Process completed with return code: {process.returncode}",
                    f"Stdout length: {len(stdout_text)} chars",
                    f"Stderr length: {len(stderr_text)} chars"
                ])
                
                if stderr_text:
                    logs.append(f"Stderr: {stderr_text[:500]}...")
                
                message = "Scraper executed successfully" if process.returncode == 0 else f"Scraper failed with code {process.returncode}"
                
                return {
                    "returncode": process.returncode,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "structured_output": structured_output,
                    "message": message,
                    "logs": logs
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                logs.append(f"Process killed due to timeout ({timeout}s)")
                return {
                    "returncode": -1,
                    "stdout": "",
                    "stderr": f"Process timeout after {timeout} seconds",
                    "structured_output": None,
                    "message": f"Scraper timed out after {timeout} seconds",
                    "logs": logs
                }
                
        except Exception as e:
            logs.append(f"Execution error: {str(e)}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "structured_output": None,
                "message": f"Execution error: {str(e)}",
                "logs": logs
            }
        finally:
            # Cleanup temporary files
            for temp_file in [params_file_path, output_file_path, wrapper_file_path]:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception:
                    pass
    
    def _create_wrapper_script(self, entry_path: Path, params_file: str, output_file: str) -> str:
        """Create a wrapper script to execute the scraper with parameters."""
        return f'''
import sys
import json
import os
import traceback
from pathlib import Path

# Add scraper directory to path
scraper_dir = Path("{entry_path.parent}")
sys.path.insert(0, str(scraper_dir))

def main():
    try:
        # Load parameters
        params = {{}}
        try:
            with open("{params_file}", "r") as f:
                params = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load parameters: {{e}}")
        
        # Set parameters as environment variables and sys.argv
        for key, value in params.items():
            os.environ[f"SCRAPER_{{key.upper()}}"] = str(value)
        
        # Prepare sys.argv with parameters
        original_argv = sys.argv[:]
        sys.argv = ["{entry_path.name}"]
        for key, value in params.items():
            sys.argv.extend([f"--{{key}}", str(value)])
        
        # Import and execute the scraper
        print(f"Executing scraper: {{sys.argv}}")
        
        # Try different execution methods
        entry_file = Path("{entry_path}")
        
        if entry_file.name == "__main__.py":
            # Module execution
            module_name = entry_file.parent.name
            import importlib
            module = importlib.import_module(module_name)
            if hasattr(module, 'main'):
                result = module.main()
            else:
                # Execute as script
                with open(entry_file, 'r') as f:
                    code = f.read()
                exec(code, {{"__name__": "__main__"}})
        else:
            # Direct script execution
            with open(entry_file, 'r') as f:
                code = f.read()
            
            # Create execution environment
            exec_globals = {{
                "__name__": "__main__",
                "__file__": str(entry_file),
                "params": params
            }}
            
            exec(code, exec_globals)
        
        # Try to capture any output files
        output_data = {{
            "success": True,
            "offers": [],
            "message": "Scraper executed successfully"
        }}
        
        # Look for common output files
        output_files = ["results.json", "output.json", "data.json", "offers.json"]
        results_dirs = ["results", "output", "data"]
        
        for output_file_name in output_files:
            if (scraper_dir / output_file_name).exists():
                try:
                    with open(scraper_dir / output_file_name, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            output_data["offers"] = data
                        elif isinstance(data, dict) and "offers" in data:
                            output_data["offers"] = data["offers"]
                        elif isinstance(data, dict) and "results" in data:
                            output_data["offers"] = data["results"]
                        break
                except Exception as e:
                    print(f"Could not parse output file {{output_file_name}}: {{e}}")
        
        # Look in results directories
        for results_dir in results_dirs:
            results_path = scraper_dir / results_dir
            if results_path.exists() and results_path.is_dir():
                for json_file in results_path.glob("*.json"):
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list) and len(data) > len(output_data["offers"]):
                                output_data["offers"] = data
                            elif isinstance(data, dict):
                                if "offers" in data and len(data["offers"]) > len(output_data["offers"]):
                                    output_data["offers"] = data["offers"]
                                elif "results" in data and len(data["results"]) > len(output_data["offers"]):
                                    output_data["offers"] = data["results"]
                    except Exception as e:
                        print(f"Could not parse result file {{json_file}}: {{e}}")
        
        # Save structured output
        with open("{output_file}", "w") as f:
            json.dump(output_data, f)
        
        print(f"Scraper completed successfully. Found {{len(output_data['offers'])}} offers.")
        
    except Exception as e:
        error_data = {{
            "success": False,
            "offers": [],
            "message": f"Scraper execution failed: {{str(e)}}",
            "error": str(e),
            "traceback": traceback.format_exc()
        }}
        
        try:
            with open("{output_file}", "w") as f:
                json.dump(error_data, f)
        except Exception:
            pass
        
        print(f"Scraper failed: {{e}}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for scraper execution."""
        env = os.environ.copy()
        
        # Add common Python paths
        python_path = env.get('PYTHONPATH', '')
        if python_path:
            env['PYTHONPATH'] = f"{self.external_scrapers_path}:{python_path}"
        else:
            env['PYTHONPATH'] = str(self.external_scrapers_path)
        
        # Disable buffering for real-time output
        env['PYTHONUNBUFFERED'] = '1'
        
        return env
    
    def _parse_scraper_output(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Parse scraper output to extract offers."""
        offers = []
        
        try:
            # Try to parse JSON from stdout
            lines = stdout.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('{') or line.startswith('['):
                    try:
                        data = json.loads(line)
                        if isinstance(data, list):
                            offers.extend(data)
                        elif isinstance(data, dict):
                            if 'offers' in data:
                                offers.extend(data['offers'])
                            elif 'results' in data:
                                offers.extend(data['results'])
                            else:
                                offers.append(data)
                    except json.JSONDecodeError:
                        continue
            
            # Normalize offer format
            normalized_offers = []
            for offer in offers:
                if isinstance(offer, dict):
                    normalized_offer = self._normalize_offer(offer)
                    if normalized_offer:
                        normalized_offers.append(normalized_offer)
            
            return normalized_offers
            
        except Exception as e:
            logger.error(f"Error parsing scraper output: {e}")
            return []
    
    def _normalize_offer(self, offer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize offer data to standard format."""
        try:
            # Map common field variations to standard names
            field_mappings = {
                'title': ['title', 'name', 'offer_name', 'job_title', 'product_name'],
                'url': ['url', 'link', 'href', 'job_url', 'product_url', 'offer_url'],
                'description': ['description', 'desc', 'summary', 'job_description'],
                'payout': ['payout', 'salary', 'price', 'cost', 'amount', 'pay'],
                'category': ['category', 'type', 'job_type', 'product_type'],
                'company': ['company', 'employer', 'brand', 'network'],
                'location': ['location', 'address', 'city', 'country'],
                'date': ['date', 'posted_date', 'created_date', 'timestamp']
            }
            
            normalized = {}
            
            for standard_field, variations in field_mappings.items():
                for variation in variations:
                    if variation in offer:
                        normalized[standard_field] = offer[variation]
                        break
            
            # Ensure we have at least a title or name
            if not normalized.get('title'):
                return None
            
            # Add original data for reference
            normalized['original_data'] = offer
            normalized['source'] = 'external_scraper'
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error normalizing offer: {e}")
            return None
