'''
Base Inference Engine
=====================
This module provides the foundational architecture for all inference engines
in the application. It employs the Template Method design pattern to dictate
the generic, step-by-step algorithm for processing data row by row during
evaluation. Child classes inherit this base and override specific hooks
(initialization, single-row evaluation, and result storage) to inject their
own distinct logic.
'''
import pandas as pd
from typing import cast
from abc import ABC, abstractmethod
from collections.abc import Callable

from data import Data

class BaseEngine(ABC):
    '''
    Abstract base class for inference engines.

    :ivar _meta: Reference to the application's Data container for evaluating rules.
    :vartype _meta: Data
    :ivar _results: Cached pandas DataFrame containing the computed inference results.
    :vartype _results: pd.DataFrame
    :ivar _colnames: Tuple of variable names forming the columns of the results table.
    :vartype _colnames: tuple[str, ...]
    '''
    @property
    @abstractmethod
    def results(self) -> pd.DataFrame:
        pass # pragma: no cover

    @abstractmethod
    def _init(self, meta: Data) -> None:
        '''
        Initialize required data structures for the evaluation process.

        :param meta: Application Data container.
        :type meta: Data
        '''
        pass # pragma: no cover

    @abstractmethod
    def _eval(self, data: pd.Series) -> pd.Series:
        '''
        Evaluate a single row or subset of data.

        :param data: Pandas Series containing row data.
        :type data: pd.Series
        :return: Pandas Series containing evaluation results for the row.
        :rtype: pd.Series
        '''
        pass # pragma: no cover

    @abstractmethod
    def _append(self, results: pd.Series) -> None:
        '''
        Store or append the results of a single row evaluation.

        :param results: Pandas Series containing row evaluation results.
        :type results: pd.Series
        '''
        pass # pragma: no cover

    def evaluate(self, data: Data, progress_fn: Callable[[int, int], None] | None=None) -> None:
        '''
        Evaluate input data and store results.

        :param data: Input Data containing raw/processed data.
        :type data: Data
        :param progress_fn: Optional callback for reporting progress (current, total).
        :type progress_fn: Callable[[int, int], None] | None
        '''
        # Total rows
        ix, nrows = 0, len(data.data)
        # Initialize results attribute
        self._init(data)
        # Iter through each row of results
        for _, row in data.data.iterrows():
            # Update progress, if any
            if progress_fn: progress_fn(ix, nrows)
            # Evaluate the row and append results
            self._append(
                self._eval(row)
            )
            # Increase counter
            ix += 1
        # Update progress to completion
        if progress_fn: progress_fn(nrows, nrows)
        # Store results
        data.store(self.results, cast(type[object], self))