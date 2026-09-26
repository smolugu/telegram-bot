from framework.models.nyam_market_context import NewYorkMarketContext


class PingRuntime:
    def __init__(self):
        # Persistent daily/session state

        self.start_time = None
        self.week_start_ny = None
        self.week_start_utc = None
        self.nq_contract = None
        self.es_contract = None

        self.nq_market_context = None
        self.es_market_context = None

        self.nq_london_market_context = None
        self.es_london_market_context = None

        self.nq_ny_market_context = None
        self.es_ny_market_context = None

        # Weekly state
        self.nq_weekly_state = None
        self.es_weekly_state = None

        # Contract-lifetime state
        self.nq_auction_engine = None
        self.es_auction_engine = None

        # Intraday state
        self.nq_seven_hour_builder = None
        self.es_seven_hour_builder = None

        # HTF candles
        self.nq_d = None
        self.es_d = None
        self.nq_7h = None
        self.es_7h = None
        self.nq_4h = None
        self.es_4h = None
        self.nq_1h = None
        self.es_1h = None


        self.nq_ib_candidate = None
        self.es_ib_candidate = None

        self.nq_buy_candidate = None
        self.nq_sell_candidate = None
        self.es_buy_candidate = None
        self.es_sell_candidate = None

        # Liquidity carried across days
        self.liquidity_nq = None
        self.liquidity_es = None
        # self.prev_liquidity_nq = None
        # self.prev_liquidity_es = None

        # Daily values
        self.nq_daily_atr = None
        self.es_daily_atr = None

        self.nq_pdh = None
        self.nq_pdl = None
        self.es_pdh = None
        self.es_pdl = None

        # Current processing state
        self.current_window = None


