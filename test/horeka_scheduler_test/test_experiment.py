import os
#os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import sys
import subprocess
import torch
import time
import numpy as np

from cw2.cw_data import cw_logging
from cw2.experiment import AbstractExperiment, ExperimentSurrender


class TestExperiment(AbstractExperiment):

    def initialize(self, cw_config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
        np.random.seed(rep * 13)
        print("Hello, repetition ", rep, "here. I see ", torch.cuda.device_count(), " GPU(s)")
        if torch.cuda.is_available():
            device = torch.device("cuda")
            print(torch.cuda.get_device_name(device))
            print(torch.cuda.get_device_properties(device))

    def run(self, cw_config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
        sleep_time = np.random.rand() * 10
        print("Going to sleep for {:.5f} sec".format(sleep_time))
        time.sleep(sleep_time)
        exit_gracefully = np.random.rand() < 0.5
        if exit_gracefully:
            print("Done (Rep", rep, ")")
            return
        else:
            raise Exception("AAHHH I AM DYING! (Rep ", rep, ")")

    def finalize(self, surrender: ExperimentSurrender = None, crash: bool = False):
        pass


if __name__ == "__main__":
    from cw2.cluster_work import ClusterWork

    sys.argv.append("horeka_config.yml")
    sys.argv.append("-o")

    cw = ClusterWork(TestExperiment)
    cw.run()

