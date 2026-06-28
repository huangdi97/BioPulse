# ruff: noqa: E402
"""Domain-split SQLAlchemy table definitions.

Each domain module defines its own tables + indexes, all sharing this metadata instance.
"""

from sqlalchemy import MetaData

metadata = MetaData()

from cloud.app.models.agent import *  # noqa: F403
from cloud.app.models.agent_tables_extra import *  # noqa: F403
from cloud.app.models.auth_user import *  # noqa: F403
from cloud.app.models.cognition import *  # noqa: F403
from cloud.app.models.cognition_tables_extra import *  # noqa: F403
from cloud.app.models.compliance_audit import *  # noqa: F403
from cloud.app.models.crm import *  # noqa: F403
from cloud.app.models.integration import *  # noqa: F403
from cloud.app.models.privacy import *  # noqa: F403
from cloud.app.models.training import *  # noqa: F403
