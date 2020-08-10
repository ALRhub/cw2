from cw2 import scheduler

class Loader(scheduler.AbstractScheduler):
    def run(self, job_idx=None, overwrite: bool = False):
        all_data = {}
        
        joblist = self.joblist

        if job_idx is not None:
            joblist = [self.joblist[job_idx]]

        for j in joblist:
            all_data = {}
            for r in j.repetitions:
                rep_data = j.load_rep(r)
                all_data.update(rep_data)

        return all_data