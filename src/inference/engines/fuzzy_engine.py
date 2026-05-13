'''
Fuzzy Logic Engine
==================
This module implements the core FuzzyEngine, inheriting the BaseEngine Template
Method. It evaluates complex fuzzy logic rule sets against input data, computing
aggregate membership activation strengths and returning defuzzified centroid scores.
'''
import numpy as np
import pandas as pd
import skfuzzy as fuzz
from typing import cast, override

from data import Data
from ..fuzzy.variables import Variable
from .base_engine import BaseEngine

class FuzzyEngine(BaseEngine):
    '''
    Inference engine based on fuzzy logic.

    :ivar _input_variables: Dictionary of linguistic variables used as inputs.
    :vartype _input_variables: dict[str, Variable]
    :ivar _output_variable: The linguistic variable representing the output.
    :vartype _output_variable: Variable
    :ivar _rules: Tuple or list of fuzzy rules guiding the inference process.
    :vartype _rules: tuple[Rule, ...] | list[Rule]
    '''
    @property
    @override
    def results(self) -> pd.DataFrame:
        '''
        Get the inference results.

        :return: DataFrame containing Fuzzy engine results.
        '''
        return self._results

    @override
    def _init(self, meta: Data) -> None:
        '''
        Initialize the engine state for evaluation.

        :param meta: Application Data container.
        '''
        self._meta: Data = meta
        self._colnames: tuple[str, ...] = tuple(meta.variables.keys())
        self._results: pd.DataFrame = pd.DataFrame(columns=self._colnames)

    @override
    def _eval(self, data: pd.Series) -> pd.Series:
        '''
        Evaluate input Data, apply fuzzy inference and store results.

        :param data: Input Data containing features matching variable names.
        :type data: pd.Series
        :return: Pandas Series containing the fuzzified context and defuzzified result.
        :rtype: pd.Series
        :raises AssertionError: If the output variable is not properly initialized in Data.
        '''
        # Get output variable
        outvar: Variable | None = self._meta.outvar
        assert(outvar is not None)
        # Create context: Fuzzified input + output vars membership functions
        context: dict[str, dict[str, np.ndarray]] = {}
        # Loop through variable names
        for var in self._meta.variables.keys():
            # This excludes fuzzifiying output variable
            if var in data.index:
                # Fuzzify input data
                context[var] = self._meta.variables[var].fuzzify(
                    cast(
                        float | np.ndarray,
                        data[var]
                    )
                )
            elif (var == outvar.name):
                # Store output variable membership function
                context[var] = self._meta.variables[var].terms
        # Cache for rule activations
        activations: list[np.ndarray] = []
        for rule in self._meta.rules:
            # Append rule activation
            activations.append(
                rule.evaluate(context)
            )
        # Compute aggregation of rule activations (OR ALL)
        aggregated: float | np.ndarray =  cast(
            float | np.ndarray,
            np.fmax.reduce(activations)
        )
        # Compute result deffuzifiying
        result: float | np.ndarray = cast(
            float | np.ndarray,
            fuzz.defuzz(outvar.universe, aggregated, 'centroid')
        )
        # Return results and context, overwrite outvar mf with its evaluation and add new results column
        return pd.Series(context | {outvar.name: aggregated, 'RESULTS': result})

    @override
    def _append(self, results: pd.Series) -> None:
        '''
        Append a result row to the results DataFrame.

        :param results: Pandas Series containing row evaluation results.
        '''
        self._results = pd.concat([self._results, results.to_frame().T], ignore_index=True)