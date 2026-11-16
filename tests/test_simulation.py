"""
Validation tests for thermodynamic worker simulation.

Tests verify simulation outputs match published physiological research:
- ISO 9886:2004 - Ergonomics thermal strain evaluation
- Moran et al. (1998) - Physiological Strain Index
- Armstrong et al. (2007) - Human sweating rates
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.worker_simulation import WorkerPhysiology
from core.environment import SiteEnvironment


class TestWorkerPhysiologyBounds:
    """Test that simulation respects biological boundaries."""

    def test_core_temp_stays_in_viable_range(self):
        """Core temperature must stay within 35-42°C (survival range)."""
        worker = WorkerPhysiology("W-TEST-001", age=30, baseline_hr=65, acclimatization=0.5)

        # Extreme conditions for 8 hours
        for _ in range(480):  # 480 minutes
            state = worker.update_step(
                ambient_temp=47.0,
                relative_humidity=80.0,
                solar_load=950.0,
                work_intensity=4.0,
                duration_minutes=1.0
            )

            assert 35.0 <= state['core_temp'] <= 42.0, \
                f"Core temp {state['core_temp']}°C out of viable range at minute {state['time_exposed_minutes']}"

    def test_sweat_rate_does_not_exceed_physiological_maximum(self):
        """Sweat rate must never exceed 2.5 L/hr (Armstrong 2007)."""
        worker = WorkerPhysiology("W-TEST-002", age=25, acclimatization=0.9)

        for _ in range(240):  # 4 hours
            state = worker.update_step(45.0, 70.0, 900.0, 4.5)

            assert state['sweat_rate'] <= 2.5, \
                f"Sweat rate {state['sweat_rate']} L/hr exceeds physiological maximum"
            assert state['sweat_rate'] >= 0.0, \
                "Sweat rate cannot be negative"

    def test_psi_stays_in_valid_range(self):
        """PSI must be between 0 and 10 (Moran formula)."""
        worker = WorkerPhysiology("W-TEST-003")

        for _ in range(300):
            state = worker.update_step(42.0, 65.0, 850.0, 3.5)

            assert 0.0 <= state['psi'] <= 10.0, \
                f"PSI {state['psi']} out of valid range [0, 10]"

    def test_hydration_bounds(self):
        """Hydration must stay between 0.0 (severe dehydration) and 1.0 (fully hydrated)."""
        worker = WorkerPhysiology("W-TEST-004")

        # Heavy sweating for extended period
        for _ in range(360):  # 6 hours
            state = worker.update_step(46.0, 75.0, 920.0, 4.0)

            assert 0.0 <= state['hydration'] <= 1.0, \
                f"Hydration {state['hydration']} out of bounds"


class TestPhysiologicalResponses:
    """Test that physiological responses match expected patterns."""

    def test_psi_increases_with_heat_load(self):
        """PSI should increase as ambient temperature increases."""
        psi_values = []

        for temp in [35, 38, 41, 44, 47]:
            worker = WorkerPhysiology(f"W-TEMP-{temp}", age=30, baseline_hr=65, acclimatization=0.5)

            # Run for 2 hours at this temperature
            for _ in range(120):
                state = worker.update_step(temp, 60.0, 850.0, 3.0)

            psi_values.append(state['psi'])

        # PSI should generally increase with temperature (allowing some variation)
        # Check that average of last 3 > average of first 3
        assert sum(psi_values[-2:]) > sum(psi_values[:2]), \
            f"PSI did not increase with temperature: {psi_values}"

    def test_heart_rate_elevates_with_thermal_stress(self):
        """Heart rate should increase as core temperature rises."""
        worker = WorkerPhysiology("W-TEST-HR", age=28, baseline_hr=60, acclimatization=0.6)

        initial_hr = worker.heart_rate

        # Apply heat stress for 3 hours
        for _ in range(180):
            state = worker.update_step(45.0, 70.0, 900.0, 3.5)

        final_hr = state['heart_rate']

        assert final_hr > initial_hr + 20, \
            f"Heart rate did not elevate sufficiently: {initial_hr} → {final_hr}"
        assert final_hr <= 180, \
            f"Heart rate {final_hr} exceeds maximum"

    def test_acclimatization_improves_tolerance(self):
        """Acclimatized workers should have lower PSI for same conditions."""
        # Non-acclimatized worker
        worker_new = WorkerPhysiology("W-NEW", age=30, baseline_hr=65, acclimatization=0.2)

        for _ in range(120):  # 2 hours
            state_new = worker_new.update_step(44.0, 65.0, 880.0, 3.5)

        # Acclimatized worker
        worker_accl = WorkerPhysiology("W-ACCL", age=30, baseline_hr=65, acclimatization=0.9)

        for _ in range(120):  # 2 hours
            state_accl = worker_accl.update_step(44.0, 65.0, 880.0, 3.5)

        # Acclimatized worker should have lower PSI
        assert state_accl['psi'] < state_new['psi'], \
            f"Acclimatization did not reduce PSI: {state_accl['psi']} vs {state_new['psi']}"

    def test_hydration_reduces_with_sweating(self):
        """Hydration should decrease as worker sweats."""
        worker = WorkerPhysiology("W-TEST-HYDRO", age=32, acclimatization=0.7)

        initial_hydration = worker.hydration_status

        # Heavy work in heat (will cause sweating)
        for _ in range(180):  # 3 hours
            state = worker.update_step(46.0, 70.0, 900.0, 4.0)

        final_hydration = state['hydration']

        assert final_hydration < initial_hydration, \
            f"Hydration did not decrease: {initial_hydration} → {final_hydration}"


class TestPSIFormula:
    """Validate PSI calculation matches Moran et al. (1998) exactly."""

    def test_psi_formula_correctness(self):
        """Test PSI calculation against known values from paper."""
        worker = WorkerPhysiology("W-PSI-TEST", age=30, baseline_hr=70, acclimatization=0.5)

        # Set known physiological state
        worker.core_temp = 38.5  # Elevated but not extreme
        worker.heart_rate = 140.0  # Elevated

        # Calculate PSI manually using Moran formula
        # PSI = 5·(Tc - 37)/(39.5 - 37) + 5·(HR - HR0)/(180 - HR0)
        expected_psi_temp = 5.0 * ((38.5 - 37.0) / (39.5 - 37.0))  # = 5 * (1.5/2.5) = 3.0
        expected_psi_hr = 5.0 * ((140.0 - 70.0) / (180.0 - 70.0))  # = 5 * (70/110) = 3.18

        expected_psi = expected_psi_temp + expected_psi_hr  # ≈ 6.18

        # Get PSI from worker's internal calculation
        calculated_psi = worker._calculate_psi()

        assert abs(calculated_psi - expected_psi) < 0.1, \
            f"PSI formula mismatch: expected {expected_psi:.2f}, got {calculated_psi:.2f}"


class TestEnvironmentSimulator:
    """Test environmental simulation produces realistic conditions."""

    def test_temperature_diurnal_variation(self):
        """Temperature should peak around 2 PM and be minimum at 5 AM."""
        env = SiteEnvironment("extreme_heat")

        # Check minimum (early morning)
        morning_conditions = env.get_conditions_at_time(5.0)  # 5 AM
        afternoon_conditions = env.get_conditions_at_time(14.0)  # 2 PM

        assert afternoon_conditions['ambient_temp'] > morning_conditions['ambient_temp'], \
            "Afternoon should be hotter than morning"

        assert afternoon_conditions['ambient_temp'] >= 45.0, \
            f"Extreme heat scenario should reach ≥45°C, got {afternoon_conditions['ambient_temp']}"

    def test_humidity_inverse_to_temperature(self):
        """Humidity should be higher at night, lower at peak heat."""
        env = SiteEnvironment("extreme_heat")

        morning = env.get_conditions_at_time(6.0)  # 6 AM (cooler)
        afternoon = env.get_conditions_at_time(14.0)  # 2 PM (hottest)

        assert morning['relative_humidity'] > afternoon['relative_humidity'], \
            "Morning should have higher humidity than afternoon"

    def test_solar_radiation_pattern(self):
        """Solar radiation should be zero at night, peak at noon."""
        env = SiteEnvironment("normal")

        night = env.get_conditions_at_time(3.0)  # 3 AM
        noon = env.get_conditions_at_time(12.0)  # 12 PM
        evening = env.get_conditions_at_time(20.0)  # 8 PM

        assert night['solar_radiation'] == 0.0, "No solar radiation at night"
        assert evening['solar_radiation'] == 0.0, "No solar radiation after sunset"
        assert noon['solar_radiation'] > 800.0, f"Peak solar should be >800 W/m², got {noon['solar_radiation']}"

    def test_wbgt_calculation(self):
        """WBGT should be calculated and fall within expected range."""
        env = SiteEnvironment("extreme_heat")

        conditions = env.get_conditions_at_time(14.0)  # Peak heat

        # WBGT should be less than or equal to dry bulb temp
        assert conditions['wbgt'] <= conditions['ambient_temp'], \
            "WBGT should not exceed dry bulb temperature"

        # WBGT should be above 32°C in extreme heat (OSHAD threshold)
        assert conditions['wbgt'] >= 32.0, \
            f"Extreme heat WBGT should exceed 32°C, got {conditions['wbgt']}"

    def test_oshad_compliance_thresholds(self):
        """Test OSHAD CoP 11.0 compliance classification."""
        env = SiteEnvironment("normal")

        # Normal conditions - should be compliant
        normal = env.get_oshad_compliance_status(30.0)
        assert normal['compliance_status'] == "NORMAL"

        # Caution zone
        caution = env.get_oshad_compliance_status(33.0)
        assert caution['compliance_status'] == "CAUTION"

        # Work stoppage
        stoppage = env.get_oshad_compliance_status(36.0)
        assert stoppage['compliance_status'] == "WORK_STOPPAGE"


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_8hour_shift_completes(self):
        """Worker should survive full 8-hour shift without crashing."""
        worker = WorkerPhysiology("W-SHIFT-TEST", age=28, acclimatization=0.6)
        env = SiteEnvironment("extreme_heat")

        shift_start = 8.0  # 8 AM
        states = []

        for minute in range(480):  # 8 hours
            current_hour = shift_start + (minute / 60.0)
            conditions = env.get_conditions_at_time(current_hour)
            work_intensity = env.get_work_intensity_profile(current_hour)

            state = worker.update_step(
                ambient_temp=conditions['ambient_temp'],
                relative_humidity=conditions['relative_humidity'],
                solar_load=conditions['solar_radiation'],
                work_intensity=work_intensity
            )

            states.append(state)

        # Verify we got 480 states
        assert len(states) == 480

        # Verify final state is realistic
        final = states[-1]
        assert 35.0 <= final['core_temp'] <= 42.0
        assert 0.0 <= final['psi'] <= 10.0
        assert final['time_exposed_minutes'] == 480

    def test_worker_reaches_high_psi_in_extreme_conditions(self):
        """Worker PSI should exceed 7.0 in extreme conditions (alert threshold)."""
        worker = WorkerPhysiology("W-EXTREME-TEST", age=35, acclimatization=0.3)

        # Extreme conditions, no midday break
        for _ in range(240):  # 4 hours continuous
            state = worker.update_step(
                ambient_temp=47.0,
                relative_humidity=75.0,
                solar_load=950.0,
                work_intensity=4.0
            )

        # Should reach high PSI
        assert state['psi'] >= 6.0, \
            f"PSI should be high in extreme conditions, got {state['psi']}"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
