import pyomo.environ as pyomo
from pyomo.network import Port
from pyomo.environ import units as u
from typing import Union
import datetime
import numpy as np

from hybrid.dispatch.dispatch import Dispatch


class CspDispatch(Dispatch):
    """
    Dispatch model for Concentrating Solar Power (CSP) with thermal energy storage.
    """

    def __init__(self,
                 pyomo_model: pyomo.ConcreteModel,
                 index_set: pyomo.Set,
                 system_model,
                 financial_model,
                 block_set_name: str = 'csp'):

        super().__init__(pyomo_model, index_set, system_model, financial_model, block_set_name=block_set_name)
        self._create_linking_constraints()

    def dispatch_block_rule(self, csp):
        """
        Called during Dispatch's __init__
        """
        # Parameters
        self._create_storage_parameters(csp)
        self._create_receiver_parameters(csp)
        self._create_cycle_parameters(csp)
        # Variables
        self._create_storage_variables(csp)
        self._create_receiver_variables(csp)
        self._create_cycle_variables(csp)
        # Constraints
        self._create_storage_constraints(csp)
        self._create_receiver_constraints(csp)
        self._create_cycle_constraints(csp)
        # Ports
        self._create_csp_port(csp)

    ##################################
    # Parameters                     #
    ##################################
    # TODO: Commenting out all of the parameters currently not be used.

    @staticmethod
    def _create_storage_parameters(csp):
        csp.time_duration = pyomo.Param(
            doc="Time step [hour]",
            default=1.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.hr)
        csp.storage_capacity = pyomo.Param(
            doc="Thermal energy storage capacity [MWht]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MWh)

    @staticmethod
    def _create_receiver_parameters(csp):
        # Cost Parameters
        csp.cost_per_field_generation = pyomo.Param(
            doc="Generation cost for the csp field [$/MWht]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.USD / u.MWh)
        csp.cost_per_field_start = pyomo.Param(
            doc="Penalty for field start-up [$/start]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.USD)  # $/start
        # Performance Parameters
        csp.available_thermal_generation = pyomo.Param(
            doc="Available solar thermal generation from the csp field [MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MW)
        csp.field_startup_losses = pyomo.Param(
            doc="Solar field startup or shutdown parasitic loss [MWhe]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MWh)
        csp.receiver_required_startup_energy = pyomo.Param(
            doc="Required energy expended to start receiver [MWht]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MWh)
        csp.receiver_pumping_losses = pyomo.Param(
            doc="Solar field and/or receiver pumping power per unit power produced [MWe/MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.dimensionless)
        csp.minimum_receiver_power = pyomo.Param(
            doc="Minimum operational thermal power delivered by receiver [MWt]",
            default=1.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MW)
        csp.allowable_receiver_startup_power = pyomo.Param(
            doc="Allowable power per period for receiver start-up [MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MW)
        csp.field_track_losses = pyomo.Param(
            doc="Solar field tracking parasitic loss [MWe]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MW)
        # csp.heat_trace_losses = pyomo.Param(
        #     doc="Piping heat trace parasitic loss [MWe]",
        #     default=0.0,
        #     within=pyomo.NonNegativeReals,
        #     mutable=True,
        #     units=u.MW)

    @staticmethod
    def _create_cycle_parameters(csp):
        # Cost parameters
        csp.cost_per_cycle_generation = pyomo.Param(
            doc="Generation cost for power cycle [$/MWh]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.USD / u.MWh)  # Electric
        csp.cost_per_cycle_start = pyomo.Param(
            doc="Penalty for power cycle start [$/start]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.USD)  # $/start
        csp.cost_per_change_thermal_input = pyomo.Param(
            doc="Penalty for change in power cycle thermal input [$/MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.USD / u.MW)  # $/(Delta)MW (thermal)
        # Performance parameters
        csp.cycle_ambient_efficiency_correction = pyomo.Param(
            doc="Cycle efficiency ambient temperature adjustment [-]",
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.dimensionless)
        csp.condenser_losses = pyomo.Param(
            doc="Normalized condenser parasitic losses [-]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.dimensionless)
        csp.cycle_required_startup_energy = pyomo.Param(
            doc="Required energy expended to start cycle [MWht]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MWh)
        csp.cycle_nominal_efficiency = pyomo.Param(
            doc="Power cycle nominal efficiency [-]",
            default=0.0,
            within=pyomo.PercentFraction,
            mutable=True,
            units=u.dimensionless)
        csp.cycle_performance_slope = pyomo.Param(
            doc="Slope of linear approximation of power cycle performance curve [MWe/MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.dimensionless)
        csp.cycle_pumping_losses = pyomo.Param(
            doc="Cycle heat transfer fluid pumping power per unit energy expended [MWe/MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.dimensionless)
        csp.allowable_cycle_startup_power = pyomo.Param(
            doc="Allowable power per period for cycle start-up [MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MW)
        csp.minimum_cycle_thermal_power = pyomo.Param(
            doc="Minimum operational thermal power delivered to the power cycle [MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MW)
        csp.maximum_cycle_thermal_power = pyomo.Param(
            doc="Maximum operational thermal power delivered to the power cycle [MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MW)
        # csp.minimum_cycle_power = pyomo.Param(
        #     doc="Minimum cycle electric power output [MWe]",
        #     default=0.0,
        #     within=pyomo.NonNegativeReals,
        #     mutable=True,
        #     units=u.MW)
        csp.maximum_cycle_power = pyomo.Param(
            doc="Maximum cycle electric power output [MWe]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MW)

    ##################################
    # Variables                      #
    ##################################

    @staticmethod
    def _create_storage_variables(csp):
        csp.thermal_energy_storage = pyomo.Var(
            doc="Thermal energy storage reserve quantity [MWht]",
            domain=pyomo.NonNegativeReals,
            bounds=(0, csp.storage_capacity),
            units=u.MWh)
        # initial variables
        csp.previous_thermal_energy_storage = pyomo.Var(
            doc="Thermal energy storage reserve quantity at the beginning of the period [MWht]",
            domain=pyomo.NonNegativeReals,
            bounds=(0, csp.storage_capacity),
            units=u.MWh)

    @staticmethod
    def _create_receiver_variables(csp):
        csp.receiver_startup_inventory = pyomo.Var(
            doc="Receiver start-up energy inventory [MWht]",
            domain=pyomo.NonNegativeReals,
            units=u.MWh)
        csp.receiver_thermal_power = pyomo.Var(
            doc="Thermal power delivered by the receiver [MWt]",
            domain=pyomo.NonNegativeReals,
            units=u.MW)
        csp.receiver_startup_consumption = pyomo.Var(
            doc="Receiver start-up power consumption [MWt]",
            domain=pyomo.NonNegativeReals,
            units=u.MW)
        csp.is_field_generating = pyomo.Var(
            doc="1 if solar field is generating 'usable' thermal power; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)
        csp.is_field_starting = pyomo.Var(
            doc="1 if solar field is starting up; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)
        csp.incur_field_start = pyomo.Var(
            doc="1 if solar field start-up penalty is incurred; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)
        # initial variables
        csp.previous_receiver_startup_inventory = pyomo.Var(
            doc="Previous receiver start-up energy inventory [MWht]",
            domain=pyomo.NonNegativeReals,
            units=u.MWh)
        csp.was_field_generating = pyomo.Var(
            doc="1 if solar field was generating 'usable' thermal power in the previous time period; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)
        csp.was_field_starting = pyomo.Var(
            doc="1 if solar field was starting up in the previous time period; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)

    @staticmethod
    def _create_cycle_variables(csp):
        csp.system_load = pyomo.Var(
            doc="Load of csp system [MWe]",
            domain=pyomo.NonNegativeReals,
            units=u.MW)
        csp.cycle_startup_inventory = pyomo.Var(
            doc="Cycle start-up energy inventory [MWht]",
            domain=pyomo.NonNegativeReals,
            units=u.MWh)
        csp.cycle_generation = pyomo.Var(
            doc="Power cycle electricity generation [MWe]",
            domain=pyomo.NonNegativeReals,
            units=u.MW)
        csp.cycle_thermal_ramp = pyomo.Var(
            doc="Power cycle positive change in thermal energy input [MWt]",
            domain=pyomo.NonNegativeReals,
            bounds=(0, csp.maximum_cycle_thermal_power),
            units=u.MW)
        csp.cycle_thermal_power = pyomo.Var(
            doc="Cycle thermal power utilization [MWt]",
            domain=pyomo.NonNegativeReals,
            bounds=(0, csp.maximum_cycle_thermal_power),
            units=u.MW)
        csp.is_cycle_generating = pyomo.Var(
            doc="1 if cycle is generating electric power; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)
        csp.is_cycle_starting = pyomo.Var(
            doc="1 if cycle is starting up; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)
        csp.incur_cycle_start = pyomo.Var(
            doc="1 if cycle start-up penalty is incurred; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)
        # Initial variables
        csp.previous_cycle_startup_inventory = pyomo.Var(
            doc="Previous cycle start-up energy inventory [MWht]",
            domain=pyomo.NonNegativeReals,
            units=u.MWh)
        csp.previous_cycle_thermal_power = pyomo.Var(
            doc="Cycle thermal power in the previous period [MWt]",
            domain=pyomo.NonNegativeReals,
            bounds=(0, csp.maximum_cycle_thermal_power),
            units=u.MW)
        csp.was_cycle_generating = pyomo.Var(
            doc="1 if cycle was generating electric power in previous time period; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)
        csp.was_cycle_starting = pyomo.Var(
            doc="1 if cycle was starting up in previous time period; 0 Otherwise [-]",
            domain=pyomo.Binary,
            units=u.dimensionless)

    ##################################
    # Constraints                    #
    ##################################

    @staticmethod
    def _create_storage_constraints(csp):
        csp.storage_inventory = pyomo.Constraint(
            doc="Thermal energy storage energy balance",
            expr=(csp.thermal_energy_storage - csp.previous_thermal_energy_storage ==
                  csp.time_duration * (csp.receiver_thermal_power
                                       - (csp.allowable_cycle_startup_power * csp.is_cycle_starting
                                          + csp.cycle_thermal_power)
                                       )
                  ))

    @staticmethod
    def _create_receiver_constraints(csp):
        # Start-up
        csp.receiver_startup_inventory_balance = pyomo.Constraint(
            doc="Receiver startup energy inventory balance",
            expr=csp.receiver_startup_inventory <= (csp.previous_receiver_startup_inventory
                                                    + csp.time_duration * csp.receiver_startup_consumption))
        csp.receiver_startup_inventory_reset = pyomo.Constraint(
            doc="Resets receiver and/or field startup inventory when startup is completed",
            expr=csp.receiver_startup_inventory <= csp.receiver_required_startup_energy * csp.is_field_starting)
        csp.receiver_operation_startup = pyomo.Constraint(
            doc="Thermal production is allowed only upon completion of start-up or operating in previous time period",
            expr=csp.is_field_generating <= (csp.receiver_startup_inventory
                                             / csp.receiver_required_startup_energy) + csp.was_field_generating)
        csp.receiver_startup_delay = pyomo.Constraint(
            doc="If field previously was producing, it cannot startup this period",
            expr=csp.is_field_starting + csp.was_field_generating <= 1)
        csp.receiver_startup_limit = pyomo.Constraint(
            doc="Receiver and/or field startup energy consumption limit",
            expr=csp.receiver_startup_consumption <= (csp.allowable_receiver_startup_power
                                                      * csp.is_field_starting))
        csp.receiver_startup_cut = pyomo.Constraint(
            doc="Receiver and/or field trivial resource startup cut",
            expr=csp.is_field_starting <= csp.available_thermal_generation / csp.minimum_receiver_power)
        # Supply and demand
        csp.receiver_energy_balance = pyomo.Constraint(
            doc="Receiver generation and startup usage must be below available",
            expr=csp.available_thermal_generation >= csp.receiver_thermal_power + csp.receiver_startup_consumption)
        csp.maximum_field_generation = pyomo.Constraint(
            doc="Receiver maximum generation limit",
            expr=csp.receiver_thermal_power <= csp.available_thermal_generation * csp.is_field_generating)
        csp.minimum_field_generation = pyomo.Constraint(
            doc="Receiver minimum generation limit",
            expr=csp.receiver_thermal_power >= csp.minimum_receiver_power * csp.is_field_generating)
        csp.receiver_generation_cut = pyomo.Constraint(
            doc="Receiver and/or field trivial resource generation cut",
            expr=csp.is_field_generating <= csp.available_thermal_generation / csp.minimum_receiver_power)
        # Logic associated with receiver modes
        csp.field_startup = pyomo.Constraint(
            doc="Ensures that field start is accounted",
            expr=csp.incur_field_start >= csp.is_field_starting - csp.was_field_starting)

    @staticmethod
    def _create_cycle_constraints(csp):
        # Start-up
        csp.cycle_startup_inventory_balance = pyomo.Constraint(
            doc="Cycle startup energy inventory balance",
            expr=csp.cycle_startup_inventory <= (csp.previous_cycle_startup_inventory
                                                 + (csp.time_duration
                                                    * csp.allowable_cycle_startup_power
                                                    * csp.is_cycle_starting)))
        csp.cycle_startup_inventory_reset = pyomo.Constraint(
            doc="Resets power cycle startup inventory when startup is completed",
            expr=csp.cycle_startup_inventory <= csp.cycle_required_startup_energy * csp.is_cycle_starting)
        csp.cycle_operation_startup = pyomo.Constraint(
            doc="Electric production is allowed only upon completion of start-up or operating in previous time period",
            expr=csp.is_cycle_generating <= (csp.cycle_startup_inventory
                                             / csp.cycle_required_startup_energy) + csp.was_cycle_generating)
        csp.cycle_startup_delay = pyomo.Constraint(
            doc="If cycle previously was generating, it cannot startup this period",
            expr=csp.is_cycle_starting + csp.was_cycle_generating <= 1)
        # Supply and demand
        csp.maximum_cycle_thermal_consumption = pyomo.Constraint(
            doc="Power cycle maximum thermal energy consumption maximum limit",
            expr=csp.cycle_thermal_power <= csp.maximum_cycle_thermal_power * csp.is_cycle_generating)
        csp.minimum_cycle_thermal_consumption = pyomo.Constraint(
            doc="Power cycle minimum thermal energy consumption minimum limit",
            expr=csp.cycle_thermal_power >= csp.minimum_cycle_thermal_power * csp.is_cycle_generating)
        csp.cycle_performance_curve = pyomo.Constraint(
            doc="Power cycle relationship between electrical power and thermal input with corrections "
                "for ambient temperature",
            expr=(csp.cycle_generation ==
                  (csp.cycle_ambient_efficiency_correction / csp.cycle_nominal_efficiency)
                  * (csp.cycle_performance_slope * csp.cycle_thermal_power
                     + (csp.maximum_cycle_power - csp.cycle_performance_slope
                        * csp.maximum_cycle_thermal_power) * csp.is_cycle_generating)))
        csp.cycle_thermal_ramp_constraint = pyomo.Constraint(
            doc="Positive ramping of power cycle thermal power",
            expr=csp.cycle_thermal_ramp >= csp.cycle_thermal_power - csp.previous_cycle_thermal_power)
        # Logic governing cycle modes
        csp.cycle_startup = pyomo.Constraint(
            doc="Ensures that cycle start is accounted",
            expr=csp.incur_cycle_start >= csp.is_cycle_starting - csp.was_cycle_starting)
        # System load
        csp.generation_balance = pyomo.Constraint(
            doc="Calculates csp system load for grid model",
            expr=csp.system_load == (csp.cycle_generation * csp.condenser_losses
                                     + csp.receiver_pumping_losses * (csp.receiver_thermal_power
                                                                      + csp.receiver_startup_consumption)
                                     + csp.cycle_pumping_losses * (csp.cycle_thermal_power
                                                                   + (csp.allowable_cycle_startup_power
                                                                      * csp.is_cycle_starting))
                                     + csp.field_track_losses * csp.is_field_generating
                                     # + csp.heat_trace_losses * csp.is_field_starting
                                     + (csp.field_startup_losses/csp.time_duration) * csp.is_field_starting))

    ##################################
    # Ports                          #
    ##################################

    @staticmethod
    def _create_csp_port(csp):
        csp.port = Port()
        csp.port.add(csp.cycle_generation)
        csp.port.add(csp.system_load)

    ##################################
    # Linking Constraints            #
    ##################################

    def _create_linking_constraints(self):
        self._create_storage_linking_constraints()
        self._create_receiver_linking_constraints()
        self._create_cycle_linking_constraints()

    ##################################
    # Initial Parameters             #
    ##################################

    def _create_storage_linking_constraints(self):
        self.model.initial_thermal_energy_storage = pyomo.Param(
            doc="Initial thermal energy storage reserve quantity at beginning of the horizon [MWht]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            # validate= # TODO: Might be worth looking into
            mutable=True,
            units=u.MWh)

        def tes_linking_rule(m, t):
            if t == self.blocks.index_set().first():
                return self.blocks[t].previous_thermal_energy_storage == self.model.initial_thermal_energy_storage
            return self.blocks[t].previous_thermal_energy_storage == self.blocks[t - 1].thermal_energy_storage
        self.model.tes_linking = pyomo.Constraint(
            self.blocks.index_set(),
            doc="Thermal energy storage block linking constraint",
            rule=tes_linking_rule)

    def _create_receiver_linking_constraints(self):
        self.model.initial_receiver_startup_inventory = pyomo.Param(
            doc="Initial receiver start-up energy inventory at beginning of the horizon [MWht]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MWh)
        self.model.is_field_generating_initial = pyomo.Param(
            doc="1 if solar field is generating 'usable' thermal power at beginning of the horizon; 0 Otherwise [-]",
            default=0.0,
            within=pyomo.Binary,
            mutable=True,
            units=u.dimensionless)
        self.model.is_field_starting_initial = pyomo.Param(
            doc="1 if solar field is starting up at beginning of the horizon; 0 Otherwise [-]",
            default=0.0,
            within=pyomo.Binary,
            mutable=True,
            units=u.dimensionless)

        def receiver_startup_inventory_linking_rule(m, t):
            if t == self.blocks.index_set().first():
                return self.blocks[t].previous_receiver_startup_inventory == self.model.initial_receiver_startup_inventory
            return self.blocks[t].previous_receiver_startup_inventory == self.blocks[t - 1].receiver_startup_inventory
        self.model.receiver_startup_inventory_linking = pyomo.Constraint(
            self.blocks.index_set(),
            doc="Receiver startup inventory block linking constraint",
            rule=receiver_startup_inventory_linking_rule)

        def field_generating_linking_rule(m, t):
            if t == self.blocks.index_set().first():
                return self.blocks[t].was_field_generating == self.model.is_field_generating_initial
            return self.blocks[t].was_field_generating == self.blocks[t - 1].is_field_generating
        self.model.field_generating_linking = pyomo.Constraint(
            self.blocks.index_set(),
            doc="Is field generating binary block linking constraint",
            rule=field_generating_linking_rule)

        def field_starting_linking_rule(m, t):
            if t == self.blocks.index_set().first():
                return self.blocks[t].was_field_starting == self.model.is_field_starting_initial
            return self.blocks[t].was_field_starting == self.blocks[t - 1].is_field_starting
        self.model.field_starting_linking = pyomo.Constraint(
            self.blocks.index_set(),
            doc="Is field starting up binary block linking constraint",
            rule=field_starting_linking_rule)

    def _create_cycle_linking_constraints(self):
        self.model.initial_cycle_startup_inventory = pyomo.Param(
            doc="Initial cycle start-up energy inventory at beginning of the horizon [MWht]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            mutable=True,
            units=u.MWh)
        self.model.initial_cycle_thermal_power = pyomo.Param(
            doc="Initial cycle thermal power at beginning of the horizon [MWt]",
            default=0.0,
            within=pyomo.NonNegativeReals,
            # validate= # TODO: bounds->(0, csp.maximum_cycle_thermal_power), Sec. 4.7.1
            mutable=True,
            units=u.MW)
        self.model.is_cycle_generating_initial = pyomo.Param(
            doc="1 if cycle is generating electric power at beginning of the horizon; 0 Otherwise [-]",
            default=0.0,
            within=pyomo.Binary,
            mutable=True,
            units=u.dimensionless)
        self.model.is_cycle_starting_initial = pyomo.Param(
            doc="1 if cycle is starting up at beginning of the horizon; 0 Otherwise [-]",
            default=0.0,
            within=pyomo.Binary,
            mutable=True,
            units=u.dimensionless)

        def cycle_startup_inventory_linking_rule(m, t):
            if t == self.blocks.index_set().first():
                return self.blocks[t].previous_cycle_startup_inventory == self.model.initial_cycle_startup_inventory
            return self.blocks[t].previous_cycle_startup_inventory == self.blocks[t - 1].cycle_startup_inventory
        self.model.cycle_startup_inventory_linking = pyomo.Constraint(
            self.blocks.index_set(),
            doc="Cycle startup inventory block linking constraint",
            rule=cycle_startup_inventory_linking_rule)

        def cycle_thermal_power_linking_rule(m, t):
            if t == self.blocks.index_set().first():
                return self.blocks[t].previous_cycle_thermal_power == self.model.initial_cycle_thermal_power
            return self.blocks[t].previous_cycle_thermal_power == self.blocks[t - 1].cycle_thermal_power
        self.model.cycle_thermal_power_linking = pyomo.Constraint(
            self.blocks.index_set(),
            doc="Cycle thermal power block linking constraint",
            rule=cycle_thermal_power_linking_rule)

        def cycle_generating_linking_rule(m, t):
            if t == self.blocks.index_set().first():
                return self.blocks[t].was_cycle_generating == self.model.is_cycle_generating_initial
            return self.blocks[t].was_cycle_generating == self.blocks[t - 1].is_cycle_generating
        self.model.cycle_generating_linking = pyomo.Constraint(
            self.blocks.index_set(),
            doc="Is cycle generating binary block linking constraint",
            rule=cycle_generating_linking_rule)

        def cycle_starting_linking_rule(m, t):
            if t == self.blocks.index_set().first():
                return self.blocks[t].was_cycle_starting == self.model.is_cycle_starting_initial
            return self.blocks[t].was_cycle_starting == self.blocks[t - 1].is_cycle_starting
        self.model.cycle_starting_linking = pyomo.Constraint(
            self.blocks.index_set(),
            doc="Is cycle starting up binary block linking constraint",
            rule=cycle_starting_linking_rule)

    def initialize_parameters(self):
        csp = self._system_model

        cycle_rated_thermal = csp.cycle_thermal_rating
        field_rated_thermal = csp.field_thermal_rating

        # Cost Parameters
        self.cost_per_field_generation = 0.5
        self.cost_per_field_start = 1.5 * field_rated_thermal
        self.cost_per_cycle_generation = 2.0
        self.cost_per_cycle_start = 40.0 * csp.value('P_ref')
        self.cost_per_change_thermal_input = 0.5

        # Solar field and thermal energy storage performance parameters
        self.field_startup_losses = csp.value('p_start') * csp.number_of_reflector_units / 1e3
        self.receiver_required_startup_energy = csp.value('rec_qf_delay') * field_rated_thermal
        self.storage_capacity = csp.tes_hours * cycle_rated_thermal
        self.minimum_receiver_power = csp.minimum_receiver_power_fraction * field_rated_thermal
        self.allowable_receiver_startup_power = self.receiver_required_startup_energy / csp.value('rec_su_delay')
        self.receiver_pumping_losses = csp.estimate_receiver_pumping_parasitic()
        self.field_track_losses = csp.field_tracking_power
        #self.heat_trace_losses = 0.00163 * field_rated_thermal     # TODO: need to update for troughs

        # Power cycle performance
        self.cycle_required_startup_energy = csp.value('startup_frac') * cycle_rated_thermal
        self.cycle_nominal_efficiency = csp.cycle_nominal_efficiency

        design_mass_flow = csp.get_cycle_design_mass_flow()
        self.cycle_pumping_losses = csp.value('pb_pump_coef') * design_mass_flow / (cycle_rated_thermal * 1e3)
        self.allowable_cycle_startup_power = self.cycle_required_startup_energy / csp.value('startup_time')
        self.minimum_cycle_thermal_power = csp.value('cycle_cutoff_frac') * cycle_rated_thermal
        self.maximum_cycle_thermal_power = csp.value('cycle_max_frac') * cycle_rated_thermal
        self.set_part_load_cycle_parameters()

    def update_time_series_parameters(self, start_time: int):
        """
        Sets up SSC simulation to get time series performance parameters after simulation.
        : param start_time: hour of the year starting dispatch horizon
        """
        n_horizon = len(self.blocks.index_set())
        self.time_duration = [1.0] * n_horizon  # assume hourly for now

        # Set available thermal energy based on forecast
        thermal_resource = self._system_model.solar_thermal_resource
        temperature = list(self._system_model.year_weather_df.Temperature.values)
        if start_time + n_horizon > len(thermal_resource):
            field_gen = list(thermal_resource[start_time:])
            field_gen.extend(list(thermal_resource[0:n_horizon - len(field_gen)]))

            dry_bulb_temperature = list(temperature[start_time:])
            dry_bulb_temperature.extend(list(temperature[0:n_horizon - len(dry_bulb_temperature)]))
        else:
            field_gen = thermal_resource[start_time:start_time + n_horizon]
            dry_bulb_temperature = temperature[start_time:start_time + n_horizon]

        self.available_thermal_generation = field_gen
        # Set cycle performance parameters that depend on ambient temperature
        self.set_ambient_temperature_cycle_parameters(dry_bulb_temperature)

        self.update_initial_conditions()  # other dispatch models do not have this method

    def set_part_load_cycle_parameters(self):
        """Set parameters in dispatch model for off-design cycle performance."""
        # --- Cycle part-load efficiency
        tables = self._system_model.cycle_efficiency_tables
        if 'cycle_eff_load_table' in tables:
            q_pb_design = self._system_model.cycle_thermal_rating
            num_pts = len(tables['cycle_eff_load_table'])
            norm_heat_pts = [tables['cycle_eff_load_table'][i][0] / q_pb_design for i in range(num_pts)]  # Load fraction
            efficiency_pts = [tables['cycle_eff_load_table'][i][1] for i in range(num_pts)]  # Efficiency
            self.set_linearized_cycle_part_load_params(norm_heat_pts, efficiency_pts)
        elif 'ud_ind_od' in tables:
            # Tables not returned from ssc, but can be taken from user-defined cycle inputs
            D = self.interpret_user_defined_cycle_data(tables['ud_ind_od'])
            k = 3 * D['nT'] + D['nm']
            norm_heat_pts = D['mpts']  # Load fraction
            efficiency_pts = [self._system_model.cycle_nominal_efficiency * (tables['ud_ind_od'][k + p][3] / tables['ud_ind_od'][k + p][4])
                              for p in range(len(norm_heat_pts))]  # Efficiency
            self.set_linearized_cycle_part_load_params(norm_heat_pts, efficiency_pts)
        else:
            print('WARNING: Dispatch optimization cycle part-load efficiency is not set. '
                  'Defaulting to constant efficiency vs load.')
            self.cycle_performance_slope = self._system_model.cycle_nominal_efficiency
            # self.minimum_cycle_power = self.minimum_cycle_thermal_power * self._system_model.cycle_nominal_efficiency
            self.maximum_cycle_power = self.maximum_cycle_thermal_power * self._system_model.cycle_nominal_efficiency

    def set_linearized_cycle_part_load_params(self, norm_heat_pts, efficiency_pts):
        q_pb_design = self._system_model.cycle_thermal_rating
        fpts = [self._system_model.value('cycle_cutoff_frac'), self._system_model.value('cycle_max_frac')]
        step = norm_heat_pts[1] - norm_heat_pts[0]
        q, eta = [ [] for v in range(2)]
        for j in range(2):
            # Find first point in user-defined array of load fractions
            p = max(0, min(int((fpts[j] - norm_heat_pts[0]) / step), len(norm_heat_pts) - 2))
            eta.append(efficiency_pts[p] + (efficiency_pts[p + 1] - efficiency_pts[p]) / step * (fpts[j] - norm_heat_pts[p]))
            q.append(fpts[j]*q_pb_design)
        etap = (q[1]*eta[1]-q[0]*eta[0])/(q[1]-q[0])
        b = q[1]*(eta[1] - etap)
        self.cycle_performance_slope = etap
        # self.minimum_cycle_power = b + self.minimum_cycle_thermal_power * self.cycle_performance_slope
        self.maximum_cycle_power = b + self.maximum_cycle_thermal_power * self.cycle_performance_slope
        return

    def set_ambient_temperature_cycle_parameters(self, dry_bulb_temperature):
        """Set ambient temperature dependent cycle performance parameters."""
        # --- Cycle ambient-temperature efficiency corrections
        tables = self._system_model.cycle_efficiency_tables
        if 'cycle_eff_Tdb_table' in tables:
            nT = len(tables['cycle_eff_Tdb_table'])
            Tpts = [tables['cycle_eff_Tdb_table'][i][0] for i in range(nT)]
            efficiency_pts = [tables['cycle_eff_Tdb_table'][i][1] * self._system_model.cycle_nominal_efficiency for i in range(nT)]  # Efficiency
            wcondfpts = [tables['cycle_wcond_Tdb_table'][i][1] for i in range(nT)]  # Fraction of cycle design gross output consumed by cooling
            self.set_cycle_ambient_corrections(dry_bulb_temperature, Tpts, efficiency_pts, wcondfpts)
        elif 'ud_ind_od' in tables:
            # Tables not returned from ssc, but can be taken from user-defined cycle inputs
            D = self.interpret_user_defined_cycle_data(tables['ud_ind_od'])
            k = 3 * D['nT'] + 3 * D['nm'] + D[
                'nTamb']  # first index in udpc data corresponding to performance at design point HTF T, and design point mass flow
            npts = D['nTamb']
            efficiency_pts = [self._system_model.cycle_nominal_efficiency * (tables['ud_ind_od'][j][3] / tables['ud_ind_od'][j][4])
                              for j in range(k, k + npts)]  # Efficiency
            wcondfpts = [(self._system_model.value('ud_f_W_dot_cool_des') / 100.) * tables['ud_ind_od'][j][5] for j in
                         range(k, k + npts)]  # Fraction of cycle design gross output consumed by cooling
            self.set_cycle_ambient_corrections(dry_bulb_temperature, D['Tambpts'], efficiency_pts, wcondfpts)
        else:
            print('WARNING: Dispatch optimization cycle ambient temperature corrections are not set up.')
            n = len(dry_bulb_temperature)
            self.cycle_ambient_efficiency_correction = [self._system_model.cycle_nominal_efficiency] * n
            self.condenser_losses = [0.0] * n
        return

    def set_cycle_ambient_corrections(self, Tdb, Tpts, etapts, wcondfpts):
        n = len(Tdb)            # Tdb = set of ambient temperature points for each dispatch time step
        npts = len(Tpts)        # Tpts = ambient temperature points with tabulated values
        cycle_ambient_efficiency_correction = [1.0]*n
        condenser_losses = [0.0]*n
        Tstep = Tpts[1] - Tpts[0]
        for j in range(n):
            i = max(0, min( int((Tdb[j] - Tpts[0]) / Tstep), npts-2) )
            r = (Tdb[j] - Tpts[i]) / Tstep
            cycle_ambient_efficiency_correction[j] = etapts[i] + (etapts[i + 1] - etapts[i]) * r
            condenser_losses[j] = wcondfpts[i] + (wcondfpts[i + 1] - wcondfpts[i]) * r
        self.cycle_ambient_efficiency_correction = cycle_ambient_efficiency_correction
        self.condenser_losses = condenser_losses
        return

    @staticmethod
    def interpret_user_defined_cycle_data(ud_ind_od):
        data = np.array(ud_ind_od)

        i0 = 0
        nT = np.where(np.diff(data[i0::, 0]) < 0)[0][0] + 1
        Tpts = data[i0:i0 + nT, 0]
        mlevels = [data[j, 1] for j in [i0, i0 + nT, i0 + 2 * nT]]

        i0 = 3 * nT
        nm = np.where(np.diff(data[i0::, 1]) < 0)[0][0] + 1
        mpts = data[i0:i0 + nm, 1]
        Tamblevels = [data[j, 2] for j in [i0, i0 + nm, i0 + 2 * nm]]

        i0 = 3 * nT + 3 * nm
        nTamb = np.where(np.diff(data[i0::, 2]) < 0)[0][0] + 1
        Tambpts = data[i0:i0 + nTamb, 2]
        Tlevels = [data[j, 0] for j in [i0, i0 + nm, i0 + 2 * nm]]

        return {'nT': nT, 'Tpts': Tpts, 'Tlevels': Tlevels, 'nm': nm, 'mpts': mpts, 'mlevels': mlevels, 'nTamb': nTamb,
                'Tambpts': Tambpts, 'Tamblevels': Tamblevels}

    def update_initial_conditions(self):
        csp = self._system_model

        m_des = csp.get_design_storage_mass()
        m_hot = csp.initial_tes_hot_mass_fraction * m_des  # Available active mass in hot tank
        cp = csp.get_cp_htf(0.5 * (csp.plant_state['T_tank_hot_init'] + csp.htf_cold_design_temperature))  # J/kg/K
        self.initial_thermal_energy_storage = min(self.storage_capacity,
                                                  m_hot * cp * (csp.plant_state['T_tank_hot_init']
                                                                - csp.htf_cold_design_temperature) * 1.e-6 / 3600)

        self.is_field_generating_initial = (csp.plant_state['rec_op_mode_initial'] == 2)
        self.is_field_starting_initial = (csp.plant_state['rec_op_mode_initial'] == 1)

        # Initial startup energy accumulated
        # ssc seems to report nan when startup is completed
        if csp.plant_state['pc_startup_energy_remain_initial'] != csp.plant_state['pc_startup_energy_remain_initial']:
            self.initial_cycle_startup_inventory = self.cycle_required_startup_energy
        else:
            self.initial_cycle_startup_inventory = max(0.0, self.cycle_required_startup_energy
                                                       - csp.plant_state['pc_startup_energy_remain_initial'] / 1e3)
            if self.initial_cycle_startup_inventory > (1.0 - 1.e-6) * self.cycle_required_startup_energy:
                self.initial_cycle_startup_inventory = self.cycle_required_startup_energy

        self.is_cycle_generating_initial = (csp.plant_state['pc_op_mode_initial'] == 1)
        self.is_cycle_starting_initial = (csp.plant_state['pc_op_mode_initial'] == 0
                                          or csp.plant_state['pc_op_mode_initial'] == 4)
        # self.ycsb0 = (plant.state['pc_op_mode_initial'] == 2)

        if self.is_cycle_generating_initial:
            self.initial_cycle_thermal_power = csp.plant_state['heat_into_cycle']
        else:
            self.initial_cycle_thermal_power = 0.0

    @staticmethod
    def get_start_end_datetime(start_time: int, n_horizon: int):
        # Setting simulation times
        start_datetime = CspDispatch.get_start_datetime_by_hour(start_time)
        # Handling end of simulation horizon -> assumes hourly data
        if start_time + n_horizon > 8760:
            end_datetime = start_datetime + datetime.timedelta(hours=8760 - start_time)
        else:
            end_datetime = start_datetime + datetime.timedelta(hours=n_horizon)
        return start_datetime, end_datetime

    @staticmethod
    def get_start_datetime_by_hour(start_time: int):
        """
        Get datetime for start_time hour of the year
        : param start_time: hour of year
        : return: datetime object
        """
        # TODO: bring in the correct year from site data - or replace outside of function?
        beginning_of_year = datetime.datetime(2009, 1, 1, 0)
        return beginning_of_year + datetime.timedelta(hours=start_time)

    @staticmethod
    def seconds_since_newyear(dt):
        # Substitute a non-leap year (2009) to keep multiple of 8760 assumption:
        newyear = datetime.datetime(2009, 1, 1, 0, 0, 0, 0)
        time_diff = dt - newyear
        return int(time_diff.total_seconds())


    #################################
    # INPUTS                        #
    #################################
    @property
    def time_duration(self) -> list:
        """Dispatch horizon time steps [hour]"""
        # TODO: Should we make this constant within dispatch horizon?
        return [self.blocks[t].time_duration.value for t in self.blocks.index_set()]

    @time_duration.setter
    def time_duration(self, time_duration: list):
        """Dispatch horizon time steps [hour]"""
        if len(time_duration) == len(self.blocks):
            for t, delta in zip(self.blocks, time_duration):
                self.blocks[t].time_duration = round(delta, self.round_digits)
        else:
            raise ValueError(self.time_duration.__name__ + " list must be the same length as time horizon")

    @property
    def available_thermal_generation(self) -> list:
        """Available solar thermal generation from the csp field [MWt]"""
        return [self.blocks[t].available_thermal_generation.value for t in self.blocks.index_set()]

    @available_thermal_generation.setter
    def available_thermal_generation(self, available_thermal_generation: list):
        """Available solar thermal generation from the csp field [MWt]"""
        if len(available_thermal_generation) == len(self.blocks):
            for t, value in zip(self.blocks, available_thermal_generation):
                self.blocks[t].available_thermal_generation = round(value, self.round_digits)
        else:
            raise ValueError(self.available_thermal_generation.__name__ + " list must be the same length as time horizon")

    @property
    def cycle_ambient_efficiency_correction(self) -> list:
        """Cycle efficiency ambient temperature adjustment factor [-]"""
        return [self.blocks[t].cycle_ambient_efficiency_correction.value for t in self.blocks.index_set()]

    @cycle_ambient_efficiency_correction.setter
    def cycle_ambient_efficiency_correction(self, cycle_ambient_efficiency_correction: list):
        """Cycle efficiency ambient temperature adjustment factor [-]"""
        if len(cycle_ambient_efficiency_correction) == len(self.blocks):
            for t, value in zip(self.blocks, cycle_ambient_efficiency_correction):
                self.blocks[t].cycle_ambient_efficiency_correction = round(value, self.round_digits)
        else:
            raise ValueError(self.cycle_ambient_efficiency_correction.__name__ + " list must be the same length as time horizon")

    @property
    def condenser_losses(self) -> list:
        """Normalized condenser parasitic losses [-]"""
        return [self.blocks[t].condenser_losses.value for t in self.blocks.index_set()]

    @condenser_losses.setter
    def condenser_losses(self, condenser_losses: list):
        """Normalized condenser parasitic losses [-]"""
        if len(condenser_losses) == len(self.blocks):
            for t, value in zip(self.blocks, condenser_losses):
                self.blocks[t].condenser_losses = round(value, self.round_digits)
        else:
            raise ValueError(self.condenser_losses.__name__ + " list must be the same length as time horizon")

    @property
    def cost_per_field_generation(self) -> float:
        """Generation cost for the csp field [$/MWht]"""
        for t in self.blocks.index_set():
            return self.blocks[t].cost_per_field_generation.value

    @cost_per_field_generation.setter
    def cost_per_field_generation(self, om_dollar_per_mwh_thermal: float):
        """Generation cost for the csp field [$/MWht]"""
        for t in self.blocks.index_set():
            self.blocks[t].cost_per_field_generation.set_value(round(om_dollar_per_mwh_thermal, self.round_digits))

    @property
    def cost_per_field_start(self) -> float:
        """Penalty for field start-up [$/start]"""
        for t in self.blocks.index_set():
            return self.blocks[t].cost_per_field_start.value

    @cost_per_field_start.setter
    def cost_per_field_start(self, dollars_per_start: float):
        """Penalty for field start-up [$/start]"""
        for t in self.blocks.index_set():
            self.blocks[t].cost_per_field_start.set_value(round(dollars_per_start, self.round_digits))

    @property
    def cost_per_cycle_generation(self) -> float:
        """Generation cost for power cycle [$/MWhe]"""
        for t in self.blocks.index_set():
            return self.blocks[t].cost_per_cycle_generation.value

    @cost_per_cycle_generation.setter
    def cost_per_cycle_generation(self, om_dollar_per_mwh_electric: float):
        """Generation cost for power cycle [$/MWhe]"""
        for t in self.blocks.index_set():
            self.blocks[t].cost_per_cycle_generation.set_value(round(om_dollar_per_mwh_electric, self.round_digits))

    @property
    def cost_per_cycle_start(self) -> float:
        """Penalty for power cycle start [$/start]"""
        for t in self.blocks.index_set():
            return self.blocks[t].cost_per_cycle_start.value

    @cost_per_cycle_start.setter
    def cost_per_cycle_start(self, dollars_per_start: float):
        """Penalty for power cycle start [$/start]"""
        for t in self.blocks.index_set():
            self.blocks[t].cost_per_cycle_start.set_value(round(dollars_per_start, self.round_digits))

    @property
    def cost_per_change_thermal_input(self) -> float:
        """Penalty for change in power cycle thermal input [$/MWt]"""
        for t in self.blocks.index_set():
            return self.blocks[t].cost_per_change_thermal_input.value

    @cost_per_change_thermal_input.setter
    def cost_per_change_thermal_input(self, dollars_per_thermal_power: float):
        """Penalty for change in power cycle thermal input [$/MWt]"""
        for t in self.blocks.index_set():
            self.blocks[t].cost_per_change_thermal_input.set_value(round(dollars_per_thermal_power, self.round_digits))

    @property
    def field_startup_losses(self) -> float:
        """Solar field startup or shutdown parasitic loss [MWhe]"""
        for t in self.blocks.index_set():
            return self.blocks[t].field_startup_losses.value

    @field_startup_losses.setter
    def field_startup_losses(self, field_startup_losses: float):
        """Solar field startup or shutdown parasitic loss [MWhe]"""
        for t in self.blocks.index_set():
            self.blocks[t].field_startup_losses.set_value(round(field_startup_losses, self.round_digits))

    @property
    def receiver_required_startup_energy(self) -> float:
        """Required energy expended to start receiver [MWht]"""
        for t in self.blocks.index_set():
            return self.blocks[t].receiver_required_startup_energy.value

    @receiver_required_startup_energy.setter
    def receiver_required_startup_energy(self, energy: float):
        """Required energy expended to start receiver [MWht]"""
        for t in self.blocks.index_set():
            self.blocks[t].receiver_required_startup_energy.set_value(round(energy, self.round_digits))

    @property
    def storage_capacity(self) -> float:
        """Thermal energy storage capacity [MWht]"""
        for t in self.blocks.index_set():
            return self.blocks[t].storage_capacity.value

    @storage_capacity.setter
    def storage_capacity(self, energy: float):
        """Thermal energy storage capacity [MWht]"""
        for t in self.blocks.index_set():
            self.blocks[t].storage_capacity.set_value(round(energy, self.round_digits))

    @property
    def receiver_pumping_losses(self) -> float:
        """Solar field and/or receiver pumping power per unit power produced [MWe/MWt]"""
        for t in self.blocks.index_set():
            return self.blocks[t].receiver_pumping_losses.value

    @receiver_pumping_losses.setter
    def receiver_pumping_losses(self, electric_per_thermal: float):
        """Solar field and/or receiver pumping power per unit power produced [MWe/MWt]"""
        for t in self.blocks.index_set():
            self.blocks[t].receiver_pumping_losses.set_value(round(electric_per_thermal, self.round_digits))

    @property
    def minimum_receiver_power(self) -> float:
        """Minimum operational thermal power delivered by receiver [MWht]"""
        for t in self.blocks.index_set():
            return self.blocks[t].minimum_receiver_power.value

    @minimum_receiver_power.setter
    def minimum_receiver_power(self, thermal_power: float):
        """Minimum operational thermal power delivered by receiver [MWt]"""
        for t in self.blocks.index_set():
            self.blocks[t].minimum_receiver_power.set_value(round(thermal_power, self.round_digits))

    @property
    def allowable_receiver_startup_power(self) -> float:
        """Allowable power per period for receiver start-up [MWt]"""
        for t in self.blocks.index_set():
            return self.blocks[t].allowable_receiver_startup_power.value

    @allowable_receiver_startup_power.setter
    def allowable_receiver_startup_power(self, thermal_power: float):
        """Allowable power per period for receiver start-up [MWt]"""
        for t in self.blocks.index_set():
            self.blocks[t].allowable_receiver_startup_power.set_value(round(thermal_power, self.round_digits))

    @property
    def field_track_losses(self) -> float:
        """Solar field tracking parasitic loss [MWe]"""
        for t in self.blocks.index_set():
            return self.blocks[t].field_track_losses.value

    @field_track_losses.setter
    def field_track_losses(self, electric_power: float):
        """Solar field tracking parasitic loss [MWe]"""
        for t in self.blocks.index_set():
            self.blocks[t].field_track_losses.set_value(round(electric_power, self.round_digits))

    # @property
    # def heat_trace_losses(self) -> float:
    #     """Piping heat trace parasitic loss [MWe]"""
    #     for t in self.blocks.index_set():
    #         return self.blocks[t].heat_trace_losses.value
    #
    # @heat_trace_losses.setter
    # def heat_trace_losses(self, electric_power: float):
    #     """Piping heat trace parasitic loss [MWe]"""
    #     for t in self.blocks.index_set():
    #         self.blocks[t].heat_trace_losses.set_value(round(electric_power, self.round_digits))

    @property
    def cycle_required_startup_energy(self) -> float:
        """Required energy expended to start cycle [MWht]"""
        for t in self.blocks.index_set():
            return self.blocks[t].cycle_required_startup_energy.value

    @cycle_required_startup_energy.setter
    def cycle_required_startup_energy(self, thermal_energy: float):
        """Required energy expended to start cycle [MWht]"""
        for t in self.blocks.index_set():
            self.blocks[t].cycle_required_startup_energy.set_value(round(thermal_energy, self.round_digits))

    @property
    def cycle_nominal_efficiency(self) -> float:
        """Power cycle nominal efficiency [-]"""
        for t in self.blocks.index_set():
            return self.blocks[t].cycle_nominal_efficiency.value

    @cycle_nominal_efficiency.setter
    def cycle_nominal_efficiency(self, efficiency: float):
        """Power cycle nominal efficiency [-]"""
        efficiency = self._check_efficiency_value(efficiency)
        for t in self.blocks.index_set():
            self.blocks[t].cycle_nominal_efficiency.set_value(round(efficiency, self.round_digits))

    @property
    def cycle_performance_slope(self) -> float:
        """Slope of linear approximation of power cycle performance curve [MWe/MWt]"""
        for t in self.blocks.index_set():
            return self.blocks[t].cycle_performance_slope.value

    @cycle_performance_slope.setter
    def cycle_performance_slope(self, slope: float):
        """Slope of linear approximation of power cycle performance curve [MWe/MWt]"""
        for t in self.blocks.index_set():
            self.blocks[t].cycle_performance_slope.set_value(round(slope, self.round_digits))

    @property
    def cycle_pumping_losses(self) -> float:
        """Cycle heat transfer fluid pumping power per unit energy expended [MWe/MWt]"""
        for t in self.blocks.index_set():
            return self.blocks[t].cycle_pumping_losses.value

    @cycle_pumping_losses.setter
    def cycle_pumping_losses(self, electric_per_thermal: float):
        """Cycle heat transfer fluid pumping power per unit energy expended [MWe/MWt]"""
        for t in self.blocks.index_set():
            self.blocks[t].cycle_pumping_losses.set_value(round(electric_per_thermal, self.round_digits))

    @property
    def allowable_cycle_startup_power(self) -> float:
        """Allowable power per period for cycle start-up [MWt]"""
        for t in self.blocks.index_set():
            return self.blocks[t].allowable_cycle_startup_power.value

    @allowable_cycle_startup_power.setter
    def allowable_cycle_startup_power(self, thermal_power: float):
        """Allowable power per period for cycle start-up [MWt]"""
        for t in self.blocks.index_set():
            self.blocks[t].allowable_cycle_startup_power.set_value(round(thermal_power, self.round_digits))

    @property
    def minimum_cycle_thermal_power(self) -> float:
        """Minimum operational thermal power delivered to the power cycle [MWt]"""
        for t in self.blocks.index_set():
            return self.blocks[t].minimum_cycle_thermal_power.value

    @minimum_cycle_thermal_power.setter
    def minimum_cycle_thermal_power(self, thermal_power: float):
        """Minimum operational thermal power delivered to the power cycle [MWt]"""
        for t in self.blocks.index_set():
            self.blocks[t].minimum_cycle_thermal_power.set_value(round(thermal_power, self.round_digits))

    @property
    def maximum_cycle_thermal_power(self) -> float:
        """Maximum operational thermal power delivered to the power cycle [MWt]"""
        for t in self.blocks.index_set():
            return self.blocks[t].maximum_cycle_thermal_power.value

    @maximum_cycle_thermal_power.setter
    def maximum_cycle_thermal_power(self, thermal_power: float):
        """Maximum operational thermal power delivered to the power cycle [MWt]"""
        for t in self.blocks.index_set():
            self.blocks[t].maximum_cycle_thermal_power.set_value(round(thermal_power, self.round_digits))

    # @property
    # def minimum_cycle_power(self) -> float:
    #     """Minimum cycle electric power output [MWe]"""
    #     for t in self.blocks.index_set():
    #         return self.blocks[t].minimum_cycle_power.value
    #
    # @minimum_cycle_power.setter
    # def minimum_cycle_power(self, electric_power: float):
    #     """Minimum cycle electric power output [MWe]"""
    #     for t in self.blocks.index_set():
    #         self.blocks[t].minimum_cycle_power.set_value(round(electric_power, self.round_digits))

    @property
    def maximum_cycle_power(self) -> float:
        """Maximum cycle electric power output [MWe]"""
        for t in self.blocks.index_set():
            return self.blocks[t].maximum_cycle_power.value

    @maximum_cycle_power.setter
    def maximum_cycle_power(self, electric_power: float):
        """Maximum cycle electric power output [MWe]"""
        for t in self.blocks.index_set():
            self.blocks[t].maximum_cycle_power.set_value(round(electric_power, self.round_digits))

    # INITIAL CONDITIONS
    @property
    def initial_thermal_energy_storage(self) -> float:
        """Initial thermal energy storage reserve quantity at beginning of the horizon [MWht]"""
        return self.model.initial_thermal_energy_storage.value

    @initial_thermal_energy_storage.setter
    def initial_thermal_energy_storage(self, initial_energy: float):
        """Initial thermal energy storage reserve quantity at beginning of the horizon [MWht]"""
        self.model.initial_thermal_energy_storage = round(initial_energy, self.round_digits)

    @property
    def initial_receiver_startup_inventory(self) -> float:
        """Initial receiver start-up energy inventory at beginning of the horizon [MWht]"""
        return self.model.initial_receiver_startup_inventory.value

    @initial_receiver_startup_inventory.setter
    def initial_receiver_startup_inventory(self, initial_energy: float):
        """Initial receiver start-up energy inventory at beginning of the horizon [MWht]"""
        self.model.initial_receiver_startup_inventory = round(initial_energy, self.round_digits)

    @property
    def is_field_generating_initial(self) -> bool:
        """True (1) if solar field is generating 'usable' thermal power at beginning of the horizon;
         False (0) Otherwise [-]"""
        return bool(self.model.is_field_generating_initial.value)

    @is_field_generating_initial.setter
    def is_field_generating_initial(self, is_field_generating: Union[bool, int]):
        """True (1) if solar field is generating 'usable' thermal power at beginning of the horizon;
         False (0) Otherwise [-]"""
        self.model.is_field_generating_initial = int(is_field_generating)

    @property
    def is_field_starting_initial(self) -> bool:
        """True (1) if solar field  is starting up at beginning of the horizon; False (0) Otherwise [-]"""
        return bool(self.model.is_field_starting_initial.value)

    @is_field_starting_initial.setter
    def is_field_starting_initial(self, is_field_starting: Union[bool, int]):
        """True (1) if solar field  is starting up at beginning of the horizon; False (0) Otherwise [-]"""
        self.model.is_field_starting_initial = int(is_field_starting)

    @property
    def initial_cycle_startup_inventory(self) -> float:
        """Initial cycle start-up energy inventory at beginning of the horizon [MWht]"""
        return self.model.initial_cycle_startup_inventory.value

    @initial_cycle_startup_inventory.setter
    def initial_cycle_startup_inventory(self, initial_energy: float):
        """Initial cycle start-up energy inventory at beginning of the horizon [MWht]"""
        self.model.initial_cycle_startup_inventory = round(initial_energy, self.round_digits)

    @property
    def initial_cycle_thermal_power(self) -> float:
        """Initial cycle thermal power at beginning of the horizon [MWt]"""
        return self.model.initial_cycle_thermal_power.value

    @initial_cycle_thermal_power.setter
    def initial_cycle_thermal_power(self, initial_power: float):
        """Initial cycle thermal power at beginning of the horizon [MWt]"""
        self.model.initial_cycle_thermal_power = round(initial_power, self.round_digits)

    @property
    def is_cycle_generating_initial(self) -> bool:
        """True (1) if cycle is generating electric power at beginning of the horizon; False (0) Otherwise [-]"""
        return bool(self.model.is_cycle_generating_initial.value)

    @is_cycle_generating_initial.setter
    def is_cycle_generating_initial(self, is_cycle_generating: Union[bool, int]):
        """True (1) if cycle is generating electric power at beginning of the horizon; False (0) Otherwise [-]"""
        self.model.is_cycle_generating_initial = int(is_cycle_generating)

    @property
    def is_cycle_starting_initial(self) -> bool:
        """True (1) if cycle is starting up at beginning of the horizon; False (0) Otherwise [-]"""
        return bool(self.model.is_cycle_starting_initial.value)

    @is_cycle_starting_initial.setter
    def is_cycle_starting_initial(self, is_cycle_starting: Union[bool, int]):
        """True (1) if cycle is starting up at beginning of the horizon; False (0) Otherwise [-]"""
        self.model.is_cycle_starting_initial = int(is_cycle_starting)

    # OUTPUTS
    @property
    def thermal_energy_storage(self) -> list:
        """Thermal energy storage reserve quantity [MWht]"""
        return [round(self.blocks[t].thermal_energy_storage.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def receiver_startup_inventory(self) -> list:
        """Receiver start-up energy inventory [MWht]"""
        return [round(self.blocks[t].receiver_startup_inventory.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def receiver_thermal_power(self) -> list:
        """Thermal power delivered by the receiver [MWt]"""
        return [round(self.blocks[t].receiver_thermal_power.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def receiver_startup_consumption(self) -> list:
        """Receiver start-up power consumption [MWt]"""
        return [round(self.blocks[t].receiver_startup_consumption.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def is_field_generating(self) -> list:
        """1 if solar field is generating 'usable' thermal power; 0 Otherwise [-]"""
        return [round(self.blocks[t].is_field_generating.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def is_field_starting(self) -> list:
        """1 if solar field is starting up; 0 Otherwise [-]"""
        return [round(self.blocks[t].is_field_starting.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def incur_field_start(self) -> list:
        """1 if solar field start-up penalty is incurred; 0 Otherwise [-]"""
        return [round(self.blocks[t].incur_field_start.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def cycle_startup_inventory(self) -> list:
        """Cycle start-up energy inventory [MWht]"""
        return [round(self.blocks[t].cycle_startup_inventory.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def system_load(self) -> list:
        """Net generation of csp system [MWe]"""
        return [round(self.blocks[t].system_load.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def cycle_generation(self) -> list:
        """Power cycle electricity generation [MWe]"""
        return [round(self.blocks[t].cycle_generation.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def cycle_thermal_ramp(self) -> list:
        """Power cycle positive change in thermal energy input [MWt]"""
        return [round(self.blocks[t].cycle_thermal_ramp.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def cycle_thermal_power(self) -> list:
        """Cycle thermal power utilization [MWt]"""
        return [round(self.blocks[t].cycle_thermal_power.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def is_cycle_generating(self) -> list:
        """1 if cycle is generating electric power; 0 Otherwise [-]"""
        return [round(self.blocks[t].is_cycle_generating.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def is_cycle_starting(self) -> list:
        """1 if cycle is starting up; 0 Otherwise [-]"""
        return [round(self.blocks[t].is_cycle_starting.value, self.round_digits) for t in self.blocks.index_set()]

    @property
    def incur_cycle_start(self) -> list:
        """1 if cycle start-up penalty is incurred; 0 Otherwise [-]"""
        return [round(self.blocks[t].incur_cycle_start.value, self.round_digits) for t in self.blocks.index_set()]

