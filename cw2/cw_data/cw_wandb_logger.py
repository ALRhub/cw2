import os
import warnings
from time import sleep
from random import random

# To prevent conflicts between wandb and the joblib scheduler
# see https://github.com/wandb/client/issues/1525 for reference
os.environ["WANDB_START_METHOD"] = "thread"

import attrdict as ad
import wandb
from typing import Optional, Iterable

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

    def __init__(self, ignore_keys: Optional[Iterable] = None, allow_keys: Optional[Iterable] = None):
        super(WandBLogger, self).__init__(ignore_keys=ignore_keys, allow_keys=allow_keys)
        self.log_path = ""
        self.run = None

    def initialize(self, config: ad.AttrDict, rep: int, rep_log_path: str) -> None:
        if "wandb" in config.keys():
            self.log_path = rep_log_path
            self.config = ad.AttrDict(config.wandb)
            reset_wandb_env()
            job_name = config['_experiment_name'].replace("__", "_")
            runname = job_name + "_rep_{:02d}".format(rep)
            last_error = None
            
            for i in range(10):
                
                try:
                    self.run = wandb.init(project=config.wandb.project,
                                          group=config.wandb.group,
                                          job_type=job_name[:127],
                                          name=runname[:127],
                                          config=config.params,
                                          dir=rep_log_path,
                                          settings=wandb.Settings(_disable_stats=config.wandb.get("disable_stats",
                                                                                                  False))
                                          )
                    return  # if starting the run is successful, exit the loop (and in this case the function)
                except Exception as e:
                    last_error = e
                    # implement a simple randomized exponential backoff if starting a run fails
                    waiting_time = ((random()/50)+0.01)*(2**i)
                    # wait between 0.01 and 10.24 seconds depending on the random seed and the iteration of the exponent

                    warnings.warn("Problem with starting wandb: {}. Trying again in {} seconds".format(e, waiting_time))
                    sleep(waiting_time)
            warnings.warn("wandb init failed several times.")
            raise last_error

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
