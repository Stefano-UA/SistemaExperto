'''
Tests for the data module.
'''
import pytest
import pandas as pd
import skfuzzy as fuzz
from pathlib import Path
from typing import cast, override
from pandas.testing import assert_frame_equal

from data import Data
from inference.engines import BaseEngine

class DummyEngine(BaseEngine):
    '''
    Dummy engine for testing purposes.
    '''
    @property
    @override
    def results(self) -> pd.DataFrame:
        return pd.DataFrame({'score': [10, 20]})

    @override
    def _init(self, meta: Data) -> None:
        pass

    @override
    def _eval(self, data: pd.Series) -> pd.Series:
        return pd.Series()

    @override
    def _append(self, results: pd.Series) -> None:
        pass

def test_ingest_from_csv(tmp_path: Path) -> None:
    '''
    Test successful CSV file ingestion.

    Verify that the Data container correctly reads a CSV file and
    stores its content in the internal DataFrame state.
    '''
    # Create dummy data and temporary CSV file
    df: pd.DataFrame = pd.DataFrame({'Q1': [1, 2], 'Q2': [3, 4]})
    file_path: Path = (tmp_path / 'test.csv')
    df.to_csv(file_path, index=False)
    # Instantiate Data container
    data: Data = Data()
    # Execute loading and verify success state and content
    assert(data.load_csv(str(file_path)) is True)
    assert(not data.data.empty)
    assert_frame_equal(data.data, df)

def test_ingest_from_csv_failure() -> None:
    '''
    Test graceful failure during CSV ingestion.

    Ensure that attempting to load a non-existent CSV file returns
    a failure status and leaves the data container empty.
    '''
    # Instantiate container
    data: Data = Data()
    # Attempt to load non-existent file and check assertions
    assert(data.load_csv('nonexistent.csv') is False)
    assert(data.data.empty)

def test_map(tmp_path: Path) -> None:
    '''
    Test mapping file loading and column renaming.

    Verify that a .map file correctly triggers the renaming of columns
    in the ingested DataFrame within the Data container.
    '''
    # Define mappings and create temporary .map file
    mappings: dict[str, str] = {
        'Q1': 'question_1',
        'Q2': 'question_2'
    }
    map_file: Path = (tmp_path / 'test_mappings.map')
    with open(map_file, 'w', encoding='utf-8') as file:
        for key, value in mappings.items():
            _ = file.write(f'{key} -> {value}\n')
    # Create dummy CSV data matching the mapping keys
    df: pd.DataFrame = pd.DataFrame({'Q1': [1], 'Q2': [2]})
    csv_file: Path = (tmp_path / 'test.csv')
    df.to_csv(csv_file, index=False)
    # Instantiate container and apply mapping before loading CSV
    data: Data = Data()
    assert(data.load_map(str(map_file)) is True)
    assert(data.load_csv(str(csv_file)) is True)
    # Verify that columns were renamed according to the map
    assert(list(data.data.columns) == ['question_1', 'question_2'])
    # Instantiate container and apply mapping after loading CSV
    data = Data()
    assert(data.load_csv(str(csv_file)) is True)
    assert(data.load_map(str(map_file)) is True)
    # Verify that columns were renamed according to the map
    assert(list(data.data.columns) == ['question_1', 'question_2'])

def test_map_failure() -> None:
    '''
    Test graceful failure during mapping file loading.

    Ensure that a missing .map file is handled correctly by returning
    a failure status.
    '''
    # Instantiate container
    data: Data = Data()
    # Verify failure on non-existent map file
    assert(data.load_map('nonexistent.map') is False)

def test_rules(tmp_path: Path) -> None:
    '''
    Test successful loading of fuzzy rules from a file.

    Verify that the RuleParser is correctly invoked to populate the
    internal rules tuple from a provided payload.
    '''
    # Create temporary rules file with valid DSL syntax
    rules_file: Path = (tmp_path / 'test.rules')
    with open(rules_file, 'w', encoding='utf-8') as file:
        _ = file.write('IF Var1 IS Low AND Var3 IS High THEN VarOut IS High\n')
        _ = file.write('IF Var2 IS High AND Var4 IS Low THEN VarOut IS High\n')
    # Instantiate container and load rules
    data: Data = Data()
    assert(data.load_rules(str(rules_file)) is True)
    # Verify rules were parsed and stored
    assert(len(data.rules) == 2)
    assert(str(data.rules[0]) == 'IF (Var1 IS Low AND Var3 IS High) THEN VarOut IS High')
    assert(str(data.rules[1]) == 'IF (Var2 IS High AND Var4 IS Low) THEN VarOut IS High')

def test_rules_failure() -> None:
    '''
    Test graceful failure during rule file loading.

    Ensure that missing rule files result in an empty rules tuple
    and a failure return status.
    '''
    # Instantiate container
    data: Data = Data()
    # Verify failure and empty state
    assert(data.load_rules('nonexistent.rules') is False)
    assert(data.rules == ())

def test_vars(tmp_path: Path) -> None:
    '''
    Test successful loading of fuzzy variables from a file.

    Verify that the VariableParser correctly populates the internal
    variables dictionary from a provided payload.
    '''
    # Create temporary variables file with valid DSL syntax
    vars_file: Path = (tmp_path / 'test.vars')
    with open(vars_file, 'w', encoding='utf-8') as file:
        _ = file.write('TestVar1<0, 10>: (Low<trapmf, 0, 0, 2, 4>; High<trapmf, 2, 4, 10, 10>)\n')
        _ = file.write('TestVar2<0, 20>: (Low<trapmf, 0, 0, 2, 8>; High<trapmf, 2, 4, 10, 20>)\n')
        _ = file.write('OutVar<5, 20>: (Low<trapmf, 5, 5, 7, 10>; High<trapmf, 2, 4, 10, 20>)\n')
    # Instantiate container and load variables
    data: Data = Data()
    assert(data.load_vars(str(vars_file)) is True)
    # Verify variables were correctly parsed and indexed
    assert(len(data.variables) == 3)
    assert(data.variables['TestVar1'].name == 'TestVar1')
    assert(data.variables['TestVar2'].name == 'TestVar2')
    assert(data.variables['OutVar'].name == 'OutVar')
    # Check domains were got correctly
    assert(data.variables['TestVar1'].universe.min() == 0)
    assert(data.variables['TestVar2'].universe.min() == 0)
    assert(data.variables['OutVar'].universe.min() == 5)
    assert(data.variables['TestVar1'].universe.max() == 10)
    assert(data.variables['TestVar2'].universe.max() == 20)
    assert(data.variables['OutVar'].universe.max() == 20)
    # Check terms were got correctly
    for var, term, params in [
        ('TestVar1', 'Low',  [0, 0, 2, 4]),
        ('TestVar2', 'Low',  [0, 0, 2, 8]),
        ('OutVar',    'Low',  [5, 5, 7, 10]),
        ('TestVar1', 'High', [2, 4, 10, 10]),
        ('TestVar2', 'High', [2, 4, 10, 20]),
        ('OutVar',    'High', [2, 4, 10, 20]),
    ]:
        assert (data.variables[var].terms[term] == fuzz.trapmf(data.variables[var].universe, params)).all() # pyright: ignore[reportAny]
    # Check output variable (last) is correct
    assert(data.outvar is not None)
    assert(data.outvar.name == 'OutVar')

def test_vars_failure() -> None:
    '''
    Test graceful failure during variable file loading.

    Ensure that missing variable files result in an empty variables
    dictionary and a failure return status.
    '''
    # Instantiate container
    data: Data = Data()
    # Verify failure and empty state
    assert(data.load_vars('nonexistent.vars') is False)
    assert(data.variables == {})

def test_save_results() -> None:
    '''
    Test inference results storage.

    Verify that evaluated results from an inference engine are
    correctly cached within the Data container's results dictionary.
    '''
    # Instantiate container and prepare dummy results
    data: Data = Data()
    df_results: pd.DataFrame = pd.DataFrame({'score': [10, 20]})
    engine: DummyEngine = DummyEngine()
    # Store results using a dummy engine instance
    data.store(df_results, cast(type[object], engine))
    # Verify that results are stored with an engine-specific key
    res: dict[str, pd.DataFrame] = data.results
    assert(len(res) == 1)
    key: str = list(res.keys())[0]
    assert('DummyEngine' in key)
    assert(list(res[key]['score']) == [10, 20])