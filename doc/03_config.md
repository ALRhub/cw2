# 1. Configuration YAML File
- [1. Configuration YAML File](#1-configuration-yaml-file)
  - [1.1. Experiment Configuration](#11-experiment-configuration)
    - [1.1.1. Experiment Header](#111-experiment-header)
    - [1.1.2. Experiment Parameters](#112-experiment-parameters)
    - [1.1.3. Recommended Practices: Experiment Configuration](#113-recommended-practices-experiment-configuration)
      - [1.1.3.1. Params is your safe space](#1131-params-is-your-safe-space)
      - [1.1.3.2. You dont want multiple DEFAULTS...](#1132-you-dont-want-multiple-defaults)
  - [1.2. SLURM Configuration](#12-slurm-configuration)
  - [1.3. Example Templates](#13-example-templates)
  - [1.4. Important Keys](#14-important-keys)

-  [Back to Overview](./)

To configure the execution of the experiment, you need to write a YAML-file. A YAML file consists several documents which begin with `---`:
```yaml
---
# First Document


---
# Second Document
```

For **cw2** we expect each yaml document to contain a key `name`:

```yaml
---
# First Document
name: "name_1"


---
# Second Document
name: "name_2"
```

The name is used to identify an experiment configuration an can be chosen freely, **EXCEPT** for these names:
1. `DEFAULT` defines a default configuration. It may only exist *once* in your YAML file. If some parameter settings are shared between your experiments, you can define them inside the `DEFAULT` document. Unless they are specified differently in a named experiment, the settings from the `DEFAULT` will be used. The `DEFAULT` document follows the same structure as a generic experiment configuration document.

1. `SLURM` defines a slurm configuration. It may only exist *once* in your YAML file. This document defines the relevant settings for the execution on a computing cluster, and are specific to each cluster. It follows its own special structure.


## 1.1. Experiment Configuration
An experiment configuration (generic or default) has the following structure:

```yaml
name: "experiment_name"

# Experiment Header
# ...

# Experiment Parameters
# ...
```

### 1.1.1. Experiment Header

```yaml
---
name: "experiment_name"

# Required: Can also be set in DEFAULT
path: "path/to/output_dir/"   # path for saving the results
repetitions: 5    # number of repeated runs for each parameter combination

# Required for AbstractIterativeExperiments only. Can also be set in DEFAULT
iterations: 1000  # number of iterations per repetition.

# Optional: Can also be set in DEFAULT
# Only change these values if you are sure you know what you are doing.
reps_per_job: 1    # number of repetitions in each job. useful for paralellization. defaults to 1.
reps_in_parallel: 1 # number of repetitions in each job that are executed in parallel. defaults to 1.


# Experiment Parameters
# ...
# ...
```
**All fields can be defined in the `DEFAULT` document and do not need to be set in each experiment specifically.**

If you want to understand the `reps_per_job` and `reps_in_parallel` settings, please read TODO: BACKGROUND KNOWLEDGE

### 1.1.2. Experiment Parameters
The experiment parameter section is highly specific to your code and use case. You can freely define parameter names within the `params:` key, e.g.:
```yaml
---
name: "DEFAULT":
# ... all required fields


---
name: "ComputerVision"
# required fields are filled by DEFAULT

# Experiment Parameters
params:
    batchsize: 5 
    pretrained: "imagenet"

```

You can freely define parameter names and the structure, such as nested parameters, or list values.

You can use **cw2** to also quickly define a hyperparameter space using the `grid` or `list` keyword. This YAML file using `list`
```yaml
---
name: "DEFAULT":
# ... all required fields


---
name: "CV-List"
# required fields are filled by DEFAULT

# Experiment Parameters
list:
    batchsize: [3, 7]
    learning_rate: [0.4, 0.8]
```


is the same as if you had defined:
```yaml
---
name: "DEFAULT":
# ... all required fields


---
name: "CV-list-3-04"
# required fields are filled by DEFAULT

# Experiment Parameters
params:
    batchsize: 3
    learning_rate: 0.4

---
name: "CV-list-7-08"
# required fields are filled by DEFAULT

# Experiment Parameters
params:
    batchsize: 7
    learning_rate: 0.8
```

The `list` keyword requires all parameter sets to be of equal length and will combine every n-th value. The `grid` keyword will generate all possible combinations 

(i.e. in the above example 4 combinations: `(3, 0.4) (3, 0.8) (7, 0.4) (7, 0.8)`)


The final experiment configurations combining all techniques could look like:
```yaml
---
# DEFAULT parameters (Optional)
name: "DEFAULT"         # MUST BE 'DEFAULT'
path: "/default/dir/"   # location to save results in
repetitions: 5          # number of times one set of parameters is run

# Implementation default parameters
# Can be overwritten by named experiments.
params:
  net_architecture: "vgg16"


---
# Experiment 1
name: "VGG"

# Required:
# Repetitions are defined in DEFAULT
path: "/vgg/results/"   # overwrite DEFAULT setting

# Experiment Parameters:
# params.net_architecture from DEFAULT

# Creates all combinations
grid:
  learning_rate: [0.5]
  batchsize: [5, 10]


---
# Experiment 2
name: "AlexNet"

# Required settings defined in DEFAULT

# Experiment Parameters:
params:
    net_architecture: "alex_net" # overwrite DEFAULT
    learning_rate: 0.9 # no combination tryout
    batch_size: 2 # no combination tryout
```

### 1.1.3. Recommended Practices: Experiment Configuration
1. `params` is your safe space!
2. If you feel like you need multiple `DEFAULT` sections, you probably want multiple YAML files

#### 1.1.3.1. Params is your safe space
A common use case for **cw2** is the hyperparameter search for ML models. Often users only put the hyperparameters they search for into the `params` sections and keep their "constants", like training data location, outside. For example:

```yaml
---
name: "THIS IS NOT RECOMMENDED"
# Required settings
# ...

params:
    learning_rate: 0.3
    batch_size: 4

training_data: "/my/dataset"
speed_of_light: "c"
```

While this does not cause an error, I recommend you still define your constants inside the `params` sections. During runtime **cw2** will modify the internal configuration object. While it is highly unlikely, you might overwrite such an internal keyword, leading to unforeseen issues. Especially as the software evolves.

To stay on the safe side, put all your custom parameters / arguments / constants inside the `params` section. **cw2** guarantees that all the values inside this section will not be altered. For example:

```yaml
---
name: "THIS IS THE WAY"
# Required settings
# ...

params:
    learning_rate: 0.3
    batch_size: 4
    training_data: "/my/dataset"
    speed_of_light: "c"
```

#### 1.1.3.2. You dont want multiple DEFAULTS...
When running the same experiments for a long time, you may try out different parameters. Especially in the beginning, it is easier to extend the YAML file by adding a new document to the bottom of the file. After a while, you might find you have two "clusters" of configurations, maybe two algorithms / models, that you compare to each other. These models might require very different parameters, and it might not even be possible to share a common `DEFAULT` setting between those two classes.

In this case, I recommend you split the YAML file into two files, one for each approach. As you are most likely deploying such big experiments on a computing cluster using slurm, you do not have to wait for the results of the first set of tasks before starting the second.

```console
# Naive Approach
u@cluster:~$ python experiment.py BIG_OLD_LEGACY.yml -s

# Split Approach
u@cluster:~$ python experiment.py model_1.yml -s
u@cluster:~$ python experiment.py model_2.yml -s
```


## 1.2. SLURM Configuration
If you want to run a **cw2** experiment on a SLURM cluster, you __must__ include a document in your YAML configuration file with the `name` key set to `"SLURM"`. During local execution this document is ignored.

```yaml
---
# Slurm config
name: "SLURM"   # MUST BE "SLURM"
```

The following fields are __required__ to ensure correct execution of your job on the slurm cluster. Please refer to the [sbatch docu](https://slurm.schedmd.com/sbatch.html) for further explanations.
```yaml
# ... continued
# Required
job-name: "yourjob"    # this will be the experiment's name in slurm
```

The following fields are __required__ to configure your hardware requirements. These are _highly_ cluster specific. Please refer to the [sbatch docu](https://slurm.schedmd.com/sbatch.html) for further explanations.
```yaml
# ... continued
# Required - Cluster Specific
partition: "dev"
num_parallel_jobs: 120
ntasks: 1
cpus-per-task: 1
time: 30
```

All the following sections are optional arguments.
If they are not present in this slurm configuration, a default behaviour is used.
```yaml
# ... continued
# Optional
account: ""  # Account name to which Cluster Time will be booked. Cluster specific.
mem-per-cpu: 1000 # Optional - Cluster specific

experiment_copy_dst: "/path/to/code_copy/dst"       # optional. dir TO which the current code will be copied. Useful to prevent unintentional changes while the job is in queue. If not set, no copy will be made.
experiment_copy_auto_dst: /path/to/code_copy/dst"   # optional. will autoincrement and create a dir TO which the current code will be copied. Useful to prevent unintentional changes while the job is in queue. Overrules experiment_copy_dst. If not set, no copy will be made.
experiment_copy_src: "/path/to/code_copy/src"       # optional. dir FROM which the current code will be copied. Useful to prevent unintentional changes while the job is in queue. Defaults to directory of __MAIN__ file.
slurm_log: "/path/to/slurmlog/outputdir"            # optional. dir in which slurm output and error logs will be saved. Defaults to EXPERIMENTCONFIG.path
venv: "/path/to/virtual_environment"   # optional. path to your virtual environment activate-file
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
## 1.3. Example Templates
This documentation gets updated less frequently than potential feature introductions.
When in doubt, refer to the provided templates:
- [AbstractExperiment Configuration](../templates/abstract_config.yml)
- [AbstractIterativeExperiment Configuration](../templates/iterative_config.yml)

## 1.4. Important Keys
These are important configuration keys you have access to in the various methods of your `AbstractExperiment` Implementation.
- `cw_config['params']` is a dictionary containing everything under the `params` keyword, including the merged values from `DEFAULT` and `list`/`grid` keywords.
- `cw_config['_rep_log_path']` is a `str` entry pointing to the _threadsafe_ directory of this repetition. Here all **cw2** logging artifactsof this repitition will be written. If you have any results / model checkpoints you can save them here under the guarantee that no other **cw2** run will interfere.