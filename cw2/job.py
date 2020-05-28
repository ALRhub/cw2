import os


class Job():
    def __init__(self, exp_cls, exp_config, delete_old_files=False, root_dir=""):
        self.exp = exp_cls()
        self.config = exp_config
        self.__create_experiment_directory(delete_old_files, root_dir)

    # TODO: save new path with root dir appended?

    def __create_experiment_directory(self, delete_old_files=False, root_dir=""):
         # create experiment path and subdir
        os.makedirs(os.path.join(root_dir, self.config.path), exist_ok=True)

        # delete old histories if --del flag is active
        # TODO: Should this be the same path as before??
        # TODO: use shutil.rmtree?
        if delete_old_files:
            os.system('rm -rf {}/*'.format(self.config.path))

        # create a directory for the log path
        os.makedirs(os.path.join(
            root_dir, self.config.log_path), exist_ok=True)

        # create log path for each repetition
        rep_path_list = []
        for r in range(self.config.repetitions):
            rep_path = os.path.join(
                root_dir, self.config.log_path, 'rep_{:02d}'.format(r), '')
            os.makedirs(rep_path, exist_ok=True)

            rep_path_list.append(rep_path)
        self.config['rep_log_paths'] = rep_path_list

    def run(self):
        c = self.config
        for r in range(c.repetitions):
            self.exp.initialize(c, r)

            results = {}
            for n in range(c.iterations):
                results = self.exp.iterate(c, r, n)
                self.exp.save_state(c, r, n)

            self.exp.finalize()
            print(results)
