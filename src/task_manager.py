#!/usr/bin/env python3
"""
ZEJZL.NET Task Dependency Management System
Manages project tasks, dependencies, and critical path optimization
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DependencyType(str, Enum):
    FINISHES = "finishes"  # Task B must finish before Task A starts
    STARTS = "starts"     # Task B must start before Task A can continue
    REQUIRES = "requires" # Task A requires resource from Task B
    CONFLICTS = "conflicts" # Tasks A and B cannot run simultaneously

@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    estimated_hours: float = 1.0
    actual_hours: float = 0.0
    assignee: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    completion_percentage: float = 0.0
    subtasks: List[str] = field(default_factory=list)
    parent_task: Optional[str] = None

@dataclass
class Dependency:
    id: str
    from_task: str
    to_task: str
    type: DependencyType
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

@dataclass
class Project:
    id: str
    name: str
    description: str
    start_date: datetime = field(default_factory=datetime.now)
    target_date: Optional[datetime] = None
    status: str = "active"
    total_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    milestones: List[str] = field(default_factory=list)

class TaskManager:
    """Manages tasks, dependencies, and project optimization"""
    
    def __init__(self, storage_file: str = "tasks.json"):
        self.storage_file = storage_file
        self.tasks: Dict[str, Task] = {}
        self.dependencies: Dict[str, Dependency] = {}
        self.projects: Dict[str, Project] = {}
        self.critical_path_cache: Optional[List[str]] = None
        self.last_analysis = datetime.now()
    
    async def initialize(self):
        """Initialize task manager with default data"""
        await self.load_data()
        await self.create_default_project()
        await self.create_sample_tasks()
        logger.info("Task manager initialized successfully")
    
    async def load_data(self):
        """Load tasks, dependencies, and projects from storage"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                
                self.tasks = {
                    tid: Task(**task_data) 
                    for tid, task_data in data.get('tasks', {}).items()
                }
                
                self.dependencies = {
                    dep_id: Dependency(**dep_data)
                    for dep_id, dep_data in data.get('dependencies', {}).items()
                }
                
                self.projects = {
                    pid: Project(**proj_data)
                    for pid, proj_data in data.get('projects', {}).items()
                }
                
                logger.info(f"Loaded {len(self.tasks)} tasks, {len(self.dependencies)} dependencies, {len(self.projects)} projects")
        except Exception as e:
            logger.error(f"Error loading task data: {e}")
            await self.create_default_data()
    
    async def save_data(self):
        """Save tasks, dependencies, and projects to storage"""
        try:
            data = {
                'tasks': {tid: asdict(task) for tid, task in self.tasks.items()},
                'dependencies': {dep_id: asdict(dep) for dep_id, dep in self.dependencies.items()},
                'projects': {pid: asdict(proj) for pid, proj in self.projects.items()},
                'last_analysis': self.last_analysis.isoformat()
            }
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Task data saved successfully")
        except Exception as e:
            logger.error(f"Error saving task data: {e}")
    
    async def create_default_project(self):
        """Create default project if none exists"""
        if not self.projects:
            project = Project(
                id="proj-main",
                name="ZEJZL.NET Development",
                description="Main development project for zejzl.net AI framework",
                target_date=datetime.now() + timedelta(days=90)
                milestones=["Phase 1: Revenue System", "Phase 2: Dev Velocity", "Phase 3: Intelligence Layer"]
            )
            self.projects[project.id] = project
            logger.info(f"Created default project: {project.name}")
    
    async def create_sample_tasks(self):
        """Create sample tasks if none exist"""
        if not self.tasks:
            sample_tasks = [
                Task(
                    id="task-001",
                    title="Configure Stripe Payment Processing",
                    description="Set up Stripe API keys and webhook handlers",
                    priority=TaskPriority.HIGH,
                    estimated_hours=4.0,
                    tags=["payment", "stripe", "configuration"],
                    status=TaskStatus.COMPLETED  # Already done
                ),
                Task(
                    id="task-002", 
                    title="Create Automated Testing Pipeline",
                    description="Set up pytest, GitHub Actions, and coverage reporting",
                    priority=TaskPriority.HIGH,
                    estimated_hours=8.0,
                    tags=["testing", "ci-cd", "automation"],
                    status=TaskStatus.IN_PROGRESS
                ),
                Task(
                    id="task-003",
                    title="Implement Task Dependency Management",
                    description="Create system to track task dependencies and critical path",
                    priority=TaskPriority.HIGH,
                    estimated_hours=6.0,
                    tags=["dependencies", "management", "optimization"],
                    status=TaskStatus.IN_PROGRESS
                ),
                Task(
                    id="task-004",
                    title="Build Performance Dashboard",
                    description="Real-time monitoring of system performance and bottlenecks",
                    priority=TaskPriority.MEDIUM,
                    estimated_hours=5.0,
                    tags=["monitoring", "performance", "dashboard"],
                    status=TaskStatus.COMPLETED  # Already done
                ),
                Task(
                    id="task-005",
                    title="Create API Documentation",
                    description="Generate comprehensive API documentation with examples",
                    priority=TaskPriority.MEDIUM,
                    estimated_hours=10.0,
                    tags=["documentation", "api", "examples"],
                    dependencies=["task-001"],
                    status=TaskStatus.PENDING
                ),
                Task(
                    id="task-006",
                    title="Implement Rate Limiting",
                    description="Add intelligent rate limiting to prevent API abuse",
                    priority=TaskPriority.MEDIUM,
                    estimated_hours=6.0,
                    tags=["api", "rate-limiting", "security"],
                    dependencies=["task-001"],
                    status=TaskStatus.PENDING
                ),
                Task(
                    id="task-007",
                    title="Add Database Backup System",
                    description="Automated daily backups of user and system data",
                    priority=TaskPriority.LOW,
                    estimated_hours=4.0,
                    tags=["database", "backup", "reliability"],
                    status=TaskStatus.PENDING
                ),
                Task(
                    id="task-008",
                    title="Optimize Database Queries",
                    description="Analyze and optimize slow database queries",
                    priority=TaskPriority.LOW,
                    estimated_hours=8.0,
                    tags=["database", "optimization", "performance"],
                    status=TaskStatus.PENDING
                ),
                Task(
                    id="task-009",
                    title="Add Error Monitoring",
                    description="Centralized error tracking and alerting system",
                    priority=TaskPriority.MEDIUM,
                    estimated_hours=6.0,
                    tags=["monitoring", "errors", "alerts"],
                    status=TaskStatus.PENDING
                ),
                Task(
                    id="task-010",
                    title="Create Load Testing Framework",
                    description="Automated load testing for scalability validation",
                    priority=TaskPriority.LOW,
                    estimated_hours=8.0,
                    tags=["testing", "load-testing", "scalability"],
                    dependencies=["task-002"],
                    status=TaskStatus.PENDING
                )
            ]
            
            for task in sample_tasks:
                self.tasks[task.id] = task
            
            # Create sample dependencies
            sample_deps = [
                Dependency(
                    id="dep-001",
                    from_task="task-005",
                    to_task="task-001",
                    type=DependencyType.REQUIRES,
                    description="API docs require payment system to be configured"
                ),
                Dependency(
                    id="dep-002",
                    from_task="task-006",
                    to_task="task-001", 
                    type=DependencyType.REQUIRES,
                    description="Rate limiting requires payment system setup"
                ),
                Dependency(
                    id="dep-003",
                    from_task="task-010",
                    to_task="task-002",
                    type=DependencyType.REQUIRES,
                    description="Load testing requires automated testing pipeline"
                )
            ]
            
            for dep in sample_deps:
                self.dependencies[dep.id] = dep
            
            logger.info(f"Created {len(sample_tasks)} sample tasks and {len(sample_deps)} dependencies")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **kwargs):
        """Update task properties"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            task.updated_at = datetime.now()
            logger.info(f"Updated task {task_id}: {kwargs}")
    
    def add_dependency(self, from_task: str, to_task: str, dep_type: DependencyType, description: str):
        """Add a new dependency"""
        dep_id = str(uuid.uuid4())
        dependency = Dependency(
            id=dep_id,
            from_task=from_task,
            to_task=to_task,
            type=dep_type,
            description=description
        )
        self.dependencies[dep_id] = dependency
        logger.info(f"Added dependency: {from_task} -> {to_task} ({dep_type.value})")
    
    def calculate_critical_path(self) -> List[str]:
        """Calculate critical path through task dependency graph"""
        try:
            # Simple critical path calculation using longest path algorithm
            def get_task_duration(task_id: str) -> float:
                task = self.tasks.get(task_id)
                if not task:
                    return 1.0
                if task.status == TaskStatus.COMPLETED:
                    return task.actual_hours if task.actual_hours > 0 else task.estimated_hours
                return task.estimated_hours
            
            def build_dependency_graph():
                graph = {}
                for task_id in self.tasks:
                    task = self.tasks[task_id]
                    graph[task_id] = [dep.to_task for dep in self.dependencies.values() if dep.from_task == task_id]
                return graph
            
            graph = build_dependency_graph()
            
            # Calculate critical path using dynamic programming
            visited = set()
            critical_path = []
            
            def longest_path(task_id: str) -> float:
                if task_id in visited:
                    return 0
                
                visited.add(task_id)
                
                max_path = get_task_duration(task_id)
                
                for dependent_id in graph[task_id]:
                    if dependent_id in self.tasks:
                        path_length = get_task_duration(dependent_id) + longest_path(dependent_id)
                        max_path = max(max_path, path_length)
                
                return max_path
            
            # Find longest path from any task
            for task_id in self.tasks:
                path_length = longest_path(task_id)
                if path_length > sum(get_task_duration(tid) for tid in critical_path):
                    critical_path = [task_id]
                    # In real implementation, you'd backtrack to find the full path
            
            return critical_path
        
        except Exception as e:
            logger.error(f"Error calculating critical path: {e}")
            return []
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with specific status"""
        return [task for task in self.tasks.values() if task.status == status]
    
    def get_tasks_by_priority(self, priority: TaskPriority) -> List[Task]:
        """Get all tasks with specific priority or higher"""
        priorities_order = [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]
        min_priority_index = priorities_order.index(priority)
        
        return [
            task for task in self.tasks.values()
            if priorities_order.index(task.priority) <= min_priority_index and task.status != TaskStatus.COMPLETED
        ]
    
    def get_blocked_tasks(self) -> List[Task]:
        """Get tasks that are blocked by dependencies"""
        blocked_tasks = []
        
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # Check if any dependencies are unmet
                unmet_deps = [
                    dep for dep in self.dependencies.values()
                    if dep.to_task == task.id and dep.from_task not in [t.id for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
                ]
                
                if unmet_deps:
                    task.status = TaskStatus.BLOCKED
                    blocked_tasks.append(task)
        
        return blocked_tasks
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive project status"""
        if project_id not in self.projects:
            return {"error": "Project not found"}
        
        project = self.projects[project_id]
        project_tasks = [task for task in self.tasks.values() if task.parent_task is None]  # Top-level tasks
        completed_tasks = [t for t in project_tasks if t.status == TaskStatus.COMPLETED]
        blocked_tasks = [t for t in project_tasks if t.status == TaskStatus.BLOCKED]
        in_progress_tasks = [t for t in project_tasks if t.status == TaskStatus.IN_PROGRESS]
        
        total_estimated_hours = sum(task.estimated_hours for task in project_tasks)
        total_actual_hours = sum(task.actual_hours for task in project_tasks)
        
        return {
            "project": asdict(project),
            "task_summary": {
                "total": len(project_tasks),
                "completed": len(completed_tasks),
                "blocked": len(blocked_tasks),
                "in_progress": len(in_progress_tasks),
                "pending": len([t for t in project_tasks if t.status == TaskStatus.PENDING])
            },
            "progress": {
                "completion_percentage": (len(completed_tasks) / len(project_tasks)) * 100 if project_tasks else 0,
                "estimated_hours": total_estimated_hours,
                "actual_hours": total_actual_hours,
                "hours_remaining": total_estimated_hours - total_actual_hours
            },
            "critical_path": self.calculate_critical_path(),
            "priority_breakdown": {
                "critical": len(self.get_tasks_by_priority(TaskPriority.CRITICAL)),
                "high": len(self.get_tasks_by_priority(TaskPriority.HIGH)),
                "medium": len(self.get_tasks_by_priority(TaskPriority.MEDIUM)),
                "low": len(self.get_tasks_by_priority(TaskPriority.LOW))
            }
        }
    
    def get_resource_allocation(self) -> Dict[str, Any]:
        """Analyze resource allocation across tasks"""
        active_tasks = self.get_tasks_by_status(TaskStatus.IN_PROGRESS)
        total_estimated_hours = sum(task.estimated_hours for task in active_tasks)
        
        return {
            "active_tasks": len(active_tasks),
            "total_estimated_hours": total_estimated_hours,
            "average_task_duration": total_estimated_hours / len(active_tasks) if active_tasks else 0,
            "resource_utilization": {
                "high_priority_tasks": len([t for t in active_tasks if t.priority == TaskPriority.HIGH]),
                "blocked_dependencies": len(self.get_blocked_tasks()),
                "dependencies_resolved": len([d for d in self.dependencies.values() if d.resolved_at is not None])
            }
        }

# Global task manager instance
task_manager = TaskManager()

async def main():
    """Main function for task management system"""
    logger.info("🚀 Starting ZEJZL.NET Task Management System")
    
    await task_manager.initialize()
    
    # Display current status
    if "proj-main" in task_manager.projects:
        status = task_manager.get_project_status("proj-main")
        logger.info(f"📊 Project Status: {json.dumps(status, indent=2)}")
    
    # Display critical path
    critical_path = task_manager.calculate_critical_path()
    if critical_path:
        logger.info(f"🔥 Critical Path: {' -> '.join(critical_path)}")
    
    # Display resource allocation
    resources = task_manager.get_resource_allocation()
    logger.info(f"⚖️  Resource Allocation: {json.dumps(resources, indent=2)}")
    
    # Save current state
    await task_manager.save_data()
    
    logger.info("✅ Task management system operational")

if __name__ == "__main__":
    asyncio.run(main())