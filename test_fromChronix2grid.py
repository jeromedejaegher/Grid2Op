# Copyright (c) 2019-2020, RTE (https://www.rte-france.com)
# See AUTHORS.txt
# This Source Code Form is subject to the terms of the Mozilla Public License, version 2.0.
# If a copy of the Mozilla Public License, version 2.0 was not distributed with this file,
# you can obtain one at http://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0
# This file is part of Grid2Op, Grid2Op a testbed platform to model sequential decision making in power systems.

import warnings


import os
import grid2op
import numpy as np
from lightsim2grid import LightSimBackend
from grid2op.Chronics import FromChronix2grid
import pdb
import unittest

class TestFromChronix2Grid(unittest.TestCase):
    def _aux_reset_env(self):
        self.env.seed(self.seed_)
        self.env.set_id(self.scen_nm)
        return self.env.reset()
    
    def setUp(self) -> None:
        self.seed_ = 0
        self.env_nm = "wcci_2022_dev"
        self.env = grid2op.make(self.env_nm,
                                backend=LightSimBackend(),
                                chronics_class=FromChronix2grid,
                                data_feeding_kwargs={"env_path": os.path.join(grid2op.get_current_local_dir(), self.env_nm),
                                                     "with_maintenance": True,
                                                     "max_iter": 10,
                                                     "with_loss": False
                                                     }
                                )
    
    
    def test_ok(self):
        """test it can be created"""
        assert self.env.chronics_handler.real_data._gen_p.shape == (12, 62)
        assert np.all(np.isfinite(self.env.chronics_handler.real_data._gen_p))
        
    def test_seed_setid(self):
        """test env.seed(...) and env.set_id(...)"""
        id_ref = '2525122259@2050-02-28'
        # test tell_id
        sum_prod_ref = 41676.3552
        self.env.seed(self.seed_)
        self.env.reset()
        id_ = self.env.chronics_handler.get_id()
        assert id_ == id_ref, f"wrong id {id_} instead of {id_ref}"
        assert abs(self.env.chronics_handler.real_data._gen_p.sum() - sum_prod_ref) <= 1e-4
        self.env.reset()
        assert abs(self.env.chronics_handler.real_data._gen_p.sum() - 37991.1742) <= 1e-4
        self.env.set_id(id_ref)
        self.env.reset()
        assert abs(self.env.chronics_handler.real_data._gen_p.sum() - sum_prod_ref) <= 1e-4
        
        # test seed
        self.env.seed(self.seed_)
        self.env.reset()
        assert abs(self.env.chronics_handler.real_data._gen_p.sum() - sum_prod_ref) <= 1e-4
        
    def test_episode(self):
        """test that the episode can go until the end"""
        self.env.seed(0)
        obs = self.env.reset()
        assert obs.max_step == 10
        for i in range(obs.max_step - 2):
            obs, reward, done, info = self.env.step(self.env.action_space())
            assert not done
        obs, reward, done, info = self.env.step(self.env.action_space())
        assert done
        obs = self.env.reset()
        assert obs.max_step == 10
    
    def test_maintenance(self):
        self.env = grid2op.make(self.env_nm,
                                backend=LightSimBackend(),
                                chronics_class=FromChronix2grid,
                                data_feeding_kwargs={"env_path": os.path.join(grid2op.get_current_local_dir(), self.env_nm),
                                                     "with_maintenance": True,
                                                     "max_iter": 2 * 288,
                                                     "with_loss": False
                                                     }
                                )
        self.env.seed(0)
        id_ref = '0@2050-08-08'
        self.env.set_id(id_ref)
        obs = self.env.reset()
        assert np.all(obs.time_next_maintenance[[131]] == 107)
        assert np.all(obs.time_next_maintenance[:131] == -1)
        assert np.all(obs.time_next_maintenance[132:] == -1)
        assert self.env.chronics_handler.real_data.maintenance is not None
        assert self.env.chronics_handler.real_data.maintenance.sum() == 96
        assert self.env.chronics_handler.real_data.maintenance_time is not None
        assert self.env.chronics_handler.real_data.maintenance_duration is not None
if __name__ == "__main__":
    unittest.main()