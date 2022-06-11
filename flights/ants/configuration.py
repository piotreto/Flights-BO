from dataclasses import dataclass
from datetime import datetime, timedelta

'''


DIRECT_CONNECTION_IMPACT = 0.8
TIME_IMPACT = 0.4
COST_IMPACT = 0.2
PHEROMONE_IMPACT = 0.4

PHEROMONE_UPDATE = 0.5
PHEROMONE_UPDATING_TIME = 1000

COST_FUN_TIME_IMP = 0.5
'''


@dataclass
class AntColonyConfiguration:
    #technical parameters
    iters_numb: int
    result_samples: int
    ants_number: int
    ants_spawn_iters: int
    connection_samples: int

    # algorithm hyperparameters
    direct_connection_impact: float
    time_impact_nodes: float
    pheromone_impact: float

    # user's limitations
    min_time: datetime
    max_time: datetime
    min_conn_time: int
    max_conn_numb: int
    max_price: int

    pheromone_updating_time: int

    # cost function parameter
    time_impact_choice: float