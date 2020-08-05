from cw2 import cluster_work, experiment
import random

class Polynomial(experiment.AbstractIterativeExperiment):
    # ...

    def initialize(self, config: dict, rep: int) -> None:
        print("Ready to start repetition {}. Resetting everything.".format(rep))

    def iterate(self, config: dict, rep: int, n: int) -> dict:
        x = config.params.stepsize * n
        y = config.params.x_0 + config.params.x_1 * x + config.params.x_2 * (x**2)

        y_noise = y + (random.randint(-100, 100) / 100.0) * config.params.noise
        
        return {"true_y": y, "sample_y": y_noise}

    def save_state(self, config: dict, rep: int, n: int) -> None:
        pass

    def finalize(self):
        print("Finished. Closing Down.")


if __name__ == "__main__":
    cw = cluster_work.ClusterWork(Polynomial)
    cw.run()
