"""
Synthetic data generation for PINN training.

Generates thermodynamically accurate training data by running
100 simulated workers through 8-hour shifts in various conditions.

Output: 48,000 datapoints (100 workers × 480 minutes)
"""

import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import random

from worker_simulation import WorkerPhysiology
from environment import SiteEnvironment


def generate_worker_cohort(num_workers: int = 100) -> List[WorkerPhysiology]:
    """
    Generate cohort of workers with realistic demographic variability.

    Args:
        num_workers: Number of workers to generate

    Returns:
        List of WorkerPhysiology instances
    """
    workers = []

    for i in range(num_workers):
        worker_id = f"W-{i+1:05d}"  # W-00001, W-00002, ...

        # Realistic demographic distributions
        age = int(random.triangular(22, 45, 32))  # Most workers 28-35
        bmi = random.gauss(24.0, 2.5)  # Normal distribution around 24
        bmi = max(20.0, min(28.0, bmi))  # Clamp to realistic range

        baseline_hr = int(random.gauss(65, 8))  # Normal distribution
        baseline_hr = max(55, min(75, baseline_hr))

        # Acclimatization: bimodal distribution (new workers vs. experienced)
        if random.random() < 0.3:  # 30% are new/poorly acclimatized
            acclimatization = random.uniform(0.1, 0.4)
        else:  # 70% are experienced
            acclimatization = random.uniform(0.5, 0.9)

        worker = WorkerPhysiology(
            worker_id=worker_id,
            age=age,
            bmi=bmi,
            baseline_hr=baseline_hr,
            acclimatization=acclimatization
        )

        workers.append(worker)

    return workers


def run_worker_shift(
    worker: WorkerPhysiology,
    environment: SiteEnvironment,
    start_hour: float = 8.0,
    duration_minutes: int = 480
) -> List[Dict]:
    """
    Simulate one worker through complete shift.

    Args:
        worker: WorkerPhysiology instance
        environment: SiteEnvironment instance
        start_hour: Shift start time (8.0 = 8 AM)
        duration_minutes: Shift duration (480 = 8 hours)

    Returns:
        List of state dictionaries (one per minute)
    """
    states = []

    for minute in range(duration_minutes):
        current_hour = start_hour + (minute / 60.0)

        # Get environmental conditions
        conditions = environment.get_conditions_at_time(current_hour)

        # Get work intensity for this hour
        work_intensity = environment.get_work_intensity_profile(current_hour)

        # Update worker state
        state = worker.update_step(
            ambient_temp=conditions['ambient_temp'],
            relative_humidity=conditions['relative_humidity'],
            solar_load=conditions['solar_radiation'],
            work_intensity=work_intensity,
            duration_minutes=1.0
        )

        # Add environmental context to state
        state.update({
            'minute_of_shift': minute,
            'hour_of_day': current_hour,
            'wbgt': conditions['wbgt'],
            'heat_index': conditions['heat_index'],
            'work_intensity_met': work_intensity,
        })

        states.append(state)

    return states


def generate_dataset(
    num_workers: int = 100,
    scenarios: List[str] = None,
    output_dir: str = "data"
) -> Dict[str, any]:
    """
    Generate complete training dataset.

    Args:
        num_workers: Number of workers to simulate
        scenarios: Environmental scenarios to include (default: all 3)
        output_dir: Directory to save output files

    Returns:
        Dict with generation statistics
    """
    if scenarios is None:
        scenarios = ["normal", "extreme_heat", "humidity_spike"]

    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"[*] Generating synthetic dataset...")
    print(f"    Workers: {num_workers}")
    print(f"    Scenarios: {scenarios}")
    print(f"    Output: {output_dir}/")

    all_data = []
    worker_profiles = []

    for scenario in scenarios:
        print(f"\n[*] Scenario: {scenario}")

        # Create environment
        env = SiteEnvironment(scenario)

        # Generate worker cohort
        workers = generate_worker_cohort(num_workers)

        # Run each worker through shift
        for idx, worker in enumerate(workers, 1):
            if idx % 10 == 0:
                print(f"   Processing worker {idx}/{num_workers}...")

            # Run shift
            shift_data = run_worker_shift(worker, env)

            # Add scenario label
            for state in shift_data:
                state['scenario'] = scenario

            all_data.extend(shift_data)

            # Store worker profile
            worker_profile = {
                'worker_id': worker.worker_id,
                'age': worker.age,
                'bmi': worker.bmi,
                'baseline_hr': worker.baseline_hr,
                'acclimatization': worker.acclimatization,
                'body_mass_kg': worker.body_mass,
                'scenario': scenario
            }
            worker_profiles.append(worker_profile)

    # Save to CSV
    csv_path = output_path / "synthetic_telemetry.csv"
    print(f"\n[*] Saving telemetry data to {csv_path}...")

    fieldnames = list(all_data[0].keys())
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    # Save worker profiles to JSON
    json_path = output_path / "worker_profiles.json"
    print(f"[*] Saving worker profiles to {json_path}...")

    with open(json_path, 'w') as f:
        json.dump(worker_profiles, f, indent=2)

    # Generate metadata
    metadata = {
        'generated_at': datetime.now().isoformat(),
        'num_workers': num_workers,
        'scenarios': scenarios,
        'total_datapoints': len(all_data),
        'shift_duration_minutes': 480,
        'resolution_minutes': 1,
        'datapoints_per_worker': 480,
        'core_temp_range': {
            'min': min(d['core_temp'] for d in all_data),
            'max': max(d['core_temp'] for d in all_data),
            'mean': sum(d['core_temp'] for d in all_data) / len(all_data)
        },
        'psi_range': {
            'min': min(d['psi'] for d in all_data),
            'max': max(d['psi'] for d in all_data),
            'mean': sum(d['psi'] for d in all_data) / len(all_data)
        },
        'validation': {
            'core_temp_within_bounds': all(35 <= d['core_temp'] <= 42 for d in all_data),
            'psi_within_bounds': all(0 <= d['psi'] <= 10 for d in all_data),
            'sweat_rate_within_bounds': all(0 <= d['sweat_rate'] <= 2.5 for d in all_data)
        }
    }

    metadata_path = output_path / "dataset_metadata.json"
    print(f"[*] Saving metadata to {metadata_path}...")

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Generate summary statistics
    print(f"\n[SUCCESS] Dataset generation complete!")
    print(f"    Total datapoints: {len(all_data):,}")
    print(f"    Core temp range: {metadata['core_temp_range']['min']:.2f} - {metadata['core_temp_range']['max']:.2f} C")
    print(f"    PSI range: {metadata['psi_range']['min']:.2f} - {metadata['psi_range']['max']:.2f}")
    print(f"    Validation: {'PASS' if all(metadata['validation'].values()) else 'FAIL'}")

    return metadata


if __name__ == "__main__":
    # Generate dataset
    metadata = generate_dataset(
        num_workers=100,
        scenarios=["normal", "extreme_heat", "humidity_spike"],
        output_dir="data"
    )

    print(f"\n[*] Output files:")
    print(f"    data/synthetic_telemetry.csv  ({metadata['total_datapoints']:,} rows)")
    print(f"    data/worker_profiles.json  ({metadata['num_workers'] * len(metadata['scenarios'])} profiles)")
    print(f"    data/dataset_metadata.json")
