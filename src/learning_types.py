# src/learning_types.py
"""
Common types and dataclasses for the learning system.
Separated to avoid circular imports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class LearningPhase(Enum):
    """Phases of the learning loop"""
    OBSERVATION = "observation"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    IMPLEMENTATION = "implementation"
    EVALUATION = "evaluation"
    ADAPTATION = "adaptation"


@dataclass
class LearningInsight:
    """A learning insight generated from analysis"""
    insight_id: str
    insight_type: str  # "pattern", "bottleneck", "optimization", "anomaly"
    description: str
    confidence: float
    impact_potential: str  # "high", "medium", "low"
    related_agents: List[str]
    recommended_actions: List[str]
    generated_at: datetime
    applied: bool = False
    applied_at: Optional[datetime] = None
    impact_measured: Optional[Dict[str, Any]] = None


@dataclass
class LearningCycle:
    """A single learning cycle"""
    cycle_id: str
    start_time: datetime
    phase: LearningPhase = LearningPhase.OBSERVATION
    performance_data: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    optimization_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    implementation_actions: List[Dict[str, Any]] = field(default_factory=list)
    evaluation_metrics: Dict[str, Any] = field(default_factory=dict)
    end_time: Optional[datetime] = None
    success: bool = False

    def complete_phase(self, phase_data: Optional[Dict[str, Any]] = None):
        """Complete current phase and move to next"""
        if phase_data:
            if self.phase == LearningPhase.OBSERVATION:
                self.performance_data.update(phase_data)
            elif self.phase == LearningPhase.ANALYSIS:
                self.analysis_results.update(phase_data)
            elif self.phase == LearningPhase.OPTIMIZATION:
                self.optimization_recommendations.extend(phase_data.get('recommendations', []))
            elif self.phase == LearningPhase.IMPLEMENTATION:
                self.implementation_actions.extend(phase_data.get('actions', []))
            elif self.phase == LearningPhase.EVALUATION:
                self.evaluation_metrics.update(phase_data)

        # Move to next phase
        phase_order = list(LearningPhase)
        current_index = phase_order.index(self.phase)
        if current_index < len(phase_order) - 1:
            self.phase = phase_order[current_index + 1]
        else:
            self.end_time = datetime.now()
            self.success = True

    def get_duration(self) -> Optional[float]:
        """Get cycle duration in seconds"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None