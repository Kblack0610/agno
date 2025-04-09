#!/usr/bin/env python3
"""
Test Generator Module

This module provides capabilities for automatically generating tests for
Python code created by the multi-agent system.
"""

import os
import re
import ast
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple

# Optional Claude API integration
try:
    from utils.claude_api import ClaudeAPI
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """
    Analyzes Python code to identify functions, classes, and other elements
    that should be tested.
    """
    
    def __init__(self):
        """Initialize the code analyzer."""
        pass
    
    def analyze_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Analyze a Python file to extract testable elements.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary with analysis results
        """
        file_path = Path(file_path)
        if not file_path.exists() or not file_path.is_file():
            logger.error(f"File not found: {file_path}")
            return {"success": False, "error": f"File not found: {file_path}"}
        
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            
            # Parse the AST
            tree = ast.parse(code)
            
            # Extract functions
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(self._analyze_function(node, code))
            
            # Extract classes
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(self._analyze_class(node, code))
            
            # Extract imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(self._analyze_import(node, code))
            
            # Determine package name
            package_name = self._extract_package_name(file_path)
            
            # Extract main functionality
            main_functionality = self._extract_main_functionality(code)
            
            return {
                "success": True,
                "file_path": str(file_path),
                "module_name": file_path.stem,
                "package_name": package_name,
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "main_functionality": main_functionality
            }
        
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _analyze_function(self, node: ast.FunctionDef, code: str) -> Dict[str, Any]:
        """
        Analyze a function definition.
        
        Args:
            node: AST function node
            code: Source code
            
        Returns:
            Dictionary with function information
        """
        # Get function code
        function_code = ast.get_source_segment(code, node)
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Get parameter information
        params = []
        for arg in node.args.args:
            param_name = arg.arg
            param_type = None
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    param_type = arg.annotation.id
                elif isinstance(arg.annotation, ast.Subscript):
                    param_type = ast.get_source_segment(code, arg.annotation)
            
            params.append({
                "name": param_name,
                "type": param_type
            })
        
        # Get return type
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Subscript):
                return_type = ast.get_source_segment(code, node.returns)
        
        return {
            "name": node.name,
            "params": params,
            "return_type": return_type,
            "docstring": docstring,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "line_number": node.lineno,
            "code": function_code
        }
    
    def _analyze_class(self, node: ast.ClassDef, code: str) -> Dict[str, Any]:
        """
        Analyze a class definition.
        
        Args:
            node: AST class node
            code: Source code
            
        Returns:
            Dictionary with class information
        """
        # Get class code
        class_code = ast.get_source_segment(code, node)
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Get base classes
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.get_source_segment(code, base))
        
        # Get methods
        methods = []
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                methods.append(self._analyze_function(child, code))
        
        return {
            "name": node.name,
            "bases": bases,
            "methods": methods,
            "docstring": docstring,
            "line_number": node.lineno,
            "code": class_code
        }
    
    def _analyze_import(self, node: Union[ast.Import, ast.ImportFrom], code: str) -> Dict[str, Any]:
        """
        Analyze an import statement.
        
        Args:
            node: AST import node
            code: Source code
            
        Returns:
            Dictionary with import information
        """
        import_code = ast.get_source_segment(code, node)
        
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            from_module = None
        else:  # ImportFrom
            names = [alias.name for alias in node.names]
            from_module = node.module
        
        return {
            "names": names,
            "from_module": from_module,
            "code": import_code,
            "line_number": node.lineno
        }
    
    def _extract_package_name(self, file_path: Path) -> str:
        """
        Extract the package name for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Package name or empty string
        """
        try:
            # Try to determine package name from directory structure
            parent_dir = file_path.parent
            if (parent_dir / "__init__.py").exists():
                return parent_dir.name
        except Exception:
            pass
        
        return ""
    
    def _extract_main_functionality(self, code: str) -> str:
        """
        Try to determine the main functionality of the code.
        
        Args:
            code: Source code
            
        Returns:
            Description of main functionality
        """
        # Look for main function
        main_match = re.search(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', code)
        if main_match:
            # Extract the main block
            start_pos = main_match.start()
            # Simple heuristic: take the rest of the file
            main_code = code[start_pos:]
            return main_code
        
        return ""

class TestGenerator:
    """
    Generates test code for Python files based on code analysis.
    """
    
    def __init__(
            self,
            output_dir: Optional[Union[str, Path]] = None,
            use_claude: bool = False,
            claude_api_key: Optional[str] = None
        ):
        """
        Initialize the test generator.
        
        Args:
            output_dir: Directory to output generated tests (defaults to same as source)
            use_claude: Whether to use Claude API for better test generation
            claude_api_key: API key for Claude (optional if set in env var)
        """
        self.analyzer = CodeAnalyzer()
        self.output_dir = Path(output_dir) if output_dir else None
        
        # Claude API setup
        self.use_claude = use_claude and CLAUDE_AVAILABLE
        self.claude_api = None
        
        if self.use_claude:
            try:
                self.claude_api = ClaudeAPI(api_key=claude_api_key)
                logger.info("Claude API initialized for test generation")
            except Exception as e:
                logger.error(f"Failed to initialize Claude API: {e}")
                self.use_claude = False
    
    def generate_tests(
            self,
            file_path: Union[str, Path],
            output_path: Optional[Union[str, Path]] = None,
            test_framework: str = "pytest"
        ) -> Dict[str, Any]:
        """
        Generate tests for a Python file.
        
        Args:
            file_path: Path to the Python file
            output_path: Path for the output test file (optional)
            test_framework: Testing framework to use
            
        Returns:
            Dictionary with generation results
        """
        file_path = Path(file_path)
        
        # Analyze the source code
        analysis = self.analyzer.analyze_file(file_path)
        if not analysis["success"]:
            return analysis
        
        # Determine output path if not provided
        if output_path is None:
            if self.output_dir:
                output_dir = self.output_dir
            else:
                output_dir = file_path.parent
            
            # Create test file name
            test_filename = f"test_{file_path.stem}.py"
            output_path = output_dir / test_filename
        else:
            output_path = Path(output_path)
            output_dir = output_path.parent
        
        # Make sure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate tests
        if self.use_claude:
            test_code = self._generate_tests_claude(analysis, test_framework)
        else:
            test_code = self._generate_tests_template(analysis, test_framework)
        
        # Write the test file
        try:
            with open(output_path, 'w') as f:
                f.write(test_code)
            
            logger.info(f"Generated tests for {file_path} at {output_path}")
            
            return {
                "success": True,
                "source_file": str(file_path),
                "test_file": str(output_path),
                "test_framework": test_framework
            }
        
        except Exception as e:
            logger.error(f"Error writing test file: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_tests_claude(
            self,
            analysis: Dict[str, Any],
            test_framework: str
        ) -> str:
        """
        Generate tests using Claude API.
        
        Args:
            analysis: Code analysis results
            test_framework: Testing framework to use
            
        Returns:
            Generated test code
        """
        logger.info(f"Generating tests using Claude API for {analysis['file_path']}")
        
        # Create a prompt for Claude
        module_name = analysis["module_name"]
        
        # Extract functions and classes to test
        functions = analysis.get("functions", [])
        classes = analysis.get("classes", [])
        
        # Build prompt
        prompt = f"""
Please generate thorough Python test code for the following module using {test_framework}.

Module name: {module_name}
File path: {analysis['file_path']}

# Functions to test:
{self._format_functions_for_prompt(functions)}

# Classes to test:
{self._format_classes_for_prompt(classes)}

# Imports:
{self._format_imports_for_prompt(analysis.get('imports', []))}

Generate comprehensive test cases that verify the functionality of each function and class method.
Include edge cases, boundary conditions, and typical usage scenarios.
Make the tests self-contained and runnable with {test_framework}.
Add appropriate docstrings and comments to explain the tests.
The tests should follow best practices for {test_framework}.
"""
        
        try:
            # Get response from Claude
            system_prompt = f"""
You are an expert Python test writer. Your task is to generate comprehensive test code for the given module.
Follow these guidelines:
1. Write tests for all functions and methods
2. Include edge cases and boundary conditions
3. Follow best practices for {test_framework}
4. Your output should be valid Python code that can be executed directly
5. Include only the code, no explanations or markdown formatting

Your complete output will be directly saved to a Python file and should be ready to run.
"""
            
            response = self.claude_api.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=4000,
                temperature=0.2
            )
            
            # Extract the test code from the response
            content = response.get("content", [])
            test_code = ""
            
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "text":
                        test_code += item.get("text", "")
            else:
                test_code = response.get("content", "")
            
            # Clean up the response if needed
            test_code = self._clean_code_response(test_code)
            
            return test_code
        
        except Exception as e:
            logger.error(f"Error generating tests with Claude: {e}")
            # Fall back to template-based generation
            return self._generate_tests_template(analysis, test_framework)
    
    def _clean_code_response(self, code: str) -> str:
        """
        Clean up the code response from the API.
        
        Args:
            code: Code string from API
            
        Returns:
            Cleaned code
        """
        # Remove markdown code blocks if present
        code = re.sub(r'^```python\s*', '', code, flags=re.MULTILINE)
        code = re.sub(r'\s*```$', '', code, flags=re.MULTILINE)
        
        # Ensure proper imports
        if "import pytest" not in code and "pytest" in code:
            code = "import pytest\n" + code
        
        return code
    
    def _generate_tests_template(
            self,
            analysis: Dict[str, Any],
            test_framework: str
        ) -> str:
        """
        Generate tests using templates.
        
        Args:
            analysis: Code analysis results
            test_framework: Testing framework to use
            
        Returns:
            Generated test code
        """
        logger.info(f"Generating tests using templates for {analysis['file_path']}")
        
        module_name = analysis["module_name"]
        package_name = analysis.get("package_name", "")
        
        # Start with imports
        test_code = f"""#!/usr/bin/env python3
\"\"\"
Test module for {module_name}
\"\"\"

import pytest
"""
        
        # Add import for the module under test
        if package_name:
            test_code += f"from {package_name} import {module_name}\n\n"
        else:
            test_code += f"import {module_name}\n\n"
        
        # Add tests for functions
        functions = analysis.get("functions", [])
        for func in functions:
            # Skip "private" functions
            if func["name"].startswith("_"):
                continue
            
            test_code += self._generate_function_test(func, module_name, package_name, test_framework)
        
        # Add tests for classes
        classes = analysis.get("classes", [])
        for cls in classes:
            test_code += self._generate_class_test(cls, module_name, package_name, test_framework)
        
        return test_code
    
    def _generate_function_test(
            self,
            func: Dict[str, Any],
            module_name: str,
            package_name: str,
            test_framework: str
        ) -> str:
        """
        Generate test for a function.
        
        Args:
            func: Function information
            module_name: Name of the module
            package_name: Name of the package
            test_framework: Testing framework
            
        Returns:
            Test code for the function
        """
        func_name = func["name"]
        
        # Skip special methods
        if func_name.startswith("__") and func_name.endswith("__"):
            return ""
        
        test_func_name = f"test_{func_name}"
        
        test_code = f"""
def {test_func_name}():
    \"\"\"Test the {func_name} function.\"\"\"
    # TODO: Add test implementation
    # Example:
    # result = {module_name}.{func_name}()
    # assert result == expected_result
    pass

"""
        return test_code
    
    def _generate_class_test(
            self,
            cls: Dict[str, Any],
            module_name: str,
            package_name: str,
            test_framework: str
        ) -> str:
        """
        Generate test for a class.
        
        Args:
            cls: Class information
            module_name: Name of the module
            package_name: Name of the package
            test_framework: Testing framework
            
        Returns:
            Test code for the class
        """
        class_name = cls["name"]
        test_class_name = f"Test{class_name}"
        
        test_code = f"""
class {test_class_name}:
    \"\"\"Test cases for the {class_name} class.\"\"\"
    
    @pytest.fixture
    def {class_name.lower()}_instance(self):
        \"\"\"Create a test instance of {class_name}.\"\"\"
        # TODO: Initialize with appropriate test values
        return {module_name}.{class_name}()
    
"""
        
        # Add tests for methods
        methods = cls.get("methods", [])
        for method in methods:
            # Skip private methods
            if method["name"].startswith("_") and not (method["name"].startswith("__") and method["name"].endswith("__")):
                continue
            
            # Skip special methods except __init__
            if method["name"].startswith("__") and method["name"].endswith("__") and method["name"] != "__init__":
                continue
            
            test_code += self._generate_method_test(method, class_name)
        
        return test_code
    
    def _generate_method_test(self, method: Dict[str, Any], class_name: str) -> str:
        """
        Generate test for a class method.
        
        Args:
            method: Method information
            class_name: Name of the class
            
        Returns:
            Test code for the method
        """
        method_name = method["name"]
        
        # Special handling for __init__
        if method_name == "__init__":
            test_func_name = "test_initialization"
            test_code = f"""    def {test_func_name}(self, {class_name.lower()}_instance):
        \"\"\"Test the initialization of {class_name}.\"\"\"
        # TODO: Add assertions to verify initialization
        assert {class_name.lower()}_instance is not None
    
"""
            return test_code
        
        test_func_name = f"test_{method_name}"
        
        test_code = f"""    def {test_func_name}(self, {class_name.lower()}_instance):
        \"\"\"Test the {method_name} method.\"\"\"
        # TODO: Add test implementation
        # Example:
        # result = {class_name.lower()}_instance.{method_name}()
        # assert result == expected_result
        pass
    
"""
        return test_code
    
    def _format_functions_for_prompt(self, functions: List[Dict[str, Any]]) -> str:
        """
        Format functions for the prompt.
        
        Args:
            functions: List of function information
            
        Returns:
            Formatted string
        """
        if not functions:
            return "None"
        
        result = ""
        for func in functions:
            result += f"Function: {func['name']}\n"
            if func["docstring"]:
                result += f"Docstring: {func['docstring']}\n"
            
            # Parameters
            params = func.get("params", [])
            if params:
                result += "Parameters:\n"
                for param in params:
                    param_type = f": {param['type']}" if param['type'] else ""
                    result += f"  - {param['name']}{param_type}\n"
            
            # Return type
            if func["return_type"]:
                result += f"Returns: {func['return_type']}\n"
            
            result += "\n"
        
        return result
    
    def _format_classes_for_prompt(self, classes: List[Dict[str, Any]]) -> str:
        """
        Format classes for the prompt.
        
        Args:
            classes: List of class information
            
        Returns:
            Formatted string
        """
        if not classes:
            return "None"
        
        result = ""
        for cls in classes:
            result += f"Class: {cls['name']}\n"
            
            # Base classes
            bases = cls.get("bases", [])
            if bases:
                result += f"Inherits from: {', '.join(bases)}\n"
            
            # Docstring
            if cls["docstring"]:
                result += f"Docstring: {cls['docstring']}\n"
            
            # Methods
            methods = cls.get("methods", [])
            if methods:
                result += "Methods:\n"
                for method in methods:
                    result += f"  - {method['name']}\n"
            
            result += "\n"
        
        return result
    
    def _format_imports_for_prompt(self, imports: List[Dict[str, Any]]) -> str:
        """
        Format imports for the prompt.
        
        Args:
            imports: List of import information
            
        Returns:
            Formatted string
        """
        if not imports:
            return "None"
        
        result = ""
        for imp in imports:
            if imp.get("from_module"):
                result += f"from {imp['from_module']} import {', '.join(imp['names'])}\n"
            else:
                result += f"import {', '.join(imp['names'])}\n"
        
        return result

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_generator.py <file_path> [output_path] [--use-claude]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    use_claude = "--use-claude" in sys.argv
    
    generator = TestGenerator(use_claude=use_claude)
    result = generator.generate_tests(file_path, output_path)
    
    if result["success"]:
        print(f"Successfully generated tests: {result['test_file']}")
    else:
        print(f"Failed to generate tests: {result.get('error', 'Unknown error')}")
        sys.exit(1)
