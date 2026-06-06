"""Cell 网络服务，组合 CRUD 与同步混入提供 Agent 网络全功能。"""

from cloud.app.services.base import BaseService
from cloud.app.services.network_crud import NetworkCrudMixin
from cloud.app.services.network_sync import NetworkSyncMixin


class CellNetworkService(NetworkCrudMixin, NetworkSyncMixin, BaseService):
    """Cell 网络服务，整合网络 CRUD 与节点同步能力。"""

    pass
