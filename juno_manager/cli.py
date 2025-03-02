#!/usr/bin/env python3
"""
Command line interface for Juno Manager
"""
import sys
import argparse
from juno_manager.app import main

def run_cli():
    """
    Parse command line arguments and run the application
    """
    parser = argparse.ArgumentParser(
        description="Juno - JupyterLab Virtual Environment Manager",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--version", 
        action="store_true",
        help="Show version information and exit"
    )
    
    parser.add_argument(
        "--venv-dir",
        help="Set custom directory for virtual environments"
    )
    
    args = parser.parse_args()
    
    if args.version:
        from juno_manager import __version__
        print(f"Juno Manager version {__version__}")
        return 0
        
    # Import os only if we need it to set environment variables
    if args.venv_dir:
        import os
        os.environ["JUNO_VENV_DIR"] = args.venv_dir
        
    # Run the main application
    main()
    return 0

if __name__ == "__main__":
    sys.exit(run_cli())