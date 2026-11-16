"""
Environmental microclimate simulation for Abu Dhabi construction sites.

Simulates realistic diurnal temperature variations, humidity patterns,
and solar radiation for UAE summer conditions.
"""

import math
from typing import Dict
from datetime import datetime, time


class SiteEnvironment:
    """
    Simulates worksite environmental conditions in Abu Dhabi summer.

    Scenarios:
        - normal: Typical summer day (38°C, 45% RH)
        - extreme_heat: Heat wave conditions (47°C, 65% RH)
        - humidity_spike: High humidity day (42°C, 85% RH)
    """

    SCENARIOS = {
        "normal": {
            "base_temp": 38.0,  # °C
            "temp_variation": 8.0,  # °C diurnal swing
            "base_humidity": 45.0,  # % RH
            "humidity_variation": 20.0,  # % swing
            "max_solar": 900.0,  # W/m²
        },
        "extreme_heat": {
            "base_temp": 47.0,
            "temp_variation": 10.0,
            "base_humidity": 65.0,
            "humidity_variation": 15.0,
            "max_solar": 950.0,
        },
        "humidity_spike": {
            "base_temp": 42.0,
            "temp_variation": 6.0,
            "base_humidity": 85.0,
            "humidity_variation": 10.0,
            "max_solar": 700.0,  # Lower solar due to humidity/clouds
        },
    }

    def __init__(self, scenario: str = "extreme_heat"):
        """
        Initialize environment with specified scenario.

        Args:
            scenario: "normal", "extreme_heat", or "humidity_spike"
        """
        if scenario not in self.SCENARIOS:
            raise ValueError(f"Unknown scenario: {scenario}. Choose from {list(self.SCENARIOS.keys())}")

        self.scenario_name = scenario
        self.params = self.SCENARIOS[scenario]

    def get_conditions_at_time(self, hour_of_day: float) -> Dict[str, float]:
        """
        Get environmental conditions at a specific time of day.

        Realistic diurnal patterns:
        - Temperature: Minimum at 5 AM, maximum at 2 PM
        - Humidity: Inverse of temperature (high at night, low at peak heat)
        - Solar: Sunrise ~6 AM, peak at noon, sunset ~7 PM

        Args:
            hour_of_day: Hour in 24h format (0.0-24.0), e.g., 14.5 = 2:30 PM

        Returns:
            Dict with:
                ambient_temp (°C)
                relative_humidity (%)
                solar_radiation (W/m²)
                wbgt (°C) - Wet Bulb Globe Temperature
                heat_index (°C)
        """
        # === TEMPERATURE (sinusoidal with peak at 14:00) ===
        # Minimum at 5 AM (hour 5), maximum at 2 PM (hour 14)
        # Period = 24 hours, phase shift to align peak at 14:00

        hour_radians = ((hour_of_day - 5.0) / 24.0) * 2 * math.pi
        temp_factor = math.sin(hour_radians)  # -1 to 1

        # Map -1 to 1 → (base - variation) to (base + variation)
        base_temp = self.params["base_temp"]
        temp_swing = self.params["temp_variation"]

        ambient_temp = base_temp + (temp_factor * temp_swing / 2.0)

        # === HUMIDITY (inverse correlation with temperature) ===
        # High humidity at night (cool), low at peak heat
        base_humidity = self.params["base_humidity"]
        humidity_swing = self.params["humidity_variation"]

        # Inverse of temperature pattern
        humidity_factor = -temp_factor

        relative_humidity = base_humidity + (humidity_factor * humidity_swing / 2.0)
        relative_humidity = max(20, min(95, relative_humidity))  # Clamp to realistic range

        # === SOLAR RADIATION ===
        solar_radiation = self._calculate_solar_radiation(hour_of_day)

        # === WET BULB GLOBE TEMPERATURE (WBGT) ===
        wbgt = self._calculate_wbgt(ambient_temp, relative_humidity, solar_radiation)

        # === HEAT INDEX (Apparent Temperature) ===
        heat_index = self._calculate_heat_index(ambient_temp, relative_humidity)

        return {
            "hour_of_day": round(hour_of_day, 2),
            "ambient_temp": round(ambient_temp, 2),
            "relative_humidity": round(relative_humidity, 1),
            "solar_radiation": round(solar_radiation, 1),
            "wbgt": round(wbgt, 2),
            "heat_index": round(heat_index, 2),
        }

    def _calculate_solar_radiation(self, hour_of_day: float) -> float:
        """
        Calculate solar radiation based on sun position.

        Simplified model:
        - Sunrise: 6 AM
        - Peak: 12 PM (noon)
        - Sunset: 7 PM

        Args:
            hour_of_day: Hour in 24h format

        Returns:
            Solar radiation (W/m²)
        """
        sunrise = 6.0
        sunset = 19.0  # 7 PM
        solar_noon = 12.0

        # Outside daylight hours
        if hour_of_day < sunrise or hour_of_day > sunset:
            return 0.0

        # Solar elevation angle (simplified sine curve)
        # Peak at noon, zero at sunrise/sunset
        day_length = sunset - sunrise
        hour_from_sunrise = hour_of_day - sunrise
        solar_angle_factor = math.sin((hour_from_sunrise / day_length) * math.pi)

        # Maximum solar radiation
        max_solar = self.params["max_solar"]

        # Actual solar radiation
        solar_radiation = max_solar * solar_angle_factor

        return max(0, solar_radiation)

    def _calculate_wbgt(self, dry_bulb_temp: float, relative_humidity: float, solar_load: float) -> float:
        """
        Calculate Wet Bulb Globe Temperature (WBGT).

        WBGT is the ISO standard for heat stress assessment.

        Simplified formula for outdoor with solar radiation:
            WBGT = 0.7 × T_wb + 0.2 × T_g + 0.1 × T_db

        Where:
            T_wb = Wet bulb temperature (estimated from RH)
            T_g = Black globe temperature (accounts for radiant heat)
            T_db = Dry bulb temperature (ambient air temp)

        Args:
            dry_bulb_temp: Ambient air temperature (°C)
            relative_humidity: Relative humidity (%)
            solar_load: Solar radiation (W/m²)

        Returns:
            WBGT (°C)
        """
        T_db = dry_bulb_temp
        RH = relative_humidity

        # Estimate wet bulb temperature (simplified psychrometric formula)
        # T_wb ≈ T_db × atan(0.151977 × √(RH% + 8.313659)) + ...
        # Simplified: T_wb ≈ T_db - ((100 - RH) / 5) for hot conditions

        T_wb = T_db - ((100 - RH) / 5.0) * 0.3

        # Estimate black globe temperature (absorbs solar radiation)
        # T_g ≈ T_db + (solar_load / 100)
        T_g = T_db + (solar_load / 120.0)

        # WBGT formula (outdoor with sun)
        wbgt = 0.7 * T_wb + 0.2 * T_g + 0.1 * T_db

        return wbgt

    def _calculate_heat_index(self, temp_celsius: float, relative_humidity: float) -> float:
        """
        Calculate Heat Index (Apparent Temperature).

        Uses NOAA formula (Rothfusz 1990).

        Args:
            temp_celsius: Air temperature (°C)
            relative_humidity: Relative humidity (%)

        Returns:
            Heat index (°C)
        """
        # Convert to Fahrenheit for NOAA formula
        T_F = temp_celsius * 9/5 + 32
        RH = relative_humidity

        # Simple formula (for T >= 80°F)
        if T_F >= 80:
            HI = -42.379 + 2.04901523 * T_F + 10.14333127 * RH
            HI += -0.22475541 * T_F * RH
            HI += -6.83783e-3 * T_F**2
            HI += -5.481717e-2 * RH**2
            HI += 1.22874e-3 * T_F**2 * RH
            HI += 8.5282e-4 * T_F * RH**2
            HI += -1.99e-6 * T_F**2 * RH**2
        else:
            # Below 80°F, heat index ≈ temperature
            HI = T_F

        # Convert back to Celsius
        heat_index_celsius = (HI - 32) * 5/9

        return heat_index_celsius

    def get_daily_profile(self, start_hour: float = 8.0, duration_hours: float = 8.0, resolution_minutes: float = 60.0) -> list:
        """
        Get environmental conditions for an entire work shift.

        Args:
            start_hour: Shift start time (24h format, e.g., 8.0 = 8 AM)
            duration_hours: Shift duration (e.g., 8.0 hours)
            resolution_minutes: Time resolution (e.g., 60 = hourly samples)

        Returns:
            List of condition dictionaries at each timestep
        """
        profile = []

        timesteps = int((duration_hours * 60) / resolution_minutes)

        for i in range(timesteps + 1):
            current_hour = start_hour + (i * resolution_minutes / 60.0)
            conditions = self.get_conditions_at_time(current_hour)
            conditions['minutes_elapsed'] = i * resolution_minutes

            profile.append(conditions)

        return profile

    def get_work_intensity_profile(self, hour_of_day: float) -> float:
        """
        Get typical work intensity (met units) by time of day.

        Construction work patterns:
        - Morning (8-10 AM): Moderate work (3.0 met)
        - Late morning (10 AM-12 PM): Heavy work (4.0 met)
        - Midday break (12:30-3:30 PM): Rest/light work (1.5 met) - UAE mandatory
        - Afternoon (3:30-5 PM): Moderate work (3.0 met)
        - Late afternoon (5-6 PM): Light work (2.0 met) - winding down

        Args:
            hour_of_day: Hour in 24h format

        Returns:
            Work intensity (met units)
                1.0 = Resting
                2.0 = Light work (walking)
                3.0 = Moderate work (lifting, digging)
                4.0 = Heavy work (shoveling, carrying)
                5.0 = Very heavy work (sustained intense effort)
        """
        if hour_of_day < 8.0:
            return 1.0  # Pre-work rest

        elif 8.0 <= hour_of_day < 10.0:
            return 3.0  # Morning moderate work

        elif 10.0 <= hour_of_day < 12.5:
            return 4.0  # Late morning heavy work

        elif 12.5 <= hour_of_day < 15.5:
            # UAE MOHRE mandated midday break (12:30 PM - 3:30 PM)
            return 1.5  # Rest in shade, light activity

        elif 15.5 <= hour_of_day < 17.0:
            return 3.0  # Afternoon moderate work (resuming)

        elif 17.0 <= hour_of_day < 18.0:
            return 2.0  # Wind-down light work

        else:
            return 1.0  # Post-work rest

    def get_oshad_compliance_status(self, wbgt: float) -> Dict[str, any]:
        """
        Check OSHAD CoP 11.0 compliance for given WBGT.

        ADPHC OSHAD guidelines:
        - WBGT < 32°C: Normal work permitted
        - WBGT 32-35°C: Mandatory breaks, hydration monitoring
        - WBGT > 35°C: Work stoppage required

        Args:
            wbgt: Wet Bulb Globe Temperature (°C)

        Returns:
            Dict with compliance status and recommended actions
        """
        if wbgt < 32.0:
            status = "NORMAL"
            action = "Regular work permitted with standard hydration"
            risk_level = "LOW"

        elif 32.0 <= wbgt < 35.0:
            status = "CAUTION"
            action = "Mandatory 15-min breaks every 2 hours, increase hydration"
            risk_level = "MODERATE"

        elif wbgt >= 35.0:
            status = "WORK_STOPPAGE"
            action = "Stop outdoor work, move to air-conditioned area"
            risk_level = "HIGH"

        else:
            status = "UNKNOWN"
            action = "Unable to assess"
            risk_level = "UNKNOWN"

        return {
            "wbgt": wbgt,
            "compliance_status": status,
            "recommended_action": action,
            "risk_level": risk_level,
            "oshad_cop": "11.0 Version 4.0 (July 2024)"
        }
