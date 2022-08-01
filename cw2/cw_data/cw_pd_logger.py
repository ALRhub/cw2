import os

import pandas as pd

from cw2.cw_data import cw_logging
from typing import Optional, Iterable, Dict


class PandasLogger(cw_logging.AbstractLogger):
    """Writes the results of each repetition seperately to disk
    Each repetition is saved in its own directory. Write occurs after every iteration.
    """

    def __init__(self, ignore_keys: Optional[Iterable] = None, allow_keys: Optional[Iterable] = None):
        super().__init__(ignore_keys=ignore_keys, allow_keys=allow_keys)
        self.log_path = ""
        self.csv_name = "rep.csv"
        self.pkl_name = "rep.pkl"
        self.df = pd.DataFrame()

    def initialize(self, config: Dict, rep: int, rep_log_path: str):
        self.log_path = rep_log_path
        self.csv_name = os.path.join(self.log_path, 'rep_{}.csv'.format(rep))
        self.pkl_name = os.path.join(self.log_path, 'rep_{}.pkl'.format(rep))
        self.df = pd.DataFrame()

    def process(self, log_data: dict) -> None:
        data = self.filter(log_data)

        self.df = self.df.append(data, ignore_index=True)

        try:
            self.df.to_csv(self.csv_name, index_label='index')
        except:
            cw_logging.getLogger().warning('Could not save {}'.format(self.csv_name))

        try:
            self.df.to_pickle(self.pkl_name)
        except:
            cw_logging.getLogger().warning('Could not save {}'.format(self.pkl_name))

    def finalize(self) -> None:
        pass

    def load(self):
        payload = {}
        df: pd.DataFrame = None

        # Check if file exists
        try:
            df = pd.read_pickle(self.pkl_name)
        except FileNotFoundError as _:
            warn = "{} does not exist".format(self.pkl_name)
            cw_logging.getLogger().warning(warn)
            return warn

        # Enrich Payload with descriptive statistics for loading DF structure
        """
        for c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                payload['{}_min'.format(c)] = df[c].min()
                payload['{}_max'.format(c)] = df[c].max()
                payload['{}_mean'.format(c)] = df[c].mean()
                payload['{}_std'.format(c)] = df[c].std()

            payload['{}_last'.format(c)] = df[c].iloc[-1]
        """
        payload[self.__class__.__name__] = df
        return payload
