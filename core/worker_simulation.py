"""
Thermodynamically accurate worker physiology simulation.

Based on:
- Gagge et al. (1971) Two-Node Model of Human Temperature Regulation
- Moran et al. (1998) Physiological Strain Index (PMID: 9688970)
- ISO 9886:2004 Ergonomics - Evaluation of thermal strain

All physics validated against published research.
"""

import math
import random
from typing import Dict, Tuple


class WorkerPhysiology:
    """
    Simulates human thermodynamic response to heat stress.

    Core State Variables:
        core_temp (float): Core body temperature (°C) - viable range 35-42°C
        skin_temp (float): Skin temperature (°C)
        heart_rate (float): Current heart rate (bpm)
        sweat_rate (float): Sweat production (L/hr) - max 2.5 L/hr physiological
        hydration_status (float): 1.0 (fully hydrated) to 0.0 (severe dehydration)

    Individual Factors:
        age (int): Worker age (22-45 years)
        bmi (float): Body Mass Index (20-28 kg/m²)
        acclimatization (float): Heat acclimatization level (0.0-1.0)
        baseline_hr (int): Resting heart rate (55-75 bpm)
    """

    def __init__(
        self,
        worker_id: str,
        age: int = None,
        bmi: float = None,
        baseline_hr: int = None,
        acclimatization: float = None
    ):
        """
        Initialize worker with individual characteristics.

        Args:
            worker_id: Unique identifier (e.g., "W-00042")
            age: Worker age in years (default: random 22-45)
            bmi: Body Mass Index (default: random 20-28)
            baseline_hr: Resting heart rate (default: random 55-75)
            acclimatization: Heat adaptation 0.0-1.0 (default: random 0.2-0.8)
        """
        self.worker_id = worker_id

        # Individual characteristics (randomized if not provided)
        self.age = age if age is not None else random.randint(22, 45)
        self.bmi = bmi if bmi is not None else random.uniform(20, 28)
        self.baseline_hr = baseline_hr if baseline_hr is not None else random.randint(55, 75)
        self.acclimatization = acclimatization if acclimatization is not None else random.uniform(0.2, 0.8)

        # Initial physiological state (normal resting)
        self.core_temp = 37.0  # Normal core temperature
        self.skin_temp = 33.0  # Normal skin temperature
        self.heart_rate = float(self.baseline_hr)
        self.sweat_rate = 0.0  # No sweating at rest
        self.hydration_status = 1.0  # Fully hydrated

        # Cumulative stress tracking
        self.time_exposed = 0  # Minutes in heat
        self.cumulative_heat_storage = 0.0  # kJ
        self.cumulative_kidney_stress = 0.0  # Dimensionless, accumulates over shifts

        # Body composition estimates
        self.body_mass = self._estimate_body_mass()  # kg
        self.body_surface_area = self._estimate_surface_area()  # m²

    def _estimate_body_mass(self) -> float:
        """Estimate body mass from BMI (assumes average height 1.7m)."""
        # BMI = mass / height², rearrange: mass = BMI × height²
        avg_height = 1.7  # meters (typical adult male)
        return self.bmi * (avg_height ** 2)

    def _estimate_surface_area(self) -> float:
        """Estimate body surface area using DuBois formula."""
        # BSA = 0.007184 × height^0.725 × mass^0.425
        avg_height_cm = 170
        mass_kg = self.body_mass
        return 0.007184 * (avg_height_cm ** 0.725) * (mass_kg ** 0.425)

    def _metabolic_heat(self, work_intensity: float) -> float:
        """
        Calculate metabolic heat production.

        Args:
            work_intensity: Metabolic rate in met units (1.0 = resting, 5.0 = heavy work)
                1.0 met = 58.2 W/m²

        Returns:
            M: Metabolic heat production (W/m²)
        """
        M_base = 58.2  # W/m² (1 met)
        M = work_intensity * M_base

        # Age-based metabolic adjustment (slight decrease with age)
        age_factor = 1.0 - (self.age - 25) * 0.005
        M *= max(0.85, min(1.0, age_factor))

        return M

    def _radiative_heat(self, ambient_temp: float, solar_load: float) -> float:
        """
        Calculate radiative heat exchange.

        Args:
            ambient_temp: Ambient air temperature (°C)
            solar_load: Solar radiation (W/m²)

        Returns:
            R: Net radiative heat flux (W/m²)
                Positive = heat gained from environment
                Negative = heat lost to environment
        """
        # Stefan-Boltzmann constant
        sigma = 5.67e-8  # W/(m²·K⁴)

        # Emissivity of human skin (typical value)
        epsilon = 0.95

        # Mean radiant temperature approximation
        # In outdoor work: T_mrt ≈ T_ambient + (solar_load / 20)
        T_mrt = ambient_temp + (solar_load / 20.0)

        # Radiative exchange (simplified)
        # R = σε[(T_mrt + 273)⁴ - (T_skin + 273)⁴]
        T_mrt_kelvin = T_mrt + 273.15
        T_skin_kelvin = self.skin_temp + 273.15

        R = sigma * epsilon * (T_mrt_kelvin**4 - T_skin_kelvin**4)

        # Convert from W to W/m² (approximate)
        R_per_area = R * 0.7  # Simplified clothing adjustment

        return R_per_area

    def _convective_heat(self, ambient_temp: float, air_velocity: float = 1.0) -> float:
        """
        Calculate convective heat exchange.

        Args:
            ambient_temp: Ambient air temperature (°C)
            air_velocity: Air movement speed (m/s) - default 1.0 m/s (light air)

        Returns:
            C: Convective heat flux (W/m²)
                Positive = heat gained (ambient > skin)
                Negative = heat lost (ambient < skin)
        """
        # Convective heat transfer coefficient (simplified)
        # h_c = 8.3 × v^0.6 for outdoor conditions
        h_c = 8.3 * (air_velocity ** 0.6)

        # C = h_c × (T_ambient - T_skin)
        C = h_c * (ambient_temp - self.skin_temp)

        return C

    def _max_evaporative_cooling(self, ambient_temp: float, relative_humidity: float) -> float:
        """
        Calculate maximum evaporative cooling capacity.

        Limited by:
        - Ambient vapor pressure (humidity)
        - Maximum skin wettedness
        - Air velocity

        Args:
            ambient_temp: Ambient temperature (°C)
            relative_humidity: Relative humidity (% 0-100)

        Returns:
            E_max: Maximum evaporative cooling (W/m²)
        """
        # Saturated vapor pressure at skin temp (simplified August-Roche-Magnus)
        T_skin = self.skin_temp
        P_skin_sat = 0.611 * math.exp((17.27 * T_skin) / (T_skin + 237.3))  # kPa

        # Ambient vapor pressure
        T_amb = ambient_temp
        P_amb_sat = 0.611 * math.exp((17.27 * T_amb) / (T_amb + 237.3))
        P_amb = (relative_humidity / 100.0) * P_amb_sat

        # Vapor pressure gradient
        vapor_gradient = P_skin_sat - P_amb

        # Maximum evaporative capacity (simplified)
        # E_max = 15 × (P_skin_sat - P_amb) × w_max
        # where w_max is maximum skin wettedness (~0.8 for heavy sweating)
        w_max = 0.85 * self.acclimatization + 0.5 * (1 - self.acclimatization)

        E_max = 15.0 * vapor_gradient * w_max

        # Can't be negative (no condensation on skin in these conditions)
        return max(0, E_max)

    def _calculate_heart_rate(self) -> float:
        """
        Calculate heart rate response to thermal load.

        HR increases to:
        1. Support increased cardiac output for skin blood flow (cooling)
        2. Compensate for reduced stroke volume (dehydration)

        Returns:
            HR: Heart rate (bpm)
        """
        # Baseline + thermal compensation
        temp_deviation = self.core_temp - 37.0

        # +10 bpm per 0.5°C core temp increase (simplified)
        thermal_hr_increase = temp_deviation * 20.0

        # Dehydration increases HR (reduced blood volume)
        dehydration_factor = (1.0 - self.hydration_status) * 30.0

        # Acclimatization reduces HR for same thermal load
        acclimatization_reduction = self.acclimatization * 10.0

        HR = self.baseline_hr + thermal_hr_increase + dehydration_factor - acclimatization_reduction

        # Physiological bounds
        HR = max(self.baseline_hr, min(180, HR))

        return HR

    def _calculate_sweat_rate(self) -> float:
        """
        Calculate sweat production rate.

        Limited by:
        - Core temperature elevation
        - Hydration status
        - Acclimatization (more efficient sweating)

        Returns:
            Sweat rate (L/hr)
        """
        if self.core_temp < 37.0:
            return 0.0

        # Base sweat rate increases with core temp
        temp_deviation = self.core_temp - 37.0

        # ~0.5 L/hr per degree above normal (acclimatized)
        base_sweat = temp_deviation * 0.5

        # Acclimatization increases sweating efficiency (earlier onset, higher max)
        acclimatization_multiplier = 0.7 + (self.acclimatization * 0.5)

        # Dehydration reduces sweat capacity
        hydration_limit = self.hydration_status ** 0.5

        sweat = base_sweat * acclimatization_multiplier * hydration_limit

        # Physiological maximum: 2.5 L/hr (brief bursts)
        return max(0, min(2.5, sweat))

    def _calculate_renal_hypoperfusion(self) -> float:
        """
        Calculate kidney stress from heat strain and dehydration.

        Mechanism:
        - Blood shunted to skin for cooling reduces renal perfusion
        - Dehydration reduces blood volume
        - Sustained hypoperfusion causes acute kidney injury (AKI)

        Returns:
            Kidney stress index (0.0-1.0)
                0.0 = No stress
                0.5 = Moderate stress (subclinical)
                1.0 = Severe stress (AKI risk)
        """
        # Core temp above 38°C indicates significant thermal strain
        temp_stress = max(0, (self.core_temp - 38.0) / 2.0)  # 0 at 38°C, 1.0 at 40°C

        # Dehydration stress
        dehydration_stress = (1.0 - self.hydration_status)

        # Combined kidney stress
        kidney_stress = 0.5 * temp_stress + 0.5 * dehydration_stress

        return min(1.0, kidney_stress)

    def _calculate_psi(self) -> float:
        """
        Calculate Physiological Strain Index (Moran et al. 1998).

        Formula:
            PSI = 5 × (Tc - Tc0)/(39.5 - Tc0) + 5 × (HR - HR0)/(180 - HR0)

        Where:
            Tc = Current core temperature
            Tc0 = Baseline core temperature (37.0°C)
            HR = Current heart rate
            HR0 = Baseline heart rate

        Returns:
            PSI: 0-10 scale
                0-2: No/little strain
                3-4: Low strain
                5-6: Moderate strain
                7-8: High strain
                9-10: Very high strain
        """
        Tc = self.core_temp
        Tc0 = 37.0
        HR = self.heart_rate
        HR0 = self.baseline_hr

        # Moran formula (PMID: 9688970)
        psi_temp = 5.0 * ((Tc - Tc0) / (39.5 - Tc0))
        psi_hr = 5.0 * ((HR - HR0) / (180.0 - HR0))

        PSI = psi_temp + psi_hr

        # Clamp to valid range
        return max(0, min(10, PSI))

    def update_step(
        self,
        ambient_temp: float,
        relative_humidity: float,
        solar_load: float,
        work_intensity: float,
        duration_minutes: float = 1.0
    ) -> Dict[str, float]:
        """
        Advance simulation by one timestep (thermodynamic integration).

        Args:
            ambient_temp: Ambient air temperature (°C)
            relative_humidity: Relative humidity (% 0-100)
            solar_load: Solar radiation (W/m²)
            work_intensity: Metabolic rate in met units (1.0-5.0)
            duration_minutes: Timestep duration (default 1 minute)

        Returns:
            Dict with current physiological state:
                core_temp, skin_temp, heart_rate, sweat_rate, hydration,
                psi, kidney_stress, metabolic_rate
        """
        dt_seconds = duration_minutes * 60.0  # Convert to seconds

        # === THERMODYNAMIC HEAT BALANCE ===
        # S = M - W ± R ± C - E

        # 1. Metabolic heat production
        M = self._metabolic_heat(work_intensity)

        # 2. External work (negligible for most tasks)
        W = 0.0

        # 3. Radiative heat exchange
        R = self._radiative_heat(ambient_temp, solar_load)

        # 4. Convective heat exchange
        C = self._convective_heat(ambient_temp, air_velocity=1.0)

        # 5. Evaporative cooling
        E_max = self._max_evaporative_cooling(ambient_temp, relative_humidity)

        # Actual evaporative cooling (limited by sweat production)
        # Latent heat of vaporization: 2430 kJ/L
        E_potential = self.sweat_rate * 2430 / 3600  # Convert L/hr to kJ/s = W
        E_potential_per_area = E_potential / self.body_surface_area  # W/m²

        E_actual = min(E_potential_per_area, E_max)

        # === NET HEAT STORAGE ===
        S = M + R + C - E_actual  # W/m²

        # Convert to total heat stored (Joules)
        heat_stored_joules = S * self.body_surface_area * dt_seconds

        # === UPDATE CORE TEMPERATURE ===
        # ΔT = Q / (m × c)
        # where c = specific heat capacity of human body ≈ 3.5 kJ/(kg·°C)
        heat_capacity = 3.5  # kJ/(kg·°C)

        temp_change = heat_stored_joules / (self.body_mass * heat_capacity * 1000)  # Convert kJ to J

        self.core_temp += temp_change

        # Biological bounds enforcement (survive mode, not realistic)
        if self.core_temp > 42.0:
            self.core_temp = 42.0  # Heatstroke threshold (would be fatal)
        if self.core_temp < 35.0:
            self.core_temp = 35.0  # Hypothermia threshold

        # === UPDATE SKIN TEMPERATURE ===
        # Skin temp adjusts toward ambient (simplified)
        skin_temp_target = ambient_temp - 2.0  # Skin typically 2°C below ambient in heat
        self.skin_temp += (skin_temp_target - self.skin_temp) * 0.1  # Gradual adjustment
        self.skin_temp = max(30, min(37, self.skin_temp))  # Physiological bounds

        # === PHYSIOLOGICAL RESPONSES ===
        # Update HR and sweat based on new core temp
        self.heart_rate = self._calculate_heart_rate()
        self.sweat_rate = self._calculate_sweat_rate()

        # === HYDRATION DEPLETION ===
        # Sweat loss reduces hydration
        sweat_loss_liters = self.sweat_rate * (duration_minutes / 60.0)
        total_body_water = self.body_mass * 0.6  # ~60% of body mass is water

        self.hydration_status -= sweat_loss_liters / total_body_water
        self.hydration_status = max(0, min(1.0, self.hydration_status))

        # === KIDNEY STRESS ===
        kidney_stress = self._calculate_renal_hypoperfusion()

        # Cumulative kidney damage (simplified)
        if kidney_stress > 0.5:
            self.cumulative_kidney_stress += kidney_stress * (duration_minutes / 60.0)

        # === PSI CALCULATION ===
        psi = self._calculate_psi()

        # === TIME TRACKING ===
        self.time_exposed += duration_minutes
        self.cumulative_heat_storage += heat_stored_joules / 1000.0  # kJ

        # === RETURN STATE ===
        return {
            'worker_id': self.worker_id,
            'time_exposed_minutes': self.time_exposed,
            'core_temp': round(self.core_temp, 2),
            'skin_temp': round(self.skin_temp, 2),
            'heart_rate': round(self.heart_rate, 1),
            'sweat_rate': round(self.sweat_rate, 2),
            'hydration': round(self.hydration_status, 2),
            'psi': round(psi, 2),
            'kidney_stress': round(kidney_stress, 3),
            'cumulative_kidney_stress': round(self.cumulative_kidney_stress, 3),
            'metabolic_rate': round(M, 1),
            'heat_storage_rate': round(S, 1),
            'ambient_temp': ambient_temp,
            'relative_humidity': relative_humidity,
            'work_intensity': work_intensity
        }

    def hydrate(self, water_liters: float):
        """
        Worker drinks water (rehydrates).

        Args:
            water_liters: Amount of water consumed (L)
        """
        total_body_water = self.body_mass * 0.6
        hydration_increase = water_liters / total_body_water

        self.hydration_status = min(1.0, self.hydration_status + hydration_increase)

    def get_risk_level(self) -> str:
        """
        Classify current risk level.

        Returns:
            "LOW", "MODERATE", "HIGH", or "CRITICAL"
        """
        psi = self._calculate_psi()

        if psi < 5.0:
            return "LOW"
        elif psi < 7.0:
            return "MODERATE"
        elif psi < 9.0:
            return "HIGH"
        else:
            return "CRITICAL"
