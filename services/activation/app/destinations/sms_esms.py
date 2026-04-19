"""
eSMS (Vietnam) destination: send bulk SMS to segment members.

Config keys:
  api_key       — eSMS API key
  secret_key    — eSMS secret key
  brand_name    — SMS sender name (brandname approved by eSMS)
  message       — SMS message template (supports {full_name} placeholder)
  sms_type      — 2 = brandname, 4 = OTP (default 2)
"""
import hashlib
import logging
from string import Template

import httpx

from app.destinations.base import BaseDestination

logger = logging.getLogger(__name__)

ESMS_URL = "https://rest.esms.vn/MainService.svc/json/SendMultipleMessage_V4_post_json/"


class ESMSDestination(BaseDestination):
    BATCH_SIZE = 200

    def send(self, profiles: list[dict]) -> tuple[int, list[str]]:
        sent = 0
        errors = []
        message_template = self.config.get("message", "Xin chào {full_name}, chúng tôi có ưu đãi đặc biệt dành cho bạn!")
        api_key = self.config["api_key"]
        secret_key = self.config["secret_key"]
        brand_name = self.config.get("brand_name", "")
        sms_type = str(self.config.get("sms_type", 2))

        for i in range(0, len(profiles), self.BATCH_SIZE):
            batch = profiles[i : i + self.BATCH_SIZE]
            sms_list = []
            for p in batch:
                phone = p.get("phone", "")
                if not phone:
                    continue
                # Normalise: +84xxx → 84xxx (eSMS format)
                if phone.startswith("+"):
                    phone = phone[1:]
                traits = p.get("traits", {})
                full_name = traits.get("full_name") or "Quý khách"
                msg = message_template.replace("{full_name}", full_name)
                sms_list.append({"Phone": phone, "Content": msg, "IsUnicode": "1"})

            if not sms_list:
                continue

            payload = {
                "ApiKey": api_key,
                "SecretKey": secret_key,
                "Brandname": brand_name,
                "SmsType": sms_type,
                "SmsList": sms_list,
            }
            try:
                response = httpx.post(ESMS_URL, json=payload, timeout=30)
                data = response.json()
                if data.get("CodeResult") == "100":
                    sent += len(sms_list)
                else:
                    errors.append(f"Batch {i}: eSMS error {data.get('CodeResult')} - {data.get('ErrorMessage')}")
            except Exception as e:
                errors.append(f"Batch {i}: {e}")
                logger.error("eSMS error: %s", e)

        return sent, errors

    def test(self) -> bool:
        return bool(self.config.get("api_key") and self.config.get("secret_key"))
