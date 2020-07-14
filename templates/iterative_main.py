from cw2 import cluster_work, experiment

class MyIterativeExperiment(experiment.AbstractIterativeExperiment):
    # ...

    def initialize(self, config: dict, rep: int) -> None:
        print("Ready to start repetition {}. Resetting everything.".format(rep))

    def iterate(self, config: dict, rep: int, n: int) -> dict:
        return {"Result": "Current Iteration is {}".format(n)}

    def save_state(self, config: dict, rep: int, n: int) -> None:
        if n % 50 == 0:
            print("I am stateless. Nothing to write to disk.")
    
    def finalize(self):
        print("Finished. Closing Down.")


if __name__ == "__main__":
    cw = cluster_work.ClusterWork(MyIterativeExperiment)
    cw.run()
