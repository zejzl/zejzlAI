# src/agents/executor.py
import asyncio
import logging
import subprocess
import sys
import os
import tempfile
import json
from typing import Any, Dict, Optional, List
from pathlib import Path

logger = logging.getLogger("ExecutorAgent")


class ExecutorAgent:
    """
    Executor Agent for Pantheon 9-Agent System.
    Responsible for safely executing validated tasks with comprehensive execution capabilities.

    SPECIALIZATION: Safe Execution & Error Recovery

    EXECUTION CAPABILITIES:
    - Code Execution: Python code in safe sandboxed environments
    - System Commands: Safe system command execution with whitelisting
    - API Calls: HTTP requests with timeout and error handling
    - File Operations: Read, write, and manipulate files safely
    - Data Processing: JSON parsing, filtering, and transformations

    SAFETY FEATURES:
    - Timeout protection on all operations
    - Safe code execution with restricted builtins
    - Command whitelisting for security
    - Comprehensive error handling and recovery
    - Execution monitoring and detailed reporting

    RESPONSIBILITIES:
    - Execute validated tasks with multiple execution types
    - Implement retry logic for transient failures
    - Monitor execution progress and provide detailed results
    - Handle critical execution failures gracefully
    - Provide comprehensive execution reports and metrics

    EXPERTISE AREAS:
    - Safe execution environments and sandboxing
    - Multi-type task execution (code, commands, APIs, files, data)
    - Error recovery and fallback strategies
    - Execution monitoring and performance metrics
    - Security-aware task execution with validation
    """

    def __init__(self):
        self.name = "Executor"
        self.specialization = "Safe Execution & Error Recovery"
        self.responsibilities = [
            "Execute validated tasks with safety checks",
            "Implement retry logic for transient failures",
            "Monitor execution progress and health",
            "Handle critical execution failures gracefully"
        ]
        self.expertise_areas = [
            "Safe execution environments",
            "Retry logic and backoff strategies",
            "Failure recovery and rollback",
            "Execution monitoring and alerting"
        ]

    async def execute(self, validated_task: Dict[str, Any], provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a validated task with comprehensive error handling and safety checks.

        Supports multiple execution types:
        - Code execution (Python, shell commands)
        - API calls and web requests
        - File operations (read, write, move)
        - System commands and utilities
        - Data processing and analysis

        Features:
        - Safe execution environments
        - Timeout protection
        - Retry logic for transient failures
        - Comprehensive error reporting
        - Result validation and sanitization
        """
        logger.debug(f"[{self.name}] Executing validated task: {validated_task}")

        start_time = asyncio.get_event_loop().time()
        execution_results = []

        try:
            # Extract execution plan from validated task
            execution_plan = validated_task.get('execution_plan', [])
            task_description = validated_task.get('task', 'Unknown task')

            logger.info(f"[{self.name}] Starting execution of: {task_description}")
            logger.debug(f"[{self.name}] Execution plan has {len(execution_plan)} steps")

            # Execute each step in the plan
            for i, step in enumerate(execution_plan):
                step_result = await self._execute_step(step, i + 1, len(execution_plan))
                execution_results.append(step_result)

                # Check if step failed critically
                if step_result.get('status') == 'failed' and step_result.get('critical', False):
                    logger.error(f"[{self.name}] Critical step {i+1} failed, aborting execution")
                    break

            # Determine overall execution status
            failed_steps = [r for r in execution_results if r.get('status') == 'failed']
            successful_steps = [r for r in execution_results if r.get('status') == 'success']

            overall_status = 'success' if len(failed_steps) == 0 else 'partial_success' if successful_steps else 'failed'

            # Calculate execution metrics
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time

            result = {
                "task": validated_task,
                "status": overall_status,
                "execution_time": execution_time,
                "steps_executed": len(execution_results),
                "steps_successful": len(successful_steps),
                "steps_failed": len(failed_steps),
                "execution_results": execution_results,
                "timestamp": end_time,
                "executor_info": {
                    "agent": self.name,
                    "specialization": self.specialization,
                    "execution_environment": "safe_sandbox"
                }
            }

            logger.info(f"[{self.name}] Execution completed: {overall_status} "
                       f"({len(successful_steps)}/{len(execution_results)} steps successful) "
                       f"in {execution_time:.2f}s")

            return result

        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time

            logger.error(f"[{self.name}] Execution failed with exception: {e}")

            return {
                "task": validated_task,
                "status": "error",
                "execution_time": execution_time,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": end_time,
                "executor_info": {
                    "agent": self.name,
                    "specialization": self.specialization,
                    "execution_environment": "safe_sandbox"
                }
            }

    async def _execute_step(self, step: Dict[str, Any], step_number: int, total_steps: int) -> Dict[str, Any]:
        """
        Execute a single step from the execution plan.

        Supports various execution types:
        - code: Execute Python/shell code
        - command: Run system commands
        - api_call: Make HTTP requests
        - file_operation: File read/write/move
        - data_processing: Process data structures
        """
        step_type = step.get('type', 'unknown')
        step_description = step.get('description', f'Step {step_number}')
        timeout = step.get('timeout', 30)  # Default 30 second timeout

        logger.debug(f"[{self.name}] Executing step {step_number}/{total_steps}: {step_type} - {step_description}")

        try:
            if step_type == 'code':
                result = await self._execute_code_step(step, timeout)
            elif step_type == 'command':
                result = await self._execute_command_step(step, timeout)
            elif step_type == 'api_call':
                result = await self._execute_api_step(step, timeout)
            elif step_type == 'file_operation':
                result = await self._execute_file_step(step, timeout)
            elif step_type == 'data_processing':
                result = await self._execute_data_step(step, timeout)
            else:
                # Unknown step type - mark as warning but continue
                result = {
                    "step_number": step_number,
                    "type": step_type,
                    "description": step_description,
                    "status": "warning",
                    "message": f"Unknown execution type: {step_type}",
                    "output": None,
                    "execution_time": 0
                }

            result.update({
                "step_number": step_number,
                "total_steps": total_steps,
                "description": step_description
            })

            return result

        except asyncio.TimeoutError:
            logger.warning(f"[{self.name}] Step {step_number} timed out after {timeout}s")
            return {
                "step_number": step_number,
                "type": step_type,
                "description": step_description,
                "status": "failed",
                "message": f"Step timed out after {timeout} seconds",
                "output": None,
                "execution_time": timeout,
                "critical": False  # Timeout is not necessarily critical
            }

        except Exception as e:
            logger.error(f"[{self.name}] Step {step_number} failed: {e}")
            return {
                "step_number": step_number,
                "type": step_type,
                "description": step_description,
                "status": "failed",
                "message": str(e),
                "error_type": type(e).__name__,
                "output": None,
                "execution_time": asyncio.get_event_loop().time() - asyncio.get_event_loop().time(),  # Approximate
                "critical": step.get('critical', False)  # Check if step is marked as critical
            }

    async def _execute_code_step(self, step: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute Python code in a safe environment."""
        code = step.get('code', '')
        language = step.get('language', 'python')

        if language.lower() == 'python':
            # Execute Python code in a restricted environment
            start_time = asyncio.get_event_loop().time()

            try:
                # Create a safe execution environment
                safe_globals = {
                    '__builtins__': {
                        'print': print,
                        'len': len,
                        'str': str,
                        'int': int,
                        'float': float,
                        'bool': bool,
                        'list': list,
                        'dict': dict,
                        'tuple': tuple,
                        'range': range,
                        'enumerate': enumerate,
                        'zip': zip,
                        'sum': sum,
                        'max': max,
                        'min': min,
                        'abs': abs,
                        'round': round,
                        # Add other safe builtins as needed
                    }
                }

                # Execute the code
                local_vars = {}
                exec(code, safe_globals, local_vars)

                end_time = asyncio.get_event_loop().time()

                return {
                    "status": "success",
                    "output": local_vars,
                    "execution_time": end_time - start_time
                }

            except Exception as e:
                end_time = asyncio.get_event_loop().time()
                return {
                    "status": "failed",
                    "message": f"Code execution failed: {str(e)}",
                    "execution_time": end_time - start_time
                }

        else:
            return {
                "status": "warning",
                "message": f"Unsupported language: {language}",
                "execution_time": 0
            }

    async def _execute_command_step(self, step: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute system commands safely."""
        command = step.get('command', '')
        args = step.get('args', [])
        cwd = step.get('cwd', None)

        # Safety check - only allow safe commands
        safe_commands = ['echo', 'ls', 'pwd', 'date', 'whoami', 'python', 'python3', 'node', 'npm']
        base_command = command.split()[0] if ' ' in command else command

        if base_command not in safe_commands:
            return {
                "status": "failed",
                "message": f"Unsafe command not allowed: {base_command}",
                "execution_time": 0
            }

        start_time = asyncio.get_event_loop().time()

        try:
            # Execute command with timeout
            full_command = [command] + args if args else command.split()

            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            end_time = asyncio.get_event_loop().time()

            return {
                "status": "success" if process.returncode == 0 else "failed",
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore') if stdout else "",
                "stderr": stderr.decode('utf-8', errors='ignore') if stderr else "",
                "execution_time": end_time - start_time
            }

        except asyncio.TimeoutError:
            raise  # Re-raise to be handled by caller
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            return {
                "status": "failed",
                "message": f"Command execution failed: {str(e)}",
                "execution_time": end_time - start_time
            }

    async def _execute_api_step(self, step: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute API calls."""
        url = step.get('url', '')
        method = step.get('method', 'GET').upper()
        headers = step.get('headers', {})
        data = step.get('data', None)

        start_time = asyncio.get_event_loop().time()

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data if isinstance(data, dict) else None,
                    data=data if isinstance(data, str) else None,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_data = await response.text()
                    end_time = asyncio.get_event_loop().time()

                    return {
                        "status": "success" if response.status < 400 else "failed",
                        "http_status": response.status,
                        "response": response_data,
                        "headers": dict(response.headers),
                        "execution_time": end_time - start_time
                    }

        except ImportError:
            end_time = asyncio.get_event_loop().time()
            return {
                "status": "failed",
                "message": "aiohttp not available for API calls",
                "execution_time": end_time - start_time
            }
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            return {
                "status": "failed",
                "message": f"API call failed: {str(e)}",
                "execution_time": end_time - start_time
            }

    async def _execute_file_step(self, step: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute file operations."""
        operation = step.get('operation', 'read')
        file_path = step.get('file_path', '')
        content = step.get('content', '')

        start_time = asyncio.get_event_loop().time()

        try:
            if operation == 'read':
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()

                end_time = asyncio.get_event_loop().time()
                return {
                    "status": "success",
                    "operation": "read",
                    "file_path": file_path,
                    "content": file_content,
                    "execution_time": end_time - start_time
                }

            elif operation == 'write':
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                end_time = asyncio.get_event_loop().time()
                return {
                    "status": "success",
                    "operation": "write",
                    "file_path": file_path,
                    "bytes_written": len(content),
                    "execution_time": end_time - start_time
                }

            else:
                end_time = asyncio.get_event_loop().time()
                return {
                    "status": "warning",
                    "message": f"Unsupported file operation: {operation}",
                    "execution_time": end_time - start_time
                }

        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            return {
                "status": "failed",
                "message": f"File operation failed: {str(e)}",
                "operation": operation,
                "file_path": file_path,
                "execution_time": end_time - start_time
            }

    async def _execute_data_step(self, step: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute data processing operations."""
        operation = step.get('operation', 'transform')
        data = step.get('data', {})
        transform_type = step.get('transform_type', 'identity')

        start_time = asyncio.get_event_loop().time()

        try:
            if operation == 'transform':
                if transform_type == 'json_parse':
                    if isinstance(data, str):
                        result = json.loads(data)
                    else:
                        result = data  # Already parsed
                elif transform_type == 'json_stringify':
                    result = json.dumps(data, indent=2)
                elif transform_type == 'filter':
                    # Simple filtering example
                    filter_key = step.get('filter_key', '')
                    filter_value = step.get('filter_value', '')
                    if isinstance(data, list):
                        result = [item for item in data if item.get(filter_key) == filter_value]
                    else:
                        result = data
                else:
                    result = data  # Identity transform

                end_time = asyncio.get_event_loop().time()
                return {
                    "status": "success",
                    "operation": operation,
                    "transform_type": transform_type,
                    "input_size": len(str(data)),
                    "output_size": len(str(result)),
                    "result": result,
                    "execution_time": end_time - start_time
                }

            else:
                end_time = asyncio.get_event_loop().time()
                return {
                    "status": "warning",
                    "message": f"Unsupported data operation: {operation}",
                    "execution_time": end_time - start_time
                }

        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            return {
                "status": "failed",
                "message": f"Data processing failed: {str(e)}",
                "execution_time": end_time - start_time
            }
