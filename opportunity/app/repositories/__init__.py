import importlib.util
import os
import sys

# Load the original repositories.py module (shadowed by this package directory)
_old_path = os.path.join(os.path.dirname(__file__), "..", "repositories.py")
_spec = importlib.util.spec_from_file_location("_old_repositories_module", os.path.abspath(_old_path))
_old_mod = importlib.util.module_from_spec(_spec)
sys.modules["_old_repositories_module"] = _old_mod
_spec.loader.exec_module(_old_mod)

# Re-export every public name from the old module so all existing imports still work
from _old_repositories_module import *  # noqa: F403

# Import new-style repository classes from sub-modules
from .bidding_repository import BiddingRepository, BiddingAgentRepository, BookmarkRepository
from .contact_repository import ContactRepository, OpportunityRepository, ResearchRepository
from .scoring_repository import ScoringRepository, StatsRepository, TrendRepository, PubPeerRepository
