import abc
import datetime as dt
import logging
import os
import pprint
from typing import List

import attrdict


class AbstractLogger(abc.ABC):
    """Abstract Base Class for all Loggers
    """

    @abc.abstractmethod
    def initialize(self, config: attrdict.AttrDict, rep: int, rep_log_path: str) -> None:
        """needs to be implemented by subclass.
        Called once at the start of each repetition.
        Used to configure / reset the Logger for each repetition.

        Arguments:
            config {attrdict.Attrdict} -- configuration
            rep {int} -- repetition counter
        """
        raise NotImplementedError

    @abc.abstractmethod
    def process(self, data) -> None:
        """needs to be implemented by subclass.
        The main method. Defines how the logger handles the result of each iteration.

        Arguments:
            data -- data payload to be processed by logger
        """
        raise NotImplementedError

    @abc.abstractmethod
    def finalize(self) -> None:
        """needs to be implemented by subclass.
        Called at the end of each repetition.
        Use it to finalize the processing like write to disk or other cleanup
        """
        raise NotImplementedError

    @abc.abstractmethod
    def load(self):
        """needs to be implemented by subclass.
        called when the data should be loaded after execution is complete.
        """
        raise NotImplementedError


class LoggerArray(AbstractLogger):
    """Storage for multiple AbstractLogger objects.
    Behaves to the outside like a simple AbstractLogger implementation.
    Used to apply multiple loggers in a run.
    """

    def __init__(self):
        self._logger_array: List[AbstractLogger] = []

    def add(self, logger: AbstractLogger) -> None:
        self._logger_array.append(logger)

    def initialize(self, config: attrdict.AttrDict, rep: int, rep_log_path: str) -> None:
        for logger in self._logger_array:
            logger.initialize(config, rep, rep_log_path)

    def process(self, data) -> None:
        for logger in self._logger_array:
            logger.process(data)

    def finalize(self) -> None:
        for logger in self._logger_array:
            logger.finalize()

    def load(self):
        data = {}
        for logger in self._logger_array:
            try:
                d = logger.load()
            except:
                d = "Error when loading {}".format(logger.__class__.__name__)
    
            if d is not None:
                if not isinstance(d, dict):
                    d = {logger.__class__.__name__: d}
                data.update(d)
        return data

    def is_empty(self) -> bool:
        return len(self._logger_array) == 0


class Printer(AbstractLogger):
    """Prints the result of each iteration to the console.
    """

    def initialize(self, config: attrdict.AttrDict, rep: int, rep_log_path: str) -> None:
        pass

    def process(self, data) -> None:
        print()
        pprint.pprint(data)

    def finalize(self) -> None:
        pass

    def load(self):
        pass
