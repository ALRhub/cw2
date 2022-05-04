# 7. Logging Results

- [7. Logging Results](#7-logging-results)
  - [7.1. Console Logger](#71-console-logger)
  - [7.2. Logger Interface](#72-logger-interface)
  - [7.3. Advanced Loggers](#73-advanced-loggers)
    - [7.3.1. Pandas](#731-pandas)
    - [7.3.2. WandB](#732-wandb)

**cw2** comes with a a variety of logging capabilities. This document will explain how to use the basic "Console" logging to document `print()`-like statements.

## 7.1. Console Logger
When you create a `cw2.ClusterWork` instance in your _main_, a custom [python logging](https://docs.python.org/3/howto/logging.html) object is created. You can use this object to "print" statements to the console and they will be automatically saved into a logfile on disk in your output folder (TODO: FILESYTEM). Two files will be written:

- `out.log` contains every message you passed to the logger
- `err.log` contains only error messages

You can access it from anywhere within a **cw2** program by:

```python
from cw2.cw_data import cw_logging

# retrieve logger
l = cw_logging.get_logger()

# Print Generic Message()
l.info("This will be written to out.log")

# Print Error Message
l.error("This will be written to err.log AND out.log")
```

You do not need to initialize or close the logger object. It is handled automatically by **cw2**.

## 7.2. Logger Interface
If you want to implement your own custom logger, you have to implement the corresponding interface [`AbstractLogger`](../cw2/cw_data/cw_logging.py)

```Python
from cw2.cw_data import cw_logging

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
        # Finalize the processing, e.g. write the internal data to disk and close all writers
        write_to_disk(self.data, self.log_path)

    def load(self):
        # Implement this function to load potential results
        self.data = read_from_disk(self.log_path)
        return self.data
```

The execution order is very similar to the order of an [`AbstractIterativeExperiment`](../cw2/experiment.py):

```Python
log = AbstractLogger()     # Initialize only GLOBAL values & CONSTANTS
for r in repetitions:
    log.initialize(...)    # Initialize / Reset the logger for each repetition.

    for i in iterations:
      result = experiment.iterate(...) # Obtain some data from an experiment
      log.process(result)    # Log the result
    
    log.finalize()      # Finalize / Clean the logger after each repetition
```
Each logger is responsible themselves to check results and how handle them.


## 7.3. Advanced Loggers
**cw2** provides advanced logging functionality in form of a [Pandas Dataframe](https://pandas.pydata.org/) Logger for Excel-like table structures, and a [Weights & Biases (WandB)](https://wandb.ai/site) Logger for advanced metrics.
### 7.3.1. Pandas
### 7.3.2. WandB
This description is intended as a first primer, and is not tested by me.

To instantiate the WandB logger, you need to add it to the LoggerArray.

```Python
if __name__ == "__main__":
    cw = ClusterWork(YourExp)

    cw.add_logger(WandBLogger())
    cw.run()
```

Your `config.yml` find needs to be configured for wandb:
Please refer to the official WandB documentation and the WandBLogger code to learn, what options you have and their effect.

```yaml
---
name: some_exp
repetitions: 5
params:
    ...

wandb:
    project: project_name
    group: group_name
```

Logging data with the WandBLogger is the same as every other logger:

For `AbstractIterativeExperiment` implementations, the complete result dictionary returned by your `iterate()` function will be logged, unless you used the `ignore_keys` parameters during Logger creation:

```Python
# logs everything
wandb_l = WandBLogger()

# logs everything except for the key secret
wandb_l = WandBLogger(ignore_keys=['secret'])
```

When using an `AbstractExperiment` implementation, you have to log results manually:

```Python
def run(self, config, repetition, logger):
    do_something()
    results = {
        # fill dictionary
    }
    logger.process(results)
```

Optional config parameters of the wandb logger:
```yaml
wandb: 
    optional_config: value_of_this_config
```
- **log_model**: bool, indicates whether the model shall be logged by the wandb or not. 
When it is false or not given, nothing happens.
When it is true, the wandb logger will assume you have saved some meaning model files (such as NN weights) under `rep_xx/log/model`. 
In the end of each repetition, the logger will upload all the files saved there as an Artifact. 
The wandb logger does not care about the content and types of the files in such directory, or how did you save model in such directory.
If such directory does not exist, or it contains no file, then wandb logger will log a warning but will not raise any error to break your experiment. 
In your own experiment class, you can get this directory in the initialize function and save model:
```python
class MyCoolExp(experiment.AbstractIterativeExperiment):
    def initialize(self, cw_config: dict,
                       rep: int, logger: cw_logging.LoggerArray) -> None:
        self.net = CoolNet()
        
        # Get the determined directory to save the model
        self.save_model_dir = cw_config.save_model_dir
        
        # You need to make a new dir of this given save model dir too!
        # os.mkdir(...)

        # You may save your model for every M epochs
        self.save_model_interval = 100
        
    def save_state(self, cw_config: dict, rep: int, n: int) -> None:        
        if self.save_model_dir and ((n + 1) % self.save_model_interval == 0
                                    or (n + 1) == cw_config.iterations):
        self.net.save_weights(log_dir=self.save_model_dir, epoch=n + 1)
```

- **model_name**: string, name of the saved model. 
It is only useful when **log_model** is set. 
If the **model_name** is not set, the saved model will use "model" as its default name.


- **log_interval**: int value. If it is given, it indicates that you want to log result in a given interval. 
This helps in the experiment which contains too many iterations (epochs), so that you do not want to log stuff for every iteration.   

[Back to Overview](./)