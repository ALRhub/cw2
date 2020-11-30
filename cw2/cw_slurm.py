import os
import shutil
import subprocess
import sys

import attrdict

import __main__
from cw2 import cli_parser, config, cw_error, util
from cw2.cw_data import cw_logging


def run_slurm(conf: config.Config, num_jobs: int) -> None:
    """starts slurm execution

    Args:
        conf (config.Config): config object
        num_jobs (int): total number of jobs
    """
    sc = _finalize_slurm_config(conf, num_jobs)

    _prepare_dir(sc, conf)
    slurm_script = _create_slurm_script(sc, conf)

    cmd = "sbatch " + slurm_script

    print(cmd)
    subprocess.check_output(cmd, shell=True)


def _finalize_slurm_config(conf: config.Config, num_jobs: int) -> attrdict.AttrDict:
    """enrich slurm configuration with dynamicallyy computed values

    Args:
        conf (config.Config): configuration object.
        num_jobs (int): total number of defined jobs

    Returns:
        attrdict.AttrDict: complete slurm configuration dictionary
    """
    sc = conf.slurm_config
    if sc is None:
        raise cw_error.MissingConfigError(
            "No SLURM configuration found in {}".format(conf.config_path))

    exp_output_path = conf.exp_configs[0]["_basic_path"]

    # counting starts at 0
    sc['last_job_idx'] = num_jobs - 1

    if "path_to_template" not in sc:
        sc['path_to_template'] = os.path.join(
            os.path.dirname(__file__), 'default_sbatch.sh')
        if not os.path.exists(sc['path_to_template']):
            raise cw_error.ConfigKeyError(
                "Could not find default sbatch template. Please specify your own 'path_to_template'.")

    if "slurm_log" not in sc:
        sc["slurm_log"] = os.path.join(exp_output_path, "slurmlog")

    if "slurm_output" not in sc:
        sc["slurm_output"] = os.path.join(exp_output_path, "sbatch.sh")

    if "account" not in sc:
        sc["account"] = ""

    if "venv" not in sc:
        sc["venv"] = ""
    else:
        sc["venv"] = "source activate {}".format(sc["venv"])

    if "sh_lines" not in sc:
        sc["sh_lines"] = ""
    else:
        sc["sh_lines"] = "\n".join(sc["sh_lines"])

    sc["pythonpath"] = ""

    cw_options = cli_parser.Arguments().get()

    sc["cw_args"] = ""
    if cw_options.overwrite:
        sc["cw_args"] += " -o"
    if cw_options.experiments is not None:
        sc["cw_args"] += " -e " + " ".join(cw_options["experiments"])

    sc = _build_sbatch_args(sc)
    sc = _complete_exp_copy_config(sc, conf)

    return sc


def _build_sbatch_args(sc: attrdict.AttrDict) -> attrdict.AttrDict:
    """if optional SBATCH arguments are present, build a corresponding string.

    Args:
        sc (attrdict.AttrDict): slurm_config dictionary

    Returns:
        attrdict.AttrDict: extended slurm_config dictionary
    """
    if "sbatch_args" not in sc:
        sc["sbatch_args"] = ""
        return sc

    sbatch_args = sc['sbatch_args']
    args_list = []
    for k in sbatch_args:
        args_list.append("#SBATCH --{} {}".format(k, sbatch_args[k]))
    sc['sbatch_args'] = "\n".join(args_list)
    return sc


def _prepare_dir(sc: attrdict.AttrDict, conf: config.Config) -> None:
    """writes all the helper files associated with slurm execution

    Args:
        sc (attrdict.AttrDict): enriched slurm configuration
        conf (config.Config): overall configuration object
    """
    #os.makedirs(sc["slurm_log"], exist_ok=True)
    _copy_exp_files(sc, conf)


def _complete_exp_copy_config(sc: attrdict.AttrDict, conf: config.Config) -> attrdict.AttrDict:
    """checks for and handles experiment_copy keys.
    If both keys are present, copy src to dst and execute in dst.
    If both keys are missing, set cwd() as src and config["path"] as dst. Execute in cwd().
    If one key is missing throw an exception.

    Args:
        sc (attrdict.AttrDict): slurm-configuration dictionary
        conf (config.Config): config object

    Raises:
        cw_error.ConfigKeyError: If one key is missing.

    Returns:
        attrdict.AttrDict: updated slurm-configuration object.
    """
    # Validity Check
    exp_output_path = conf.exp_configs[0]["_basic_path"]
    cp_error_count = 0
    missing_arg = ""
    if "experiment_copy_dst" not in sc:
        sc["experiment_copy_dst"] = os.path.join(exp_output_path, 'code')
        cp_error_count += 1
        missing_arg = "experiment_copy_dst"

    if "experiment_copy_src" not in sc:
        sc["experiment_copy_src"] = os.getcwd()
        cp_error_count += 1
        missing_arg = "experiment_copy_src"

    if cp_error_count == 0:
        sc["experiment_execution_dir"] = sc["experiment_copy_dst"]
        sc["zip"] = False
        sc["pythonpath"] = _build_python_path(sc)
    elif cp_error_count == 1:
        raise cw_error.ConfigKeyError(
            "Incomplete SLURM experiment copy config. Missing key: {}".format(missing_arg))
    else:
        sc["experiment_execution_dir"] = sc["experiment_copy_src"]
        sc["zip"] = True
        cw_logging.getLogger().info(
            "No experiment_copy configuration found. Will zip cwd() for documentation.")
    return sc


def _copy_exp_files(sc: attrdict.AttrDict, conf: config.Config) -> None:
    """copy the experiment files to a new location.
    Copys both the python source files, and the YAML configuration

    Args:
        sc (attrdict.AttrDict): slurm-config dictionary
        conf (config.Config): config object

    Raises:
        cw_error.ConfigKeyError: If the the new destination is a subdirectory of the src folder.
    """
    src = sc["experiment_copy_src"]
    dst = sc["experiment_copy_dst"]

    # shutil.copy2(conf.config_path, os.path.join(dst, conf.f_name))

    cw_options = cli_parser.Arguments().get()
    if cw_options['nocodecopy']:
        print('Skipping Code Copy')
        return

    ign = shutil.ignore_patterns('*.pyc', 'tmp*')

    if not cw_options['skipsizecheck']:
        _check_src_size(src, sc['zip'])

    if sc['zip']:
        shutil.make_archive(dst, 'zip', src)
    else:
        if util.check_subdir(src, dst):
            raise cw_error.ConfigKeyError(
                "experiment_copy_dst is a subdirectory of experiment_copy_src. Recursive Copying is bad.")

        try:
            os.makedirs(dst, exist_ok=cw_options['overwrite'])
        except FileExistsError:
            raise cw_error.ConfigKeyError(
                "{} already exists. Please define a different 'experiment_copy_dst', use '-o' to overwrite or '--nocodecopy' to skip.")

        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, ignore=ign)
            else:
                shutil.copy2(s, d)

def _check_src_size(src: str, zipflag: bool):
    """Check if the src directory is smaller than 200MByte

    Args:
        src (str): source directory
        zipflag (bool): should it be zipped

    Raises:
        cw_error.ConfigKeyError: Abort with error message, as a too large dir indicates a missconfigured experiment.
    """
    dirsize = util.get_size(src)
    if dirsize > 200.0:
        cw_logging.getLogger().warning("SourceDir {} is greater than 200MByte".format(src))
        if zipflag:
            msg = "CWD {} is greater than 200MByte. If you are sure you want to zip this dir, use --skipsizecheck.\nElse define experiment_copy__ configuration keys or use --nocodecopy option.".format(
                src)
        else:
            msg = "experiment_copy_src {} is greater than 200MByte. If you are sure you want to copy this dir, use --skipsizecheck.\nElse change the experiment_copy_src configuration or use --nocodecopy option.".format(
                src)
        raise cw_error.ConfigKeyError(msg)

def _build_python_path(sc: attrdict.AttrDict) -> str:
    """clean the python path for the new experiment copy

    Args:
        sc (attrdict.AttrDict): slurm configuration

    Returns:
        str: python path bash command for slurm script
    """
    pypath = sys.path.copy()

    src = sc["experiment_copy_src"]
    dst = sc["experiment_copy_dst"]

    new_path = [x for x in pypath if x != src]
    new_path.append(dst)
    return "export PYTHONPATH=" + ":".join(new_path)


def _create_slurm_script(sc: attrdict.AttrDict, conf: config.Config) -> str:
    """creates an sbatch.sh script for slurm

    Args:
        sc (attrdict.AttrDict): enriched slurm configuration
        conf (config.Config): Configuration object 

    Returns:
        str: path to slurm file
    """

    template_path = sc["path_to_template"]
    output_path = sc["slurm_output"]

    experiment_code = __main__.__file__

    fid_in = open(template_path, 'r')
    fid_out = open(output_path, 'w')

    tline = fid_in.readline()

    while tline:
        tline = tline.replace('%%partition%%', sc['partition'])
        tline = tline.replace('%%account%%', sc['account'])
        tline = tline.replace('%%job-name%%', sc['job-name'])

        tline = tline.replace('%%last_job_idx%%',
                              '{:d}'.format(sc['last_job_idx']))
        tline = tline.replace('%%num_parallel_jobs%%',
                              '{:d}'.format(sc['num_parallel_jobs']))

        tline = tline.replace('%%experiment_execution_dir%%',
                              sc['experiment_execution_dir'])

        tline = tline.replace('%%slurm_log%%', sc['slurm_log'])

        tline = tline.replace(
            '%%mem-per-cpu%%', '{:d}'.format(sc['mem-per-cpu']))
        tline = tline.replace('%%ntasks%%', '{:d}'.format(sc['ntasks']))
        tline = tline.replace('%%cpus-per-task%%',
                              '{:d}'.format(sc['cpus-per-task']))
        tline = tline.replace('%%time%%', '{:d}:{:d}:00'.format(
            sc['time'] // 60, sc['time'] % 60))

        tline = tline.replace('%%sh_lines%%', sc["sh_lines"])

        tline = tline.replace('%%venv%%', sc["venv"])
        tline = tline.replace('%%pythonpath%%', sc['pythonpath'])

        tline = tline.replace('%%python_script%%', experiment_code)
        tline = tline.replace('%%path_to_yaml_config%%', conf.config_path)

        tline = tline.replace('%%cw_args%%', sc["cw_args"])
        tline = tline.replace('%%sbatch_args%%', sc["sbatch_args"])

        fid_out.write(tline)

        tline = fid_in.readline()
    fid_in.close()
    fid_out.close()
    return output_path
