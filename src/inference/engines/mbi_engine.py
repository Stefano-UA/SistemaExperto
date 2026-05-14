'''
Deterministic MBI Engine
========================
This module implements the MBIEngine, inheriting the BaseEngine Template Method.
It evaluates raw data using standard deterministic Maslach Burnout Inventory
thresholds to output categorical risk classifications ('Low', 'Mid', 'High').
'''
import pandas as pd
from typing import override

from data import Data
from .base_engine import BaseEngine

class MBIEngine(BaseEngine):
    '''
    Inference engine based on Maslach Burnout Inventory deterministic rules.

    :cvar ranges: Dictionary mapping MBI dimension groups to their range delimiters for discerning between 'Low', 'Mid' and 'High'
    :vartype ranges: dict[str, tuple[float, float]]
    '''
    ranges: dict[str, tuple[float, float]] = {
        'AgotamientoEmocional': (11.25, 33.75), # Max 45 in our case
        'Despersonalizacion': (6.25, 18.75), # Max 25 in our case
        'RealizacionPersonal': (10, 30) # Max 40 in our case
    } # Set based on 25 and 75 percentiles

    @property
    @override
    def results(self) -> pd.DataFrame:
        '''
        Get the inference results.

        :return: DataFrame containing MBI results.
        '''
        return self._results

    @override
    def _init(self, meta: Data) -> None:
        '''
        Initialize the engine state for evaluation.

        :param meta: Application Data container.
        '''
        self._results = pd.DataFrame(columns=['mbi_score', 'mbi_risk_level'])

    @override
    def _eval(self, data: pd.Series) -> pd.Series:
        '''
        Evaluate a single data row to determine the MBI risk level.

        :param data: Pandas Series containing row data for each dimension.
        :return: Pandas Series containing the 'mbi_risk_level'.
        '''
        # Values dictionary
        vals: dict[str, str] = {}
        # Loop through MBI ranges
        for key,range in type(self).ranges.items():
            # Get classification
            if (data[key] < range[0]):
                vals[key] = 'Low'
            elif (data[key] <= range[1]):
                vals[key] = 'Mid'
            else:
                vals[key] = 'High'
        # Calculate numeric score for comparison mapping (out of 100)
        # Max values: AE(45), D(25), RP(40 - inverted)
        normalized_ae = (data['AgotamientoEmocional'] / 45.0) * 100
        normalized_d = (data['Despersonalizacion'] / 25.0) * 100
        normalized_rp = ((40.0 - data['RealizacionPersonal']) / 40.0) * 100
        mbi_score = (normalized_ae + normalized_d + normalized_rp) / 3.0
        # High risk level
        if (vals['AgotamientoEmocional'] == 'High'):
            if (vals['Despersonalizacion'] == 'High'):
                if (vals['RealizacionPersonal'] == 'Low'):
                    return pd.Series({'mbi_score': mbi_score, 'mbi_risk_level': 'High'})
        # Low risk level
        if (vals['AgotamientoEmocional'] == 'Low'):
            if (vals['Despersonalizacion'] == 'Low'):
                if (vals['RealizacionPersonal'] == 'High'):
                    return pd.Series({'mbi_score': mbi_score, 'mbi_risk_level': 'Low'})
        # Mid risk level
        return pd.Series({'mbi_score': mbi_score, 'mbi_risk_level': 'Mid'})

    @override
    def _append(self, results: pd.Series) -> None:
        '''
        Append a result row to the results DataFrame.

        :param results: Pandas Series containing row evaluation results.
        '''
        self._results = pd.concat([self._results, results.to_frame().T], ignore_index=True)
