# src/agents/consensus.py
"""
Conflict Resolution and Consensus Algorithms for ZEJZL.NET Pantheon System.

Provides mechanisms for agents to resolve conflicts and reach consensus on decisions,
using weighted voting based on agent expertise and specialization relevance.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from collections import defaultdict, Counter

logger = logging.getLogger("ConsensusManager")


class ConflictType(Enum):
    """Types of conflicts that can occur"""
    VALIDATION_DISAGREEMENT = "validation_disagreement"
    EXECUTION_CONFLICT = "execution_conflict"
    PLANNING_DISPUTE = "planning_dispute"
    RESOURCE_ALLOCATION = "resource_allocation"
    PRIORITY_CONFLICT = "priority_conflict"


class ConsensusMethod(Enum):
    """Methods for reaching consensus"""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_VOTE = "weighted_vote"
    EXPERTISE_WEIGHTED = "expertise_weighted"
    RANKED_CHOICE = "ranked_choice"
    CONSENSUS_THRESHOLD = "consensus_threshold"


@dataclass
class ConflictResolution:
    """Result of conflict resolution"""
    resolved: bool
    consensus_value: Optional[Any] = None
    confidence_score: float = 0.0
    dissenting_agents: List[str] = None
    resolution_method: str = ""
    reasoning: str = ""

    def __post_init__(self):
        if self.dissenting_agents is None:
            self.dissenting_agents = []


@dataclass
class AgentOpinion:
    """An agent's opinion on a conflict"""
    agent_name: str
    agent_role: str
    opinion: Any
    confidence: float  # 0.0 to 1.0
    reasoning: str = ""
    expertise_relevance: float = 0.5  # How relevant is this agent's expertise


class ConsensusManager:
    """
    Manages conflict resolution and consensus building among agents
    """

    def __init__(self):
        # Expertise weights for different conflict types
        self.expertise_weights = {
            ConflictType.VALIDATION_DISAGREEMENT: {
                "validator": 1.0,
                "executor": 0.8,
                "analyzer": 0.6,
                "observer": 0.4,
                "reasoner": 0.5,
                "actor": 0.3,
                "learner": 0.4,
                "improver": 0.5,
                "memory": 0.2
            },
            ConflictType.EXECUTION_CONFLICT: {
                "executor": 1.0,
                "actor": 0.9,
                "validator": 0.7,
                "reasoner": 0.6,
                "analyzer": 0.4,
                "observer": 0.3,
                "learner": 0.4,
                "improver": 0.5,
                "memory": 0.2
            },
            ConflictType.PLANNING_DISPUTE: {
                "reasoner": 1.0,
                "analyzer": 0.8,
                "learner": 0.7,
                "observer": 0.6,
                "validator": 0.5,
                "executor": 0.4,
                "actor": 0.4,
                "improver": 0.5,
                "memory": 0.3
            },
            ConflictType.RESOURCE_ALLOCATION: {
                "reasoner": 0.8,
                "analyzer": 0.9,
                "executor": 0.7,
                "validator": 0.6,
                "observer": 0.5,
                "actor": 0.5,
                "learner": 0.6,
                "improver": 0.7,
                "memory": 0.4
            },
            ConflictType.PRIORITY_CONFLICT: {
                "reasoner": 0.9,
                "analyzer": 0.8,
                "validator": 0.7,
                "executor": 0.6,
                "learner": 0.6,
                "observer": 0.5,
                "actor": 0.4,
                "improver": 0.5,
                "memory": 0.3
            }
        }

    async def resolve_conflict(self, conflict_type: ConflictType,
                              opinions: List[AgentOpinion],
                              method: ConsensusMethod = ConsensusMethod.EXPERTISE_WEIGHTED,
                              min_consensus_threshold: float = 0.7) -> ConflictResolution:
        """
        Resolve a conflict using the specified consensus method
        """
        if not opinions:
            return ConflictResolution(
                resolved=False,
                reasoning="No opinions provided"
            )

        if len(opinions) == 1:
            return ConflictResolution(
                resolved=True,
                consensus_value=opinions[0].opinion,
                confidence_score=opinions[0].confidence,
                resolution_method="single_opinion",
                reasoning="Only one opinion provided"
            )

        try:
            if method == ConsensusMethod.MAJORITY_VOTE:
                return await self._majority_vote(opinions)
            elif method == ConsensusMethod.WEIGHTED_VOTE:
                return await self._weighted_vote(opinions)
            elif method == ConsensusMethod.EXPERTISE_WEIGHTED:
                return await self._expertise_weighted_vote(conflict_type, opinions)
            elif method == ConsensusMethod.RANKED_CHOICE:
                return await self._ranked_choice_vote(opinions)
            elif method == ConsensusMethod.CONSENSUS_THRESHOLD:
                return await self._consensus_threshold(opinions, min_consensus_threshold)
            else:
                return ConflictResolution(
                    resolved=False,
                    reasoning=f"Unsupported consensus method: {method}"
                )
        except Exception as e:
            logger.error(f"Error in conflict resolution: {e}")
            return ConflictResolution(
                resolved=False,
                reasoning=f"Resolution failed: {str(e)}"
            )

    async def _majority_vote(self, opinions: List[AgentOpinion]) -> ConflictResolution:
        """Simple majority vote"""
        vote_counts = Counter(op.opinion for op in opinions)
        total_votes = len(opinions)

        if not vote_counts:
            return ConflictResolution(resolved=False, reasoning="No votes counted")

        winner, winner_count = vote_counts.most_common(1)[0]
        confidence = winner_count / total_votes

        dissenting = [op.agent_name for op in opinions if op.opinion != winner]

        return ConflictResolution(
            resolved=True,
            consensus_value=winner,
            confidence_score=confidence,
            dissenting_agents=dissenting,
            resolution_method="majority_vote",
            reasoning=f"Majority vote: {winner_count}/{total_votes} for {winner}"
        )

    async def _weighted_vote(self, opinions: List[AgentOpinion]) -> ConflictResolution:
        """Weighted vote based on agent confidence"""
        if not opinions:
            return ConflictResolution(resolved=False, reasoning="No opinions")

        # Weight by confidence
        weighted_votes = defaultdict(float)
        total_weight = 0

        for op in opinions:
            weight = op.confidence
            weighted_votes[op.opinion] += weight
            total_weight += weight

        if total_weight == 0:
            return ConflictResolution(resolved=False, reasoning="Zero total weight")

        # Find winner
        winner = max(weighted_votes.items(), key=lambda x: x[1])
        winner_opinion, winner_weight = winner

        confidence = winner_weight / total_weight
        dissenting = [op.agent_name for op in opinions if op.opinion != winner_opinion]

        return ConflictResolution(
            resolved=True,
            consensus_value=winner_opinion,
            confidence_score=confidence,
            dissenting_agents=dissenting,
            resolution_method="weighted_vote",
            reasoning=f"Weighted vote: {winner_weight:.2f}/{total_weight:.2f} for {winner_opinion}"
        )

    async def _expertise_weighted_vote(self, conflict_type: ConflictType,
                                     opinions: List[AgentOpinion]) -> ConflictResolution:
        """Weighted vote based on expertise relevance to conflict type"""
        weights = self.expertise_weights.get(conflict_type, {})

        if not weights:
            # Fall back to regular weighted vote
            return await self._weighted_vote(opinions)

        # Calculate expertise-weighted scores
        weighted_scores = defaultdict(float)
        total_weight = 0

        for op in opinions:
            role_weight = weights.get(op.agent_role.lower(), 0.5)
            expertise_weight = op.expertise_relevance
            confidence_weight = op.confidence

            combined_weight = role_weight * expertise_weight * confidence_weight
            weighted_scores[op.opinion] += combined_weight
            total_weight += combined_weight

        if total_weight == 0:
            return ConflictResolution(resolved=False, reasoning="Zero expertise weight")

        # Find winner
        winner = max(weighted_scores.items(), key=lambda x: x[1])
        winner_opinion, winner_score = winner

        confidence = winner_score / total_weight
        dissenting = [op.agent_name for op in opinions if op.opinion != winner_opinion]

        return ConflictResolution(
            resolved=True,
            consensus_value=winner_opinion,
            confidence_score=confidence,
            dissenting_agents=dissenting,
            resolution_method="expertise_weighted",
            reasoning=f"Expertise-weighted consensus: {winner_score:.2f}/{total_weight:.2f} for {winner_opinion}"
        )

    async def _ranked_choice_vote(self, opinions: List[AgentOpinion]) -> ConflictResolution:
        """Ranked choice voting (simplified implementation)"""
        # This is a simplified version - assumes opinions are ordered preferences
        # In practice, would need proper ranked choice implementation
        return await self._majority_vote(opinions)  # Placeholder

    async def _consensus_threshold(self, opinions: List[AgentOpinion],
                                 threshold: float) -> ConflictResolution:
        """Require consensus above threshold"""
        if not opinions:
            return ConflictResolution(resolved=False, reasoning="No opinions")

        # Check if any opinion has majority above threshold
        total_opinions = len(opinions)
        threshold_count = int(total_opinions * threshold)

        vote_counts = Counter(op.opinion for op in opinions)
        winner, winner_count = vote_counts.most_common(1)[0]

        if winner_count >= threshold_count:
            confidence = winner_count / total_opinions
            dissenting = [op.agent_name for op in opinions if op.opinion != winner]

            return ConflictResolution(
                resolved=True,
                consensus_value=winner,
                confidence_score=confidence,
                dissenting_agents=dissenting,
                resolution_method="consensus_threshold",
                reasoning=f"Consensus threshold met: {winner_count}/{total_opinions} >= {threshold_count}"
            )
        else:
            return ConflictResolution(
                resolved=False,
                reasoning=f"Consensus threshold not met: {winner_count}/{total_opinions} < {threshold_count}"
            )

    def update_expertise_weights(self, conflict_type: ConflictType,
                               role_weights: Dict[str, float]):
        """Update expertise weights for a conflict type"""
        if conflict_type not in self.expertise_weights:
            self.expertise_weights[conflict_type] = {}

        self.expertise_weights[conflict_type].update(role_weights)
        logger.info(f"Updated expertise weights for {conflict_type.value}")

    async def detect_conflict(self, opinions: List[AgentOpinion],
                            conflict_threshold: float = 0.5) -> Optional[ConflictType]:
        """
        Detect if there's a conflict in opinions
        Returns conflict type if conflict detected, None otherwise
        """
        if len(opinions) < 2:
            return None

        # Simple conflict detection: check if opinions differ significantly
        unique_opinions = set(op.opinion for op in opinions)
        if len(unique_opinions) > 1:
            # Calculate disagreement level
            max_agreement = max(Counter(op.opinion for op in opinions).values())
            agreement_ratio = max_agreement / len(opinions)

            if agreement_ratio < (1 - conflict_threshold):
                # Try to classify conflict type based on agent roles
                involved_roles = set(op.agent_role for op in opinions)

                if "validator" in involved_roles:
                    return ConflictType.VALIDATION_DISAGREEMENT
                elif "executor" in involved_roles:
                    return ConflictType.EXECUTION_CONFLICT
                elif "reasoner" in involved_roles:
                    return ConflictType.PLANNING_DISPUTE
                else:
                    return ConflictType.PRIORITY_CONFLICT

        return None