from .configuration import AntColonyConfiguration
from ..data import Network  # maybe you need AntNetwork for some reason, then overwrite it in the ant.data.py


class AntColonyAlgorithm:
    def __init__(
        self,
        network: Network,
        configuration: AntColonyConfiguration
    ) -> None:
        pass