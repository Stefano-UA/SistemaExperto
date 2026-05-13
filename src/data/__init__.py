'''
Data Management Package
=======================
This package provides a centralized container and robust parsers for loading, validating,
and managing all domain-specific data sets, mapping configurations, fuzzy linguistic
variables, and logic rules required by the application.
'''
from .data import Data

__all__ = ['Data']