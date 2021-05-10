# Loading Results
We provide a simple function to access the results from your runs. An example can be found in `polynom_tutorial\polynom_load.py`:

```Python
from cw2 import cluster_work, cw_logging

cw = cluster_work.ClusterWork(None)

# Add all the loggers whose results you want to load.
cw.add_logger(cw_logging.PandasRepSaver())
# ...


# res is a pandas.DataFrame
res = cw.load()
```

The resulting object is a `pandas.DataFrame` with each repetition as a row, and each configuration parameter and logger result as a column.
You can use all the available `pandas` methods to filter and do your own analysis of the results.

Additionally we offer our own processing functions with an extension of the `pandas` API: `df.cw2`
For example, to select a single repetition in the result dataframe `res` from the example above, use `df.cw2.repetition()`:

```Python
# ...
res = cw.load()
repetition_0 = res.cw2.repetition(0)
```

To select all runs with a specific hyper-parameter setting, use `df.cw2.filter()`:
```Python
# ...
res = cw.load()

# parameter dict - same structure as CONFIG.params
interesting_params = {
  'param1': 1
}

interesting_results = res.cw2.filter(
  interesting_params
)
```