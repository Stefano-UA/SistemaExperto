'''
Tests for the UI controller module.
'''
import os
import pytest
import pandas as pd
from pathlib import Path
from typing import cast, override
from rich.console import Console
from pytest_mock import MockerFixture
from pandas.testing import assert_frame_equal

from data import Data
from ui.display import Display
from ui.controller import Controller
from inference.engines import BaseEngine

class DummyEngine(BaseEngine):
    '''
    Dummy engine for testing.
    '''
    @property
    @override
    def results(self) -> pd.DataFrame:
        return self._results

    @override
    def _init(self, meta: Data) -> None:
        self._results: pd.DataFrame = pd.DataFrame(columns=['dummy_score'])

    @override
    def _eval(self, data: pd.Series) -> pd.Series:
        return pd.Series({'dummy_score': 10.0})

    @override
    def _append(self, results: pd.Series) -> None:
        self._results = pd.concat([self._results, results.to_frame().T], ignore_index=True)

def test_controller_initialization() -> None:
    '''
    Test Controller instantiation.

    Verify that the Controller correctly sets up its internal state dictionary,
    data container, and engine bindings upon initialization with a Display.
    '''
    # Create display and controller
    display: Display = Display('Test', Console())
    controller: Controller = Controller(display)
    # Check the state is correctly initialized
    assert isinstance(controller.state, dict)
    assert(controller.state['data'] is None)
    assert(controller.state['rules'] is None)
    assert(controller.state['mappings'] is None)
    assert(controller.state['variables'] is None)
    assert(controller.state['engine'] in Controller.engines)

def test_controller_load_data(tmp_path: Path, mocker: MockerFixture) -> None:
    '''
    Test CSV data loading through the controller.

    Mock the interactive FileBrowser to simulate a user selecting a CSV file,
    and verify that the Controller successfully delegates the ingestion to the Data container.
    '''
    # Create dummy data
    df: pd.DataFrame = pd.DataFrame({'val': [1, 2]})
    file_path: Path = (tmp_path / 'test_data.csv')
    df.to_csv(file_path, index=False)
    # Create display and controller
    display: Display = Display('Test', Console())
    controller: Controller = Controller(display)
    # Mock the FileBrowser to return our path
    _ = mocker.patch('ui.browser.FileBrowser.run', return_value=str(file_path))
    # Check the load returns true and data is equal to what it should
    assert(controller.load_data() is True)
    assert(not controller.data.data.empty)
    assert_frame_equal(controller.data.data, df)

def test_controller_load_mappings(tmp_path: Path, mocker: MockerFixture) -> None:
    '''
    Test .map data loading through the controller.

    Mock the interactive FileBrowser to simulate a user selecting a .map file,
    and verify that the Controller successfully delegates the ingestion to the Data container.
    '''
    # Create dummy data
    mappings: dict[str, str] = {
        'test_str': 'test_value',
        'test_str2': 'test_value2',
        'test_str3': 'test_value3'
    }
    file_path: Path = (tmp_path / 'test_mappings.map')
    with open(file_path, 'w', encoding=os.getenv('ENC', 'utf-8')) as file:
        for key, value in mappings.items():
            _ = file.write(f'{key} -> {value}\n')
    # Create display and controller
    display: Display = Display('Test', Console())
    controller: Controller = Controller(display)
    # Mock the FileBrowser to return our path
    _ = mocker.patch('ui.browser.FileBrowser.run', return_value=str(file_path))
    # Check the load returns true and data is equal to what it should
    assert(controller.load_mappings() is True)
    assert isinstance(controller.data._mappings, dict) # pyright: ignore[reportPrivateUsage]
    assert(controller.data._mappings == mappings) # pyright: ignore[reportPrivateUsage]

def test_controller_load_rules(tmp_path: Path, mocker: MockerFixture) -> None:
    '''
    Test .rules data loading through the controller.

    Mock the interactive FileBrowser to simulate a user selecting a .rules file,
    and verify that the Controller successfully delegates the ingestion to the Data container.
    '''
    # Create dummy data
    file_path: Path = (tmp_path / 'test_rules.rules')
    with open(file_path, 'w', encoding=os.getenv('ENC', 'utf-8')) as file:
        _ = file.write('IF Var1 IS Set1 AND Var2 IS Set4 OR NOT Var3 IS Set7 THEN Burnout IS high\n')
    # Create display and controller
    display: Display = Display('Test', Console())
    controller: Controller = Controller(display)
    # Mock the FileBrowser to return our path
    _ = mocker.patch('ui.browser.FileBrowser.run', return_value=str(file_path))
    # Check the load returns true and data is equal to what it should
    assert(controller.load_rules() is True)
    assert isinstance(controller.data.rules, tuple)
    assert(len(controller.data.rules) == 1)

def test_controller_load_variables(tmp_path: Path, mocker: MockerFixture) -> None:
    '''
    Test .vars data loading through the controller.

    Mock the interactive FileBrowser to simulate a user selecting a .vars file,
    and verify that the Controller successfully delegates the ingestion to the Data container.
    '''
    # Create dummy data
    file_path: Path = (tmp_path / 'test_vars.vars')
    with open(file_path, 'w', encoding=os.getenv('ENC', 'utf-8')) as file:
        _ = file.write('Var1<0, 20>: (Set1<trapmf, 0, 0, 5, 10>; Set2<trapmf, 5, 10, 15, 20>)\n')
        _ = file.write('Var2<0, 25>: (Set4<trapmf, 0, 0, 10, 20>; Set5<trapmf, 10, 20, 25, 25>)\n')
        _ = file.write('Burnout<0, 10>: (low<trapmf, 0, 0, 2, 4>; high<trapmf, 6, 8, 10, 10>)\n')
    # Create display and controller
    display: Display = Display('Test', Console())
    controller: Controller = Controller(display)
    # Mock the FileBrowser to return our path
    _ = mocker.patch('ui.browser.FileBrowser.run', return_value=str(file_path))
    # Check the load returns true and data is equal to what it should
    assert(controller.load_variables() is True)
    assert isinstance(controller.data.variables, dict)
    assert(len(controller.data.variables) == 3)
    assert('Var1' in controller.data.variables)
    assert('Var2' in controller.data.variables)
    assert('Burnout' in controller.data.variables)
    assert(controller.data.variables['Var1'].universe.min() == 0)
    assert(controller.data.variables['Var2'].universe.min() == 0)
    assert(controller.data.variables['Burnout'].universe.min() == 0)
    assert(controller.data.variables['Var1'].universe.max() == 20)
    assert(controller.data.variables['Var2'].universe.max() == 25)
    assert(controller.data.variables['Burnout'].universe.max() == 10)

def test_controller_switch_engine() -> None:
    '''
    Test engine switching logic in the controller.

    Iterate through multiple engine switches and verify that the controller
    cycles through the available engine types defined in its class attribute.
    '''
    # Create display and controller
    display: Display = Display('Test', Console())
    controller: Controller = Controller(display)
    # Assert a bunch of times
    for _ in range(16):
        last: type[BaseEngine] = cast(
            type[BaseEngine],
            controller.state['engine']
        )
        assert(controller.state['engine'] in Controller.engines)
        assert(controller.switch_engine() is None)
        assert(controller.state['engine'] in Controller.engines)
        assert(last != controller.state['engine'])

def test_controller_execute_inference(tmp_path: Path, mocker: MockerFixture) -> None:
    '''
    Test inference execution delegation.

    Simulate data loading, switch to a dummy engine, and invoke inference execution.
    Ensure that the Controller correctly captures and stores the evaluation results.
    '''
    # Create dummy data
    df: pd.DataFrame = pd.DataFrame({'val': [1, 2]})
    file_path: Path = (tmp_path / 'test_data.csv')
    df.to_csv(file_path, index=False)
    # Create display and controller
    display: Display = Display('Test', Console())
    controller: Controller = Controller(display)
    # Mock the FileBrowser to return our path
    _ = mocker.patch('ui.browser.FileBrowser.run', return_value=str(file_path))
    _ = controller.load_data()
    # Override engine to DummyEngine
    controller.state['engine'] = DummyEngine
    # Execute inference
    controller.execute_inference()
    # Check it saved to data (only one result)
    assert(len(controller.data.results) == 1)
    # Get DummyEngine results
    res: pd.DataFrame = next(reversed(controller.data.results.values()))
    assert('dummy_score' in res.columns)
    assert(list(res['dummy_score']) == [10.0, 10.0])

def test_controller_generate_visualizations(mocker: MockerFixture) -> None:
    '''
    Test visualization pipeline execution.

    Verify that the Controller's generate_visualizations method executes cleanly
    without crashing, even when data is empty or results are absent.
    '''
    # Create display and controller
    display: Display = Display('Test', Console())
    controller: Controller = Controller(display)
    # Do nothing if no data, should not crash
    controller.generate_visualizations()
