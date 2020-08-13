from copy import deepcopy
from typing import List

import pandas as pd

from cw2 import job, scheduler, util


class Loader(scheduler.AbstractScheduler):
    def run(self, overwrite: bool = False):
        all_data = CWResult()

        for j in self.joblist:
            all_data.load_job(j)

        return all_data

    def _load_job(self, j: job.Job) -> List[dict]:
        job_config = deepcopy(j.config)
        job_dict = {k: job_config[k] for k in ['name', 'params']}

        job_data = []

        for r in j.repetitions:
            rep_data = j.load_rep(r)
            rep_data.update({'r': r, 'rep_path': j.get_rep_path(r)})
            rep_data.update(job_dict)
            job_data.append(rep_data)
        return job_data

#TODO: Use https://pandas.pydata.org/pandas-docs/stable/development/extending.html isntead?
class CWResult():
    def __init__(self):
        self.data_list = []
        self.df = None

    def load_job(self, j: job.Job) -> None:
        job_config = deepcopy(j.config)
        job_dict = {}
        job_dict['name'] = job_config['name']

        job_dict.update(util.flatten_dict(job_config['params']))

        
        for r in j.repetitions:
            rep_data = j.load_rep(r)
            rep_data.update({'r': r, 'rep_path': j.get_rep_path(r)})
            rep_data.update(job_dict)
            self.data_list.append(rep_data)
        
    def get_data(self):
        if self.df is None:
            self.df = pd.DataFrame(self.data_list)
        return self.df

    def filter(self, param: 'str', value):
        return self.df[self.df[param] == value]