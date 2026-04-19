"""
SendGrid destination: add profiles to a SendGrid contact list.

Config keys:
  api_key       — SendGrid API key
  list_id       — SendGrid Marketing Campaigns list UUID (optional)
  custom_fields — dict mapping CDP trait keys → SendGrid custom field IDs
"""
import logging

import sendgrid
from sendgrid.helpers.mail import Mail

from app.destinations.base import BaseDestination

logger = logging.getLogger(__name__)

UPSERT_URL = "https://api.sendgrid.com/v3/marketing/contacts"


class SendGridDestination(BaseDestination):
    BATCH_SIZE = 1000  # SendGrid max per request

    def __init__(self, config: dict):
        super().__init__(config)
        self._client = sendgrid.SendGridAPIClient(api_key=config["api_key"])

    def send(self, profiles: list[dict]) -> tuple[int, list[str]]:
        sent = 0
        errors = []
        list_id = self.config.get("list_id")
        custom_field_map = self.config.get("custom_fields", {})

        for i in range(0, len(profiles), self.BATCH_SIZE):
            batch = profiles[i : i + self.BATCH_SIZE]
            contacts = []
            for p in batch:
                traits = p.get("traits", {})
                contact = {
                    "email": p.get("email", ""),
                    "first_name": (traits.get("full_name") or "").split()[0] if traits.get("full_name") else "",
                    "last_name": " ".join((traits.get("full_name") or "").split()[1:]),
                    "phone_number": p.get("phone", ""),
                    "custom_fields": {
                        cf_id: traits.get(trait_key)
                        for trait_key, cf_id in custom_field_map.items()
                        if traits.get(trait_key) is not None
                    },
                }
                contacts.append(contact)

            payload = {"contacts": contacts}
            if list_id:
                payload["list_ids"] = [list_id]

            try:
                response = self._client.client.marketing.contacts.put(request_body=payload)
                if response.status_code in (200, 201, 202):
                    sent += len(batch)
                else:
                    errors.append(f"Batch {i}: HTTP {response.status_code}")
            except Exception as e:
                errors.append(f"Batch {i}: {e}")
                logger.error("SendGrid batch error: %s", e)

        return sent, errors

    def test(self) -> bool:
        try:
            resp = self._client.client.marketing.lists.get()
            return resp.status_code == 200
        except Exception:
            return False
