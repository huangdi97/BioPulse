from cloud.app.services.attribution_calc import AttributionCalcMixin
from cloud.app.services.attribution_check import AttributionCheckMixin
from cloud.app.services.base import BaseService


class CausalAttributionService(AttributionCalcMixin, AttributionCheckMixin, BaseService):
    pass
