import abc
import logging
import os
import pprint
import sys
from typing import Iterable, Optional, Dict, List


class AbstractLogger(abc.ABC):
    """Abstract Base Class for all Loggers
    """

    def __init__(self, ignore_keys: Optional[Iterable] = None, allow_keys: Optional[Iterable] = None):
        """
        Initialize a logger that records based on (a subset of) the provided keys
        :param ignore_keys: A list of keys
        :param allow_keys:
        """
        assert ignore_keys is None or allow_keys is None, \
            "Logging keys can either be whitelisted ('ignore_keys') or blacklisted ('allow_keys'), but not both"
        self.ignore_keys = ignore_keys
        self.allow_keys = allow_keys

    def filter(self, data: Dict) -> Dict:
        """
        Base Function. Either filters out ignored keys or looks for allowed ones

        Args:
            data: data payload dict
        """
        if self.ignore_keys is not None:  # blacklist ignored keys
            return {key: value for key, value in data.items() if key not in self.ignore_keys}
        elif self.allow_keys is not None:  # whitelist allowed keys
            return {key: value for key, value in data.items() if key in self.allow_keys}
        else:  # use all keys
            return data

    def preprocess(self, *args):
        """
        intended to be called during Experiment.initialize()
        """
        pass

    @abc.abstractmethod
    def initialize(self, config: dict, rep: int, rep_log_path: str) -> None:
        """needs to be implemented by subclass.
        Called once at the start of each repetition.
        Used to configure / reset the Logger for each repetition.

        Arguments:
            config {attrdict.Attrdict} -- configuration
            rep {int} -- repetition counter
        """
        raise NotImplementedError

    @abc.abstractmethod
    def process(self, data: dict) -> None:
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

    def initialize(self, config: dict, rep: int, rep_log_path: str) -> None:
        for logger in self._logger_array:
            logger.initialize(config, rep, rep_log_path)

    def preprocess(self, *args):
        for logger in self._logger_array:
            logger.preprocess(*args)

    def process(self, data: dict) -> None:
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
                getLogger().exception(logger.__class__.__name__)
                d = "Error when loading {}".format(logger.__class__.__name__)

            if d is not None:
                if not isinstance(d, dict):
                    d = {logger.__class__.__name__: d}
                data.update(d)
        return data

    def __iter__(self):
        return iter(self._logger_array)

    def is_empty(self) -> bool:
        return len(self._logger_array) == 0


class Printer(AbstractLogger):
    """Prints the result of each iteration to the console.
    """

    def initialize(self, config: dict, rep: int, rep_log_path: str) -> None:
        pass

    def process(self, data: dict) -> None:
        data_ = self.filter(data)
        pprint.pprint(data_)

    def finalize(self) -> None:
        pass

    def load(self):
        pass


class PythonLogger(AbstractLogger):
    """
    Logger which writes calls to logging.getLogger('cw2') on to disk
    """

    def __init__(self):
        self.logger = getLogger()

    def initialize(self, config: dict, rep: int, rep_log_path: str) -> None:
        self.outh = logging.FileHandler(os.path.join(rep_log_path, 'out.log'), delay=True)
        self.outh.setLevel(logging.INFO)
        self.outh.setFormatter(_formatter)
        self.logger.addHandler(self.outh)

        self.errh = logging.FileHandler(os.path.join(rep_log_path, 'err.log'))
        self.errh.setLevel(logging.ERROR)
        self.errh.setFormatter(_formatter)
        self.logger.addHandler(self.errh)

    def process(self, data: dict) -> None:
        pass

    def finalize(self) -> None:
        for h in [self.outh, self.errh]:
            h.flush()
            h.close()
            self.logger.removeHandler(h)

    def load(self):
        pass


### logging module functionality ####

class _CWFormatter(logging.Formatter):
    """Taken From CW V1
    """

    def __init__(self):
        # self.std_formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s')
        self.std_formatter = logging.Formatter('[%(name)s] [%(levelname)s] %(message)s')
        self.red_formatter = logging.Formatter(
            '[%(asctime)s]:[%(name)s] [%(levelname)s] %(message)s')

    def format(self, record: logging.LogRecord):
        if record.levelno < logging.ERROR:
            return self.std_formatter.format(record)
        else:
            return self.red_formatter.format(record)


_formatter = _CWFormatter()


def getLogger() -> logging.Logger:
    """creates a logging.getLogger('cw2') object with initialization.
    Parallelization via joblib needs a more sophisticated getLogger function.

    Returns:
        logging.Logger
    """
    _logging_logger = logging.getLogger('cw2')

    if _logging_logger.getEffectiveLevel() > logging.INFO:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        ch.setFormatter(_formatter)

        _logging_logger.setLevel(logging.INFO)
        _logging_logger.addHandler(ch)

    return _logging_logger
