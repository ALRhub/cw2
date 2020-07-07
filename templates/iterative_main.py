from cw2 import cluster_work, experiment

class MyExperiment(experiment.AbstractIterativeExperiment):
    # ...

    def iterate(self, config: dict, rep: int, n: int) -> dict:
        return {"Result": "Current Iteration is {}".format(n)}

    def save_state(self, config: dict, rep: int, n: int) -> None:
        if n % 50 == 0:
            print("I am stateless")


if __name__ == "__main__":
    cw = cluster_work.ClusterWork(MyExperiment)
    cw.run()
