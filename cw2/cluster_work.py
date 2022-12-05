from typing import List, Type

from cw2 import cli_parser, experiment, job, scheduler
from cw2.cw_config import cw_config
from cw2.cw_data import cw_loading, cw_logging


class ClusterWork:
    def __init__(self, exp_cls: Type[experiment.AbstractExperiment] = None):

        self.args = cli_parser.Arguments().get()
        self.exp_cls = exp_cls
        self.config = cw_config.Config(self.args['config'],
                                       self.args['experiments'],
                                       self.args['debug'],
                                       self.args['debugall'])

        self.logArray = cw_logging.LoggerArray()

        if not self.args['noconsolelog']:
            self.add_logger(cw_logging.PythonLogger())
        self.joblist = None

    def add_logger(self, logger: cw_logging.AbstractLogger) -> None:
        """add a logger to the ClusterWork pipeline

        Args:
            logger (cw_logging.AbstractLogger): logger object to be called during execution
        """
        self.logArray.add(logger)

    def _get_jobs(self, delete: bool = False, root_dir: str = "", read_only: bool = False) -> List[job.Job]:
        """private method. creates and returns all configured jobs.

        Args:
            delete (bool, optional): delete all old data inside the job directories. Defaults to False.
            root_dir (str, optional): [description]. Defaults to "".

        Returns:
            List[job.Job]: list of all configured job objects
        """
        if self.joblist is None:
            factory = job.JobFactory(
                self.exp_cls, self.logArray, delete, root_dir, read_only)
            self.joblist = factory.create_jobs(self.config.exp_configs)
        return self.joblist

    def run(self, root_dir: str = "", sch: scheduler.AbstractScheduler = None):
        """Run ClusterWork computations.

        Args:
            root_dir (str, optional): [description]. Defaults to "".
        """
        if self.exp_cls is None:
            raise NotImplementedError(
                "Cannot run with missing experiment.AbstractExperiment Implementation.")

        self.config.to_yaml(relpath=True)

        args = self.args

        # Handle SLURM execution
        if args['slurm']:
            s = scheduler.SlurmScheduler(self.config)
        else:
            # Do Local execution
            if sch is None:
                if scheduler.GPUDistributingLocalScheduler.use_distributed_gpu_scheduling(self.config):
                    scheduler_cls = scheduler.get_gpu_scheduler_cls(self.config.slurm_config.get("scheduler", "mp"))
                    s = scheduler_cls(self.config)
                else:
                    s = scheduler.LocalScheduler()
            else:
                s = sch

        self._run_scheduler(s, root_dir)

    def load(self, root_dir: str = ""):
        """Loads all saved information.

        Args:
            root_dir (str, optional): [description]. Defaults to "".

        Returns:
            pd.DataFrame: saved data in Dataframe form.
        """

        loader = cw_loading.Loader()

        return self._run_scheduler(loader, root_dir, True)

    def _run_scheduler(self, s: scheduler.AbstractScheduler, root_dir: str = "", read_only: bool = False):
        if self.logArray.is_empty():
            cw_logging.getLogger().warning("No Logger has been added. Are you sure?")

        args = self.args
        job_list = self._get_jobs(False, root_dir, read_only)

        if args['job'] is not None:
            job_list = [job_list[args['job']]]

        s.assign(job_list)
        return s.run(overwrite=args['overwrite'])
