# cw2 - ClusterWork 2

A second iteration of a the software framework ClusterWork to easily deploy experiments on an computing cluster using SLURM.

## Installation
0. We recommend creating a virtual environment with [virtualenv](https://virtualenv.pypa.io/en/stable/) or [conda](https://conda.io/miniconda.html) before installing **cw2**:
    - Create a conda environment and activate it:
    ```bash
    conda create -n my_env python=3
    conda activate my_env
    ```
    - Or create a virtualenv environment and activate it
    ```bash
    virtualenv -p python3 /path/to/my_env
    source /path/to/my_env/bin/activate
    ```
1. Clone or Download **cw2**
    ```bash
    git clone https://github.com/ALRhub/cw2.git
    ```

2. Install **cw2**:
     ```bash
     cd /path/to/cw2
     pip install .
     ```

## Quickstart
Please refer to the [Quickstart Guide](doc/01_quickstart.md) in the documentation folder.

## Program Execution
To start an experiment locally, e.g. for testing:
```bash
python3 YOUR_MAIN.py YOUR_CONFIG.yml
```

To start an experiment on a slurm cluster:
```bash
python3 YOUR_MAIN.py YOUR_CONFIG.yml -s
```

