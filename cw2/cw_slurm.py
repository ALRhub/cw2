import os
import sys

import attrdict

import __main__
from cw2 import cli_parser, config

DEFAULT_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "slurm_template.txt")
DEFAULT_OUTPUT = "./sbatch.sh"


def finalize_slurm_config(configuration: config.Config) -> attrdict:
    slurm_config = configuration.slurm_config

    # numjobs is last job index, counting starts at 0
    slurm_config['num_jobs'] = configuration.total_num_reps() - 1

    if "experiment_cwd" not in slurm_config:
        slurm_config["experiment_cwd"] = os.getcwd()

    if "experiment_log" not in slurm_config:
        slurm_config["experiment_log"] = os.path.join(slurm_config["experiment_cwd"], 'log')
    os.makedirs(slurm_config["experiment_log"], exist_ok=True)

    # TODO: Automatically fill in python path?
    print(sys.path)

    return slurm_config


def create_slurm_skript(configuration: config.Config, template_path: str = DEFAULT_TEMPLATE, output_path: str = DEFAULT_OUTPUT):
    fid_in = open(template_path, 'r')
    fid_out = open(output_path, 'w')

    tline = fid_in.readline()

    cw_options = cli_parser.Arguments().get()
    experiment_selectors = "" if cw_options.experiments is None else "-e " + \
        " ".join(cw_options.experiments)

    slurm_config = finalize_slurm_config(configuration)

    experiment_code = __main__.__file__

    while tline:
        tline = tline.replace('%%project_name%%', slurm_config['project_name'])
        tline = tline.replace('%%experiment_name%%',
                              slurm_config['experiment_name'])
        tline = tline.replace('%%time_limit%%', '{:d}:{:d}:00'.format(slurm_config['time_limit'] // 60,
                                                                      slurm_config['time_limit'] % 60))

        tline = tline.replace('%%experiment_root%%',
                              slurm_config['experiment_root'])
        tline = tline.replace('%%experiment_cwd%%',
                              slurm_config['experiment_cwd'])
        tline = tline.replace('%%experiment_log%%',
                              slurm_config['experiment_log'])
        tline = tline.replace('%%python_script%%', experiment_code)
        tline = tline.replace('%%exp_name%%', experiment_selectors)
        tline = tline.replace('%%path_to_yaml_config%%', configuration.config_path)
        tline = tline.replace(
            '%%num_jobs%%', '{:d}'.format(slurm_config['num_jobs']))
        tline = tline.replace('%%num_parallel_jobs%%', '{:d}'.format(
            slurm_config['num_parallel_jobs']))
        tline = tline.replace('%%mem%%', '{:d}'.format(slurm_config['mem']))
        tline = tline.replace('%%number_of_jobs%%', '{:d}'.format(
            slurm_config['number_of_jobs']))
        tline = tline.replace('%%number_of_cpu_per_job%%', '{:d}'.format(
            slurm_config['number_of_cpu_per_job']))

        fid_out.write(tline)

        tline = fid_in.readline()
    fid_in.close()
    fid_out.close()
    return output_path
