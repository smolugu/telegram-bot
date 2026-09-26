from enum import Enum


class AuctionPhaseEnums(str, Enum):
    WAITING = "waiting"
    EARLY_EXPANSION = "early_expansion"
    MID_EXPANSION = "mid_expansion"
    LATE_EXPANSION = "late_expansion"
    DISTRIBUTION = "distribution"
    COMPLETE = "complete"

class StructurePhaseEnums(str, Enum):
    COMPRESSION = "compression"
    MIGRATION = "migration"
    EARLY_EXPANSION = "early_expansion"
    
    

class GroupEnums(str, Enum):
    COMPRESSION = "compression"
    DECOMPRESSION = "decompression"
    ACCEPTANCE = "acceptance"
    REBALANCE = "rebalance"
    REINTEGRATION = "reintegration"
    VALUEFLIP = "value_flip"