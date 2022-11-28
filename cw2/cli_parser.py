import argparse


class Arguments:
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
        p.add_argument('--nocodecopy', action='store_true', help='Skip code copy.')
        p.add_argument('--zip', action='store_true', help='Make a Zip Copy of the Code.')
        p.add_argument('--skipsizecheck', action='store_true', help='Skip check if code copy src < 200MByte')
        p.add_argument('--multicopy', action='store_true', help='Create a code copy for each job seperately')
        p.add_argument('--noconsolelog', action='store_true', help='Disables writing internal console log files')
        p.add_argument('--debug', action='store_true', default=False, help='Enable debug mode.')
        p.add_argument('--debugall', action='store_true', default=False, help='Enable debug mode for arguments.')

        self.args = p.parse_args(namespace=self)

    def get(self) -> dict:
        return vars(self.args)
