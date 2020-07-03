import argparse
import attrdict


class Arguments():
    def __init__(self):
        p = argparse.ArgumentParser()
        p.add_argument('config', metavar='CONFIG.yml')
        p.add_argument('-j', '--job', type=int, default=None,
                       help='Run only the specified job. CAVEAT: Should only be used with slurm arrays.')

        # XXX: Disable delete for now
        # p.add_argument('-d', '--delete', action='store_true',
        #                help='CAUTION deletes results of previous runs.')
        
        p.add_argument('-e', '--experiments', nargs='+', default=None,
                        help='Allows to specify which experiments should be run.')
        p.add_argument('-s', '--slurm', action='store_true',
                        help='Run using SLURM Workload Manager.')
        p.add_argument('-o', '--overwrite', action='store_true',
                        help='Overwrite existing results.')

        self.args = p.parse_args(namespace=self)
    
    def get(self) -> dict:
        return attrdict.AttrDict(vars(self.args))