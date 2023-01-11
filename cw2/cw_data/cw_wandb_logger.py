import os
import warnings
from time import sleep
from random import random

# To prevent conflicts between wandb and the joblib scheduler
# see https://github.com/wandb/client/issues/1525 for reference
os.environ["WANDB_START_METHOD"] = "thread"

import wandb
from typing import Optional, Iterable, List, Dict
from itertools import groupby

from cw2.cw_data import cw_logging
from cw2.util import get_file_names_in_directory


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


def group_parameters(list_of_strings: List[str]):
    """ groups different strings that start with a common substring (using "." as delimiter)
        and outputs a single, more concise string.
    Example:
        outstring = group_parameters['local', 'mod.enc.tidentity', 'mod.hea.nhl5', 'mod.hea.ioFalse', 'mod.enc.hd64']
        % outstring will be 'local,mod_[enc_[hd64,tidentity],hea_[ioFalse,nhl5]]'
    """
    groups = []
    uniquekeys = []
    num_subgroups = 0
    substring = ""

    for k, g in groupby(sorted(list_of_strings), lambda string: string.split(".")[0]):
        groups.append(list(g))
        uniquekeys.append(k)

        if len(groups[-1]) == 1:
            substring += groups[-1][0] + ","
            num_subgroups += 1
        else:
            remainder = [s.replace(k, "", 1) for s in groups[-1]]
            remainder = [s.replace(".", "", 1) for s in remainder]
            if len(remainder) > 0:
                subgroups, num_subs = group_parameters(remainder)
                if num_subs > 1:
                    substring += k + "_[" + subgroups + "],"
                else:
                    substring += k + "_" + subgroups + ","
                num_subgroups += num_subs
    return substring[:-1], len(groups)


class WandBLogger(cw_logging.AbstractLogger):

    def __init__(self, ignore_keys: Optional[Iterable] = None, allow_keys: Optional[Iterable] = None):
        super(WandBLogger, self).__init__(ignore_keys=ignore_keys, allow_keys=allow_keys)
        self.log_path = ""
        self.run = None

    def initialize(self, config: Dict, rep: int, rep_log_path: str) -> None:
        if "wandb" in config.keys():
            self.init_fields(config, rep, rep_log_path)
            self.connect_to_wandb()

        else:
            warnings.warn("No 'wandb' field in yaml - Ignoring Weights & Biases Logger")

    def init_fields(self,  config: Dict, rep: int, rep_log_path: str):
        self.log_path = rep_log_path
        self.rep = rep
        self.config = config['wandb']
        self.cw2_config = config
        reset_wandb_env()
        self.job_name = config['_experiment_name'].replace("__", "_")
        self.use_group_parameters = self.config.get("use_group_parameters", False)
        if self.use_group_parameters:
            self.job_name = group_parameters(self.job_name.split("_"))[0]
        self.runname = self.job_name + "_rep_{:02d}".format(rep)

        # optional: change the job_type to a fixed alias if the option is present
        if "job_type" in self.config:
            self.job_name = self.config['job_type']
        # have entity and group config entry optional
        self.entity = self.config.get("entity", None)
        self.group = self.config.get("group", None)
        # Get the model logging directory
        self.wandb_log_model = self.config.get("log_model", False)
        if self.wandb_log_model:
            self.save_model_dir = os.path.join(self.log_path, "model")
            self.cw2_config["save_model_dir"] = self.save_model_dir
            self.model_name = self.config.get("model_name", "model")
        else:
            self.save_model_dir = None

    def connect_to_wandb(self):
        last_error = None
        for i in range(10):

            try:
                self.run = wandb.init(project=self.cw2_config['wandb']['project'],
                                      entity=self.entity,
                                      group=self.group,
                                      job_type=self.job_name[:63],
                                      name=self.runname[:63],
                                      config=self.cw2_config['params'],
                                      dir=self.log_path,
                                      settings=wandb.Settings(_disable_stats=self.cw2_config['wandb'].get("disable_stats",
                                                                                              False)),
                                      mode="online" if self.cw2_config['wandb'].get("enabled", True) else "disabled",
                                      )
                return  # if starting the run is successful, exit the loop (and in this case the function)
            except Exception as e:
                last_error = e
                # implement a simple randomized exponential backoff if starting a run fails
                waiting_time = ((random() / 50) + 0.01) * (2 ** i)
                # wait between 0.01 and 10.24 seconds depending on the random seed and the iteration of the exponent

                warnings.warn("Problem with starting wandb: {}. Trying again in {} seconds".format(e, waiting_time))
                sleep(waiting_time)
        warnings.warn("wandb init failed several times.")
        raise last_error

    def process(self, data: dict) -> None:
        if self.run is not None:

            # Skip logging if interval is defined but not satisfied
            log_interval = self.config.get("log_interval", None)
            if log_interval is not None and data["iter"] % log_interval != 0:
                return

            if "histogram" in self.config:
                for el in self.config['histogram']:
                    if el in data:
                        self.run.log({el: wandb.Histogram(np_histogram=data[el])}, step=data["iter"])
            filtered_data = self.filter(data)
            step = data.get("iter", None)
            self.run.log(filtered_data, step=step)

    def finalize(self) -> None:
        if self.run is not None:
            self.log_model()
            self.run.finish()

    def load(self):
        pass

    def log_model(self):
        """
        Log model as an Artifact

        Returns:
            None
        """
        if self.wandb_log_model is False:
            return

        # Initialize wandb artifact
        model_artifact = wandb.Artifact(name=self.model_name, type="model")

        # Get all file names in log dir
        file_names = get_file_names_in_directory(self.save_model_dir)

        if file_names is None:
            warnings.warn("save model dir is not available or empty.")
            return

        # Add files into artifact
        for file in file_names:
            model_artifact.add_file(os.path.join(self.save_model_dir, file))

        aliases = ["latest", f"finished-rep-{self.rep}"]

        # Log and upload
        self.run.log_artifact(model_artifact, aliases=aliases)

