import os
import random

from cw2 import cluster_work, experiment, cw_error
from cw2.cw_data import cw_logging, cw_pd_logger


class Polynomial(experiment.AbstractIterativeExperiment):
    # ...

    def initialize(self, config: dict, rep: int, logger: cw_logging.AbstractLogger) -> None:
        random.seed(rep)

    def iterate(self, config: dict, rep: int, n: int) -> dict:
        if n > 100:
            raise cw_error.ExperimentSurrender()

        params = config['params']

        x_0 = params['x_0']
        x_1 = params['x_1']
        x_2 = params['x_2']
        x_3 = params['x_3']

        x = params['stepsize'] * n
        y = x_3 * (x ** 3) + x_2 * (x**2) + x_1 * x + x_0

        y_noise = y + (random.randint(-10, 10) / 10.0) * params['noise']

        y = 3 / 0

        return {"true_y": y, "sample_y": y_noise}

    def save_state(self, config: dict, rep: int, n: int) -> None:
        pass

    def finalize(self, surrender: bool = False, crash: bool = False):
        print("Finished. Closing Down.")


if __name__ == "__main__":
    cw = cluster_work.ClusterWork(Polynomial)
    cw.add_logger(cw_pd_logger.PandasLogger())
    cw.run()
