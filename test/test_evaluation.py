'''
Tests for evaluation module.
'''
import pytest
import pandas as pd

from evaluation import Evaluator

def test_calculate_discrepancy() -> None:
    '''
    Test MAE and MSE calculations.

    Verify that the Evaluator correctly computes the Mean Absolute Error (MAE)
    and Mean Squared Error (MSE) between two sets of inference results.
    '''
    # Prepare dummy scores for comparison
    mbi_df: pd.DataFrame = pd.DataFrame({'mbi_score': [2.0, 4.0, 5.0]})
    fuzzy_df: pd.DataFrame = pd.DataFrame({'fuzzy_burnout_score': [2.5, 4.0, 4.0]})
    # Instantiate evaluator with score series
    evaluator: Evaluator = Evaluator(mbi_df['mbi_score'], fuzzy_df['fuzzy_burnout_score'])
    # Assert that metrics match expected statistical results
    assert(evaluator.mae == pytest.approx(0.5))
    assert(evaluator.mse == pytest.approx(1.25 / 3))

def test_calculate_discrepancy_empty() -> None:
    '''
    Test error metric calculation with missing data.

    Ensure that the Evaluator handles empty input series gracefully by
    returning zeroed metrics instead of crashing.
    '''
    # Prepare empty dataframes
    df1: pd.DataFrame = pd.DataFrame({'score1': []})
    df2: pd.DataFrame = pd.DataFrame({'score2': []})
    # Instantiate and verify zeroed state
    evaluator: Evaluator = Evaluator(df1['score1'], df2['score2'])
    assert(evaluator.mae == 0.0)
    assert(evaluator.mse == 0.0)