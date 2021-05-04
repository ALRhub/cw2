# cw2 - ClusterWork 2

A second iteration of a the software framework ClusterWork to easily deploy experiments on an computing cluster using SLURM.

## Installation
0. We recommend creating a virtual environment with [virtualenv](https://virtualenv.pypa.io/en/stable/) or [conda](https://conda.io/miniconda.html) before installing **cw2**:
    - Create a conda environment and activate it:
    ```bash
    conda create -n my_env python=3
    conda activate my_env
    ```
    - Or create a virtualenv environment and activate it
    ```bash
    virtualenv -p python3 /path/to/my_env
    source /path/to/my_env/bin/activate
    ```
1. Clone or Download **cw2**
    ```bash
    git clone https://github.com/ALRhub/cw2.git
    ```

2. Install **cw2**:
     ```bash
     cd /path/to/cw2
     pip install .
     ```

## Program Execution
To start an experiment locally, e.g. for testing:
```bash
python3 YOUR_MAIN.py YOUR_CONFIG.yml
```

To start an experiment on a slurm cluster:
```bash
python3 YOUR_MAIN.py YOUR_CONFIG.yml -s
```

#### CLI args
The following args are currently supported by CW2:
| Flag  |Name           | Effect|
|-------|---------------|-------|
| -s    |--slurm        | Run using SLURM Workload Manager.|
| -o    | --overwrite   | Overwrite existing results.|
| -e name1 [...] | --experiments | Allows to specify which experiments should be run. Corresponds to the `name` field of the configuration YAML.
|     | --zip   | Creates a ZIP archive for documentation purposes of $CWD or, if set, "experiment_copy_src".|
|     | --skipsizecheck   | Disables a safety size check when Zipping or Code-Copying. The safety prevents unecessarily copying / archiving big files such as training data.|


### Logging
If you want to log your own INFO or WARNING messages, use the `cw2.cw_data.cw_logging.getLogger()` object. It is an instance of pythons `logging.Logger()`.
The messages will be saved to disk in your repetition directory.

### CW_Logging
We provide an abstract interface for result logging functionality with `cw2.cw_data.cw_logging.AbstractLogger`.

#### Implementing `cw2.cw_logging.AbstractLogger()`
```Python
from cw2 import cw_logging

class MyLogger(cw_logging.AbstractLogger):
    # ...

    def initialize(self, config: attrdict.AttrDict, rep: int, rep_log_path: str):
        # Initialize / Reset the logger for a new repetition
        self.log_path = rep_log_path + 'my_file.txt'
        self.data_list = []

    def process(self, data) -> None:
        # Processes incoming data.
        # Need to do your own check if data is in the format you expect.
        print(data)
        self.data_list.append(data)

    def finalize(self) -> None:
        # Finalize the processing, e.g. write the internal data to disk.
        write_to_disk(self.data, self.log_path)

    def load(self):
        # Implement this function to load potential results
        self.data = read_from_disk(self.log_path)
        return self.data
```

The execution order is very similar to the order of an `cw2.experiment.AbstractExperiment`:

```Python
log = AbstractLogger()     # Initialize only global CONSTANTS
for r in repetitions:
    log.initialize(...)    # Initialize / Reset the logger for each repetition.

    for i in iterations:
      result = experiment.iterate(...) # Obtain some data from an experiment
      log.process(result)    # Log the result
    
    log.finalize()      # Finalize / Clean the logger after each repetition
```
Each logger is responsible themselves to look up if results exist and are readable.

### CW_Loading
We provide a simple function to access the results from your runs. An example can be found in `polynom_tutorial\polynom_load.py`:

```Python
from cw2 import cluster_work, cw_logging

cw = cluster_work.ClusterWork(None)

# Add all the loggers whose results you want to load.
cw.add_logger(cw_logging.PandasRepSaver())
# ...


# res is a pandas.DataFrame
res = cw.load()
```

The resulting object is a `pandas.DataFrame` with each repetition as a row, and each configuration parameter and logger result as a column.
You can use all the available `pandas` methods to filter and do your own analysis of the results.

Additionally we offer our own processing functions with an extension of the `pandas` API: `df.cw2`
For example, to select a single repetition in the result dataframe `res` from the example above, use `df.cw2.repetition()`:

```Python
# ...
res = cw.load()
repetition_0 = res.cw2.repetition(0)
```

To select all runs with a specific hyper-parameter setting, use `df.cw2.filter()`:
```Python
# ...
res = cw.load()

# parameter dict - same structure as CONFIG.params
interesting_params = {
  'param1': 1
}

interesting_results = res.cw2.filter(
  interesting_params
)
```

### Error Handling
Should any kind of exception be raised during an Experiment execution (`initialize()` or `run()`), `CW2` will abort this experiment run, log the error including stacktrace to a log file in the repetition directory and continue with the next task.

If you want to end an (iterative) experiment early, you can raise the `cw_error.ExperimentSurrender` exception to gracefully abort the experiment execution.