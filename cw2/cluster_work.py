import subprocess

from cw2 import (cli_parser, config, cw_logging, cw_slurm, experiment, job,
                 scheduler)


def run(exp_cls: experiment.AbstractExperiment, root_dir: str = ""):
    args = cli_parser.Arguments().get()

    _config = config.Config(args.config, args.experiments)
    exp_configs = _config.exp_configs

    logArray = cw_logging.LoggerArray()
    logArray.add(cw_logging.PandasRepSaver())

    if args.slurm:
        slurm_script = cw_slurm.create_slurm_script(_config)

        cmd = "sbatch " + slurm_script
        print(cmd)

        subprocess.check_output(cmd, shell=True)
        return

    rep = None
    if args.job is not None:
        exp_configs, rep = _config.get_single_job(args.job)

    factory = job.JobFactory(exp_cls, logArray, args.delete, root_dir)
    _jobs = factory.create_jobs(exp_configs, rep)

    s = scheduler.LocalScheduler()
    s.assign(_jobs, exp_cls)

    s.run(rep)
