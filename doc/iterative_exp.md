#  Creating an Iterative Experiment
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

    def initialize(self, config: dict, rep: int, logger) -> None:
        print("Ready to start repetition {}. Resetting everything.".format(rep))

    def iterate(self, config: dict, rep: int, n: int) -> dict:
        return {"Result": "Current Iteration is {}".format(n)}

    def save_state(self, config: dict, rep: int, n: int) -> None:
        if n % 50 == 0:
            print("I am stateless. Nothing to write to disk.")
    
    def finalize(self, surrender: bool = False, crash: bool = False):
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