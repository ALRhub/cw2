#!/bin/bash
#SBATCH -p dev
# #SBATCH -A 
#SBATCH --array 0-19%120
#SBATCH -J cma
# #SBATCH -D %%experiment_root%%    # Already done with cd below - also, difference to cwd ??
#SBATCH --mail-type=END
# Please use the complete path details :
#SBATCH -o /home/max_li/exp_output/rosenbrock/log/out_%A_%a.log
#SBATCH -e /home/max_li/exp_output/rosenbrock/log/err_%A_%a.log
#
#SBATCH -n 1         # Number of tasks
#SBATCH -c 1  # Number of cores per task
#SBATCH --mem-per-cpu=1000         # Main memory in MByte per MPI task
#SBATCH -t 0:30:00             # 1:00:00 Hours, minutes and seconds, or '#SBATCH -t 10' - only minutes

# -------------------------------

# Load the required modules
# module load gcc openmpi/gcc
export OPENBLAS_NUM_THREADS=1
export PYTHONPATH=$PYTHONPATH:/home/max_li/cluster_work_v2/

# Activate the virtualenv / conda environment
source activate /home/max_li/venv/bin/activate

# cd into the working directory
cd /home/max_li/code/cw2/cma_tutorial

python3 cma_main.py cma_config.yml -j $SLURM_ARRAY_TASK_ID -e rosenbrock