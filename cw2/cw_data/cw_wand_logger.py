import os
import attrdict
# import pandas as pd
import wandb
from cw2.cw_data import cw_logging


class WandLogger(cw_logging.AbstractLogger):
    def __init__(self, ignore_keys: list = []):
        self.log_path = ""
        self.csv_name = "rep.csv"
        self.pkl_name = "rep.pkl"
        self.ignore_keys = ignore_keys
        #self.index = 0

    def initialize(self, config: attrdict.AttrDict, rep: int, rep_log_path: str) -> None:
        wandb.init(project=config.name, config=config.params, group=config.name + "_{:02d}".format(rep))

    def process(self, data: dict) -> None:
        wandb.log(data)

    def finalize(self) -> None:
        pass

    def load(self):
        pass