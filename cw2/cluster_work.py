import logging
from typing import List

from cw2 import (cli_parser, config, cw_logging, cw_slurm, experiment, job,
                 scheduler)


class ClusterWork():
    def __init__(self, exp_cls: experiment.AbstractExperiment = None):
        self.args = cli_parser.Arguments().get()
        self.exp_cls = exp_cls
        self.config = config.Config(self.args.config, self.args.experiments)

        # Default Logger inlcudes Pandas CSV Saver
        self.logArray = cw_logging.LoggerArray()

    def add_logger(self, logger: cw_logging.AbstractLogger) -> None:
        """add a logger to the ClusterWork pipeline

        Args:
            logger (cw_logging.AbstractLogger): logger object to be called during execution
        """
        self.logArray.add(logger)

    def _get_jobs(self, delete: bool = False, root_dir: str = "") -> List[job.Job]:
        """private method. creates and returns all configured jobs.

        Args:
            delete (bool, optional): delete all old data inside the job directories. Defaults to False.
            root_dir (str, optional): [description]. Defaults to "".

        Returns:
            List[job.Job]: list of all configured job objects
        """
        factory = job.JobFactory(self.exp_cls, self.logArray, delete, root_dir)
        joblist = factory.create_jobs(self.config.exp_configs)
        return joblist

    def run(self, root_dir: str = ""):
        """Run ClusterWork computations.

        Args:
            root_dir (str, optional): [description]. Defaults to "".
        """
        if self.exp_cls is None:
            raise NotImplementedError(
                "Cannot run with missing experiment.AbstractExperiment Implementation.")

        if self.logArray.is_empty():
            logging.warning("No Logger has been added. Are you sure?")

        args = self.args

        # XXX: Disable Delete for now
        # _jobs = self._get_jobs(self.args.delete, root_dir)
        _jobs = self._get_jobs(False, root_dir)

        # Handle SLURM execution
        if args.slurm:
            return cw_slurm.run_slurm(self.config, len(_jobs))

        # Do Local execution
        s = scheduler.LocalScheduler()
        s.assign(_jobs)

        job_idx = None
        if args.job is not None:
            job_idx = args.job
        s.run(job_idx, overwrite=args.overwrite)

    def load(self, root_dir: str = "") -> dict:
        """Loads all saved information.

        Args:
            root_dir (str, optional): [description]. Defaults to "".

        Returns:
            dict: saved data in dict form. keys are the job's log folders, values are dicts of logger -> data
        """
        _jobs = self._get_jobs(False, root_dir)
        all_data = {}

        if self.logArray.is_empty():
            logging.warning("No Logger has been added. Are you sure?")

        for j in _jobs:
            for r in j.repetitions:
                self.logArray.initialize(j.config, r)
                data = self.logArray.load()
                all_data[j.get_rep_path(r)] = data
        return all_data
