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
    exp_path = conf.exp_configs[0]['_experiment_path']
    sc["exp_path"] = exp_path

    # numjobs is last job index, counting starts at 0
    sc['num_jobs'] = num_jobs - 1

    if "experiment_wd" not in sc:
        sc["experiment_wd"] = exp_path

    if "experiment_log" not in sc:
        sc["experiment_log"] = os.path.join(exp_path, 'slurmlog')

    if "slurm_ouput" not in sc:
        sc["slurm_output"] = os.path.join(exp_path, 'sbatch.sh')

    if "config_output" not in sc:
        sc["config_output"] = os.path.join(exp_path, "relative_" + conf.f_name)

    cw_options = cli_parser.Arguments().get()
    sc["experiment_selectors"] = ""

    if cw_options.experiments is not None:
        sc["experiment_selectors"] = "-e " + " ".join(cw_options.experiments)

    # TODO: Automatically fill in python path?
    print(sys.path)

    return sc


def _prepare_dir(sc: attrdict.AttrDict, conf: config.Config) -> None:
    """writes all the helper files associated with slurm execution

    Args:
        sc (attrdict.AttrDict): enriched slurm configuration
        conf (config.Config): overall configuration object
    """
    os.makedirs(sc["experiment_log"], exist_ok=True)
    os.makedirs(sc["experiment_wd"], exist_ok=True)
    conf.to_yaml(sc["config_output"])

    src = os.getcwd()
    dst = sc["experiment_wd"]
    ign = shutil.ignore_patterns('*.pyc', 'tmp*')

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=ign)
        else:
            shutil.copy2(s, d)


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
        tline = tline.replace('%%project_name%%', sc['project_name'])
        tline = tline.replace('%%experiment_name%%',
                              sc['experiment_name'])
        tline = tline.replace('%%time_limit%%', '{:d}:{:d}:00'.format(sc['time_limit'] // 60,
                                                                      sc['time_limit'] % 60))

        #tline = tline.replace('%%experiment_root%%', sc['experiment_root'])
        tline = tline.replace('%%experiment_wd%%', sc['experiment_wd'])
        tline = tline.replace('%%experiment_log%%', sc['experiment_log'])
        tline = tline.replace('%%python_script%%', experiment_code)
        tline = tline.replace('%%exp_name%%', sc["experiment_selectors"])
        tline = tline.replace('%%path_to_yaml_config%%', conf.config_path)
        tline = tline.replace('%%num_jobs%%', '{:d}'.format(sc['num_jobs']))
        tline = tline.replace('%%num_parallel_jobs%%',
                              '{:d}'.format(sc['num_parallel_jobs']))
        tline = tline.replace('%%mem%%', '{:d}'.format(sc['mem']))
        tline = tline.replace('%%number_of_jobs%%',
                              '{:d}'.format(sc['number_of_jobs']))
        tline = tline.replace('%%number_of_cpu_per_job%%',
                              '{:d}'.format(sc['number_of_cpu_per_job']))

        fid_out.write(tline)

        tline = fid_in.readline()
    fid_in.close()
    fid_out.close()
    return output_path
