
"""Continuous Monitoring Script - Watches for code changes and triggers testing agents

Install dependencies: `pip install agno watchdog pytest flake8 mypy`
"""

import time
import os
import hashlib
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import our code testing agent
from code_testing_agent import code_testing_agent

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self, agent, monitored_extensions=('.py',), ignored_patterns=('__pycache__', '.git', 'venv', '.env')):
        self.agent = agent
        self.monitored_extensions = monitored_extensions
        self.ignored_patterns = ignored_patterns
        self.file_hashes = {}
        self.scan_existing_files()
        
    def scan_existing_files(self):
        # Scan existing files and store their hashes
        print("Scanning existing files...")
        for root, _, files in os.walk('.'):
            if any(ignored in root for ignored in self.ignored_patterns):
                continue
                
            for file in files:
                if file.endswith(self.monitored_extensions):
                    path = os.path.join(root, file)
                    self.file_hashes[path] = self._get_file_hash(path)
        print(f"Found {len(self.file_hashes)} files to monitor")
    
    def _get_file_hash(self, path):
        # Get the hash of a file's contents
        try:
            with open(path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def _should_process_file(self, path):
        # Check if the file should be processed
        if not path.endswith(self.monitored_extensions):
            return False
            
        if any(ignored in path for ignored in self.ignored_patterns):
            return False
            
        return True
    
    def on_modified(self, event):
        # Handle file modification events
        if event.is_directory:
            return
            
        if not self._should_process_file(event.src_path):
            return
            
        new_hash = self._get_file_hash(event.src_path)
        if new_hash != self.file_hashes.get(event.src_path):
            self.file_hashes[event.src_path] = new_hash
            self._process_file_change(event.src_path)
    
    def on_created(self, event):
        # Handle file creation events
        if event.is_directory:
            return
            
        if not self._should_process_file(event.src_path):
            return
            
        self.file_hashes[event.src_path] = self._get_file_hash(event.src_path)
        self._process_file_change(event.src_path)
    
    def _process_file_change(self, file_path):
        # Process a file change by running the testing agent
        print(f"\n{'='*80}\nCode change detected in {file_path}\n{'='*80}")
        
        # Get the file content
        content = self.agent.tools.get_file_content(file_path)
        
        # Run the agent to test the file
        prompt = f"Analyze the following code file: {file_path}\n\n```python\n{content}\n```\n\nProvide a comprehensive analysis including test results, code quality issues, and improvement suggestions."
        
        print(f"Starting analysis...")
        result = self.agent.run(prompt)
        print(f"\nAnalysis complete:\n{'-'*80}\n{result}\n{'-'*80}")
        
        # If this is a test file, run the tests directly
        if "test_" in os.path.basename(file_path):
            print("\nRunning tests directly since this is a test file...")
            test_result = self.agent.tools.run_tests(os.path.dirname(file_path))
            status = 'PASSED' if test_result['success'] else 'FAILED'
            print(f"Test results: {status}")
            if not test_result['success']:
                print(test_result['errors'])


def parse_arguments():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Continuous code testing monitor')
    parser.add_argument('--directory', '-d', type=str, default='.',
                        help='Directory to monitor (default: current directory)')
    parser.add_argument('--extensions', '-e', type=str, default='.py',
                        help='Comma-separated list of file extensions to monitor (default: .py)')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    
    # Convert extensions string to tuple
    extensions = tuple(args.extensions.split(','))
    
    # Change to the target directory
    os.chdir(os.path.abspath(args.directory))
    
    # Create the observer and event handler
    observer = Observer()
    event_handler = CodeChangeHandler(code_testing_agent, monitored_extensions=extensions)
    observer.schedule(event_handler, '.', recursive=True)
    
    # Start the observer
    observer.start()
    
    try:
        print(f"\nContinuous code testing agent is running...")
        print(f"Monitoring directory: {os.path.abspath('.')}")
        print(f"Watching for changes to files with extensions: {extensions}")
        print("Press Ctrl+C to stop\n")
        
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nMonitoring stopped")
    
    observer.join()
