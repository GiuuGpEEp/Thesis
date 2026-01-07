import pytest
from unittest.mock import MagicMock
import sys
from pathlib import Path

# Configurazione per l'importazione
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import Comparer

# --- Dati Fittizi per un Confronto Perfetto (N=2) ---

# XML: Formato di output di Parser.parsing()
MOCK_XML_PERFECT = [
    {
        "id": "164", 
        "name": "ITIN_1",
        "trackCircuitList": ["TC_X", "TC_Y"], # Lista di stringhe
    "SwitchMotorId": "101",
    "SwitchMotorName": "SW_A",
    "SwitchMotorState": "1"
    },
    {
        "id": "164", 
        "name": "ITIN_2",
        "trackCircuitList": ["TC_Z"], 
        "SwitchMotorId": None, # Caso Switch mancante
        "SwitchMotorName": None,
        "SwitchMotorState": None
    },
]

# DB: Formato di output di DbExtractor.get_data()
MOCK_DB_PERFECT = [
    {
        'id': 1, 
        'nome': "ITIN_1",
        'trackCircuits': ["TC_X", "TC_Y"], # Lista di stringhe
        'switch': {
            'SwitchMotorId': 101, # L'ID nel DB è un intero (norm. a stringa nel Comparer)
            'SwitchMotorName': "SW_A",
            'SwitchMotorState': 1 # Lo stato nel DB è un intero (norm. a stringa nel Comparer)
        }
    },
    {
        'id': 2, 
        'nome': "ITIN_2",
        'trackCircuits': ["TC_Z"], 
        'switch': None # Caso Switch mancante
    },
]


# Fixture per i logger fittizi (riutilizzata)
@pytest.fixture
def mock_loggers():
    # Usa unittest.mock.MagicMock per i logger
    mock_logger = MagicMock()
    return mock_logger, mock_logger 

# Faccio il mock della funzione di scrittura per verificare cosa è stato scritto
@pytest.fixture
def mock_file_writer():
    # Patcha direttamente la funzione nel modulo FileWriter con un MagicMock
    import FileWriter
    mock_fn = MagicMock(return_value=None)
    FileWriter.write_existing_file = mock_fn
    return mock_fn

def test_c01_perfect_match(mock_loggers, mock_file_writer):
    """Verifica che un confronto tra set di dati identici produca 100% OK e 0 differenze."""
    
    defaultLogger, errorLogger = mock_loggers

    # Esecuzione della funzione da testare
    ok_count, diff_count = Comparer.compare_data(
        MOCK_XML_PERFECT, 
        MOCK_DB_PERFECT, 
        defaultLogger, 
        errorLogger
    )

    # ASSERZIONI (Verifica del Risultato Atteso)
    
    # Conteggi
    N = len(MOCK_XML_PERFECT)
    assert ok_count == N, f"Ci aspettavamo {N} OK, trovati {ok_count}"
    assert diff_count == 0, f"Ci aspettavamo 0 differenze, trovate {diff_count}"

    # Log di Errore
    # Nessuna differenza trovata, quindi nessun errore critico e nessun warning di differenze
    errorLogger.error.assert_not_called()
    errorLogger.warning.assert_not_called()

    # Verifica del Report (Output)
    # Verifichiamo che per ogni itinerario sia stato scritto "Stato: OK"
    
    # Raccogli tutte le chiamate fatte a FileWriter.write_existing_file
    call_messages = [c[0][0] for c in mock_file_writer.call_args_list]

    # Verifica che ci siano esattamente N messaggi "Stato: OK"
    ok_messages_count = sum(1 for msg in call_messages if "Stato: OK" in msg)
    assert ok_messages_count == N, f"Ci aspettavamo {N} messaggi 'Stato: OK' nel report."

    # Verifica che non sia mai stato scritto "Stato: DIFFERENZE"
    diff_messages_count = sum(1 for msg in call_messages if "Stato: DIFFERENZE" in msg)
    assert diff_messages_count == 0, "Non dovrebbero esserci messaggi di 'DIFFERENZE' nel report."


def test_c02_all_different(mock_loggers, mock_file_writer):
    """Confronto tra due liste di pari lunghezza ma con dati completamente diversi."""
    defaultLogger, errorLogger = mock_loggers

    # XML contiene ITIN_A, ITIN_B
    xml = [
        {"id": "164", "name": "ITIN_A", "trackCircuitList": ["X"] , "SwitchMotorId": None, "SwitchMotorName": None, "SwitchMotorState": None},
        {"id": "164", "name": "ITIN_B", "trackCircuitList": ["Y"] , "SwitchMotorId": None, "SwitchMotorName": None, "SwitchMotorState": None},
    ]

    # DB contiene nomi diversi
    db = [
        {'id': 1, 'nome': 'ITIN_C', 'trackCircuits': ['Z'], 'switch': None},
        {'id': 2, 'nome': 'ITIN_D', 'trackCircuits': ['W'], 'switch': None},
    ]

    ok_count, diff_count = Comparer.compare_data(xml, db, defaultLogger, errorLogger)

    # Non ci sono corrispondenze, quindi nessun OK
    assert ok_count == 0
    # Il comparer marca gli itinerari mancanti ma non conta queste righe come 'diff_count'
    assert diff_count == 0

    # Verifica che siano stati scritti due messaggi che indicano itinerario MANCANTE
    call_messages = [c[0][0] for c in mock_file_writer.call_args_list]
    missing_messages_count = sum(1 for msg in call_messages if "MANCANTE" in msg)
    assert missing_messages_count == 2

    # Verifica che il logger di warning sia stato chiamato per ciascun itinerario mancante
    assert defaultLogger.warning.call_count >= 2


def test_c03_partial_diff(mock_loggers, mock_file_writer):
    """Confronto parziale: alcune corrispondenze OK, altre con differenze."""
    defaultLogger, errorLogger = mock_loggers

    xml = [
        {"id": "164", "name": "IT_OK", "trackCircuitList": ["A"], "SwitchMotorId": None, "SwitchMotorName": None, "SwitchMotorState": None},
        {"id": "164", "name": "IT_DIFF", "trackCircuitList": ["B"], "SwitchMotorId": None, "SwitchMotorName": None, "SwitchMotorState": None},
        {"id": "164", "name": "IT_OK2", "trackCircuitList": ["C"], "SwitchMotorId": None, "SwitchMotorName": None, "SwitchMotorState": None},
    ]

    db = [
        {'id': 1, 'nome': 'IT_OK', 'trackCircuits': ['A'], 'switch': None},
        {'id': 2, 'nome': 'IT_DIFF', 'trackCircuits': ['DIFFERENT_B'], 'switch': None},
        {'id': 3, 'nome': 'IT_OK2', 'trackCircuits': ['C'], 'switch': None},
    ]

    ok_count, diff_count = Comparer.compare_data(xml, db, defaultLogger, errorLogger)

    assert ok_count == 2
    assert diff_count == 1

    # Verifica che sia stato loggato esattamente un errore relativo alle differenze
    assert errorLogger.error.call_count >= 1


def test_c04_check_missing_itinerari(mock_loggers, mock_file_writer):
    """Verifica che `check_missing_itinerari` segnali correttamente gli itinerari presenti nel DB ma mancanti nell'XML."""
    defaultLogger, errorLogger = mock_loggers

    xml_items = [
        {'name': 'A'},
        {'name': 'B'},
    ]
    db_items = [
        {'nome': 'A'},
        {'nome': 'B'},
        {'nome': 'C'},
    ]

    # Assicuriamoci che FileWriter.write_existing_file sia il mock usato
    import FileWriter
    # re-apply mock in case previous tests changed it
    mock_fn = mock_file_writer
    FileWriter.write_existing_file = mock_fn

    Comparer.check_missing_itinerari(xml_items, db_items, defaultLogger, errorLogger)

    # Verifica che sia stata scritta una riga che segnala l'itinerario mancante 'C'
    call_messages = [c[0][0] for c in mock_fn.call_args_list]
    found = any('MANCANTE' in m and 'Itinerario C' in m for m in call_messages)
    assert found, f"Ci aspettavamo una riga che segnala l'itinerario mancante 'C' nelle chiamate: {call_messages}"

    # Verifica che il logger abbia emesso un warning per l'itinerario mancante
    defaultLogger.warning.assert_called()