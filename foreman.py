from workload import config, job
import scheduler

class Foreman:
    def __init__(self, config_path, job_cls: job.AbstractJob, delete_old_files: bool = False, root_dir: str = ""):
        self.config = config.Config(config_path)
        self.jobs = []

        for exp_c in self.config.exp_configs:
            j = job_cls()
            j.configure(exp_c, delete_old_files, root_dir)
            self.jobs.append(j)

        s = scheduler.LocalScheduler()
        s.assign(self.jobs)
        s.run()