from cloud.app.services.base import BaseService
from cloud.app.services.network_crud import NetworkCrudMixin
from cloud.app.services.network_sync import NetworkSyncMixin


class CellNetworkService(NetworkCrudMixin, NetworkSyncMixin, BaseService):
    pass
