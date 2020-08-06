# CW2

A second iteration of a the software framework ClusterWork to easily deploy experiments on an computing cluster using SLURM.

## Installation
0. Creating a virtual environment with [virtualenv](https://virtualenv.pypa.io/en/stable/) or [conda](https://conda.io/miniconda.html) is recommended. Create and activate the environment before installing **CW2**:
    - Create a conda environment and activate it:
    ```bash
    conda create -n my_env python=3
    source activate my_env
    ```
    - Or create a virtualenv environment and activate it
    ```bash
    virtualenv -p python3 /path/to/my_env
    source /path/to/my_env/bin/activate
    ```
1. Clone or Download **CW2**
    ```bash
    git clone https://github.com/ALRhub/cw2.git
    ```

2. Install CW2:
    The `-e` option of pip makes the project editable, i.e., pip will only reference to the git directory and hence changes in the git will be directly available in your environment. If you install without the `-e` option, pip will copy the source to your python packages.
     ```bash
     cd /path/to/cw2
     pip install -e .
     ```

## Usage Guide (Iterative Experiment)
To run an iterative experiment on a computing cluster, the following highlevel steps are required:

1. Implement `cw2.experiment.AbstractIterativeExperiment()`:
2. Write a small Main() function
3. Write a simple YAML-file to configure your experiment.
5. Adopt a shell script that starts your experiment on your cluster.
6. Execute the python programm.

You can find a barebones template in the `template` folder.

### Implementing `cw2.experiment.AbstractIterativeExperiment()`
```Python
from cw2 import experiment

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
```
The internal execution order of an `AbstractIterativeExperiment` is, in abstract:

```Python
exp = AbstractIterativeExperiment()     # Initialize only global CONSTANTS
for r in repetitions:
    exp.initialize(...)    # Initialize / Reset the experiment for each repetition.
    for i in iterations:
        result = exp.iterate(...)   # Make a single iteration, return the result
        log(result)                 # Log the result
        exp.save_state(...)         # Save the current experiment state
    exp.finalize()      # Finalize / Clean the experiment after each repetition
```

CW2 does not come with any logging functionality by default. Please add any `cw2.cw_logging.AbstractLogger` implementation you need for your experiment in the main function.

### Main Function
The main function initializes and starts the `CW2` Manager.
```Python
from cw2 import cluster_work, cw_logging

if __name__ == "__main__":
    cw = cluster_work.ClusterWork(MyExperiment)

    # Add Logger
    cw.add_logger(cw_logger.AbstractLogger())

    cw.run()
```

### Configuration YAML
To configure the execution of the experiment, we need to write a small YAML-file. The YAML file consists several documents which are separated by a line of `---`. 
There are two special kind of optional documents:
1. By setting the key `name` to `"DEFAULT"`, a default document is defined. This default document will then form the basis for all following experiment documents.
2. By setting the key `name` to `"SLURM"`, special configuration parameters for the execution on a SLURM cluster can be defined. For more details on the slurm configuration see the next section.

Every document beside these two special documents represents an experiment.

#### Configuration: Experiments
The required keys for each experiment are `name`, `repetitions`, and `path`. An iterative Experiment also nees the key `iterations`. The parameters found below the key `params` overwrite the default parameters defined in the experiment class.

```yaml
---
# DEFAULT parameters (Optional)
name: "DEFAULT"   # MUST BE 'DEFAULT'

# Implementation default parameters
params:
  param_1: "default_value"

# Will be overwritten by named experiments.
---
# Experiment 1
name: "experiment_name"

# Required: Can also be set in DEFAULT
path: "path/to/output_dir/"   # location to save results in
repetitions: 5    # number of times one set of parameters is run
iterations: 1000  # number of iterations per repetition

# Experiment Parameters: Can also be set in DEFAULT.
params:
  param_1: "exp_value_1" # overwrites Default
  param_2: "exp_value_2" # new experiment specific parameter
```

Experiments can be expanded by __either__ the `list` __or__ `grid` feature.
These will expand the experiment paramter space during runtime.

```yaml
# DEFAULT ...
---
# This is a list experiment
name: "list_experiment"
param:
  c: "constant"

list:
  param_1: [1, 2]
  param_2: ["a", "b"]



# It is equivalent to the following 2 documents
---
name: "expanded_experiment_1"
param:
  c: "constant"
  param_1: 1
  param_2: "a"
---
name: "expanded_experiment_2"
param:
  c: "constant"
  param_1: 2
  param_2: "b"

```

Using the `grid` feature would generate all 4 `param_` combinations during runtime.

#### Configuration: SLURM
If you want to run a CW2 experiment on a SLURM cluster, you __must__ include document in your YAML configuration file with the key `name` set to `"SLURM"`. It is used to fill the `sbatch_template.sh` file used for execution. During local execution this document is ignored.

```yaml
---
# Slurm config
name: "SLURM"   # MUST BE "SLURM"
```

The following fields are __required__ to ensure correct execution of your job on the slurm cluster. Please refer to the [sbatch docu](https://slurm.schedmd.com/sbatch.html) for further explanations.
```yaml
# ... continued
# Required
partition: "dev"
account: ""  # important for HHLR cluster
job: "cma"    # this will be the experiment's name in slurm
path_to_template: "/path/to/sbatch_template.sh"   # Path to YOUR prepared sbatch script
```

The following fields are __required__ to configure your hardware requirements. These are highly cluster specific. Please refer to the [sbatch docu](https://slurm.schedmd.com/sbatch.html) for further explanations.
```yaml
# ... continued
# Required - Cluster Specific
num_parallel_jobs: 120
ntasks: 1
cpus-per-task: 1
mem-per-cpu: 1000
time: 30
```

All the following sections are optional arguments.
If they are not present in this slurm configuration, a default behaviour is used.
```yaml
# ... continued
experiment_copy_dst: "/path/to/code_copy/dst"       # optional. dir TO which the current code will be copied. Useful to prevent unintentional changes while the job is in queue. If not set, no copy will be made.
experiment_copy_src: "/path/to/code_copy/src"       # optional. dir FROM which the current code will be copied. Useful to prevent unintentional changes while the job is in queue. Defaults to directory of __MAIN__ file.
slurm_log: "/path/to/slurmlog/outputdir"            # optional. dir in which slurm output and error logs will be saved. Defaults to EXPERIMENTCONFIG.path
venv: "/path/to/virtual_environment/bin/activate"   # optional. path to your virtual environment activate-file
```

If you have further need to configure slurm, you can use all the options offered by the [sbatch docu](https://slurm.schedmd.com/sbatch.html). Please use the following style of defining _keyword_ -> _value_ pairs:

```yaml
# ... continued
# Optional SBATCH Arguments
sbatch_args:    # Dictionary of SBATCH keywords and arguments
  kw_1: "arg1"  # Will construct the line: #SBATCH --kw_1 arg1
  kw_2: "arg2"  # Will construct the line: #SBATCH --kw_2 arg2
```

Sometimes it is necessary to do execute some additional instructions in the linux shell before starting the python process using slurm. You can define arbitrarily many additional shell instructions using the following format:
```yaml
# ... continued
# Optional shell instructions
sh_lines:       # List of strings
  - "line 1"
  - "line 2"
```

### Execution
To start an experiment locally:
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


### CW_Logging
We provide an abstract interface for logging functionality with `cw2.cw_logging.AbstractLogger`.

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

