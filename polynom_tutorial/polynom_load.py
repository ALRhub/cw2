import matplotlib.pyplot as plt

from cw2 import cluster_work, cw_logging

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(None)
    cw.add_logger(cw_logging.PandasRepSaver())
    res = cw.load()
    
    print(res.data())
    print(res.get_repetition(2).data())
    print(res.data().cw2.repetition(2))
    print(res.data().cw2.filter({'optim_params': {'n_samples': 6}}))

    for job in res:
        single_df = job["PandasRepSaver"]
        single_df[["sample_y", "true_y"]].plot.line()
        plt.savefig(job['rep_path'] + "plot.png")
