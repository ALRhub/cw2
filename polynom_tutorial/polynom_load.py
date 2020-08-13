import matplotlib.pyplot as plt

from cw2 import cluster_work, cw_logging

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(None)
    cw.add_logger(cw_logging.PandasRepSaver())
    res = cw.load().get_data()
    
    print(res)
    print(res[0])

    for job in res:
        single_df = job["PandasRepSaver"]
        single_df[["sample_y", "true_y"]].plot.line()
        plt.savefig(job['rep_path'] + "plot.png")
