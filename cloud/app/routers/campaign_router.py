from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette import status

from cloud.app.services.engagement.campaign_service import CampaignService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/api/v1/campaigns", tags=["Campaigns"])


class CreateCampaignRequest(BaseModel):
    name: str
    channel: str
    target_hcps: list[str] = []


class TrackOpenRequest(BaseModel):
    campaign_id: str
    hcp_id: str
    channel: str


class TrackClickRequest(BaseModel):
    campaign_id: str
    hcp_id: str
    channel: str
    url: str


@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_campaign(
    body: CreateCampaignRequest,
    current_user: dict = Depends(require_scope("visit")),
    service: CampaignService = Depends(CampaignService),
):
    campaign_id = service.create_campaign(name=body.name, channel=body.channel, target_hcps=body.target_hcps)
    return success(data={"campaign_id": campaign_id})


@router.post("/{campaign_id}/send")
def send_campaign(
    campaign_id: str,
    current_user: dict = Depends(require_scope("visit")),
    service: CampaignService = Depends(CampaignService),
):
    result = service.send_campaign(campaign_id)
    return success(data=result)


@router.get("/{campaign_id}/stats")
def get_campaign_stats(
    campaign_id: str,
    current_user: dict = Depends(require_scope("visit")),
    service: CampaignService = Depends(CampaignService),
):
    result = service.get_stats(campaign_id)
    return success(data=result)


@router.post("/track/open")
def track_open(
    body: TrackOpenRequest,
    current_user: dict = Depends(require_scope("visit")),
    service: CampaignService = Depends(CampaignService),
):
    result = service.track_open(campaign_id=body.campaign_id, hcp_id=body.hcp_id, channel=body.channel)
    return success(data=result)


@router.post("/track/click")
def track_click(
    body: TrackClickRequest,
    current_user: dict = Depends(require_scope("visit")),
    service: CampaignService = Depends(CampaignService),
):
    result = service.track_click(campaign_id=body.campaign_id, hcp_id=body.hcp_id, channel=body.channel, url=body.url)
    return success(data=result)
