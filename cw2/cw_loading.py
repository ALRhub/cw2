from copy import deepcopy
from typing import List

import pandas as pd

from cw2 import job, scheduler


class Loader(scheduler.AbstractScheduler):
    def run(self, overwrite: bool = False):
        all_data = []         

        for j in self.joblist:
            all_data += self._load_job(j)

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
