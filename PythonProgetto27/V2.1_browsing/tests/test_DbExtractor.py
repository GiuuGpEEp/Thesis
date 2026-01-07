import pytest
from unittest.mock import MagicMock, patch, call
import sys
from pathlib import Path
import pyodbc

# Configurazione per l'importazione
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import DbExtractor

# --- Dati Fittizi per le tre Query SQL ---

# Q1: itinerari (id_itine, nome)
MOCK_ITINERARI = [
    (101, 'ITIN_A '), 
    (102, 'ITIN_B ')
]

# Q2: blocchi/TC (id_itine, cdb, ente, id_ente)
MOCK_BLOCCHI = [
    # Blocco per ITIN_A: TC normale (cdb == ente)
    (101, 'TC_A', 'TC_A', 201), 
    # Blocco per ITIN_A: Switch (cdb != ente), richiede join con Q3 su id_ente
    (101, 'PT_A_CDB', 'PT_A_ENT', 301), 
    # Blocco per ITIN_B: TC con nome duplicato (da testare la deduplica)
    (102, 'TC_B1', 'TC_B1', 401),
    (102, 'TC_B1', 'TC_B1', 402), 
]

# Q3: Switch (id_itine, id_cassa, nome, statocassa)
MOCK_SWITCH = [
    # Corrisponde all'id_ente 301 dell'ITIN_A
    (101, 301, 'SW_A', 'R '), # Stato 'R' (Reverse) -> Mappato a 2
    # Switch fittizio non usato nel merge
    (999, 901, 'SW_Z', 'N '),
]

# Fixture per i logger fittizi (riutilizzata dal test P01)
@pytest.fixture
def mock_loggers():
    mock_logger = MagicMock()
    return mock_logger, mock_logger 

@patch('pyodbc.connect')
def test_d01_db_extraction_success(mock_pyodbc_connect, mock_loggers):
    """
    Verifica l'estrazione e il corretto merge dei dati dalle tre query DB.
    Si usa @patch per simulare la connessione a pyodbc.
    """
    
    defaultLogger, errorLogger = mock_loggers
    
    # --- Configurazione del Mock del Cursore ---
    mock_conn = mock_pyodbc_connect.return_value # Oggetto connessione simulato
    mock_cursor = mock_conn.cursor.return_value # Oggetto cursore simulato

    # La funzione fetchall() deve restituire i dati corretti per ogni chiamata
    # Usiamo side_effect per definire risultati diversi a ogni chiamata di fetchall()
    mock_cursor.fetchall.side_effect = [
        MOCK_ITINERARI,  # Prima chiamata (QUERY 1: itinerari)
        MOCK_BLOCCHI,    # Seconda chiamata (QUERY 2: blocchi/TC)
        MOCK_SWITCH      # Terza chiamata (QUERY 3: switch)
    ]
    
    # --- Esecuzione della Funzione ---
    risultato_estratto = DbExtractor.get_data("STRINGA_FITTIZIA", defaultLogger, errorLogger)

    # --- ASSERZIONI ---
    
    # A. Conteggio e Tipo
    assert isinstance(risultato_estratto, list)
    assert len(risultato_estratto) == 2, "Dovrebbero essere stati estratti 2 itinerari."
    
    # B. Verifica Itinerario A ('ITIN_A')
    itin_a = [i for i in risultato_estratto if i['nome'] == 'ITIN_A'][0]
    
    # Verifica TrackCircuits (Q2)
    assert 'TC_A' in itin_a['trackCircuits']
    
    # Verifica Switch (Q2 + Q3)
    assert itin_a['switch']['SwitchMotorId'] == 301
    assert itin_a['switch']['SwitchMotorName'] == 'SW_A'
    # Verifica la mappatura dello stato: 'R' -> 2
    assert itin_a['switch']['SwitchMotorState'] == 2 
    
    # C. Verifica Itinerario B ('ITIN_B')
    itin_b = [i for i in risultato_estratto if i['nome'] == 'ITIN_B'][0]
    
    # Verifica Deduplica (Q2)
    assert itin_b['trackCircuits'] == ['TC_B1'], "La lista TC deve contenere solo 'TC_B1' (deduplicato)."
    
    # Verifica switch mancante
    assert itin_b['switch'] is None
    
    # D. Pulizia e Log
    # Verifica che la connessione sia stata chiusa correttamente (blocco finally)
    mock_conn.close.assert_called_once()
    mock_cursor.close.assert_called_once()
    
    # Verifica che non ci siano stati errori gravi
    errorLogger.error.assert_not_called()

@patch('pyodbc.connect')
def test_d02_db_extraction_failure(mock_pyodbc_connect, mock_loggers):
    """
    Verifica la gestione di un errore di connessione al database (pyodbc.Error).
    """
    
    defaultLogger, errorLogger = mock_loggers
    
    # --- Configurazione del Mock per forzare l'errore ---
    # Simula l'errore sollevando pyodbc.Error al tentativo di connessione.
    # Stiamo assumendo che l'errore avvenga nella riga: conn = pyodbc.connect(conn_string)
    mock_pyodbc_connect.side_effect = pyodbc.Error("Simulated connection failed: [SQL State 08001]")
    
    # 2. Configura i mock di connessione/cursore per essere sicuri che esistano 
    #    e che il blocco 'finally' tenti di chiuderli (anche se fallisce prima)
    mock_conn = mock_pyodbc_connect.return_value 
    mock_cursor = mock_conn.cursor.return_value 

    # --- Esecuzione della Funzione ---
    risultato_estratto = DbExtractor.get_data("STRINGA_ERRATA", defaultLogger, errorLogger)

    # --- ASSERZIONI ---
    
    # Valore di Ritorno
    # L'eccezione viene gestita e deve restituire una lista vuota.
    assert risultato_estratto == [], "Il risultato deve essere una lista vuota in caso di errore di connessione."
    
    # Gestione dell'Errore e Log
    # Verifica che errorLogger.error sia stato chiamato
    errorLogger.error.assert_called_once()
    
    # Verifica che il messaggio contenga la frase specifica del blocco 'except pyodbc.Error'
    call_args, _ = errorLogger.error.call_args
    assert "Errore durante l'accesso al database" in call_args[0]
    
    # Verifica che il logger abbia comunque registrato il tentativo di chiusura della connessione (se implementato correttamente)
    defaultLogger.info.assert_any_call("Connessione al database chiusa.")