import matplotlib.pyplot as plt

from cw2 import cluster_work, cw_logging

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(None)
    cw.add_logger(cw_logging.PandasRepSaver())

    # load() -> pd.DataFrame
    df = cw.load()
    
    rep0 = df.cw2.filter({
        "x_1": 0
    })

    print(df.head())


    for i, job in df.iterrows():
        single_df = job["PandasRepSaver"]
        single_df[["sample_y", "true_y"]].plot.line()
        plt.savefig(job['rep_path'] + "plot.png")
