import abc
import datetime as dt

from cw2.cw_data import cw_logging
from cw2.cw_error import ExperimentSurrender


class AbstractExperiment(abc.ABC):
    @abc.abstractmethod
    def initialize(self, config: dict, rep: int, logger: cw_logging.AbstractLogger) -> None:
        """needs to be implemented by subclass.
        Called once at the start of each repition for initialization purposes.

        Arguments:
            config {dict} -- parameter configuration
            rep {int} -- repition counter
            logger {cw_logging.AbstractLogger} -- initialized loggers for preprocessing
        """
        raise NotImplementedError

    @abc.abstractmethod
    def run(self, config: dict, rep: int) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def finalize(self):
        """needs to be implemented by subclass.
        Called after all the iterations have finished at the end of the repitition.
        """
        raise NotImplementedError


class AbstractIterativeExperiment(AbstractExperiment):
    @abc.abstractmethod
    def iterate(self, config: dict, rep: int, n: int) -> dict:
        """needs to be implemented by subclass.
        The iteration procedure.

        Arguments:
            config {dict} -- parameter configuration
            rep {int} -- repitition counter
            n {int} -- iteration counter

        Returns:
            dict -- result map
        """
        raise NotImplementedError

    @abc.abstractmethod
    def save_state(self, config: dict, rep: int, n: int) -> None:
        """needs to be implemented by subclass.
        Intended to save an intermediate state after each iteration.
        Arguments:
            config {dict} -- parameter configuration
            rep {int} -- repitition counter
            n {int} -- [description]
        """
        raise NotImplementedError

    def run(self, config: dict, rep: int, logger: cw_logging.AbstractLogger) -> None:
        for n in range(config["iterations"]):
            surrender = False
            try:
                res = self.iterate(config, rep, n)
            except ExperimentSurrender as e:
                res = e.payload
                surrender = True

            res["ts"] = dt.datetime.now()
            res["rep"] = rep
            res["iter"] = n
            logger.process(res)

            self.save_state(config, rep, n)

            if surrender:
                raise ExperimentSurrender()

        logger.finalize()