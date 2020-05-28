#!/bin/bash
#SBATCH -p dev
# #SBATCH -A %%project_name%%
#SBATCH --array 0-%%num_jobs%%%%%num_parallel_jobs%%
#SBATCH -J %%experiment_name%%
#SBATCH -D %%experiment_root%%
#SBATCH --mail-type=END
# Please use the complete path details :
#SBATCH -o %%experiment_cwd%%/log/out_%A_%a.log
#SBATCH -e %%experiment_cwd%%/log/err_%A_%a.log
#
#SBATCH -n %%number_of_jobs%%         # Number of tasks
#SBATCH -c %%number_of_cpu_per_job%%  # Number of cores per task
#SBATCH --mem-per-cpu=%%mem%%         # Main memory in MByte per MPI task
#SBATCH -t %%time_limit%%             # 1:00:00 Hours, minutes and seconds, or '#SBATCH -t 10' - only minutes

# -------------------------------

# Load the required modules
# module load gcc openmpi/gcc
export OPENBLAS_NUM_THREADS=1

# Activate the virtualenv / conda environment
source activate /home/max/nfs/venvs/stochastic_search/bin/activate

# cd into the working directory
cd %%experiment_root%%

# mpiexec -map-by core -bind-to core python3.6 -c "%%python_script%%" %%path_to_yaml_config%% -m -g 1 -l DEBUG -j $SLURM_ARRAY_TASK_ID %%exp_name%%
python3.6 -c "%%python_script%%" %%path_to_yaml_config%% -l DEBUG -j $SLURM_ARRAY_TASK_ID %%exp_name%%
