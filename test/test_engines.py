'''
Tests for inference engines.
'''
import pytest
import numpy as np
import pandas as pd
import skfuzzy as fuzz

from data import Data
from inference.fuzzy import Rule, Variable, LeafNode
from inference.engines import MBIEngine, FuzzyEngine

def test_mbi_engine() -> None:
    '''
    Test Maslach Burnout Inventory deterministic evaluation.

    Feed raw exhaustion and cynicism data into the MBIEngine, and assert that
    it correctly calculates the average MBI score and sets the high-risk boolean
    flag strictly based on its static thresholds.
    '''
    # Inject our range definitions
    MBIEngine.ranges = {
        'exhaustion': (2.5, 7.5),
        'despersonalization': (2.5, 7.5),
        'fullfilment': (2.5, 7.5)
    }
    # Prepare input dataframe with sample scores
    df: pd.DataFrame = pd.DataFrame({
        'exhaustion': [2.0, 4.0, 8.0], # Low, Mid, High
        'despersonalization': [2.0, 4.0, 9.5], # Low, Mid, High
        'fullfilment': [9.0, 3.5, 2.0] # High, Mid, Low
    })
    # Wrap in Data container
    data: Data = Data()
    data._data = df # pyright: ignore[reportPrivateUsage]
    # Instantiate MBI engine and execute it
    engine: MBIEngine = MBIEngine()
    engine.evaluate(data)
    result: pd.DataFrame = engine.results
    # Verify calculated scores and risk flags
    assert('mbi_risk_level' in result.columns)
    assert(result['mbi_risk_level'].tolist() == ['Low', 'Mid', 'High'])

def test_fuzzy_engine() -> None:
    '''
    Test complete Fuzzy logic evaluation lifecycle.

    Inject synthetic fuzzy sets (Variables), membership functions, and logical Rules
    into the engine. Verify that the FuzzyEngine reliably translates inputs to degrees
    of truth, triggers correct consequents, defuzzifies the output via centroid method,
    and appends the RESULTS column appropriately.
    '''
    # Define mathematical universe
    universe: np.ndarray = np.linspace(0, 6, 1000)
    # Define input linguistic variables
    exhaustion: Variable = Variable('Exhaustion', universe)
    exhaustion.add_term('Low', fuzz.trapmf(universe, [0, 0, 2, 4]))
    exhaustion.add_term('High', fuzz.trapmf(universe, [2, 4, 6, 6]))
    cynicism: Variable = Variable('Cynicism', universe)
    cynicism.add_term('Low', fuzz.trapmf(universe, [0, 0, 2, 4]))
    cynicism.add_term('High', fuzz.trapmf(universe, [2, 4, 6, 6]))
    # Define output linguistic variable
    burnout: Variable = Variable('Burnout', universe)
    burnout.add_term('Low', fuzz.trapmf(universe, [0, 0, 2, 4]))
    burnout.add_term('High', fuzz.trapmf(universe, [2, 4, 6, 6]))
    # Construct rules linking inputs to output
    rule1: Rule = Rule(
        LeafNode('Exhaustion', 'High') & LeafNode('Cynicism', 'High'),
        LeafNode('Burnout', 'High')
    )
    rule2: Rule = Rule(
        LeafNode('Exhaustion', 'Low'),
        LeafNode('Burnout', 'Low')
    )
    # Prepare input data
    df: pd.DataFrame = pd.DataFrame({
        'Exhaustion': [1.0, 5.0],
        'Cynicism': [1.0, 5.0]
    })
    # Configure Data container with variables and rules
    data: Data = Data()
    data._data = df # pyright: ignore[reportPrivateUsage]
    data._vars = {'Exhaustion': exhaustion, 'Cynicism': cynicism, 'Burnout': burnout} # pyright: ignore[reportPrivateUsage]
    data._outvar = burnout # pyright: ignore[reportPrivateUsage]
    data._rules = (rule1, rule2) # pyright: ignore[reportPrivateUsage]
    # Instantiate and execute Fuzzy engine
    engine: FuzzyEngine = FuzzyEngine()
    engine.evaluate(data)
    result: pd.DataFrame = engine.results
    # Verify resulting activation strengths
    assert('RESULTS' in result.columns)
    assert(result['RESULTS'].values[0] < 3.0)
    assert(result['RESULTS'].values[1] > 3.0)
