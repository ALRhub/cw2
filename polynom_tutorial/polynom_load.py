import matplotlib.pyplot as plt

from cw2 import cluster_work, cw_logging

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(None)
    cw.add_logger(cw_logging.PandasRepSaver())
    res = cw.load()
    
    print(res)

    for job in res.keys():
        for logger in res[job].keys():
            single_df = res[job][logger]
            single_df[["sample_y", "true_y"]].plot.line()
            plt.savefig(job + "plot.png")
