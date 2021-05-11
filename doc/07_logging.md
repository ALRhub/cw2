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


[Back to Overview](./)