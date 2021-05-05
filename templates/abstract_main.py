from cw2 import cluster_work, cw_error, experiment
from cw2.cw_data import cw_logging


class MyExperiment(experiment.AbstractExperiment):
    # ...

    def initialize(self, config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
        cw_logging.getLogger().info("Ready to start repetition {}. Resetting everything.".format(rep))

    def run(self, config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
        # Do Something non-iteratively and logging the result.
        cw_logging.getLogger().info("Doing Something.")
        logger.process("Some Result")
        cw_logging.getLogger().warning("Something went wrong")
    
    def finalize(self, surrender: cw_error.ExperimentSurrender = None, crash: bool = False):
        if surrender is not None:
            cw_logging.getLogger().info("Run was surrendered early.")
        
        if crash:
            cw_logging.getLogger().warning("Run crashed with an exception.")
        cw_logging.getLogger().info("Finished. Closing Down.")

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(MyExperiment)

    # If loggers are wanted, must be instantiated manually
    logger1 = cw_logging.AbstractLogger()
    logger2 = cw_logging.AbstractLogger()
    cw.add_logger(logger1)
    cw.add_logger(logger2)

    cw.run()
