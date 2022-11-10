import datetime
import os
import shutil
import subprocess
import sys

import __main__

from cw2 import cli_parser, cw_error, util
from cw2.cw_config import cw_config
from cw2.cw_data import cw_logging
import cw2.cw_slurm.cw_slurm_keys as SKEYS
import cw2.cw_config.cw_conf_keys as CKEYS


class SlurmConfig:
    def __init__(self, conf: cw_config.Config) -> None:
        self.conf = conf
        self.slurm_conf = conf.slurm_config

        if self.slurm_conf is None:
            raise cw_error.MissingConfigError(
                "No SLURM configuration found in {}".format(self.conf.config_path))

        self._check_template()

    def _check_template(self):
        """check if an sbatch.sh template is present.
        If no costum template has been specified, the default will be used.
        """

        if SKEYS.TEMPLATE_PATH not in self.slurm_conf:
            self.slurm_conf[SKEYS.TEMPLATE_PATH] = os.path.join(
                os.path.dirname(__file__), '../default_sbatch.sh')

        if not os.path.exists(self.slurm_conf[SKEYS.TEMPLATE_PATH]):
            raise cw_error.ConfigKeyError(
                "Could not find default sbatch template. Please specify your own 'path_to_template'.")

    def _complete_optionals(self):
        """Fill in any optional values.
        """

        sc: dict = self.slurm_conf

        exp_output_path = self.conf.exp_configs[0][CKEYS.i_BASIC_PATH]

        # CREATE OPTIONAL COLLECTIONS
        # Must be done first:
        sc.setdefault(SKEYS.SBATCH_ARGS, {})

        # SET DEFAULT VALUES
        sc.setdefault(SKEYS.SLURM_LOG, os.path.join(exp_output_path, "slurmlog"))
        sc.setdefault(SKEYS.SLURM_OUT, os.path.join(exp_output_path, "sbatch.sh"))
        sc.setdefault(SKEYS.ACCOUNT, "")

        # COMPLEX CONVERSIONS
        if isinstance(sc[SKEYS.TIME], int):
            sc[SKEYS.TIME] = '{:d}:{:d}:00'.format(
                sc[SKEYS.TIME] // 60, sc[SKEYS.TIME] % 60)

        if SKEYS.CPU_MEM in sc:
            sc[SKEYS.SBATCH_ARGS][SKEYS.CPU_MEM] = sc.get(SKEYS.CPU_MEM)

        # DEFAULT OR COMPLEX CONVERSION
        if SKEYS.VENV in sc:
            sc[SKEYS.VENV] = "source activate {}".format(sc[SKEYS.VENV])
        else:
            sc[SKEYS.VENV] = ""

        if SKEYS.SH_LINES in sc:
            sc[SKEYS.SH_LINES] = "\n".join(sc[SKEYS.SH_LINES])
        else:
            sc[SKEYS.SH_LINES] = ""

    def _complete_cli_args(self):
        """identify and process the relevant CLI flags from the original call.
        """
        sc = self.slurm_conf
        cw_options = cli_parser.Arguments().get()

        sc[SKEYS.CW_ARGS] = ""
        if cw_options['overwrite']:
            sc[SKEYS.CW_ARGS] += " -o"
        if cw_options['experiments'] is not None:
            sc[SKEYS.CW_ARGS] += " -e " + " ".join(cw_options["experiments"])

    def _complete_sbatch_args(self):
        """if optional SBATCH arguments are present, build a corresponding string.
        """
        sc = self.slurm_conf

        if SKEYS.SBATCH_ARGS not in sc:  # Check if empty
            sc[SKEYS.SBATCH_ARGS] = ""
            return
        else:  # Else build String
            sbatch_args = sc.get(SKEYS.SBATCH_ARGS)

            args_list = ["#SBATCH --{} {}".format(k, v)
                         for k, v in sbatch_args.items()]
            sc[SKEYS.SBATCH_ARGS] = "\n".join(args_list)

    def finalize(self, num_jobs: int):
        """enrich slurm configuration with dynamically computed values

        Args:
            num_jobs (int): total number of defined jobs
        """

        # counting starts at 0
        self.slurm_conf[SKEYS.LAST_IDX] = num_jobs - 1

        # Order is important!
        self._complete_optionals()
        self._complete_cli_args()
        self._complete_sbatch_args()


class SlurmDirectoryManager:
    MODE_COPY = "COPY"
    MODE_MULTI = "MULTI"
    MODE_NOCOPY = "NOCOPY"
    MODE_ZIP = "ZIP"

    def __init__(self, sc: SlurmConfig, conf: cw_config.Config) -> None:
        self.slurm_config = sc
        self.conf = conf
        self.m = self.set_mode()
        os.makedirs(sc.slurm_conf[SKEYS.SLURM_LOG], exist_ok=True)

    def set_mode(self):
        """find which code-copy mode is configured

        Raises:
            cw_error.ConfigKeyError: if incomplete definition

        Returns:
            code-copy mode
        """
        sc = self.slurm_config.slurm_conf

        # COUNT MISSING ARGS
        cp_error_count = 0
        missing_arg = ""
        if SKEYS.EXP_CP_AUTO not in sc and SKEYS.EXP_CP_DST not in sc:
            cp_error_count += 1
            missing_arg = SKEYS.EXP_CP_DST

        if SKEYS.EXP_CP_SRC not in sc:
            cp_error_count += 1
            missing_arg = SKEYS.EXP_CP_SRC

        # MODE SWITCH
        if cp_error_count == 1:
            raise cw_error.ConfigKeyError(
                "Incomplete SLURM experiment copy config. Missing key: {}".format(missing_arg))

        cw_options = cli_parser.Arguments().get()
        if cw_options.get('zip'):
            return self.MODE_ZIP

        if cw_options.get('multicopy'):
            if cp_error_count == 0:
                return self.MODE_MULTI
            else:
                raise cw_error.ConfigKeyError(
                    "Incomplete SLURM experiment copy config. Please define SRC and DST for --multicopy")

        if cp_error_count == 0:
            return self.MODE_COPY
        return self.MODE_NOCOPY

    def dir_size_validation(self, src):
        """validates that the SRC for code copy is below 200MB in size

        Args:
            src: src path

        Raises:
            cw_error.ConfigKeyError: if directory is greater than 200MB
        """
        cw_options = cli_parser.Arguments().get()
        if cw_options.get('skipsizecheck'):
            return

        dirsize = util.get_size(src)
        if dirsize > 200.0:
            cw_logging.getLogger().warning("SourceDir {} is greater than 200MByte".format(src))
            msg = "Directory {} is greater than 200MByte." \
                  " If you are sure you want to copy/zip this dir, use --skipsizecheck." \
                  "\nElse check experiment_copy__ configuration keys".format(src)
            raise cw_error.ConfigKeyError(msg)

    def get_exp_src(self) -> str:
        """retrieves the code-copy src.
        Uses CWD as default unless specified

        Returns:
            src path
        """
        sc = self.slurm_config.slurm_conf
        return sc.get(SKEYS.EXP_CP_SRC, os.getcwd())

    def get_exp_dst(self):
        """retrieves the code-copy dst.
        Uses CWD as default unless specified

        Returns:
            src path
        """
        sc = self.slurm_config.slurm_conf
        if SKEYS.EXP_CP_AUTO in sc and SKEYS.EXP_CP_DST not in sc:
            sc[SKEYS.EXP_CP_DST] = os.path.join(sc.get(SKEYS.EXP_CP_AUTO),
                                                datetime.datetime.now().strftime("%Y%m%d%G%M%S"))
        if SKEYS.EXP_CP_DST in sc:
            return sc[SKEYS.EXP_CP_DST]
        else:
            exp_output_path = self.conf.exp_configs[0][CKEYS.i_BASIC_PATH]
            return os.path.join(exp_output_path, 'code')

    def zip_exp(self):
        """procedure for creating a zip backup
        """
        src = self.get_exp_src()
        dst = self.get_exp_dst()
        self.dir_size_validation(src)

        shutil.make_archive(dst, 'zip', src)

    def create_single_copy(self):
        """creates a copy of the exp for slurm execution
        """
        src = self.get_exp_src()
        dst = self.get_exp_dst()
        self._copy_files(src, dst)

    def create_multi_copy(self, num_jobs: int):
        """creates multiple copies of the exp, one for each slurm job

        Args:
            num_jobs (int): number of total jobs
        """
        src = self.get_exp_src()
        dst_base = self.get_exp_dst()

        for i in range(num_jobs):
            dst = os.path.join(dst_base, str(i))
            self._copy_files(src, dst)

        # Add MultiCopy ChangeDir to Slurmconf
        self.slurm_config.slurm_conf[SKEYS.SH_LINES] += "\ncd {} \n".format(os.path.join(self.get_exp_dst(),
                                                                                         "$SLURM_ARRAY_TASK_ID"))

    def _copy_files(self, src, dst):
        """copies files from src to dst

        Args:
            src: source directory
            dst: destination directory

        Raises:
            cw_error.ConfigKeyError: if the dst is inside the source. Recursive copying!
            cw_error.ConfigKeyError: if the dst already exists and overwrite is not forced.
        """
        self.dir_size_validation(src)

        # Check Filesystem
        if util.check_subdir(src, dst):
            raise cw_error.ConfigKeyError(
                "experiment_copy_dst is a subdirectory of experiment_copy_src. Recursive Copying is bad.")
        try:
            os.makedirs(
                dst, exist_ok=cli_parser.Arguments().get()['overwrite'])
        except FileExistsError:
            raise cw_error.ConfigKeyError(
                "{} already exists. Please define a different 'experiment_copy_dst', use '-o' to overwrite or '--nocodecopy' to skip.")

        # Copy files
        ign = shutil.ignore_patterns('*.pyc', 'tmp*', '.git*')
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, ignore=ign)
            else:
                shutil.copy2(s, d)

    def move_files(self, num_jobs: int):
        """moves exp files according to detected copy mode
        Args:
            num_jobs: number of slurm jobs for multi-copy
        """
        # Check Skip Flag
        cw_options = cli_parser.Arguments().get()
        if cw_options.get('nocodecopy'):
            print('Skipping Code Copy')
            return

        if self.m == self.MODE_COPY:
            self.create_single_copy()

        if self.m == self.MODE_MULTI:
            self.create_multi_copy(num_jobs)

        if self.m == self.MODE_ZIP:
            self.zip_exp()

    def get_exp_exec_dir(self) -> str:
        """retrieves the experiment execution dir.
        This dir depends on the exp_copy_dst

        Returns:
            str: experiment execution directory
        """
        if self.m == self.MODE_COPY or self.m == self.MODE_MULTI:
            return self.get_exp_dst()

        return self.get_exp_src()

    def get_py_path(self) -> str:
        """computes a modified python path, depending on the experiment_copy procedure

        Returns:
            str: python path setting
        """
        if self.m in [self.MODE_NOCOPY, self.MODE_ZIP]:
            return ""

        pypath = sys.path.copy()

        src = self.get_exp_src()
        dst = self.get_exp_dst()

        if self.m == self.MODE_MULTI:
            dst = os.path.join(dst, "$SLURM_ARRAY_TASK_ID")

        new_path = [x.replace(os.path.abspath(src), os.path.abspath(dst))
                    for x in pypath]
        # return "export PYTHONPATH=" + ":".join(new_path)
        # Maybe this is better?
        return "export PYTHONPATH=$PYTHONPATH:" + ":".join(new_path)


def run_slurm(conf: cw_config.Config, num_jobs: int) -> None:
    """starts slurm execution

    Args:
        conf (cw_config.Config): config object
        num_jobs (int): total number of jobs
    """
    # Finalize Configs
    sc = SlurmConfig(conf)
    sc.finalize(num_jobs)

    # Create Code Copies
    dir_mgr = SlurmDirectoryManager(sc, conf)
    dir_mgr.move_files(num_jobs)

    # Write and call slurm script
    slurm_script = write_slurm_script(sc, dir_mgr)
    cmd = "sbatch " + slurm_script
    print(cmd)
    subprocess.check_output(cmd, shell=True)


def write_slurm_script(slurm_conf: SlurmConfig, dir_mgr: SlurmDirectoryManager) -> str:
    """write the sbatch.sh script for slurm to disk

    Args:
        slurm_conf (SlurmConfig): Slurm configuration object

    Returns:
        str: path to the written script
    """
    sc = slurm_conf.slurm_conf
    conf = slurm_conf.conf

    template_path = sc[SKEYS.TEMPLATE_PATH]
    output_path = sc[SKEYS.SLURM_OUT]

    exp_main_file = os.path.relpath(__main__.__file__, os.getcwd())

    fid_in = open(template_path, 'r')
    fid_out = open(output_path, 'w')

    tline = fid_in.readline()

    while tline:
        tline = tline.replace('%%partition%%', sc['partition'])
        tline = tline.replace('%%account%%', sc[SKEYS.ACCOUNT])
        tline = tline.replace('%%job-name%%', sc['job-name'])

        tline = tline.replace('%%last_job_idx%%',
                              '{:d}'.format(sc[SKEYS.LAST_IDX]))
        tline = tline.replace('%%num_parallel_jobs%%',
                              '{:d}'.format(sc['num_parallel_jobs']))

        tline = tline.replace('%%experiment_execution_dir%%',
                              dir_mgr.get_exp_exec_dir())

        tline = tline.replace('%%slurm_log%%', sc[SKEYS.SLURM_LOG])

        tline = tline.replace('%%ntasks%%', '{:d}'.format(sc['ntasks']))
        tline = tline.replace('%%cpus-per-task%%',
                              '{:d}'.format(sc['cpus-per-task']))
        tline = tline.replace('%%time%%', sc[SKEYS.TIME])

        tline = tline.replace('%%sh_lines%%', sc[SKEYS.SH_LINES])

        tline = tline.replace('%%venv%%', sc[SKEYS.VENV])
        tline = tline.replace('%%pythonpath%%', dir_mgr.get_py_path())

        tline = tline.replace('%%python_script%%', exp_main_file)
        tline = tline.replace('%%path_to_yaml_config%%', conf.config_path)

        tline = tline.replace('%%cw_args%%', sc[SKEYS.CW_ARGS])
        tline = tline.replace('%%sbatch_args%%', sc[SKEYS.SBATCH_ARGS])

        fid_out.write(tline)

        tline = fid_in.readline()
    fid_in.close()
    fid_out.close()
    return output_path