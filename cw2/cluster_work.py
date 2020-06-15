from cw2 import (cli_parser, config, cw_slurm, experiment, job, logging,
                 scheduler)


def run(exp_cls: experiment.AbstractExperiment, root_dir: str = ""):
    args = cli_parser.Arguments().get()

    _config = config.Config(args.config, args.experiments)
    _jobs = []

    logArray = logging.LoggerArray()
    logArray.add(logging.PandasRepSaver())
    # logArray.add(logging.Printer())

    cw_slurm.create_slurm_skript(_config)

    for exp_conf in _config.exp_configs:
        j = job.Job(exp_cls, exp_conf, logArray,
                    args.delete, root_dir)
        _jobs.append(j)

    s = scheduler.LocalScheduler()
    s.assign(_jobs, exp_cls)
    s.run()
