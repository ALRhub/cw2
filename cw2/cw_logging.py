import abc
import datetime as dt
import os
import pprint

import attrdict
import pandas as pd


class ResultData:
    """Wrappper for result dictionaries.
    Adds additional metadata like the timestamp
    """

    def __init__(self, data: dict, rep: int, n: int):
        self._data = data

        self._data["ts"] = dt.datetime.now()
        self._data["r"] = rep
        self._data["i"] = n

    def get(self) -> dict:
        """getter for the data itself

        Returns:
            dict -- iteration result dictionary including 'metadata'
        """
        return self._data


class AbstractLogger(abc.ABC):
    """Abstract Base Class for all Loggers
    """

    def log_raw_result(self, data: dict, rep: int, n: int) -> None:
        """interface to the framework to process the raw iteration result dictionary. 
        Internally calls the process method implemented by the subclass.

        Arguments:
            data {dict} -- iteration result
            rep {int} -- repetition counter
            n {int} -- iteration counter
        """
        self.process(ResultData(data, rep, n))

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
    def process(self, res: ResultData) -> None:
        """needs to be implemented by subclass.
        The main method. Defines how the logger handles the result of each iteration.

        Arguments:
            res {ResultData} -- iteration result including metadata
        """
        raise NotImplementedError

    @abc.abstractmethod
    def finalize(self) -> None:
        """needs to be implemented by subclass.
        Called at the end of each repetition.
        Use it to finalize the processing like write to disk or other cleanup
        """
        raise NotImplementedError


class LoggerArray(AbstractLogger):
    """Storage for multiple AbstractLogger objects.
    Behaves to the outside like a simple AbstractLogger implementation.
    Used to apply multiple loggers in a run.
    """

    def __init__(self):
        self._logger_array = []

    def add(self, logger: AbstractLogger) -> None:
        self._logger_array.append(logger)

    def initialize(self, config: attrdict.AttrDict, rep: int) -> None:
        for logger in self._logger_array:
            logger.initialize(config, rep)

    def process(self, res: ResultData) -> None:
        for logger in self._logger_array:
            logger.process(res)

    def finalize(self) -> None:
        for logger in self._logger_array:
            logger.finalize()


class Printer(AbstractLogger):
    """Prints the result of each iteration to the console.
    """

    def initialize(self, config: attrdict.AttrDict, rep: int) -> None:
        pass

    def process(self, res: ResultData) -> None:
        print()
        pprint.pprint(res.get())

    def finalize(self) -> None:
        pass


class PandasAllSaver(AbstractLogger):
    """Writes the results of all repetiitions and iterations as CSV to disk.
    Write occurs only after the job execution is finished.
    XXX: Deprecated: Problems with Paralellization
    """

    def __init__(self):
        self._data = []
        self.f_name = 'results.csv'

    def initialize(self, config: attrdict.AttrDict, rep: int) -> None:
        self.f_name = os.path.join(config.path, self.f_name)
        pass

    def process(self, res: ResultData) -> None:
        full_res = res.get()
        self._data.append(full_res)

    def finalize(self) -> None:
        df = pd.DataFrame(self._data)
        df = df.set_index(["r", "i"])

        with open(self.f_name, 'w') as results_file:
            df.to_csv(results_file)


class PandasRepSaver(AbstractLogger):
    """Writes the results of each repetition seperately to disk
    Each repetition is saved in its own directory. Write occurs after every iteration.
    """

    def __init__(self):
        self.rep_paths = []
        self.f_name = "rep.csv"

    def initialize(self, config: attrdict.AttrDict, rep: int):
        self.rep_paths = config.rep_log_paths
        self.f_name = os.path.join(
            self.rep_paths[rep], 'rep_{}.csv'.format(rep))

    def process(self, res: ResultData) -> None:
        full_res = res.get()

        if full_res['i'] == 0:
            pd.DataFrame(full_res, index=[0]).to_csv(
                self.f_name, mode='w', header=True, index_label='iteration')
        else:
            pd.DataFrame(full_res, index=[full_res['i']]).to_csv(
                self.f_name, mode='a', header=False)

    def finalize(self) -> None:
        pass

    def load(self):
        return pd.read_csv(self.f_name) 
