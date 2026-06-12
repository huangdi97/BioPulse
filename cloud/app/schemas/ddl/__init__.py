"""DDL schema package - aggregates all domain SQL into SCHEMA_SQL."""

from .agent import AGENT_SQL
from .audit import AUDIT_SQL
from .auth import AUTH_SQL
from .batch3 import BATCH3_SQL
from .collab import COLLAB_SQL
from .content import CONTENT_SQL
from .customer import CUSTOMER_SQL
from .decision import DECISION_SQL
from .did import DID_SQL
from .eventbus import EVENTBUS_SQL
from .exec import EXEC_SQL
from .hcp import HCP_SQL
from .kg import KG_SQL
from .market import MARKET_SQL
from .mdt import MDT_SQL
from .memory import MEMORY_SQL
from .misc import MISC_SQL
from .privacy import PRIVACY_SQL
from .route import ROUTE_SQL
from .soap import SOAP_SQL
from .task import TASK_SQL
from .training import TRAINING_SQL
from .userprofile import USERPROFILE_SQL
from .workingmem import WORKINGMEM_SQL
from .worldtree import WORLDTREE_SQL

SCHEMA_SQL = (
    AUTH_SQL
    + CONTENT_SQL
    + AUDIT_SQL
    + TASK_SQL
    + CUSTOMER_SQL
    + MARKET_SQL
    + AGENT_SQL
    + DECISION_SQL
    + MDT_SQL
    + MEMORY_SQL
    + WORLDTREE_SQL
    + ROUTE_SQL
    + HCP_SQL
    + TRAINING_SQL
    + SOAP_SQL
    + WORKINGMEM_SQL
    + DID_SQL
    + KG_SQL
    + USERPROFILE_SQL
    + COLLAB_SQL
    + EVENTBUS_SQL
    + EXEC_SQL
    + PRIVACY_SQL
    + MISC_SQL
    + BATCH3_SQL
)

__all__ = [
    "AGENT_SQL",
    "AUDIT_SQL",
    "AUTH_SQL",
    "COLLAB_SQL",
    "CONTENT_SQL",
    "CUSTOMER_SQL",
    "DECISION_SQL",
    "DID_SQL",
    "EVENTBUS_SQL",
    "EXEC_SQL",
    "HCP_SQL",
    "KG_SQL",
    "MARKET_SQL",
    "MDT_SQL",
    "MEMORY_SQL",
    "MISC_SQL",
    "PRIVACY_SQL",
    "ROUTE_SQL",
    "SCHEMA_SQL",
    "SOAP_SQL",
    "TASK_SQL",
    "TRAINING_SQL",
    "USERPROFILE_SQL",
    "WORKINGMEM_SQL",
    "WORLDTREE_SQL",
]
