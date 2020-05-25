import os

class Job:
    def __init__(self, exp_config, delete_old_files=False, root_dir=""):
        self.config = exp_config
        self.__create_experiment_directory(delete_old_files, root_dir)

    def __create_experiment_directory(self, delete_old_files=False, root_dir=""):
         # create experiment path and subdir
        os.makedirs(os.path.join(root_dir, self.config['path']), exist_ok=True)

        # delete old histories if --del flag is active
        if delete_old_files:
            os.system('rm -rf {}/*'.format(self.config['path']))

        # create a directory for the log path
        os.makedirs(os.path.join(
            root_dir, self.config['log_path']), exist_ok=True)