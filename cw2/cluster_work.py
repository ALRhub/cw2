from cw2 import (cli_parser, config, cw_slurm, experiment, job, logging,
                 scheduler)


def run(exp_cls: experiment.AbstractExperiment, root_dir: str = ""):
    args = cli_parser.Arguments().get()

    _config = config.Config(args.config, args.experiments)
    exp_configs = _config.exp_configs

    logArray = logging.LoggerArray()
    logArray.add(logging.PandasRepSaver())
    logArray.add(logging.PandasAllSaver())

    if args.slurm:
        cw_slurm.create_slurm_skript(_config)

    rep = None
    if args.job is not None:
        exp_configs, rep = _config.get_single_job(args.job)
    
    _jobs = []
    for exp_conf in exp_configs:
        j = job.Job(exp_cls, exp_conf, logArray,
                    args.delete, root_dir)
        _jobs.append(j)

    s = scheduler.LocalScheduler()
    s.assign(_jobs, exp_cls)

    s.run(rep)
