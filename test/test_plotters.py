'''
Tests for the visualization module.
'''
import pytest
import numpy as np
import pandas as pd
import skfuzzy as fuzz
from pathlib import Path
from pytest_mock import MockerFixture

from data import Data
from visualization import Plotter
from inference.fuzzy import Variable

def _create_mock_data() -> Data:
    '''
    Helper to create a populated Data instance for testing plotters.
    '''
    # Create empty data container
    data: Data = Data()
    universe: np.ndarray = np.arange(0, 10.1, 0.1)
    # Create input variable
    var1: Variable = Variable('exhaustion', universe)
    var1.add_term('low', fuzz.trimf(universe, [0, 0, 5]))
    var1.add_term('high', fuzz.trimf(universe, [5, 10, 10]))
    # Create output variable
    outvar: Variable = Variable('burnout', universe)
    outvar.add_term('low', fuzz.trimf(universe, [0, 0, 5]))
    outvar.add_term('high', fuzz.trimf(universe, [5, 10, 10]))
    # Assign variables
    data._vars = {'exhaustion': var1, 'burnout': outvar} # pyright: ignore[reportPrivateUsage]
    data._outvar = outvar # pyright: ignore[reportPrivateUsage]
    # Create dummy results
    df1: pd.DataFrame = pd.DataFrame({
        'exhaustion': [2.0],
        'burnout': [np.array([0.5] * len(universe))], # Dummy aggregated array
        'RESULTS': [2.5]
    })
    df2: pd.DataFrame = pd.DataFrame({
        'exhaustion': [2.0],
        'burnout': [np.array([0.6] * len(universe))],
        'RESULTS': [3.0]
    })
    # Assign results
    data._results = {'engine1': df1, 'engine2': df2} # pyright: ignore[reportPrivateUsage]
    return data

def test_plot_variable(tmp_path: Path) -> None:
    '''
    Test plotting of a single linguistic variable.

    Verify that the Plotter correctly generates and saves a membership
    function plot for a specified variable.
    '''
    # Initialize mock data and plotter
    data: Data = _create_mock_data()
    plotter: Plotter = Plotter(data)
    # Plot existing variable
    plotter.plot_variable('exhaustion', str(tmp_path))
    # Verify file was created
    expected_file: Path = tmp_path / 'variables' / 'exhaustion.png'
    assert(expected_file.exists())
    # Plot non-existing variable, should not crash
    plotter.plot_variable('missing', str(tmp_path))

def test_plot_variables(tmp_path: Path, mocker: MockerFixture) -> None:
    '''
    Test batch plotting of all variables.

    Verify that calling plot_variables iterates through all stored variables
    and delegates to plot_variable.
    '''
    # Initialize mock data and plotter
    data: Data = _create_mock_data()
    plotter: Plotter = Plotter(data)
    # Spy on plot_variable
    spy = mocker.spy(plotter, 'plot_variable')
    plotter.plot_variables(str(tmp_path))
    # Assert spy was called for each variable
    assert(spy.call_count == 2)
    spy.assert_any_call('exhaustion', str(tmp_path))
    spy.assert_any_call('burnout', str(tmp_path))

def test_plot_result(tmp_path: Path) -> None:
    '''
    Test plotting of an inference result row.

    Verify Plotter correctly overlays an aggregated activation
    area and defuzzified decision line onto output variable's terms.
    '''
    # Initialize mock data and plotter
    data: Data = _create_mock_data()
    plotter: Plotter = Plotter(data)
    # Plot valid result
    plotter.plot_result('engine1', str(tmp_path), row_idx=0)
    # Verify file was created
    expected_file: Path = tmp_path / 'outvar' / 'engine1' / 'results_row0.png'
    assert(expected_file.exists())
    # Plot missing key, should not crash
    plotter.plot_result('missing', str(tmp_path), row_idx=0)
    # Plot out-of-bounds row index, should not crash
    plotter.plot_result('engine1', str(tmp_path), row_idx=99)

def test_plot_results(tmp_path: Path, mocker: MockerFixture) -> None:
    '''
    Test batch plotting of all rows in a result set.

    Verify Plotter correctly iterates through all rows in a specified
    result DataFrame and delegates plotting to plot_result.
    '''
    # Initialize mock data and plotter
    data: Data = _create_mock_data()
    plotter: Plotter = Plotter(data)
    # Spy on plot_result
    spy = mocker.spy(plotter, 'plot_result')
    plotter.plot_results('engine1', str(tmp_path))
    # Assert spy was called for the row in dummy data
    assert(spy.call_count == 1)
    spy.assert_any_call('engine1', str(tmp_path), 0)

def test_plot_comparison(tmp_path: Path) -> None:
    '''
    Test comparative plotting of two engine results.

    Verify Plotter correctly generates a scatter plot contrasting
    two sets of inference results along with MAE and MSE metrics.
    '''
    # Initialize mock data and plotter
    data: Data = _create_mock_data()
    plotter: Plotter = Plotter(data)
    # Plot valid comparison
    plotter.plot_comparison('engine1', 'engine2', str(tmp_path))
    # Verify file was created
    expected_file: Path = tmp_path / 'comparisons' / 'engine1_vs_engine2.png'
    assert(expected_file.exists())
    # Plot missing keys, should not crash
    plotter.plot_comparison('missing1', 'engine2', str(tmp_path))
    plotter.plot_comparison('engine1', 'missing2', str(tmp_path))
