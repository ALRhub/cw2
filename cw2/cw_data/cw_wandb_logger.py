import os
import warnings

# To prevent conflicts between wandb and the joblib scheduler
# see https://github.com/wandb/client/issues/1525 for reference
os.environ["WANDB_START_METHOD"] = "thread"

import attrdict as ad
import wandb

from cw2.cw_data import cw_logging


def reset_wandb_env():
    exclude = {
        "WANDB_PROJECT",
        "WANDB_ENTITY",
        "WANDB_API_KEY",
        "WANDB_START_METHOD",
    }
    for k, v in os.environ.items():
        if k.startswith("WANDB_") and k not in exclude:
            del os.environ[k]


class WandBLogger(cw_logging.AbstractLogger):

    def __init__(self, ignore_keys: list = []):
        super(WandBLogger, self).__init__(ignore_keys=ignore_keys)
        self.log_path = ""
        self.run = None

    def initialize(self, config: ad.AttrDict, rep: int, rep_log_path: str) -> None:
        if "wandb" in config.keys():
            self.log_path = rep_log_path
            self.config = ad.AttrDict(config.wandb)
            reset_wandb_env()
            job_name = config['_experiment_name'].replace("__", "_")
            self.run = wandb.init(project=config.wandb.project,
                                  group=config.wandb.group,
                                  job_type=job_name,
                                  name=job_name + "_rep_{:02d}".format(rep),
                                  config=config.params,
                                  dir=rep_log_path,
                                  settings=wandb.Settings(_disable_stats=config.wandb.get("disable_stats", False))
                                  )
        else:
            warnings.warn("No 'wandb' field in yaml - Ignoring Weights & Biases Logger")

    def process(self, data: dict) -> None:
        if self.run is not None:
            if "histogram" in self.config:
                for el in self.config.histogram:
                    if el in data:
                        self.run.log({el: wandb.Histogram(np_histogram=data[el])}, step=data["iter"])
            filtered_data = self.filter(data)
            self.run.log(filtered_data, step=data["iter"])

    def finalize(self) -> None:
        if self.run is not None:
            self.run.finish()

    def load(self):
        pass
