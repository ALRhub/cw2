#  2. Experiment Class

- [2. Experiment Class](#2-experiment-class)
  - [2.1. Initialize](#21-initialize)
    - [2.1.1 Can I use `__init__` for a global counter ? __**NO**__!!!](#211-can-i-use-__init__-for-a-global-counter--no)
  - [2.2 Run](#22-run)
    - [2.2.1 cw_config: dict](#221-cw_config-dict)
    - [2.2.2 rep: int](#222-rep-int)
    - [2.2.3 logger: LoggerArray](#223-logger-loggerarray)
  - [2.3 Finalize](#23-finalize)
  - [2.4 Iterative Experiment](#24-iterative-experiment)
    - [2.4.1 Iterate](#241-iterate)
    - [2.4.2 Save State](#242-save-state)

To run yur project with **cw2** you must implement the [`AbstractExperiment`](../cw2/experiment.py) interface.
This ensures that you can run multiple repetitions in the same process (e.g. for numerically unstable experiments) in the same process during local execution or deploy it massively parallelized using slurm on a computing cluster.

This interace provides three functions

- `initialize()`
- `run()`
- `finalize()`

corresponding to three phases during programm execution. In abstract, a **cw2** run, wether running locally in a single thread, or distirbuted using slurm, takes the form of:

```Python
exp = AbstractExperiment() # Object is created once! __init__ is only called once!!


for r in repetitions:      # Can be parallelized or sequential!
    exp.initialize(...)    # Initialize / Reset the experiment for each repetition / thread
    exp.run(...)           # Execute experiment logic
    exp.finalize()         # Finalize / Clean the experiment after each repetition / thread. Close all writers, etc.
```

A repetition is the repeated execution of an experiment with the exact same configuration of parameters.


## 2.1. Initialize
The `initialize()` should be used like the `__init__` constructor typically present with python objects. It will be called before each experiment execution, whereas the constructor is only called once at the very start. As the Experiment-Object does not get instantiated newly for each execution, unwanted carry over effects between executions might occur. Take the following example:

```python
class FaultyExperiment(AbstractExperiment):
    def __init__(self):
        # Is set only once during lifetime
        self.speed_of_light = 300 # 1000 km / s
    
    def initalize(self, ...):
        self.distance_traveled = 0

    def run(self, ...):
        self.distance_traveled += self.speed_of_light
        # Activate Warp Speed:
        self.speed_of_light *= 2

    def finalize(self, ...):
        print("Repetition " + str(rep))
        print(self.distance_traveled)
```

If you run this `FaultyExperiment` with three Repetitions, you will get an output like:
```
Repetition 0:
300

Reptition 1:
600

Repition 2:
1200
```
The `distance_traveled` sum gets reset to 0 at the start of each repetition. But the `speed_of_light` is modified during the `run()` function, which is persisted across the reptitions.

### 2.1.1 Can I use `__init__` for a global counter ? __**NO**__!!!
When deploying on a computing cluster using slurm, most likely every repetition is executed in its own independent process. This results in a dual set of requirements for your experiment implementation:

1. Each experiment repetition should be independently deployable. Do not assume that you can access any results from an earlier repetition through `self.*` fields. The only kind of persistency you can rely on, is writing results to disk.
2. Do not rely on that an Experiment Instance gets destroyed between repetitions. Always assume that `self.*` fields might carry leftover information unless explicitely (re)set in the `initialize()` method.

## 2.2 Run
Thre `run()` should implement the main logic / process of your project. There are no restrictions what you can do here. As this function is probably the most important in your implementation, we want to discuss in more detail its paramters.

```python
def run(self, cw_config: dict, rep: int, logger: cw_logging.LoggerArray) -> None:
    ...
```
### 2.2.1 cw_config: dict
`cw_config` is a dictonary containing an unrolled experiment configuration. Unrolled means that `grid` and `list` keywords have been resolved and the `DEFAULT` documents have been merged. 
Important keys of this `dict` for your implementation might be:
- `params`: containing the unrolled `params` section of your configuration file. See [Configuration YAML File](03_config.md) for more information.
- `_rep_log_path`: a path unique to this repition. You can write your results / logs to this directory. It is guaranteed to exist and to be threadsafe. No other experimental run of your deployment will access this path. See [CW2 File System](05_files.md) for more information.

### 2.2.2 rep: int
`rep` is an integer indication the repetition number of this run. As the repetitions are mostly intended to repeat the same parameter combination for numerically unstable experiments, the most likely scenario to use this parameter is to seed a random number generator, e.g.

```python
np.seed(rep)
```

The repetition number is not globally unique, meaning you cannot use the `rep` argument alone to save your results in a global database.
Assume you have the following YAML configuration:

```yaml
---
name: "exp_1"
repetitions: 2

grid:
    x: [1, 2]
    y: [3, 4]
```

The `grid` keyword will generate 2x2 = 4 parameter combinations with 2 repetitions each, resulting in a total of 8 runs.
Assume an Experiment implementation with the following `run()` function:

```python
def run(self, cw_config: dict, rep: int, ...):
    print(cw_config['params'])
    print(rep)
```
Output:
```
x: 1, y: 3
rep: 0

x: 1, y: 3
rep: 1

x: 2, y: 3
rep: 0

x: 2, y: 3
rep: 1

...
```
Only the combination of `params` and `rep` is unique in each run, or the `_rep_log_path`.


### 2.2.3 logger: LoggerArray
`logger` is a [`LoggerArray`](../cw2/cw_data/cw_logging.py) object. If you have added any Logger object, you can pass them your results / messages with
```python
msg = {}
logger.process(msg)
```
See [Logging Results](07_logging.md) for more information.

## 2.3 Finalize
The finalize function is called after `run()` has finished at the end of each repetition. The intention for this function is to close any opened writers / database connections, and maybe summarize the results from an (iterative) experiment execution. The function signature of `finalize()` differs from the other `AbstractExperiment` functions.

```python
def finalize(self, surrender: ExperimentSurrender = None, crash: bool = False):
    ...
```

If the `run()` function wants to abort early for whatever reason, e.g. converged loss function or any other kind of reason, the `run()` function can raise an [`ExperimentSurrender`](../cw2/cw_error.py) error. This custom error can take a `dict` as payload, which can then be accessed by the finalize. If you have different scenarios in which you want to abort an experimental run, this payload can be accessed through this `surrender` object by the `finalize()` function to react accordingly. See [Advanced Program Flow & Parallelization](09_program_flow.md) for more information.

`crash` is a boolean indication if `initialize()` or `run()` encountered any error, which you did not catch in your implementation. **cw2** ensures that even if a critical error occurs in those two functions, `finalize()` still gets called to perform its shutdown procedure. Following repetitions / runs in the same process should therefore not be impacted by earlier errors.


## 2.4 Iterative Experiment
If you have an experiment with an iterative process, e.g. a for-loop as main component in your `run()` method, you might want to implement the [`AbstractIterativeExperiment`](../cw2/experiment.py) interface.

This interface comes with additional functionality. For example, you can define the number of iterations in your YAML config file with the `iterations` keyword, and **cw2** handles the for-loop for you. It also provides a [`PandasLogger`](../cw2/cw_data/cw_pd_logger.py) to write your results after each iteration into an excel like structure.

### 2.4.1 Iterate
Instead of implementing the `run()` method, you have to implement `iterate()`:

```python
def iterate(self, cw_config: dict, rep: int, n: int) -> dict:
    return {"Result": "Current Iteration is {}".format(n)}
```
In addition to the `cw_config` configuration object and `rep` repetition indicator, it also receives the current iteration `n`. This function should perform one single iteration of your process and return a dict with yhour results / messages / metrics you want to log.

The following keys are already reserved:
- `"ts"` timestamp of the iteration results
- `"rep"` repetition counter
- `"iter"` iteration counter

You can again raise an [`ExperimentSurrender`](../cw2/cw_error.py) error to abort early. In this case, the payload of the error is used as the result for logging.

### 2.4.2 Save State
After each `iterate()` call, the `save_state()` function is executed.
It has the same parameters as the `iterate()` function, but does not return a result.

You could use this function to save a snapshot / model of your experiment after each iteration.

```python
def save_state(self, cw_config: dict, rep: int, n: int) -> None:
    # Save model every 50 iterations.
    if n % 50 == 0:
        self.model.to_disk(cw_config['_rep_log_path'])
```


[Back to Overview](./)