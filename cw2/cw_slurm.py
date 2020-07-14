import os
import shutil
import subprocess
import sys

import attrdict

import __main__
from cw2 import cli_parser, config


def run_slurm(conf: config.Config, num_jobs: int) -> None:
    """starts slurm execution

    Args:
        conf (config.Config): config object
        num_jobs (int): total number of jobs
    """
    sc, copy_exp = _finalize_slurm_config(conf, num_jobs)

    _prepare_dir(sc, conf, copy_exp)
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
        raise NameError(
            "No SLURM configuration found in {}".format(conf.config_path))

    exp_output_path = conf.exp_configs[0]['_experiment_path']
    copy_exp = True

    # counting starts at 0
    sc['last_job_idx'] = num_jobs - 1

    if "experiment_copy_dst" not in sc:
        sc["experiment_copy_dst"] = exp_output_path
        copy_exp = False

    if "experiment_copy_src" not in sc:
        sc["experiment_copy_src"] = os.path.dirname(os.path.abspath(__main__.__file__))
        print(sc["experiment_copy_src"])

    if "experiment_log" not in sc:
        sc["experiment_log"] = os.path.join(exp_output_path, 'slurmlog')

    if "slurm_ouput" not in sc:
        sc["slurm_output"] = os.path.join(exp_output_path, 'sbatch.sh')

    if "config_output" not in sc:
        sc["config_output"] = os.path.join(exp_output_path, "relative_" + conf.f_name)

    cw_options = cli_parser.Arguments().get()

    sc["cw_args"] = ""
    if cw_options.overwrite:
        sc["cw_args"] += " -o"
    if cw_options.experiments is not None:
        sc["cw_args"] = " -e " + " ".join(cw_options.experiments)

    return sc, copy_exp


def _prepare_dir(sc: attrdict.AttrDict, conf: config.Config, copy_exp: bool) -> None:
    """writes all the helper files associated with slurm execution

    Args:
        sc (attrdict.AttrDict): enriched slurm configuration
        conf (config.Config): overall configuration object
    """
    os.makedirs(sc["experiment_log"], exist_ok=True)
    conf.to_yaml(sc["config_output"])

    if copy_exp:
        _copy_exp_files(sc, conf)

def _copy_exp_files(sc: attrdict.AttrDict, conf: config.Config) -> None:
    # Copy code to new location
    #FIXME: Copy config too!! It can have an absolute path outside of experiment directory
    #FIXME: Use additional arg EXP_SRC
    os.makedirs(sc["experiment_copy_dst"], exist_ok=True)
    src = sc["experiment_copy_src"]
    dst = sc["experiment_copy_dst"]
    ign = shutil.ignore_patterns('*.pyc', 'tmp*')

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=ign)
        else:
            shutil.copy2(s, d)
    shutil.copy2(conf.config_path, os.path.join(dst, conf.f_name))

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

        tline = tline.replace('%%experiment_copy_dst%%',
                              sc['experiment_copy_dst'])
        tline = tline.replace('%%experiment_log%%', sc['experiment_log'])

        tline = tline.replace('%%mem-per-cpu%%', '{:d}'.format(sc['mem-per-cpu']))
        tline = tline.replace('%%ntasks%%', '{:d}'.format(sc['ntasks']))
        tline = tline.replace('%%cpus-per-task%%',
                              '{:d}'.format(sc['cpus-per-task']))
        tline = tline.replace('%%time%%', '{:d}:{:d}:00'.format(
            sc['time'] // 60, sc['time'] % 60))

        tline = tline.replace('%%python_script%%', experiment_code)
        tline = tline.replace('%%path_to_yaml_config%%', conf.f_name)
        tline = tline.replace('%%cw_args%%', sc["cw_args"])

        fid_out.write(tline)

        tline = fid_in.readline()
    fid_in.close()
    fid_out.close()
    return output_path
