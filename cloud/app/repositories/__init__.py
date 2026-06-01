# Bridge: load the old single-file repositories module and re-export all classes.
# The old file cloud/app/repositories.py is shadowed by this directory,
# so we load it via file path to maintain backward compatibility.
import importlib.util
import os
import sys

_OLD_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "repositories.py")


def _load_old_repos():
    spec = importlib.util.spec_from_file_location("cloud.app.repositories_old", _OLD_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_old_mod = _load_old_repos()
for _name in dir(_old_mod):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_old_mod, _name)

# New per-class repositories
from cloud.app.repositories.agent_repository import (
    AgentExecutionTasksRepository,
    AgentMarketplaceRepository,
    AgentPipelinesRepository,
    AgentRolesRepository,
    AgentSkillsRepository,
    OrchestrationTemplatesRepository,
    PipelineRunsRepository,
    PipelineStepRunsRepository,
    PipelineStepsRepository,
)
from cloud.app.repositories.audit_repository import (
    AuditChainEntriesRepository,
    AuditLogsRepository,
    BenchmarkReportsRepository,
    DpAuditLogRepository,
    FedAuditContributionsRepository,
    FederatedRoundsRepository,
)
from cloud.app.repositories.auth_repository import (
    SystemConfigsRepository,
    UserBehaviorsRepository,
    UserProfilesRepository,
    UsersRepository,
    UserTeamRepository,
    VcCredentialsRepository,
)
from cloud.app.repositories.board_repository import (
    BoardTasksRepository,
    TaskBoardsRepository,
    TeamsRepository,
)
from cloud.app.repositories.compliance_repository import (
    ComplianceAuditRecordsRepository,
    ComplianceRulesRepository,
    DataMaskingRulesRepository,
    DidRegistryRepository,
    NmpaComplianceLogsRepository,
)
from cloud.app.repositories.compute_repository import (
    EffectMetricsRepository,
    PrivacyBudgetsRepository,
    PrivacyComputeJobsRepository,
    SensorSessionsRepository,
)
from cloud.app.repositories.event_bus_repository import (
    EventBusDefinitionsRepository,
    EventBusMessagesRepository,
    EventDeliveryLogRepository,
)
from cloud.app.repositories.kg_repository import (
    KgEntitiesRepository,
    KgRelationsRepository,
    KgSearchCacheRepository,
)
from cloud.app.repositories.market_intel_repository import (
    MarketIntelItemsRepository,
    MarketIntelSourcesRepository,
    McpToolsRepository,
)
from cloud.app.repositories.mdt_decision_repository import (
    AsyncMdtOpinionsRepository,
    CausalAnalysesRepository,
    CausalGraphsRepository,
    CollaborationSessionsRepository,
    CollaborationStepsRepository,
    CounterfactualScenariosRepository,
    CrossCaseInsightsRepository,
    DecisionCasesRepository,
    MdtOpinionsRepository,
    MdtParticipantsRepository,
    MdtSessionsRepository,
    SoapDecisionsRepository,
    SoapTemplatesRepository,
)
from cloud.app.repositories.memory_repository import (
    EpisodicMemoryRepository,
    MemoryConsolidationLogRepository,
    MemoryEntriesRepository,
    MemoryGatesRepository,
    MemoryRecallLogRepository,
    MemoryUtilityScoresRepository,
    NodeMemoryLinksRepository,
    SleepConsolidationLogsRepository,
    WorkingMemoryRepository,
)
from cloud.app.repositories.notification_repository import (
    NotificationsRepository,
    NotificationTemplatesRepository,
)
from cloud.app.repositories.opportunity_repository import (
    CustomerInteractionsRepository,
    CustomersRepository,
    HcpInteractionsRepository,
    HcpProfilesRepository,
    HcpSimulationsRepository,
    OpportunitiesRepository,
)
from cloud.app.repositories.pi_repository import PiRepository
from cloud.app.repositories.product_repository import ProductRepository
from cloud.app.repositories.recommendation_repository import (
    ContentsRepository,
    RecommendationsRepository,
    SupplyChainItemsRepository,
)
from cloud.app.repositories.route_repository import (
    RouteLogsRepository,
    RouteRulesRepository,
    RouteStatsRepository,
)
from cloud.app.repositories.training_repository import (
    TrainingAttributionsRepository,
    TrainingCorrectionsRepository,
    TrainingModulesRepository,
    TrainingRoiAnalysisRepository,
    TrainingScriptsRepository,
    TrainingSessionsRepository,
)
from cloud.app.repositories.world_tree_repository import (
    WorldTreeNodesRepository,
    WorldTreeSnapshotsRepository,
)
