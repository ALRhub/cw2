import experiment
import scheduler
from workload import config, job


class Foreman:
    def __init__(self, config_path, exp_cls: experiment.AbstractExperiment, delete_old_files: bool = False, root_dir: str = ""):
        self.config = config.Config(config_path)
        self.jobs = []

        for exp_conf in self.config.exp_configs:
            j = job.Job(exp_cls, exp_conf, delete_old_files, root_dir)
            self.jobs.append(j)

        s = scheduler.LocalScheduler()
        s.assign(self.jobs, exp_cls)
        s.run()
