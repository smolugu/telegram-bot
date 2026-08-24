






from framework.models.auction.engine.initialize_auction_engine import initialize_auction_engine
from framework.models.auction.engine.refresh_auction_engine import refresh_auction_engine


def initialize_auction(auction_engine, candles_for_auction):

    initialize_auction_engine(auction_engine, candles_for_auction)
    

def refresh_auction(auction_engine, candle_30m, ltf_candles, last_3_4h_candles, last_3_7h_candles):
    
    refresh_auction_engine(auction_engine, candle_30m, ltf_candles, last_3_4h_candles, last_3_7h_candles)
