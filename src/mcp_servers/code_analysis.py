#!/usr/bin/env python3
"""
Code Analysis MCP Server for ZEJZL.NET
Provides code analysis tools for AI applications including:
- Code complexity analysis
- Dependency analysis
- Code quality metrics
- Language detection
- Code structure analysis
"""

import asyncio
import os
import sys
import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import subprocess
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.mcp_servers.base_server import BaseMCPServer


class CodeAnalysisMCPServer(BaseMCPServer):
    """
    MCP Server for code analysis operations
    Provides tools for analyzing codebases, complexity metrics, and code quality
    """

    def __init__(self):
        super().__init__("code_analysis", "1.0.0")
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return available tools for code analysis"""
        return [
            {
                "name": "analyze_codebase",
                "description": "Analyze entire codebase structure and metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to codebase root directory"
                        },
                        "include_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File patterns to include (e.g., ['*.py', '*.js'])",
                            "default": []
                        },
                        "exclude_patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "File patterns to exclude (e.g., ['test_*', '__pycache__'])",
                            "default": []
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "analyze_file",
                "description": "Analyze individual file for complexity and quality metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to file to analyze"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "find_dependencies",
                "description": "Find dependencies and imports in codebase",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to codebase root directory"
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language to analyze",
                            "enum": list(self.supported_languages.values())
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "calculate_complexity",
                "description": "Calculate cyclomatic complexity for functions/methods",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to file to analyze"
                        },
                        "function_name": {
                            "type": "string",
                            "description": "Specific function name to analyze (optional)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "detect_language",
                "description": "Detect programming language of a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to file to analyze"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "analyze_code_quality",
                "description": "Analyze code quality metrics and provide recommendations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to file or directory to analyze"
                        },
                        "language": {
                            "type": "string",
                            "description": "Programming language",
                            "enum": list(self.supported_languages.values())
                        }
                    },
                    "required": ["path"]
                }
            }
        ]

    def _should_include_file(self, file_path: str, include_patterns: List[str], exclude_patterns: List[str]) -> bool:
        """Check if file should be included based on patterns"""
        filename = os.path.basename(file_path)

        # Check exclude patterns first
        for pattern in exclude_patterns:
            if pattern.startswith('*') and filename.endswith(pattern[1:]):
                return False
            if pattern in file_path:
                return False

        # If include patterns specified, check them
        if include_patterns:
            for pattern in include_patterns:
                if pattern.startswith('*') and filename.endswith(pattern[1:]):
                    return True
                if pattern in file_path:
                    return True
            return False  # No include pattern matched

        return True  # No patterns specified, include all

    def _get_language_from_path(self, file_path: str) -> Optional[str]:
        """Get programming language from file extension"""
        _, ext = os.path.splitext(file_path)
        return self.supported_languages.get(ext.lower())

    async def _analyze_codebase(self, path: str, include_patterns: List[str] = None,
                               exclude_patterns: List[str] = None) -> Dict[str, Any]:
        """Analyze entire codebase structure and metrics"""
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")

        if not os.path.isdir(path):
            raise ValueError(f"Path is not a directory: {path}")

        include_patterns = include_patterns or []
        exclude_patterns = exclude_patterns or []

        # Collect all files
        all_files = []
        for root, dirs, files in os.walk(path):
            # Skip common directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'build', 'dist']]

            for file in files:
                file_path = os.path.join(root, file)
                if self._should_include_file(file_path, include_patterns, exclude_patterns):
                    lang = self._get_language_from_path(file_path)
                    if lang:
                        all_files.append({
                            'path': file_path,
                            'language': lang,
                            'size': os.path.getsize(file_path)
                        })

        # Analyze languages
        language_stats = {}
        for file_info in all_files:
            lang = file_info['language']
            if lang not in language_stats:
                language_stats[lang] = {'count': 0, 'total_size': 0, 'files': []}
            language_stats[lang]['count'] += 1
            language_stats[lang]['total_size'] += file_info['size']
            language_stats[lang]['files'].append(file_info['path'])

        # Calculate overall metrics
        total_files = len(all_files)
        total_size = sum(f['size'] for f in all_files)
        avg_file_size = total_size / total_files if total_files > 0 else 0

        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'average_file_size': avg_file_size,
            'languages': language_stats,
            'analyzed_files': all_files[:100]  # Limit for response size
        }

    async def _analyze_file(self, path: str) -> Dict[str, Any]:
        """Analyze individual file for complexity and quality metrics"""
        if not os.path.exists(path):
            raise ValueError(f"File does not exist: {path}")

        if not os.path.isfile(path):
            raise ValueError(f"Path is not a file: {path}")

        language = self._get_language_from_path(path)
        if not language:
            raise ValueError(f"Unsupported file type: {path}")

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.split('\n')
        total_lines = len(lines)
        code_lines = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
        comment_lines = len([line for line in lines if line.strip().startswith('#')])
        empty_lines = len([line for line in lines if not line.strip()])

        # Language-specific analysis
        if language == 'python':
            metrics = await self._analyze_python_file(content)
        else:
            metrics = {
                'functions': 0,
                'classes': 0,
                'complexity': 'unknown',
                'imports': 0
            }

        return {
            'file_path': path,
            'language': language,
            'size_bytes': len(content),
            'total_lines': total_lines,
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'empty_lines': empty_lines,
            'code_ratio': code_lines / total_lines if total_lines > 0 else 0,
            **metrics
        }

    async def _analyze_python_file(self, content: str) -> Dict[str, Any]:
        """Analyze Python file specifically"""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return {'functions': 0, 'classes': 0, 'complexity': 'parse_error', 'imports': 0}

        functions = []
        classes = []
        imports = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'complexity': self._calculate_python_complexity(node)
                })
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line_start': node.lineno
                })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports += 1

        avg_complexity = sum(f['complexity'] for f in functions) / len(functions) if functions else 0

        return {
            'functions': len(functions),
            'classes': len(classes),
            'imports': imports,
            'function_details': functions,
            'class_details': classes,
            'average_complexity': avg_complexity
        }

    def _calculate_python_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for Python function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and len(child.values) > 1:
                complexity += len(child.values) - 1
            elif isinstance(child, ast.Try):
                complexity += 1

        return complexity

    async def _find_dependencies(self, path: str, language: str = None) -> Dict[str, Any]:
        """Find dependencies and imports in codebase"""
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")

        if not os.path.isdir(path):
            raise ValueError(f"Path is not a directory: {path}")

        dependencies = set()
        imports_by_file = {}

        # Walk through files
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]

            for file in files:
                file_path = os.path.join(root, file)
                file_lang = self._get_language_from_path(file_path)

                if file_lang and (language is None or file_lang == language):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        file_imports = await self._extract_imports(content, file_lang)
                        if file_imports:
                            imports_by_file[file_path] = file_imports
                            dependencies.update(file_imports)

                    except Exception as e:
                        print(f"Error processing {file_path}: {e}")

        return {
            'total_files_analyzed': len(imports_by_file),
            'unique_dependencies': len(dependencies),
            'dependencies': sorted(list(dependencies)),
            'imports_by_file': imports_by_file
        }

    async def _extract_imports(self, content: str, language: str) -> Set[str]:
        """Extract imports from file content"""
        imports = set()

        if language == 'python':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])
            except:
                # Fallback regex for import statements
                import_lines = re.findall(r'^(?:from\s+(\S+)|import\s+(\S+))', content, re.MULTILINE)
                for from_mod, import_mod in import_lines:
                    mod = from_mod or import_mod
                    imports.add(mod.split('.')[0])

        elif language == 'javascript':
            # Basic JS import detection
            import_patterns = [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
                r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
            ]
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    imports.add(match.split('/')[0])

        return imports

    async def _calculate_complexity(self, path: str, function_name: str = None) -> Dict[str, Any]:
        """Calculate cyclomatic complexity for functions/methods"""
        if not os.path.exists(path):
            raise ValueError(f"File does not exist: {path}")

        language = self._get_language_from_path(path)
        if not language:
            raise ValueError(f"Unsupported file type: {path}")

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if language == 'python':
            return await self._calculate_python_complexity_file(content, function_name)
        else:
            return {'complexity_analysis': f'Complexity analysis not implemented for {language}'}

    async def _calculate_python_complexity_file(self, content: str, function_name: str = None) -> Dict[str, Any]:
        """Calculate complexity for Python file"""
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {'error': f'Syntax error: {e}'}

        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if function_name is None or node.name == function_name:
                    complexity = self._calculate_python_complexity(node)
                    functions.append({
                        'name': node.name,
                        'line_start': node.lineno,
                        'complexity': complexity,
                        'complexity_level': self._get_complexity_level(complexity)
                    })

        if function_name and not functions:
            return {'error': f'Function {function_name} not found'}

        return {
            'total_functions': len(functions),
            'functions': functions,
            'average_complexity': sum(f['complexity'] for f in functions) / len(functions) if functions else 0,
            'complexity_distribution': self._get_complexity_distribution(functions)
        }

    def _get_complexity_level(self, complexity: int) -> str:
        """Get complexity level description"""
        if complexity <= 5:
            return 'simple'
        elif complexity <= 10:
            return 'moderate'
        elif complexity <= 20:
            return 'complex'
        else:
            return 'very_complex'

    def _get_complexity_distribution(self, functions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of complexity levels"""
        levels = ['simple', 'moderate', 'complex', 'very_complex']
        distribution = {level: 0 for level in levels}

        for func in functions:
            distribution[func['complexity_level']] += 1

        return distribution

    async def _detect_language(self, path: str) -> Dict[str, Any]:
        """Detect programming language of a file"""
        if not os.path.exists(path):
            raise ValueError(f"File does not exist: {path}")

        if not os.path.isfile(path):
            raise ValueError(f"Path is not a file: {path}")

        # First check extension
        language = self._get_language_from_path(path)
        if language:
            confidence = 0.9
        else:
            confidence = 0.1
            language = 'unknown'

        # Try to detect from content
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024)  # First 1KB

            # Simple heuristics
            if 'def ' in content and 'import ' in content:
                language = 'python'
                confidence = max(confidence, 0.8)
            elif ('function' in content or 'const ' in content) and ('=>' in content or 'import ' in content):
                language = 'javascript'
                confidence = max(confidence, 0.8)
            elif 'class ' in content and ('public ' in content or 'private ' in content):
                language = 'java'
                confidence = max(confidence, 0.8)
            elif '#include' in content and ('int main' in content or 'printf' in content):
                language = 'c'
                confidence = max(confidence, 0.8)

        except Exception:
            pass

        return {
            'file_path': path,
            'detected_language': language,
            'confidence': confidence,
            'supported_languages': list(self.supported_languages.values())
        }

    async def _analyze_code_quality(self, path: str, language: str = None) -> Dict[str, Any]:
        """Analyze code quality metrics and provide recommendations"""
        if not os.path.exists(path):
            raise ValueError(f"Path does not exist: {path}")

        if os.path.isfile(path):
            return await self._analyze_file_quality(path)
        else:
            return await self._analyze_directory_quality(path, language)

    async def _analyze_file_quality(self, path: str) -> Dict[str, Any]:
        """Analyze quality of a single file"""
        analysis = await self._analyze_file(path)

        recommendations = []

        # Basic quality checks
        if analysis.get('code_ratio', 0) < 0.5:
            recommendations.append("Consider reducing empty lines and comments ratio")

        if analysis.get('total_lines', 0) > 500:
            recommendations.append("File is quite large, consider splitting into smaller files")

        avg_complexity = analysis.get('average_complexity', 0)
        if avg_complexity > 10:
            recommendations.append("High average complexity - consider refactoring complex functions")

        return {
            'file_analysis': analysis,
            'quality_score': self._calculate_quality_score(analysis),
            'recommendations': recommendations
        }

    async def _analyze_directory_quality(self, path: str, language: str = None) -> Dict[str, Any]:
        """Analyze quality of a directory"""
        codebase_analysis = await self._analyze_codebase(path)

        recommendations = []

        # Directory-level quality checks
        if len(codebase_analysis.get('languages', {})) > 3:
            recommendations.append("Multiple languages detected - consider separating concerns")

        total_files = codebase_analysis.get('total_files', 0)
        if total_files > 100:
            recommendations.append("Large codebase - ensure proper modularization")

        return {
            'codebase_analysis': codebase_analysis,
            'quality_score': 'directory_analysis_not_implemented',
            'recommendations': recommendations
        }

    def _calculate_quality_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate a simple quality score (0-100)"""
        score = 100

        # Penalize low code ratio
        code_ratio = analysis.get('code_ratio', 0)
        if code_ratio < 0.6:
            score -= (0.6 - code_ratio) * 100

        # Penalize high complexity
        avg_complexity = analysis.get('average_complexity', 0)
        if avg_complexity > 5:
            score -= min(avg_complexity - 5, 20)

        # Penalize large files
        total_lines = analysis.get('total_lines', 0)
        if total_lines > 300:
            score -= min((total_lines - 300) / 10, 20)

        return max(0, min(100, score))

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool by name"""
        if name == "analyze_codebase":
            return await self._analyze_codebase(
                arguments["path"],
                arguments.get("include_patterns", []),
                arguments.get("exclude_patterns", [])
            )
        elif name == "analyze_file":
            return await self._analyze_file(arguments["path"])
        elif name == "find_dependencies":
            return await self._find_dependencies(
                arguments["path"],
                arguments.get("language")
            )
        elif name == "calculate_complexity":
            return await self._calculate_complexity(
                arguments["path"],
                arguments.get("function_name")
            )
        elif name == "detect_language":
            return await self._detect_language(arguments["path"])
        elif name == "analyze_code_quality":
            return await self._analyze_code_quality(
                arguments["path"],
                arguments.get("language")
            )
        else:
            raise ValueError(f"Unknown tool: {name}")


if __name__ == "__main__":
    # Run as stdio server
    import argparse

    parser = argparse.ArgumentParser(description="Code Analysis MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run as stdio server")
    args = parser.parse_args()

    if args.stdio:
        server = CodeAnalysisMCPServer()
        asyncio.run(server.start_stdio_server())
    else:
        print("Code Analysis MCP Server")
        print("Run with --stdio to start the server")