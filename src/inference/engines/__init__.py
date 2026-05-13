'''
Inference Engines
=================
This package houses concrete implementations of inference strategies that derive
burnout and risk scores from processed data. It utilizes the Strategy Pattern,
a design approach that allows the system to seamlessly swap out different
evaluation algorithms (like deterministic MBI logic versus fuzzy logic) at
runtime without altering the internal code that leverages them.
'''
from .base_engine import BaseEngine
from .mbi_engine import MBIEngine
from .fuzzy_engine import FuzzyEngine

__all__ = ['BaseEngine', 'MBIEngine', 'FuzzyEngine']