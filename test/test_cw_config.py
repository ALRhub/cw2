import unittest
from typing import Dict
from unittest import main

from cw2.cw_config import conf_unfolder, cw_config


class TestParamsExpansion(unittest.TestCase):
    def setUp(self) -> None:
        self.conf_obj = cw_config.Config()

    def expand_dict(self, _d: dict) -> list:
        d = _d.copy()
        expands = conf_unfolder.expand_experiments([d], False, False)
        return [self.remove_non_param_keys(e) for e in expands]

    def create_minimal_dict(self) -> dict:
        return {"name": "exp", "path": "test", "_debug": False}

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
        params_dict["params"] = {"a": 1, "b": [2, 3], "c": {"c_1": "a", "c_2": "b"}}

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

        g["grid"]["c"] = {"c1": ["c1"], "c2": ["c2a", "c2b"]}
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

        g["list"]["c"] = {"c1": ["c1"], "c2": ["c2a, c2b"]}
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

        g["grid"]["cd"] = {"c1": ["c1"], "c2": ["c2a", "c2b"]}
        res = self.expand_dict(g)
        self.assertEqual(8, len(res))

        g["list"]["cl"] = {"c1": ["c1"], "c2": ["c2a, c2b"]}
        res = self.expand_dict(g)
        self.assertEqual(4, len(res))

    def test_multi_listt(self):
        g = self.create_minimal_dict()
        g["list1"] = {
            "a": [1],
            "b": [2],
        }
        g["list--2"] = {
            "c": [1],
            "d": [2],
        }
        res = self.expand_dict(g)
        self.assertEqual(1, len(res))

        g["list1"]["a"] = [3, 4]
        g["list1"]["b"] = [11, 12, 13]
        res = self.expand_dict(g)
        self.assertEqual(2, len(res))

        g["list--2"]["c"] = [3, 4]
        g["list--2"]["d"] = [3, 4]
        res = self.expand_dict(g)
        self.assertEqual(4, len(res))

        g["list1"]["a"] = [11, 12, 13]
        g["list1"]["b"] = [11, 12, 13]
        g["list--2"]["c"] = [11, 12, 13]
        g["list--2"]["d"] = [11, 12, 13]
        res = self.expand_dict(g)
        self.assertEqual(9, len(res))

    def test_ablation(self):
        g = self.create_minimal_dict()
        g["list1"] = {
            "a": [1],
            "b": [2],
        }
        g["ablative"] = {
            "c": [3],
        }
        res = self.expand_dict(g)
        self.assertEqual(1, len(res))

        g["ablative"] = {
            "c": [3, 4],
        }
        res = self.expand_dict(g)
        self.assertEqual(2, len(res))

        g["ablative"] = {"c": [3], "d": [4]}
        res = self.expand_dict(g)
        self.assertEqual(2, len(res))

        g["ablative"] = {"c": [3], "d": [4, 5]}
        g["list1"] = {
            "a": [1, 2],
            "b": [2, 3],
        }
        res = self.expand_dict(g)
        self.assertEqual(6, len(res))


if __name__ == "__main__":
    unittest.main()
