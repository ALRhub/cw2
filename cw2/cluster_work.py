import subprocess

from cw2 import (cli_parser, config, cw_logging, cw_slurm, experiment, job,
                 scheduler)


class ClusterWork():
    def __init__(self, exp_cls: experiment.AbstractExperiment):
        self.args = cli_parser.Arguments().get()
        self.exp_cls = exp_cls
        self.config = config.Config(self.args.config, self.args.experiments)

        self.logArray = cw_logging.LoggerArray()
        self.add_logger(cw_logging.PandasRepSaver())

    def add_logger(self, logger: cw_logging.AbstractLogger):
        self.logArray.add(logger)

    def _get_jobs(self, delete: bool = False, root_dir: str = ""):
        factory = job.JobFactory(self.exp_cls, self.logArray, delete, root_dir)
        joblist = factory.create_jobs(self.config.exp_configs)
        return joblist

    def run(self, root_dir: str = ""):
        args = self.args

        _jobs = self._get_jobs(self.args.delete, root_dir)

        job_idx = None
        if args.job is not None:
            job_idx = args.job

        if args.slurm:
            slurm_script = cw_slurm.create_slurm_script(
                self.config, len(_jobs))

            cmd = "sbatch " + slurm_script
            print(cmd)

            subprocess.check_output(cmd, shell=True)
            return

        s = scheduler.LocalScheduler()
        s.assign(_jobs)

        s.run(job_idx)

    def load(self, root_dir: str=""):
        _jobs = self._get_jobs(False, root_dir)
        all_data = {}
        for j in _jobs:
            for r in j.repetitions:
                self.logArray.initialize(j.config, r)
                data = self.logArray.load()
                all_data[j.get_rep_path(r)] = data
        return all_data
