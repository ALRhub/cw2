from typing import Dict
import unittest
from unittest import main

from cw2 import cw_config


class TestParamsExpansion(unittest.TestCase):
    def setUp(self) -> None:
        self.conf_obj = cw_config.Config()
    
    def expand_dict(self, _d: dict) -> list:
        d = _d.copy()
        expands = self.conf_obj._expand_experiments([d])
        return [self.remove_non_param_keys(e) for e in expands]

    def create_minimal_dict(self) -> dict:
        return {
            "name": "exp",
            "path": "test"
        }

    def remove_non_param_keys(self, _d: dict) -> dict:
        d = _d.copy()
        d["path"] = d["_basic_path"]
        del d["_basic_path"]
        del d["_experiment_name"]
        del d["_nested_dir"]
        del d["log_path"]
        return d

    def test_no_expansion(self):
        no_params = self.create_minimal_dict()

        res = self.expand_dict(no_params)
        self.assertEqual(1, len(res))
        self.assertDictEqual(no_params, res[0])


        params_dict = self.create_minimal_dict()
        params_dict["params"] = {
            "a": 1,
            "b": [2, 3],
            "c": {
                "c_1": "a",
                "c_2": "b"
            }
        }

        res = self.expand_dict(params_dict)
        self.assertEqual(1, len(res))
        self.assertDictEqual(params_dict, res[0])

    def test_grid_exp(self):
        g = self.create_minimal_dict()
        g["grid"] = {
            "a": [1],
            "b": [2],
        }

        res = self.expand_dict(g)
        self.assertEqual(1, len(res))

        g["grid"]["a"] = [3, 4]
        res = self.expand_dict(g)
        self.assertEqual(2, len(res))

        g["grid"]["b"] = [11, 12, 13]
        res = self.expand_dict(g)
        self.assertEqual(6, len(res))

        g["grid"]["c"] = {
            "c1": ["c1"],
            "c2": ["c2a", "c2b"]
        }
        res = self.expand_dict(g)
        self.assertEqual(12, len(res))

    def test_list_exp(self):
        g = self.create_minimal_dict()
        g["list"] = {
            "a": [1],
            "b": [2],
        }

        res = self.expand_dict(g)
        self.assertEqual(1, len(res))

        g["list"]["a"] = [3, 4]
        res = self.expand_dict(g)
        self.assertEqual(1, len(res))

        g["list"]["b"] = [11, 12, 13]
        res = self.expand_dict(g)
        self.assertEqual(2, len(res))

        g["list"]["c"] = {
            "c1": ["c1"],
            "c2": ["c2a, c2b"]
        }
        res = self.expand_dict(g)
        self.assertEqual(1, len(res))

    def test_grid_and_list(self):
        g = self.create_minimal_dict()
        g["list"] = {
            "a": [1],
            "b": [2],
        }
        g["grid"] = {
            "c": [1],
            "d": [2],
        }
        res = self.expand_dict(g)
        self.assertEqual(1, len(res))

        g["list"]["a"] = [3, 4]
        g["list"]["b"] = [11, 12, 13]
        res = self.expand_dict(g)
        self.assertEqual(2, len(res))

        g["grid"]["c"] = [3, 4]
        res = self.expand_dict(g)
        self.assertEqual(4, len(res))

        g["grid"]["cd"] = {
            "c1": ["c1"],
            "c2": ["c2a", "c2b"]
        }
        res = self.expand_dict(g)
        self.assertEqual(8, len(res))

        g["list"]["cl"] = {
            "c1": ["c1"],
            "c2": ["c2a, c2b"]
        }
        res = self.expand_dict(g)
        self.assertEqual(4, len(res))




if __name__ == "__main__":
    unittest.main()
