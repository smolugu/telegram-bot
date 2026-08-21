from dataclasses import dataclass
from typing import Optional


@dataclass
class SubscriptionResult:
    subscription_id: str
    status: str
    plan_name: str


class WhopService:

    SAMPLE_SUBSCRIPTION_ID = "sub_ping_2026_demo_001"

    async def validate_subscription(
        self,
        subscription_id: str,
    ) -> Optional[SubscriptionResult]:

        # Temporary mock.
        # Replace this method with the Whop API later.

        if subscription_id == self.SAMPLE_SUBSCRIPTION_ID:
            return SubscriptionResult(
                subscription_id=subscription_id,
                status="active",
                plan_name="Founding Member",
            )

        return None