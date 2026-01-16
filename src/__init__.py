# /src/__init__.py

# Import the ObserverAgent class from the submodule
# and make it available at the 'src' package level.

from .observer import ObserverAgent
from .actor import ActorAgent
from .analyzer import AnalyzerAgent
from .executor import ExecutorAgent
from .improver import ImproverAgent
from .learner import LearnerAgent
from .memory import MemoryAgent
from .reasoner import ReasonerAgent
from .validator import ValidatorAgent

#etc

# You could do the same for other important items
# from .utils.helpers import some_helper_function