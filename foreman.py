from workload import config, job


class Foreman:
    def __init__(self, config_path, delete_old_files: bool = False, root_dir: str = ""):
        self.config = config.Config(config_path)
        self.jobs = []

        for exp_c in self.config.exp_configs:
            self.jobs.append(job.Job(exp_c, delete_old_files, root_dir))
