"""
Code Tools Module

This module provides utilities for code generation, file operations, and
code manipulation tasks used by the execution agent.
"""

import os
import re
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import difflib

class CodeTools:
    """
    Tools for code generation, file operations, and code manipulation.
    
    Features:
    - File read/write operations
    - Code generation using external LLMs
    - Syntax highlighting and formatting
    - Code analysis
    - Code diffing
    - Safe file operations with backup
    """
    
    def __init__(self, workspace_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the code tools.
        
        Args:
            workspace_dir: Root directory for file operations (default: current directory)
        """
        self.logger = logging.getLogger('tools.code_tools')
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.logger.info(f"Initialized CodeTools with workspace: {self.workspace_dir}")
        
        # Keep track of modified files for potential rollback
        self.file_backups = {}
    
    def read_file(self, file_path: Union[str, Path]) -> str:
        """
        Read the contents of a file.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Contents of the file as a string
        
        Raises:
            FileNotFoundError: If the file doesn't exist
        """
        path = self._resolve_path(file_path)
        
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.debug(f"Read file: {path} ({len(content)} bytes)")
            return content
        except Exception as e:
            self.logger.error(f"Error reading file {path}: {e}")
            raise
    
    def write_file(
            self,
            file_path: Union[str, Path],
            content: str,
            create_backup: bool = True,
            make_executable: bool = False
        ) -> bool:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            create_backup: Whether to create a backup of the existing file
            make_executable: Whether to make the file executable
            
        Returns:
            True if the file was written successfully, False otherwise
        """
        path = self._resolve_path(file_path)
        
        # Create parent directories if they don't exist
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created directory: {path.parent}")
        
        # Create backup if requested and file exists
        if create_backup and path.exists():
            self._backup_file(path)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Make executable if requested
            if make_executable and not self._is_windows():
                os.chmod(path, 0o755)
            
            self.logger.info(f"Wrote file: {path} ({len(content)} bytes)")
            return True
        except Exception as e:
            self.logger.error(f"Error writing file {path}: {e}")
            return False
    
    def append_to_file(
            self,
            file_path: Union[str, Path],
            content: str,
            create_backup: bool = True
        ) -> bool:
        """
        Append content to a file.
        
        Args:
            file_path: Path to the file to append to
            content: Content to append to the file
            create_backup: Whether to create a backup of the existing file
            
        Returns:
            True if the content was appended successfully, False otherwise
        """
        path = self._resolve_path(file_path)
        
        # Create parent directories if they don't exist
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created directory: {path.parent}")
        
        # Create backup if requested and file exists
        if create_backup and path.exists():
            self._backup_file(path)
        
        try:
            with open(path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Appended to file: {path} ({len(content)} bytes)")
            return True
        except Exception as e:
            self.logger.error(f"Error appending to file {path}: {e}")
            return False
    
    def delete_file(
            self,
            file_path: Union[str, Path],
            create_backup: bool = True
        ) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
            create_backup: Whether to create a backup of the file
            
        Returns:
            True if the file was deleted successfully, False otherwise
        """
        path = self._resolve_path(file_path)
        
        if not path.exists():
            self.logger.warning(f"File not found, can't delete: {path}")
            return False
        
        # Create backup if requested
        if create_backup:
            self._backup_file(path)
        
        try:
            path.unlink()
            self.logger.info(f"Deleted file: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting file {path}: {e}")
            return False
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file exists, False otherwise
        """
        path = self._resolve_path(file_path)
        return path.exists() and path.is_file()
    
    def dir_exists(self, dir_path: Union[str, Path]) -> bool:
        """
        Check if a directory exists.
        
        Args:
            dir_path: Path to the directory to check
            
        Returns:
            True if the directory exists, False otherwise
        """
        path = self._resolve_path(dir_path)
        return path.exists() and path.is_dir()
    
    def list_files(
            self,
            directory: Union[str, Path],
            pattern: str = "*",
            recursive: bool = False
        ) -> List[Path]:
        """
        List files in a directory.
        
        Args:
            directory: Directory to list files from
            pattern: Glob pattern to match files against
            recursive: Whether to search recursively
            
        Returns:
            List of file paths matching the pattern
        """
        dir_path = self._resolve_path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            self.logger.warning(f"Directory not found: {dir_path}")
            return []
        
        if recursive:
            files = list(dir_path.glob(f"**/{pattern}"))
        else:
            files = list(dir_path.glob(pattern))
        
        # Filter out directories
        files = [f for f in files if f.is_file()]
        
        self.logger.debug(f"Listed {len(files)} files in {dir_path}")
        return files
    
    def create_directory(self, dir_path: Union[str, Path]) -> bool:
        """
        Create a directory.
        
        Args:
            dir_path: Path to the directory to create
            
        Returns:
            True if the directory was created or already exists, False otherwise
        """
        path = self._resolve_path(dir_path)
        
        if path.exists() and path.is_dir():
            self.logger.debug(f"Directory already exists: {path}")
            return True
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Error creating directory {path}: {e}")
            return False
    
    def modify_file(
            self,
            file_path: Union[str, Path],
            replacements: List[Tuple[int, int, str]],
            create_backup: bool = True
        ) -> bool:
        """
        Modify specific parts of a file.
        
        Args:
            file_path: Path to the file to modify
            replacements: List of (start_line, end_line, new_content) tuples
            create_backup: Whether to create a backup of the file
            
        Returns:
            True if the file was modified successfully, False otherwise
        """
        path = self._resolve_path(file_path)
        
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            return False
        
        try:
            # Read the original content
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Create backup if requested
            if create_backup:
                self._backup_file(path)
            
            # Apply replacements (in reverse order to avoid line number issues)
            for start_line, end_line, new_content in sorted(replacements, reverse=True):
                # Adjust for 0-based indexing
                start_idx = max(0, start_line - 1)
                end_idx = min(len(lines), end_line)
                
                # Replace the lines
                new_lines = new_content.splitlines(True)
                lines[start_idx:end_idx] = new_lines
            
            # Write the modified content
            with open(path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            self.logger.info(f"Modified file: {path} ({len(replacements)} replacements)")
            return True
        except Exception as e:
            self.logger.error(f"Error modifying file {path}: {e}")
            return False
    
    def search_in_file(
            self,
            file_path: Union[str, Path],
            pattern: str,
            is_regex: bool = False
        ) -> List[Tuple[int, str]]:
        """
        Search for a pattern in a file.
        
        Args:
            file_path: Path to the file to search in
            pattern: String or regex pattern to search for
            is_regex: Whether the pattern is a regex
            
        Returns:
            List of (line_number, line_content) tuples for matching lines
        """
        path = self._resolve_path(file_path)
        
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            return []
        
        matches = []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if is_regex:
                    regex = re.compile(pattern)
                    matches = [
                        (i + 1, line.rstrip('\n'))
                        for i, line in enumerate(f)
                        if regex.search(line)
                    ]
                else:
                    matches = [
                        (i + 1, line.rstrip('\n'))
                        for i, line in enumerate(f)
                        if pattern in line
                    ]
            
            self.logger.debug(f"Found {len(matches)} matches in {path}")
            return matches
        except Exception as e:
            self.logger.error(f"Error searching in file {path}: {e}")
            return []
    
    def search_in_files(
            self,
            directory: Union[str, Path],
            pattern: str,
            file_pattern: str = "*.py",
            recursive: bool = True,
            is_regex: bool = False
        ) -> Dict[str, List[Tuple[int, str]]]:
        """
        Search for a pattern across multiple files.
        
        Args:
            directory: Directory to search in
            pattern: String or regex pattern to search for
            file_pattern: Glob pattern to match files against
            recursive: Whether to search recursively
            is_regex: Whether the pattern is a regex
            
        Returns:
            Dictionary of {file_path: [(line_number, line_content), ...]}
        """
        dir_path = self._resolve_path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            self.logger.warning(f"Directory not found: {dir_path}")
            return {}
        
        results = {}
        files = self.list_files(dir_path, file_pattern, recursive)
        
        for file_path in files:
            matches = self.search_in_file(file_path, pattern, is_regex)
            if matches:
                # Convert Path to string for results
                results[str(file_path)] = matches
        
        self.logger.debug(f"Found matches in {len(results)} files")
        return results
    
    def generate_diff(
            self,
            original: str,
            modified: str,
            original_name: str = "original",
            modified_name: str = "modified"
        ) -> str:
        """
        Generate a unified diff between two strings.
        
        Args:
            original: Original content
            modified: Modified content
            original_name: Label for the original content
            modified_name: Label for the modified content
            
        Returns:
            Unified diff as a string
        """
        original_lines = original.splitlines(True)
        modified_lines = modified.splitlines(True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=original_name,
            tofile=modified_name
        )
        
        return ''.join(diff)
    
    def apply_diff(
            self,
            file_path: Union[str, Path],
            diff_content: str,
            create_backup: bool = True
        ) -> bool:
        """
        Apply a diff to a file.
        
        Args:
            file_path: Path to the file to apply the diff to
            diff_content: Unified diff content
            create_backup: Whether to create a backup of the file
            
        Returns:
            True if the diff was applied successfully, False otherwise
        """
        path = self._resolve_path(file_path)
        
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            return False
        
        # Create temporary files for the diff
        import tempfile
        
        try:
            # Create backup if requested
            if create_backup:
                self._backup_file(path)
            
            # Create temp file with the diff
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as diff_file:
                diff_file.write(diff_content)
                diff_path = diff_file.name
            
            # Apply the patch using the patch command
            result = subprocess.run(
                ['patch', '-u', str(path), diff_path],
                capture_output=True,
                text=True
            )
            
            # Clean up the temporary diff file
            os.unlink(diff_path)
            
            if result.returncode != 0:
                self.logger.error(
                    f"Error applying diff to {path}: {result.stderr}"
                )
                return False
            
            self.logger.info(f"Applied diff to file: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Error applying diff to {path}: {e}")
            return False
    
    def compare_files(
            self,
            file1: Union[str, Path],
            file2: Union[str, Path]
        ) -> str:
        """
        Compare two files and generate a diff.
        
        Args:
            file1: Path to the first file
            file2: Path to the second file
            
        Returns:
            Unified diff as a string
        """
        path1 = self._resolve_path(file1)
        path2 = self._resolve_path(file2)
        
        try:
            content1 = self.read_file(path1)
            content2 = self.read_file(path2)
            
            return self.generate_diff(
                content1,
                content2,
                original_name=str(path1),
                modified_name=str(path2)
            )
        except Exception as e:
            self.logger.error(f"Error comparing files: {e}")
            return f"Error: {e}"
    
    def restore_backup(self, file_path: Union[str, Path]) -> bool:
        """
        Restore a file from its backup.
        
        Args:
            file_path: Path to the file to restore
            
        Returns:
            True if the file was restored successfully, False otherwise
        """
        path = self._resolve_path(file_path)
        
        if str(path) not in self.file_backups:
            self.logger.warning(f"No backup found for file: {path}")
            return False
        
        try:
            content = self.file_backups[str(path)]
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"Restored file from backup: {path}")
            return True
        except Exception as e:
            self.logger.error(f"Error restoring file {path}: {e}")
            return False
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        path = self._resolve_path(file_path)
        
        if not path.exists():
            return {'exists': False}
        
        try:
            stat = path.stat()
            
            return {
                'exists': True,
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'extension': path.suffix[1:] if path.suffix else '',
                'path': str(path),
                'name': path.name,
                'parent': str(path.parent)
            }
        except Exception as e:
            self.logger.error(f"Error getting file info for {path}: {e}")
            return {'exists': False, 'error': str(e)}
    
    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """
        Resolve a path relative to the workspace directory.
        
        Args:
            path: Path to resolve
            
        Returns:
            Absolute Path object
        """
        if isinstance(path, str):
            path = Path(path)
        
        # Convert to absolute path if not already
        if not path.is_absolute():
            path = self.workspace_dir / path
        
        return path
    
    def _backup_file(self, file_path: Union[str, Path]) -> None:
        """
        Create a backup of a file.
        
        Args:
            file_path: Path to the file to backup
        """
        path = self._resolve_path(file_path)
        
        if not path.exists() or not path.is_file():
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.file_backups[str(path)] = content
            self.logger.debug(f"Created backup of file: {path}")
        except Exception as e:
            self.logger.warning(f"Error creating backup of file {path}: {e}")
    
    def _is_windows(self) -> bool:
        """Check if the current platform is Windows."""
        return sys.platform.startswith('win')


# Create a global instance for easy access
_global_code_tools = None

def get_code_tools(workspace_dir: Optional[Union[str, Path]] = None) -> CodeTools:
    """
    Get the global code tools instance.
    
    Args:
        workspace_dir: Root directory for file operations (used only on first call)
        
    Returns:
        Global CodeTools instance
    """
    global _global_code_tools
    if _global_code_tools is None:
        _global_code_tools = CodeTools(workspace_dir)
    return _global_code_tools
