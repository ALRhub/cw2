import abc
import datetime as dt
import os
import pprint

import attrdict
import pandas as pd


class ResultData:
    def __init__(self, data: dict, rep: int, n: int):
        self.data = data
        self.meta_data = self.__create_meta_data(rep, n)

    def __create_meta_data(self, rep: int, n: int) -> dict:
        meta_data = {}
        meta_data["ts"] = dt.datetime.now()
        meta_data["r"] = rep
        meta_data["i"] = n

        return meta_data


class ResultProcessor(abc.ABC):
    @abc.abstractmethod
    def process(self, res: ResultData, config: attrdict) -> None:
        pass


class ResultPrint(ResultProcessor):
    def process(self, res: ResultData, config: attrdict) -> None:
        full_res = {**res.data, **res.meta_data}
        print()
        pprint.pprint(full_res)


class PandasSaver(ResultProcessor):
    def __init__(self):
        self.df: pd.DataFrame = None

    def _setup(self, config: attrdict, full_res: dict) -> None:
        _index = pd.MultiIndex.from_product(
            [range(config.repetitions), range(config.iterations)],
            names=['r', 'i']
        )

        self.df = pd.DataFrame(
            index=_index, columns=full_res.keys(), dtype=float)

    def process(self, res: ResultData, config: attrdict) -> None:
        full_res = {**res.data, **res.meta_data}

        if self.df is None:
            self._setup(config, full_res)

        self.df.loc[full_res["r"], full_res["i"]] = full_res

        with open(os.path.join(config.path, 'results.csv'), 'w') as results_file:
            self.df.to_csv(results_file)
