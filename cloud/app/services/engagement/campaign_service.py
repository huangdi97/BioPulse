from typing import Dict, List, Optional
from uuid import uuid4


class CampaignService:
    """Campaign management service using in-memory dict storage."""

    def __init__(self):
        self._campaigns: Dict[str, dict] = {}
        self._stats: Dict[str, dict] = {}

    def create_campaign(self, name: str, channel: str, target_hcps: Optional[List[str]] = None) -> str:
        """Create a new campaign and return its unique ID."""
        campaign_id = str(uuid4())
        self._campaigns[campaign_id] = {
            "id": campaign_id,
            "name": name,
            "channel": channel,
            "target_hcps": target_hcps or [],
            "status": "draft",
        }
        self._stats[campaign_id] = {
            "sent": 0,
            "opens": 0,
            "clicks": 0,
            "open_details": [],
            "click_details": [],
        }
        return campaign_id

    def send_campaign(self, campaign_id: str) -> dict:
        """Send a campaign by ID and return the updated campaign."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            raise KeyError(f"Campaign {campaign_id} not found")
        campaign["status"] = "sent"
        self._stats[campaign_id]["sent"] = len(campaign["target_hcps"])
        return campaign

    def track_open(self, campaign_id: str, hcp_id: str, channel: str) -> dict:
        """Record an open event for a campaign."""
        if campaign_id not in self._campaigns:
            raise KeyError(f"Campaign {campaign_id} not found")
        stat = self._stats[campaign_id]
        stat["opens"] += 1
        stat["open_details"].append({"hcp_id": hcp_id, "channel": channel})
        return {"campaign_id": campaign_id, "hcp_id": hcp_id, "channel": channel}

    def track_click(self, campaign_id: str, hcp_id: str, channel: str, url: str) -> dict:
        """Record a click event for a campaign."""
        if campaign_id not in self._campaigns:
            raise KeyError(f"Campaign {campaign_id} not found")
        stat = self._stats[campaign_id]
        stat["clicks"] += 1
        stat["click_details"].append({"hcp_id": hcp_id, "channel": channel, "url": url})
        return {"campaign_id": campaign_id, "hcp_id": hcp_id, "channel": channel, "url": url}

    def get_stats(self, campaign_id: str) -> dict:
        """Return aggregate stats for a campaign."""
        campaign = self._campaigns.get(campaign_id)
        if not campaign:
            raise KeyError(f"Campaign {campaign_id} not found")
        base = self._stats[campaign_id]
        return {
            "campaign_id": campaign_id,
            "name": campaign["name"],
            "status": campaign["status"],
            "sent": base["sent"],
            "opens": base["opens"],
            "clicks": base["clicks"],
            "open_rate": round(base["opens"] / base["sent"], 4) if base["sent"] else 0.0,
            "click_rate": round(base["clicks"] / base["sent"], 4) if base["sent"] else 0.0,
        }
