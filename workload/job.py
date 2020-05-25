import abc
import os


class AbstractJob(abc.ABC):
    def _assign(self, exp_config, delete_old_files=False, root_dir=""):
        self.config = exp_config
        self.__create_experiment_directory(delete_old_files, root_dir)

    # TODO: save new path with root dir appended?
    def __create_experiment_directory(self, delete_old_files=False, root_dir=""):
         # create experiment path and subdir
        os.makedirs(os.path.join(root_dir, self.config['path']), exist_ok=True)

        # delete old histories if --del flag is active
        # TODO: Should this be the same path as before?
        if delete_old_files:
            os.system('rm -rf {}/*'.format(self.config['path']))

        # create a directory for the log path
        os.makedirs(os.path.join(
            root_dir, self.config['log_path']), exist_ok=True)

    @abc.abstractmethod
    def initialize(self, config: dict, rep: int) -> None:
        """needs to be implemented by subclass.
        Called once at the start of each repition for initialization purposes.

        Arguments:
            config {dict} -- parameter configuration
            rep {int} -- repition counter
        """
        raise NotImplementedError

    @abc.abstractmethod
    def iterate(self, config: dict, rep: int, n: int) -> dict:
        """needs to be implemented by subclass.
        The iteration procedure.

        Arguments:
            config {dict} -- parameter configuration
            rep {int} -- repitition counter
            n {int} -- iteration counter

        Returns:
            dict -- result map
        """
        raise NotImplementedError

    @abc.abstractmethod
    def finalize(self):
        """needs to be implemented by subclass.
        Called after all the iterations have finished at the end of the repitition.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def save_state(self, config: dict, rep: int, n: int) -> None:
        """needs to be implemented by subclass.
        Intended to save an intermediate state after each iteration.
        Arguments:
            config {dict} -- parameter configuration
            rep {int} -- repitition counter
            n {int} -- [description]
        """
        raise NotImplementedError

    @abc.abstractmethod
    def restore_state(self, config: dict, rep: int, n: int) -> bool:
        """needs to be implemented by subclass.
        if the experiment supports restarting within a repetition
        (on iteration level), load necessary stored state in this
        function. Otherwise, restarting will be done on repetition
        level, deleting all unfinished repetitions and restarting
        the experiments.

        Arguments:
            config {dict} -- parameter configuration
            rep {int} -- repition counter
            n {int} -- iteration counter

        Returns:
            bool -- success
        """
        raise NotImplementedError
