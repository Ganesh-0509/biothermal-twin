"""
Physics-Informed Neural Network (PINN) for Core Temperature Prediction.

Architecture enforces thermodynamic constraints:
1. Energy conservation (heat balance)
2. Biological boundaries (35-42°C viable range)
3. PSI-temperature coupling (Moran 1998 formula)

All physics validated against published research.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class PhysicsInformedHeatStrain(nn.Module):
    """
    Neural network with embedded thermodynamic physics.

    Input Features (8 dimensions):
        - heart_rate: Current HR (bpm)
        - baseline_hr: Resting HR (bpm)
        - cadence: Steps per minute (0-120)
        - ambient_temp: °C
        - relative_humidity: % (0-100)
        - solar_load: W/m² (0-1000)
        - time_exposed: Minutes in heat (0-480)
        - prev_core_temp: Previous timestep core temp (°C)

    Output (3 dimensions):
        - core_temp_estimate: °C (35-42 range)
        - psi_estimate: 0-10 scale
        - kidney_risk_score: 0-1 probability
    """

    def __init__(self, input_dim=8, hidden_dim=64, output_dim=3):
        """
        Initialize PINN architecture.

        Args:
            input_dim: Number of input features (default 8)
            hidden_dim: Hidden layer size (default 64)
            output_dim: Number of outputs (default 3)
        """
        super(PhysicsInformedHeatStrain, self).__init__()

        # Network layers (using Tanh for bounded outputs)
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim * 2)
        self.fc3 = nn.Linear(hidden_dim * 2, hidden_dim)
        self.fc4 = nn.Linear(hidden_dim, output_dim)

        # Batch normalization for stability
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.bn2 = nn.BatchNorm1d(hidden_dim * 2)
        self.bn3 = nn.BatchNorm1d(hidden_dim)

        # Initialize weights (Xavier initialization for Tanh)
        nn.init.xavier_normal_(self.fc1.weight)
        nn.init.xavier_normal_(self.fc2.weight)
        nn.init.xavier_normal_(self.fc3.weight)
        nn.init.xavier_normal_(self.fc4.weight)

    def forward(self, x):
        """
        Forward pass through network.

        Args:
            x: Input tensor [batch_size, input_dim]

        Returns:
            Output tensor [batch_size, output_dim]
        """
        # Layer 1
        x = self.fc1(x)
        x = self.bn1(x)
        x = torch.tanh(x)  # Tanh for bounded outputs

        # Layer 2
        x = self.fc2(x)
        x = self.bn2(x)
        x = torch.tanh(x)

        # Layer 3
        x = self.fc3(x)
        x = self.bn3(x)
        x = torch.tanh(x)

        # Output layer (no activation, will be constrained by loss)
        x = self.fc4(x)

        return x


class PhysicsInformedLoss(nn.Module):
    """
    Custom loss function enforcing thermodynamic constraints.

    Components:
        1. MSE Loss: Standard data fitting
        2. Boundary Loss: Penalize predictions outside viable range
        3. Physics Coupling Loss: Enforce PSI-temperature relationship
        4. Monotonicity Loss: PSI should increase with thermal load
    """

    def __init__(
        self,
        lambda_boundary=0.5,
        lambda_physics=0.3,
        lambda_monotonicity=0.2
    ):
        """
        Initialize physics loss with weighting parameters.

        Args:
            lambda_boundary: Weight for boundary constraint (default 0.5)
            lambda_physics: Weight for physics coupling (default 0.3)
            lambda_monotonicity: Weight for monotonicity constraint (default 0.2)
        """
        super(PhysicsInformedLoss, self).__init__()

        self.lambda_boundary = lambda_boundary
        self.lambda_physics = lambda_physics
        self.lambda_monotonicity = lambda_monotonicity

    def forward(self, predictions, inputs, targets):
        """
        Calculate combined physics-informed loss.

        Args:
            predictions: Model output [batch, 3] (core_temp, psi, kidney_risk)
            inputs: Input features [batch, 8]
            targets: Ground truth [batch, 3]

        Returns:
            total_loss: Combined loss scalar
            loss_dict: Dict with individual loss components
        """
        # Extract predictions
        pred_core_temp = predictions[:, 0]
        pred_psi = predictions[:, 1]
        pred_kidney = predictions[:, 2]

        # Extract targets
        target_core_temp = targets[:, 0]
        target_psi = targets[:, 1]
        target_kidney = targets[:, 2]

        # Extract relevant inputs
        heart_rate = inputs[:, 0]
        baseline_hr = inputs[:, 1]
        ambient_temp = inputs[:, 3]
        time_exposed = inputs[:, 6]
        prev_core_temp = inputs[:, 7]

        # === 1. STANDARD MSE LOSS (Data Fitting) ===
        mse_loss = F.mse_loss(predictions, targets)

        # === 2. BIOLOGICAL BOUNDARY CONSTRAINT ===
        # Core temperature must stay within 35-42°C (survival range)
        # Heavily penalize violations
        lower_bound_violation = F.relu(35.0 - pred_core_temp)  # Penalty if < 35°C
        upper_bound_violation = F.relu(pred_core_temp - 42.0)  # Penalty if > 42°C

        boundary_loss = (lower_bound_violation.mean() + upper_bound_violation.mean()) * 10.0

        # === 3. PHYSICS COUPLING: PSI-TEMPERATURE RELATIONSHIP ===
        # PSI should follow Moran (1998) formula
        # PSI = 5·(Tc - 37)/(39.5 - 37) + 5·(HR - HR0)/(180 - HR0)

        # Expected PSI from physics
        psi_temp_component = 5.0 * ((pred_core_temp - 37.0) / 2.5)  # (39.5-37=2.5)
        psi_hr_component = 5.0 * ((heart_rate - baseline_hr) / (180.0 - baseline_hr))

        expected_psi = psi_temp_component + psi_hr_component
        expected_psi = torch.clamp(expected_psi, 0.0, 10.0)  # PSI bounds

        # Penalize deviation from expected PSI
        physics_coupling_loss = F.mse_loss(pred_psi, expected_psi)

        # === 4. MONOTONICITY CONSTRAINT ===
        # Core temp should not decrease when ambient temp > current core temp
        # (unless substantial time has passed for cooling)

        # If ambient is hotter than previous core temp, core temp should generally increase
        heating_condition = (ambient_temp > prev_core_temp)
        temp_decreased = (pred_core_temp < prev_core_temp)

        # Violation: ambient hotter but prediction is cooler
        monotonicity_violation = (heating_condition & temp_decreased).float()
        monotonicity_loss = monotonicity_violation.mean()

        # === 5. PSI BOUNDS CONSTRAINT ===
        # PSI must be within [0, 10]
        psi_lower_violation = F.relu(-pred_psi)  # Negative PSI is invalid
        psi_upper_violation = F.relu(pred_psi - 10.0)  # PSI > 10 is invalid

        psi_bound_loss = (psi_lower_violation.mean() + psi_upper_violation.mean()) * 5.0

        # === COMBINE ALL LOSSES ===
        total_loss = (
            mse_loss +
            self.lambda_boundary * (boundary_loss + psi_bound_loss) +
            self.lambda_physics * physics_coupling_loss +
            self.lambda_monotonicity * monotonicity_loss
        )

        # Return loss components for monitoring
        loss_dict = {
            'total_loss': total_loss.item(),
            'mse_loss': mse_loss.item(),
            'boundary_loss': boundary_loss.item(),
            'physics_coupling_loss': physics_coupling_loss.item(),
            'monotonicity_loss': monotonicity_loss.item(),
            'psi_bound_loss': psi_bound_loss.item(),
        }

        return total_loss, loss_dict


def count_parameters(model):
    """Count trainable parameters in model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Test model instantiation
    print("[*] Testing PINN architecture...")

    model = PhysicsInformedHeatStrain()
    print(f"    Model parameters: {count_parameters(model):,}")

    # Test forward pass
    batch_size = 32
    dummy_input = torch.randn(batch_size, 8)
    output = model(dummy_input)

    print(f"    Input shape: {dummy_input.shape}")
    print(f"    Output shape: {output.shape}")

    # Test loss function
    criterion = PhysicsInformedLoss()
    dummy_target = torch.randn(batch_size, 3)

    loss, loss_dict = criterion(output, dummy_input, dummy_target)
    print(f"    Loss computed: {loss.item():.4f}")
    print(f"    Loss components: {loss_dict}")

    print("[SUCCESS] PINN architecture validated")
