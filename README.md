# cw2 - ClusterWork 2

[![Upload Python Package](https://github.com/ALRhub/cw2/actions/workflows/python-publish.yml/badge.svg)](https://github.com/ALRhub/cw2/actions/workflows/python-publish.yml)

ClusterWork 2 is a python framework to manage experiments using YAML config files. It also enables users to easily deploy multiple experiments using different configurations on computing clusters, which support the [slurm workload manager](https://slurm.schedmd.com/documentation.html).

## Installation
```bash
pip install cw2
```

## Quickstart
Please refer to the [Quickstart Guide](doc/01_quickstart.md).

## Program Execution
To start an experiment locally, e.g. for testing:
```bash
python3 YOUR_MAIN.py YOUR_CONFIG.yml
```

To start an experiment on a slurm cluster:
```bash
python3 YOUR_MAIN.py YOUR_CONFIG.yml -s
```

