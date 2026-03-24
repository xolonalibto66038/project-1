class SubscriptionRequired(Exception):
    """
    Raised anywhere in the request cycle when the user's subscription
    tier is insufficient. The SubscriptionGateMiddleware catches this
    and builds the correct redirect.
    """

    def __init__(self, required_tier, next_url=None):
        self.required_tier = required_tier
        self.next_url = next_url
        super().__init__(f"Subscription required: {required_tier}")
