from cw2 import cluster_work, cw_error, experiment
from cw2.cw_data import cw_logging


class MyIterativeExperiment(experiment.AbstractIterativeExperiment):
    # ...

    def initialize(
        self, config: dict, rep: int, logger: cw_logging.LoggerArray
    ) -> None:
        cw_logging.getLogger().info(
            "Ready to start repetition {}. Resetting everything.".format(rep)
        )

    def iterate(self, config: dict, rep: int, n: int) -> dict:
        if n > 50:
            raise cw_error.ExperimentSurrender({"Rsult": "End execution early."})

        return {"Result": "Current Iteration is {}".format(n)}

    def save_state(self, config: dict, rep: int, n: int) -> None:
        if n % 50 == 0:
            cw_logging.getLogger().info("I am stateless. Nothing to write to disk.")

    def finalize(
        self, surrender: cw_error.ExperimentSurrender = None, crash: bool = False
    ):
        if surrender is not None:
            cw_logging.getLogger().info("Run was surrendered early.")

        if crash:
            cw_logging.getLogger().warning("Run crashed with an exception.")
        cw_logging.getLogger().info("Finished. Closing Down.")


if __name__ == "__main__":
    cw = cluster_work.ClusterWork(MyIterativeExperiment)
    cw.add_logger(cw_logging.AbstractLogger())
    cw.run()
