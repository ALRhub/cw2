# 10. Advanced GPU Scheduling

Here we discuss advanced GPU Scheduling, i.e., advanced methods to distribute repetitions across GPUs.
There are two main use cases for this:

1.) **Putting Multiple Repetition on GPU**: Often, a single repetition is not enough to fully saturate the GPU (especially for the larger
Teslar Models used in HPC clusters).  Therefore, it can be beneficial to run multiple repetitions in parallel on a single GPU.

2.) **Requesting Single GPUs not possible**: Some HPC Clusters are configured in a way that requesting single GPUs via SLURM is not possible.
In this case, you'll always get multiple GPUs at once, and it's your responsibility to distribute the load across them.

**Caveat**: Please always have an eye on your jobs and make sure they behave as expected with regard to GPU utilization and runtime, do not fully rely on this! 
The underlying multiprocessing is tricky business, behaviour is not always consistent across different machines and python versions. 
There can be weird side effects. 


## 10.1. The ''gpus_per_rep'' Config Keyword

The main new functionality to control GPU usage is the `gpus_per_rep` config keyword. Although it's not an actual SLURM key-word, it needs to be specified in the SLURM block of your config.
It can be a float smaller than 1 or an integer lager or equal to 1. It does what the name suggests, it specifies how many GPUs are requested per repetition.
For it to properly work, you need to set the `reps_per_job` and `reps_in_parallel` keys accordingly. 

**Caveat**: I have no idea what happens if different values for `reps_per_job` and `reps_in_parallel` are used throught your YAML. Just don't do it (or test it).

### 10.1.1. Example 1: Using only half a GPU per repetition

Assume your Jobs are small and you want to run 2 on each single GPU. 
First, set `gpus_per_rep` to 0.5:

```yaml
---
# Slurm config
name: "SLURM"
partition: "gpu"
job-name: "half_gpu_job"
time: 20
ntasks: 1
cpus-per-task: 8  # 4 CPUs per rep!
gpus_per_rep: 0.5
sbatch_args:
  gres: "gpu:1
``` 

To have both jobs run on the same GPU in parallel, set `reps_per_job` to 2 and `reps_in_parallel` to 2 (you can also
set 'reps_per_job' to a multiple of 2):

```yml
--- 
# Default
name: DEFAULT
reps_per_job: 2
reps_in_parallel: 2
``` 
Specify your experiment as usual, the total number of repetitions should be a multiple of 2.

**Caveat**: There is nothing in CW2 to ensure GPU memory and compute is distributed evenly and not exceeded. 
It is your responsibility to take care of that! Check your code if it actually profits from this! (Don't expect a speed-up of 2x,
more something like > 1.5x)

### 10.1.2. Example 2: Using single GPUs when you can only request multiple GPUs 

Assume you are on a HPC-System where the minimum number of GPUs you can request is 4 (e.g. HoreKa).

First, set `gpus_per_rep` to 1:

```yaml
---
# Slurm config
name: "SLURM"
partition: "accelerated"
job-name: "single_gpu_job"
time: 20
ntasks: 1
cpus-per-task: 16 # 4 CPUs per rep!
gpus_per_rep: 1
sbatch_args:
  gres: "gpu:4  # Note how we request 4 GPUs here!
``` 

To have both jobs run on the same GPU in parallel, set `reps_per_job` to 4 and `reps_in_parallel` to 4 (you can also
set 'reps_per_job' to a multiple of 4):

```yml
--- 
# Default
name: DEFAULT
reps_per_job: 4
reps_in_parallel: 4
``` 
Specify your experiment as usual, the total number of repetitions should be a multiple of 4.

## 10.2 Cluster Specific Schedulers
I (Philipp B.) had issues with using this naively on both the Kluster and on HoreKa, but I am unsure if it's a general problem or just a problem of my code
(Todo: Somebody check with their stuff and tell me).
On both systems the jobs would run super slow, as the processes where stealing each others CPU resources.
I had to use different fixes for both systems, and write specific schedulers for them. 
You can use them via the `scheduler` key in the `slurm` block of your config, possible values are currently:

- "kluster": Explicitly limits the number of threads used (if you use something else than PyTorch, you probably need to have another look at that)
- "horeka": Explicitly handles the cpu affinity of individual repetitions.  

## 10.3 Use full CPU's computation power in a GPU node.
I (Bruce) had some low CPU computation speed issues when do online RL in Horeka GPU node, where I have to use both CPU (for mujoco) and GPU (for agent update). The reason is that for each experiment's generated gym environment, it can use all the cpus of this node and thus often blocks the access of the other environments or other repititions (when multple repititions are running in parallel). To solve it, I added the assigned CPU cores into the cw_config and you can manually assign theses cores to the environments yourself, e.g. one environment has one distinct core. Something like:
```python
   env_pids = [envs.processes[i].pid for i in range(num_env)]
   cores_per_env = len(cw_config["cpu_cores"]) // num_env
   cpu_cores_list = list(cw_config["cpu_cores"])
   for i, pid in enumerate(env_pids):
       cores_env = cpu_cores_list[i * cores_per_env: (i + 1) * cores_per_env]
       util.assign_process_to_cpu(pid, set(cores_env))
```
