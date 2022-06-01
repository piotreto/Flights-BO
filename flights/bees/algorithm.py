from ..data import Network
from .configuration import BeeColonyConfiguration


class BeeColonyAlgorithm:
    def __init__(
        self,
        network: Network,
        configuration: BeeColonyConfiguration
    ) -> None:
        
        self._network = network
        self._configuration = configuration

    def run(self):
        pass
