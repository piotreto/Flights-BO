from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class BeeColonyConfiguration:
    # user's limitations
    from_datetime: datetime
    to_datetime: datetime
    max_cost: float  # not used right now, simply need to add one more element to stack in dfs
    transfer_time: timedelta  # not used right now, needs to alter Airport objects
    max_transfers: int  # not used right now, need to set max_depth for dfs

    # cost function parameters
    time_priority: float  # [0, 1] value, 0 means that price is the most important, 1 means that time is
    
    # algorithm hyperparameters
    iterations: int
    
    scout_bees: int
        
    best_sites: int
    elite_sites: int
    elite_sites_bees: int
    rest_sites_bees: int
        
    max_shrinkages: int
