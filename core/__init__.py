"""
BioThermal Twin - Core Physics Simulation Module

Thermodynamic heat balance modeling for human workers in extreme heat.
Based on Gagge Two-Node model with individual variability.
"""

from .worker_simulation import WorkerPhysiology
from .environment import SiteEnvironment

__all__ = ['WorkerPhysiology', 'SiteEnvironment']
