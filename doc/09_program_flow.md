# Error Handling
Should any kind of exception be raised during an Experiment execution (`initialize()` or `run()`), `CW2` will abort this experiment run, log the error including stacktrace to a log file in the repetition directory and continue with the next task.

If you want to end an (iterative) experiment early, you can raise the `cw_error.ExperimentSurrender` exception to gracefully abort the experiment execution.