import abc
from cw2 import cw_logging
import datetime as dt

class AbstractExperiment(abc.ABC):
    @abc.abstractmethod
    def initialize(self, config: dict, rep: int) -> None:
        """needs to be implemented by subclass.
        Called once at the start of each repition for initialization purposes.

        Arguments:
            config {dict} -- parameter configuration
            rep {int} -- repition counter
        """
        raise NotImplementedError
    
    @abc.abstractmethod
    def run(self, config: dict, rep: int, logger: cw_logging.AbstractLogger) -> None:
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

    @abc.abstractmethod
    def restore_state(self, config: dict, rep: int, n: int) -> bool:
        """needs to be implemented by subclass.
        if the experiment supports restarting within a repetition
        (on iteration level), load necessary stored state in this
        function. Otherwise, restarting will be done on repetition
        level, deleting all unfinished repetitions and restarting
        the experiments.

        Arguments:
            config {dict} -- parameter configuration
            rep {int} -- repition counter
            n {int} -- iteration counter

        Returns:
            bool -- success
        """
        raise NotImplementedError

    def run(self, config: dict, rep: int, logger: cw_logging.AbstractLogger) -> None:
        for n in range(config.iterations):
            res = self.iterate(config, rep, n)
            
            res["ts"] = dt.datetime.now()
            res["rep"] = rep
            res["iter"] = n
            logger.process(res)
            
            self.save_state(config, rep, n)