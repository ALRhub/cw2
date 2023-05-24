# 6. Code Copy Feature

- [6. Code Copy Feature](#6-code-copy-feature)
  - [6.1. Enabling Code Copy](#61-enabling-code-copy)
  - [6.2. Disabling Code Copy](#62-disabling-code-copy)
  - [6.3 CLI Options](#63-cli-options)
  - [6.4 Known Challenges](#64-known-challenges)


When submitting a job to a SLURM cluster, it is likely to wait in queue until requested compute resources become available. During this queuing time, the code can still be changed, as no Python process has been started yet.

Any changes the user makes to their code in this queueing time, will be in effect once the job starts. For example:

- User starts with default codebase A. They submit their first slurm job, waiting for results.
- While waiting, the user implements a new feature, resulting in a new codebase A*.
- Wanting to compare A* to the future results of A, the user submits a second job.
- After a while, the results of both jobs are ready. The results of the first job and second job are exactly identical. The user is confused.

In the above example, both jobs ran with codebase A*, leading to identical results.

To avoid this problem, we offer the **Code Copy Feature**.

## 6.1. Enabling Code Copy
To enable code copy, add the `src` and **one (1)** `dst` argument to your `SLURM` config section:

```yaml 
# Required for Code-Copy-Feature
experiment_copy_src: "/path/to/code_copy/src"       # Code Copy Source directory.

# Choose one for Code-Copy-Feature
experiment_copy_dst: "/path/to/code_copy/dst"       # Code Copy Destination directory. Will be overwritten if called multiple times.
experiment_copy_auto_dst: "/path/to/code_copy/dst"  # Code Copy Destination directory autoincrement. Will create a new subdirectory each time.
```

If you only want to "document" the code, so that you might reproduce it later, you can use the `--zip` CLI option. This will create a Zip Archive of your code in the code-copy `dst`.

## 6.2. Disabling Code Copy
To permanently disable code copy, remove the `src` and `dst` arguments from your `SLURM` config section.
To temporarily disable code copy, add `--nocodecopy` to your `python main.py config.yaml` call.

## 6.3 CLI Options
For a full and updated list, please refer to the [CLI Args Docu](11_cli_args.md).
| Flag | Name            | Effect                                                                                                                                                                                       |
| ---- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|      | --zip           | Creates a ZIP archive for documentation purposes of $CWD or, if set, "experiment_copy_src".                                                                                                  |
|      | --skipsizecheck | Disables a safety size check when Zipping or Code-Copying. The safety prevents unecessarily copying / archiving big files such as training data.                                             |
|      | --multicopy     | Creates a Code-Copy for each Job. If you are modifying a hardcoded file in your codestructure during runtime, this feature might help ensure multiple runs do not interfere with each other. |
|      | --nocodecopy    | Do not use the Code-Copy feature, even if the config arguments are specified.                                                                                                                |

## 6.4 Known Challenges
1. Code Copy can quickly lead to a storage problems. To avoid this, we have a safety check disabling code-copy if more than 200MB are targeted. This can be disabled via `--skipsizecheck`.   
**Attention!!**  
If your `src` contains training data, it will also be copied each time.  
If your `dst` is inside of `src`, future copies will contain the old ones. This can quickly lead to a file size explosion.

2. To ensure that the copied code is executed, `cw2` will modify the `$PYTHONPATH` to point at the `dst` directory. While in my experience this should be stable, it could lead to issues if you are also modifying the `$PYTHONPATH` somewhere.

As with all more advanced features, please double check upon first execution, if your code is still executed as expected.


[Back to Overview](./)