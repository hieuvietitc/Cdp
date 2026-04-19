"""
Meta Ads (Facebook) destination: upload/sync a Custom Audience.

Config keys:
  access_token   — Meta User Access Token (or System User token)
  ad_account_id  — e.g. "act_123456789"
  audience_id    — existing Custom Audience ID (created once via API or Ads Manager)
  audience_name  — used when creating a new audience if audience_id not set
"""
import hashlib
import json
import logging

import httpx

from app.destinations.base import BaseDestination

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v19.0"
BATCH_SIZE = 10_000  # Meta max per request


def _sha256(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


class MetaAdsDestination(BaseDestination):

    def send(self, profiles: list[dict]) -> tuple[int, list[str]]:
        audience_id = self._get_or_create_audience()
        sent = 0
        errors = []

        for i in range(0, len(profiles), BATCH_SIZE):
            batch = profiles[i : i + BATCH_SIZE]
            schema = ["EMAIL", "PHONE", "FN", "LN"]
            data = []
            for p in batch:
                traits = p.get("traits", {})
                full_name = (traits.get("full_name") or "").split()
                fn = full_name[0] if full_name else ""
                ln = " ".join(full_name[1:]) if len(full_name) > 1 else ""
                phone = (p.get("phone") or "").replace("+", "").replace(" ", "")
                email = (p.get("email") or "").strip().lower()
                data.append([
                    _sha256(email) if email else "",
                    _sha256(phone) if phone else "",
                    _sha256(fn.lower()) if fn else "",
                    _sha256(ln.lower()) if ln else "",
                ])

            payload = {
                "payload": json.dumps({"schema": schema, "data": data}),
                "access_token": self.config["access_token"],
            }
            try:
                url = f"{GRAPH_URL}/{audience_id}/users"
                resp = httpx.post(url, data=payload, timeout=60)
                result = resp.json()
                if "num_received" in result:
                    sent += result.get("num_received", 0)
                else:
                    errors.append(f"Meta API error: {result.get('error', {}).get('message', 'unknown')}")
            except Exception as e:
                errors.append(str(e))
                logger.error("Meta Ads batch error: %s", e)

        return sent, errors

    def test(self) -> bool:
        try:
            resp = httpx.get(
                f"{GRAPH_URL}/me",
                params={"access_token": self.config["access_token"]},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def _get_or_create_audience(self) -> str:
        audience_id = self.config.get("audience_id")
        if audience_id:
            return audience_id

        # Create a new custom audience
        payload = {
            "name": self.config.get("audience_name", "CDP Segment"),
            "subtype": "CUSTOM",
            "customer_file_source": "USER_PROVIDED_ONLY",
            "access_token": self.config["access_token"],
        }
        resp = httpx.post(
            f"{GRAPH_URL}/{self.config['ad_account_id']}/customaudiences",
            data=payload,
            timeout=30,
        )
        result = resp.json()
        new_id = result.get("id")
        if not new_id:
            raise ValueError(f"Failed to create Meta audience: {result}")
        # Cache back in config so next run reuses it
        self.config["audience_id"] = new_id
        return new_id
