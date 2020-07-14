from cw2 import cluster_work, experiment, cw_logging

class MyExperiment(experiment.AbstractExperiment):
    # ...

    def initialize(self, config: dict, rep: int) -> None:
        print("Ready to start repetition {}. Resetting everything.".format(rep))

    def run(self, config: dict, rep: int, logger: cw_logging.AbstractLogger) -> None:
        # Initialize all loggers
        logger.initialize()

        # Do Something non-iteratively and logging the result.
        print("Doing Something.")
        logger.process("Some Result")
        print("Doing something else.")

        # Finalize all loggers (e.g. save to disk)
        logger.finalize()
    
    def finalize(self):
        print("Finished. Closing Down.")

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(MyExperiment)

    # If loggers are wanted, must be instantiated manually
    logger1 = cw_logging.AbstractLogger()
    logger2 = cw_logging.AbstractLogger()
    cw.add_logger(logger1)
    cw.add_logger(logger2)

    cw.run()
