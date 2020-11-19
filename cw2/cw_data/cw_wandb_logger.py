import os
import attrdict
# import pandas as pd
import wandb
from cw2.cw_data import cw_logging


def reset_wandb_env():
    exclude = {
        "WANDB_PROJECT",
        "WANDB_ENTITY",
        "WANDB_API_KEY",
    }
    for k, v in os.environ.items():
        if k.startswith("WANDB_") and k not in exclude:
            del os.environ[k]


class WandBLogger(cw_logging.AbstractLogger):
    def __init__(self, ignore_keys: list = []):
        self.log_path = ""
        self.ignore_keys = ignore_keys
        self.run = None
        #self.index = 0

    def initialize(self, config: attrdict.AttrDict, rep: int, rep_log_path: str) -> None:
        self.log_path = rep_log_path
        reset_wandb_env()
        self.run = wandb.init(project=config.wandb.project,
                              group=config.wandb.group,
                              job_type=config._experiment_name,
                              name=config.name + "_rep_{:02d}".format(rep),
                              config=config,
                              dir=rep_log_path
                              )

    def process(self, data: dict) -> None:
        self.run.log(data)

    def finalize(self) -> None:
        self.run.finish()

    def load(self):
        pass