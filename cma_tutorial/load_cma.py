import os

import cma
import dill
import numpy as np
from cma.bbobbenchmarks import nfreefunclasses

import cw2.cluster_work
import cw2.experiment
import cw2.cw_data.cw_pd_logger

class CWCMA(cw2.experiment.AbstractIterativeExperiment):
    def __init__(self):
        super().__init__()
        self.problem = None
        self.optimizer = None

    def initialize(self, config: dict, rep: int) -> None:
        dim = config.params.problem.dim
        x_start = config.params.optim_params.x_init * np.random.randn(dim)
        init_sigma = config.params.optim_params.init_sigma
        self.problem = nfreefunclasses[7](iinstance=rep)
        self.problem.initwithsize(curshape=(1, dim), dim=dim)
        self.optimizer = es = cma.CMAEvolutionStrategy(
            x0=x_start,
            sigma0=init_sigma,
            inopts={
                'popsize': config.params.optim_params.n_samples
            }
        )
        es.f_obj = self.problem

        def entropy(self):
            cov = self.sigma ** 2 * self.sm.covariance_matrix
            chol = np.linalg.cholesky(cov)
            ent = np.sum(np.log(np.diag(chol))) + \
                self.N / 2 * np.log(2 * np.pi) + self.N / 2
            return ent

        self.optimizer.entropy = entropy.__get__(
            self.optimizer, cma.CMAEvolutionStrategy)

        self.optimizer.adapt_sigma.initialize(self.optimizer)
        if config.params.optim_params.c_c is not None:
            self.optimizer.sp.cc = config.params.optim_params.c_c
        if config.params.optim_params.c_1 is not None:
            self.optimizer.sm._parameters['c1'] = config.params.optim_params.c_1
        if config.params.optim_params.c_mu is not None:
            self.optimizer.sm._parameters['cmu'] = config.params.optim_params.c_mu
        if config.params.optim_params.d_sigma is not None:
            self.optimizer.adapt_sigma.damps = config.params.optim_params.d_sigma
        if config.params.optim_params.c_sigma is not None:
            config.adapt_sigma.cs = config.params.optim_params.c_sigma

    def iterate(self, config: dict, rep: int, n: int) -> dict:
        # do one iteration of cma es
        solutions = self.optimizer.ask()
        f = self.problem(solutions)
        self.optimizer.tell(solutions, f)

        # collect some results from this iteration
        mean_opt = np.mean(self.optimizer.fit.fit) - self.problem.getfopt()
        median_opt = np.median(self.optimizer.fit.fit) - self.problem.getfopt()

        f0_at_mean = float(self.problem(
            self.optimizer.mean.flatten()) - self.problem.getfopt())

        results_dict = {"f_id": self.problem.funId,
                        "current_opt": f0_at_mean,
                        "mean_opt": mean_opt,
                        "median_opt": median_opt,
                        "entropy": self.optimizer.entropy(),
                        "total_samples": (n + 1) * config.params.optim_params.n_samples
                        }

        return results_dict

    def save_state(self, config: dict, rep: int, n: int) -> None:
        if n % 50 == 0:
            f_name = os.path.join(
                config.rep_log_paths[rep], 'optimizer.pkl')
            with open(f_name, 'wb') as f:
                dill.dump(self.optimizer, f)

    def finalize(self):
        pass

    def restore_state(self):
        pass


if __name__ == "__main__":
    cw = cw2.cluster_work.ClusterWork(CWCMA)
    cw.add_logger(cw2.cw_data.cw_pd_logger.PandasLogger())
    d = cw.load()
    print(d)
