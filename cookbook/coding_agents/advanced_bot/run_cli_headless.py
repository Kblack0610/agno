#!/usr/bin/env python3
"""
Headless CLI Runner

This script runs the CLI with a timeout to prevent hanging in interactive environments.
"""

import sys
import os
import signal
import argparse
import subprocess
import threading
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('headless_cli')

def run_cli_with_timeout(args, timeout=60):
    """
    Run the CLI command with a timeout.
    
    Args:
        args: CLI arguments
        timeout: Timeout in seconds
        
    Returns:
        Success status
    """
    # Construct command
    cmd = ["python3", "cli.py"] + args
    
    logger.info(f"Running CLI command: {' '.join(cmd)}")
    logger.info(f"Timeout set to {timeout} seconds")
    
    # Start process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )
    
    # Define output handling function
    def handle_output():
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                sys.stdout.write(line)
                sys.stdout.flush()
        
        # Handle any remaining output after process completes
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
    
    # Start output thread
    output_thread = threading.Thread(target=handle_output)
    output_thread.daemon = True
    output_thread.start()
    
    # Wait for process with timeout
    try:
        start_time = time.time()
        exit_code = process.wait(timeout=timeout)
        elapsed_time = time.time() - start_time
        
        logger.info(f"CLI process completed with exit code {exit_code} in {elapsed_time:.2f} seconds")
        
        # Get stderr if there was an error
        if exit_code != 0:
            stderr = process.stderr.read()
            logger.error(f"CLI process failed with stderr: {stderr}")
        
        return exit_code == 0
    
    except subprocess.TimeoutExpired:
        logger.warning(f"CLI process timed out after {timeout} seconds")
        
        # Send SIGTERM
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If still running after 5 seconds, send SIGKILL
            logger.warning("Process did not terminate gracefully, sending SIGKILL")
            process.kill()
        
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run the CLI with a timeout to prevent hanging'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,  # 5 minutes default
        help='Timeout in seconds'
    )
    
    # Capture all other arguments to pass to CLI
    parser.add_argument(
        'cli_args',
        nargs=argparse.REMAINDER,
        help='Arguments to pass to the CLI'
    )
    
    args = parser.parse_args()
    
    # Check if we have any CLI arguments
    if not args.cli_args:
        logger.error("No CLI arguments provided")
        parser.print_help()
        return 1
    
    # Remove any leading -- if present (argparse artifact)
    if args.cli_args and args.cli_args[0] == '--':
        args.cli_args.pop(0)
    
    # Run CLI with timeout
    success = run_cli_with_timeout(args.cli_args, args.timeout)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
