from cw2 import cluster_work

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(None)
    d = cw.load()
    print(d)