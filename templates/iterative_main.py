from cw2 import cluster_work, cw_logging, experiment


class MyIterativeExperiment(experiment.AbstractIterativeExperiment):
    # ...

    def initialize(self, config: dict, rep: int, logger: cw_logging.AbstractLogger) -> None:
        print("Ready to start repetition {}. Resetting everything.".format(rep))

    def iterate(self, config: dict, rep: int, n: int) -> dict:
        return {"Result": "Current Iteration is {}".format(n)}

    def save_state(self, config: dict, rep: int, n: int) -> None:
        if n % 50 == 0:
            print("I am stateless. Nothing to write to disk.")

    def finalize(self, surrender: bool = False, crash: bool = False):
        print("Finished. Closing Down.")


if __name__ == "__main__":
    cw = cluster_work.ClusterWork(MyIterativeExperiment)
    cw.add_logger(cw_logging.AbstractLogger())
    cw.run()
