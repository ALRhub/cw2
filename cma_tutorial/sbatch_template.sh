#!/bin/bash
#SBATCH -p dev
# #SBATCH -A %%project_name%%
#SBATCH --array 0-%%num_jobs%%%%%num_parallel_jobs%%
#SBATCH -J %%experiment_name%%
# #SBATCH -D %%experiment_root%%    # Already done with cd below - also, difference to cwd ??
#SBATCH --mail-type=END
# Please use the complete path details :
#SBATCH -o %%experiment_log%%/out_%A_%a.log
#SBATCH -e %%experiment_log%%/err_%A_%a.log
#
#SBATCH -n %%number_of_jobs%%         # Number of tasks
#SBATCH -c %%number_of_cpu_per_job%%  # Number of cores per task
#SBATCH --mem-per-cpu=%%mem%%         # Main memory in MByte per MPI task
#SBATCH -t %%time_limit%%             # 1:00:00 Hours, minutes and seconds, or '#SBATCH -t 10' - only minutes

# -------------------------------

# Load the required modules
# module load gcc openmpi/gcc
export OPENBLAS_NUM_THREADS=1
export PYTHONPATH=$PYTHONPATH:/home/max_li/cluster_work_v2/

# Activate the virtualenv / conda environment
source activate /home/max_li/venv/bin/activate

# cd into the working directory
cd %%experiment_wd%%

python3 %%python_script%% %%path_to_yaml_config%% -j $SLURM_ARRAY_TASK_ID %%exp_name%%