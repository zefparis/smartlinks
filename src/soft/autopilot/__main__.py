"""Main entry point for the autopilot module."""

from .runner import AlgorithmRunner
from ..dg.dependencies import get_db_session_factory

def main():
    """Initialize and start the autopilot runner."""
    print("Starting SmartLinks Autopilot...")
    
    # Initialize with database session factory
    runner = AlgorithmRunner(get_db_session_factory())
    
    # For now, just show that the runner is initialized
    print("Autopilot runner initialized successfully.")
    print("Algorithm runner is ready to load algorithms.")

if __name__ == "__main__":
    main()
