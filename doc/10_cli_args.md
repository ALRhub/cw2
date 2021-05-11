# 10. CLI args
The following args are currently supported by CW2:
| Flag  |Name           | Effect|
|-------|---------------|-------|
| -s    |--slurm        | Run using SLURM Workload Manager.|
| -o    | --overwrite   | Overwrite existing results.|
| -e name1 [...] | --experiments | Allows to specify which experiments should be run. Corresponds to the `name` field of the configuration YAML.
|     | --zip   | Creates a ZIP archive for documentation purposes of $CWD or, if set, "experiment_copy_src".|
|     | --skipsizecheck   | Disables a safety size check when Zipping or Code-Copying. The safety prevents unecessarily copying / archiving big files such as training data.|
| | --multicopy | Creates a Code-Copy for each Job. If you are modifying a hardcoded file in your codestructure during runtime, this feature might help ensure multiple runs do not interfere with each other.|