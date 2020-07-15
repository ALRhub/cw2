import abc
import datetime as dt
import logging
import os
import pprint
from typing import List

import attrdict
import pandas as pd


class AbstractLogger(abc.ABC):
    """Abstract Base Class for all Loggers
    """

    @abc.abstractmethod
    def initialize(self, config: attrdict.AttrDict, rep: int) -> None:
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

    def initialize(self, config: attrdict.AttrDict, rep: int) -> None:
        for logger in self._logger_array:
            logger.initialize(config, rep)

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
                data[logger.__class__.__name__] = d
        return data


class Printer(AbstractLogger):
    """Prints the result of each iteration to the console.
    """

    def initialize(self, config: attrdict.AttrDict, rep: int) -> None:
        pass

    def process(self, data) -> None:
        print()
        pprint.pprint(data)

    def finalize(self) -> None:
        pass

    def load(self):
        pass


class PandasRepSaver(AbstractLogger):
    """Writes the results of each repetition seperately to disk
    Each repetition is saved in its own directory. Write occurs after every iteration.
    """

    def __init__(self):
        self.log_path = ""
        self.f_name = "rep.csv"
        self.index = 0

    def initialize(self, config: attrdict.AttrDict, rep: int):
        self.log_path = config.rep_log_paths[rep]
        self.f_name = os.path.join(self.log_path, 'rep_{}.csv'.format(rep))
        self.index = 0

    def process(self, data) -> None:
        if not isinstance(data, dict):
            return

        if self.index == 0:
            pd.DataFrame(data, index=[0]).to_csv(
                self.f_name, mode='w', header=True, index_label='index')
        else:
            pd.DataFrame(data, index=[self.index]).to_csv(
                self.f_name, mode='a', header=False)

        self.index += 1

    def finalize(self) -> None:
        pass

    def load(self):
        try:
            data = pd.read_csv(self.f_name)
        except FileNotFoundError as _:
            data = "{} does not exist".format(self.f_name)
            logging.warning(data)

        return data
