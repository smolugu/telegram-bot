class WhopService:

    SAMPLE_SUBSCRIPTION_ID = "sub_ping_2026_demo_001"

    def validate_subscription(
        self,
        subscription_id: str,
    ) -> bool:

        return (
            subscription_id
            == self.SAMPLE_SUBSCRIPTION_ID
        )