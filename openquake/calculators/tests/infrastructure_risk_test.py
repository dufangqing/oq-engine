# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import numpy
from openquake.qa_tests_data.scenario_damage import case_15
from openquake.qa_tests_data.infrastructure_risk import (
    five_nodes_demsup_directed, five_nodes_demsup_directedunweighted,
    five_nodes_demsup_multidirected, demand_supply, directed, eff_loss_random,
    multidirected, multigraph, undirected)
from openquake.calculators.export import export
from openquake.calculators.tests import CalculatorTestCase

aac = numpy.testing.assert_allclose


class ScenarioDamageTestCase(CalculatorTestCase):

    def test_case_15(self):
        self.run_calc(case_15.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_ccl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_ccl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-dem_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-dem_cl.csv', fname, check_all_columns=True)

    def test_demand_supply(self):
        self.run_calc(demand_supply.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_ccl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_ccl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-dem_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-dem_cl.csv', fname, check_all_columns=True)

    def test_directed(self):
        self.run_calc(directed.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-taz_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-taz_cl.csv', fname, check_all_columns=True)

    def test_eff_loss_random(self):
        self.run_calc(eff_loss_random.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

    def test_five_nodes_demsup_directed(self):
        self.run_calc(five_nodes_demsup_directed.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_ccl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_ccl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-dem_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-dem_cl.csv', fname, check_all_columns=True)

    def test_five_nodes_demsup_directedunweighted(self):
        self.run_calc(five_nodes_demsup_directedunweighted.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_ccl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_ccl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-dem_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-dem_cl.csv', fname, check_all_columns=True)

    def test_five_nodes_demsup_multidirected(self):
        self.run_calc(five_nodes_demsup_multidirected.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_ccl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_ccl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-dem_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-dem_cl.csv', fname, check_all_columns=True)

    def test_multidirected(self):
        self.run_calc(multidirected.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-taz_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-taz_cl.csv', fname, check_all_columns=True)

    def test_multigraph(self):
        self.run_calc(multigraph.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-taz_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-taz_cl.csv', fname, check_all_columns=True)

    def test_undirected(self):
        self.run_calc(undirected.__file__, 'job.ini')
        ds = self.calc.datastore

        [fname] = export(('infra-avg_loss', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-avg_loss.csv', fname, check_all_columns=True)

        [fname] = export(('infra-event_efl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_efl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_pcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_pcl.csv', fname, check_all_columns=True)
        [fname] = export(('infra-event_wcl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-event_wcl.csv', fname, check_all_columns=True)

        [fname] = export(('infra-node_el', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-node_el.csv', fname, check_all_columns=True)

        [fname] = export(('infra-taz_cl', 'csv'), ds)
        self.assertEqualFiles(
            'expected/infra-taz_cl.csv', fname, check_all_columns=True)
