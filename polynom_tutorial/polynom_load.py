import matplotlib.pyplot as plt

from cw2 import cluster_work
from cw2.cw_data import cw_logging, cw_pd_logger

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(None)
    cw.add_logger(cw_pd_logger.PandasLogger())

    # load() -> pd.DataFrame
    df = cw.load()
    
    rep0 = df.cw2.filter({
        "x_1": 0
    })

    print(df.head())

    print(df.cw2.flatten_pd_log().shape)

    for i, job in df.iterrows():
        single_df = job["PandasLogger"]
        single_df[["sample_y", "true_y"]].plot.line()
        plt.savefig(job['rep_path'] + "plot.png")
