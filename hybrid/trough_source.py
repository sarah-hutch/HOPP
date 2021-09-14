from typing import Optional, Union, Sequence
import os

import PySAM.Singleowner as Singleowner

from hybrid.dispatch.power_sources.trough_dispatch import TroughDispatch

from hybrid.power_source import *
from hybrid.csp_source import CspPlant


class TroughPlant(CspPlant):
    _system_model: None
    _financial_model: Singleowner.Singleowner
    # _layout: TroughLayout
    _dispatch: TroughDispatch

    def __init__(self,
                 site: SiteInfo,
                 trough_config: dict):
        """

        :param trough_config: dict, with keys ('system_capacity_kw', 'solar_multiple', 'tes_hours')
        """
        financial_model = Singleowner.default('PhysicalTroughSingleOwner')

        # set-up param file paths
        # TODO: Site should have dispatch factors consistent across all models
        self.param_files = {'tech_model_params_path': 'tech_model_defaults.json',
                            'dispatch_factors_ts_path': 'dispatch_factors_ts.csv',
                            'ud_ind_od_path': 'ud_ind_od.csv',
                            'wlim_series_path': 'wlim_series.csv'}
        rel_path_to_param_files = os.path.join('pySSC_daotk', 'trough_data')
        self.param_file_paths(rel_path_to_param_files)

        super().__init__("TroughPlant", 'trough_physical', site, financial_model, trough_config)

        self._dispatch: TroughDispatch = None

    @property
    def solar_multiple(self) -> float:
        return self.ssc.get('specified_solar_multiple')

    @solar_multiple.setter
    def solar_multiple(self, solar_multiple: float):
        """
        Set the solar multiple and updates the system model. Solar multiple is defined as the the ratio of receiver
        design thermal power over power cycle design thermal power.
        :param solar_multiple:
        :return:
        """
        self.ssc.set({'specified_solar_multiple': solar_multiple})

    @property
    def cycle_thermal_rating(self) -> float:
        return self.value('P_ref') / self.value('eta_ref')

    @property
    def field_thermal_rating(self) -> float:
        # TODO: This doesn't work with specified field area option
        return self.value('specified_solar_multiple') * self.cycle_thermal_rating

    @property
    def cycle_nominal_efficiency(self) -> float:
        return self.value('eta_ref')
