'''
Evaluation metrics module.
'''
import numpy as np
import pandas as pd

class Evaluator:
    '''
    Compare engine results.
    '''
    def __init__(self, x_results: pd.DataFrame | pd.Series, y_results: pd.DataFrame | pd.Series) -> None:
        '''
        Initialize the Evaluator.

        :param x_results: First set of results.
        :param y_results: Second set of results.
        '''
        # Ensure we are working with numpy arrays for computations
        self._x_scores: np.ndarray = np.array(x_results)
        self._y_scores: np.ndarray = np.array(y_results)

    @property
    def mae(self) -> float:
        '''
        Calculate Mean Absolute Error.

        :return: MAE score.
        '''
        if (self._x_scores.size == 0) or (self._y_scores.size == 0):
            return 0.0
        return float(np.mean(np.abs(self._x_scores - self._y_scores)))

    @property
    def mse(self) -> float:
        '''
        Calculate Mean Squared Error.

        :return: MSE score.
        '''
        if (self._x_scores.size == 0) or (self._y_scores.size == 0):
            return 0.0
        return float(np.mean((self._x_scores - self._y_scores) ** 2))
