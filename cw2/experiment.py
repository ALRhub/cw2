import abc
import datetime as dt

from cw2.cw_data import cw_logging
from cw2.cw_error import ExperimentSurrender


class AbstractExperiment(abc.ABC):
    @abc.abstractmethod
    def initialize(self, cw_config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
        """needs to be implemented by subclass.
        Called once at the start of each repition for initialization purposes.

        Arguments:
            cw_config {dict} -- clusterwork experiment configuration
            rep {int} -- repition counter
            logger {cw_logging.LoggerArray} -- initialized loggers for preprocessing
        """
        raise NotImplementedError

    @abc.abstractmethod
    def run(self, cw_config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
        """needs to be implemented by subclass.
        Called after initialize(). Should be the main procedure of the experiment.

        Args:
            config (dict): clusterwork experiment configuration
            rep (int): [description]
            logger (cw_logging.LoggerArray): [description]

        Raises:
            NotImplementedError: [description]
        """
        raise NotImplementedError

    @abc.abstractmethod
    def finalize(self, surrender: ExperimentSurrender = None, crash: bool = False):
        """needs to be implemented by subclass.
        Is guaranteed to be called after the experiment has run, even in case of exceptions during execution.

        Args:
            surrender (ExperimentSurrender, optional): when the experiment raises an ExperimentSurrender, this object can be accessed here. Defaults to None.
            crash (bool, optional): indicating if the experiment raised a 'serious' Exception. Defaults to False.
        """
        raise NotImplementedError


class AbstractIterativeExperiment(AbstractExperiment):
    @abc.abstractmethod
    def iterate(self, cw_config: dict, rep: int, n: int) -> dict:
        """needs to be implemented by subclass.
        The iteration procedure.

        Arguments:
            cw_config {dict} -- clusterwork experiment configuration
            rep {int} -- repitition counter
            n {int} -- iteration counter

        Returns:
            dict -- result map
        """
        raise NotImplementedError

    @abc.abstractmethod
    def save_state(self, cw_config: dict, rep: int, n: int) -> None:
        """needs to be implemented by subclass.
        Intended to save an intermediate state after each iteration.
        Arguments:
            cw_config {dict} -- clusterwork experiment configuration
            rep {int} -- repitition counter
            n {int} -- [description]
        """
        raise NotImplementedError

    def run(self, cw_config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
        for n in range(cw_config["iterations"]):
            surrender = False
            try:
                res = self.iterate(cw_config, rep, n)
            except ExperimentSurrender as e:
                res = e.payload
                surrender = True

            res["ts"] = dt.datetime.now()
            res["rep"] = rep
            res["iter"] = n
            logger.process(res)

            self.save_state(cw_config, rep, n)

            if surrender:
                raise ExperimentSurrender()
