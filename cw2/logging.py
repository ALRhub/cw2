import abc
import datetime as dt
import os
import pprint

import attrdict
import pandas as pd


class ResultData:
    def __init__(self, data: dict, rep: int, n: int):
        self._data = data

        self._data["ts"] = dt.datetime.now()
        self._data["r"] = rep
        self._data["i"] = n

    def get(self):
        return self._data


class ResultLogger(abc.ABC):
    def log_raw_result(self, data: dict, rep: int, n: int) -> None:
        self.process(ResultData(data, rep, n))

    @abc.abstractmethod
    def configure(self, config: attrdict) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rep_setup(self, rep: int) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def process(self, res: ResultData) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rep_finalize(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def global_finalize(self) -> None:
        raise NotImplementedError


class ResultLoggerArray(ResultLogger):
    def __init__(self):
        self._logger_array = []

    def add(self, logger: ResultLogger) -> None:
        self._logger_array.append(logger)

    def configure(self, config: attrdict) -> None:
        for logger in self._logger_array:
            logger.configure(config)

    def rep_setup(self, rep: int) -> None:
        for logger in self._logger_array:
            logger.rep_setup(rep)

    def process(self, res: ResultData) -> None:
        for logger in self._logger_array:
            logger.process(res)

    def rep_finalize(self) -> None:
        for logger in self._logger_array:
            logger.rep_finalize()

    def global_finalize(self) -> None:
        for logger in self._logger_array:
            logger.global_finalize()


class Printer(ResultLogger):
    def configure(self, config: attrdict) -> None:
        pass

    def rep_setup(self, rep: int) -> None:
        pass

    def process(self, res: ResultData) -> None:
        print()
        pprint.pprint(res.get())

    def rep_finalize(self) -> None:
        pass

    def global_finalize(self) -> None:
        pass


class PandasAllSaver(ResultLogger):
    def __init__(self):
        self._data = []
        self.f_name = 'results.csv'

    def configure(self, config: attrdict) -> None:
        self.f_name = os.path.join(config.path, self.f_name)

    def rep_setup(self, rep: int) -> None:
        pass

    def process(self, res: ResultData) -> None:
        full_res = res.get()
        self._data.append(full_res)

    def rep_finalize(self) -> None:
        pass

    def global_finalize(self) -> None:
        df = pd.DataFrame(self._data)
        df = df.set_index(["r", "i"])

        with open(self.f_name, 'w') as results_file:
            df.to_csv(results_file)


class PandasRepSaver(ResultLogger):
    def __init__(self):
        self.rep_paths = []
        self.f_name = "rep.csv"

    def configure(self, config: attrdict) -> None:
        self.rep_paths = config.rep_log_paths

    def rep_setup(self, rep: int):
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

    def rep_finalize(self) -> None:
        pass

    def global_finalize(self) -> None:
        pass
