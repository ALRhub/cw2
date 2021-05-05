# 1. CW Logging Functions

- [1. CW Logging Functions](#1-cw-logging-functions)
  - [1.1. Console Logger](#11-console-logger)
  - [1.2. Logger Interface](#12-logger-interface)
  - [1.3. Advanced Loggers](#13-advanced-loggers)
    - [1.3.1. Pandas](#131-pandas)
    - [1.3.2. WandB](#132-wandb)

**cw2** comes with a a variety of logging capabilities. This document will explain how to use the basic "Console" logging to document `print()`-like statements.

We provide an overview for the provided interface with which you can define your own custom Logger. Additionally, **cw2** provides advanced logging functionality in form of a [Pandas Dataframe](https://pandas.pydata.org/) Logger for Excel-like table structures, and a [Weights & Biases (WandB)](https://wandb.ai/site) Logger for advanced metrics.

## 1.1. Console Logger
When you create a `cw2.ClusterWork` instance, a custom [python logging](https://docs.python.org/3/howto/logging.html) object is created. You can use this object to "print" statements to the console and they will be automatically saved into a logfile on disk in your output folder (TODO: FILESYTEM). Two files will be written:

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

## 1.2. Logger Interface
If you want to implement your own custom logger, you have to implement the corresponding interface [`AbstractLogger`](../cw2/cw_data/cw_logging.py)


## 1.3. Advanced Loggers
### 1.3.1. Pandas
### 1.3.2. WandB