import sys
import os
import types
import logging
from pathlib import Path
import builtins

import pytest

# Ensure project root is importable
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.file_dialog import choose_output_directory, choose_xml_file
import FileWriter
import Logger


def test_io1_choose_output_directory_no_selection(tmp_path, monkeypatch):
    """Simula ambiente senza filedialog/tkinter e input vuoto -> None restituito"""
    # Create a dummy tkinter module without filedialog to force the fallback path
    tk_mod = types.ModuleType('tkinter')
    monkeypatch.setitem(sys.modules, 'tkinter', tk_mod)

    # Ensure no submodule 'tkinter.filedialog' exists so import of it fails
    if 'tkinter.filedialog' in sys.modules:
        monkeypatch.delitem(sys.modules, 'tkinter.filedialog', raising=False)

    # Simula input vuoto (utente annulla)
    monkeypatch.setattr(builtins, 'input', lambda prompt='': '')

    res = choose_output_directory(initial_dir=str(tmp_path))
    assert res is None


def test_io2_choose_xml_file_no_selection(tmp_path, monkeypatch):
    """Simula ambiente senza filedialog/tkinter e input vuoto -> None restituito per choose_xml_file"""
    tk_mod = types.ModuleType('tkinter')
    monkeypatch.setitem(sys.modules, 'tkinter', tk_mod)
    if 'tkinter.filedialog' in sys.modules:
        monkeypatch.delitem(sys.modules, 'tkinter.filedialog', raising=False)

    # Simula input vuoto
    monkeypatch.setattr(builtins, 'input', lambda prompt='': '')

    res = choose_xml_file(initial_dir=str(tmp_path))
    assert res is None


def test_io3_file_create_and_overwrite(tmp_path):
    """Verifica che FileWriter.file_create crei/sovrascriva Report.txt nella directory di output configurata."""
    out_dir = str(tmp_path)
    # Setup logger to use the temporary directory
    defaultLogger, errorLogger = Logger.setup_directory_and_logger(out_dir)

    # Create report
    FileWriter.file_create(defaultLogger, errorLogger)
    report_path = os.path.join(Logger.get_output_dir(), 'Report.txt')
    assert os.path.exists(report_path)

    # Read file and check header lines
    content = open(report_path, encoding='utf-8').read()
    assert 'REPORT DELLE ATTIVITA' in content or 'REPORT' in content

    # Call file_create again to ensure overwrite path
    FileWriter.file_create(defaultLogger, errorLogger)
    assert os.path.exists(report_path)


def test_l01_logger_setup_directory_and_logger(tmp_path):
    out_dir = str(tmp_path)
    defaultLogger, errorLogger = Logger.setup_directory_and_logger(out_dir)

    # get_output_dir must reflect what we set
    assert Logger.get_output_dir() == out_dir

    # Log file must exist
    log_file = os.path.join(out_dir, 'logging.log')
    assert os.path.exists(log_file)

    # Loggers returned must have handlers
    assert defaultLogger is not None and len(defaultLogger.handlers) > 0
    assert errorLogger is not None and len(errorLogger.handlers) > 0


def test_l02_logger_termination_message(caplog):
    caplog.set_level(logging.INFO)
    Logger.termination_message()
    assert 'Tutte le operazioni sono state completate' in caplog.text
