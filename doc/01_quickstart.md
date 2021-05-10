#  Quickstart Guide
To deploy your experiment on a computing cluster, the following highlevel steps are required:

1. Implement `cw2.experiment.AbstractExperiment()`
2. Write a small Main() function
3. Write a simple YAML-file to configure your experiment.
4. Execute the python programm.
```bash
python your_main.py your_confi.yml -s
```

You can find a barebones template in the `template` folder.


# Main File

To start using **cw2** you first need to define your `__main__` function.
This is the function you call from the terminal to start a **cw2** experiment and serves as the entry point to the programm execution.

It creates a `ClusterWork` instance with your experiment. If you want to use any compatible loggers, you can also add them here. Finally it will start experiment:

```Python
from cw2 import cluster_work

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(MyExperiment)

    # Optional: Add loggers 
    cw.add_logger(...)

    # RUN!
    cw.run()
```