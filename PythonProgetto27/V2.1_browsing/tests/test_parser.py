import pytest
import os
import sys
from unittest.mock import MagicMock
from pathlib import Path

# Impostazxioni per assicurarsi che il modulo principale sia importabile
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Assicurati di poter importare il tuo modulo Parser
# Potrebbe essere necessario modificare l'import a seconda della tua struttura di progetto (es. 'tuo_progetto.Parser')
import Parser

# --- Dati XML di Mock per il test P01 ---
# Contiene 2 itinerari validi (plantId='164') e 1 itinerario non valido (plantId='999')
MOCK_XML_CONTENT = """
<root>
    <IXLItemList>
        <IXLItem plantId="164" name="ITIN_VAL_A">
            <TrackCircuitList>
                <TrackCircuit name="TC_A1"/>
                <TrackCircuit name="TC_A2"/>
            </TrackCircuitList>
            <PointList>
                <Point name="PT_101">
                    <Switch switchMotorId="SM_001" switchMotorName="M1" switchMotorState="NORMAL"/>
                </Point>
            </PointList>
        </IXLItem>
        
        <IXLItem plantId="999" name="ITIN_NON_VAL">
            <TrackCircuitList><TrackCircuit name="TC_B1"/></TrackCircuitList>
        </IXLItem>
        
        <IXLItem plantId="164" name="ITIN_VAL_B">
            <PointList>
                <Point name="PT_102">
                    <Switch switchMotorId="SM_002" switchMotorName="M2" switchMotorState="REVERSE"/>
                </Point>
            </PointList>
        </IXLItem>
        
    </IXLItemList>
</root>
"""

# --- Dati XML di Mock per il test P02 ---
# Contiene 2 itinerari NON validi (plantId='999')
MOCK_XML_NO_VALID_ID_CONTENT = """
<root>
    <IXLItemList>
        <IXLItem plantId="999" name="ITIN_NON_VAL_1">
            <TrackCircuitList><TrackCircuit name="TC_N1"/></TrackCircuitList>
        </IXLItem>
        <IXLItem plantId="165" name="ITIN_NON_VAL_2">
            <PointList/>
        </IXLItem>
    </IXLItemList>
</root>
"""

# --- Dati XML di Mock per il test P03 ---
# Contiene dati non validi che forzeranno un errore di parsing da parte di ET.parse
MOCK_XML_MALFORMED_CONTENT = """
<root>
    <tag_aperto_senza_chiusura
    Questo non è XML valido!
</root>
"""

# Fixture (setup e teardown) per creare un file XML temporaneo e pulirlo dopo il test
@pytest.fixture
def valid_xml_file(tmp_path):
    # tmp_path è una fixture integrata di pytest per creare cartelle temporanee
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "test.xml"
    p.write_text(MOCK_XML_CONTENT)
    return str(p) # Restituisce il percorso assoluto del file

# Fixture per i logger fittizi (per isolare il test)
@pytest.fixture
def mock_loggers():
    # Usa unittest.mock.MagicMock per evitare la dipendenza dal plugin pytest-mock
    mock_logger = MagicMock()
    return mock_logger, mock_logger # Ritorna defaultLogger, errorLogger


# Fixture per creare un file XML temporaneo SENZA ID validi
@pytest.fixture
def invalid_id_xml_file(tmp_path):
    d = tmp_path / "sub_invalid"
    d.mkdir()
    p = d / "test_no_id.xml"
    p.write_text(MOCK_XML_NO_VALID_ID_CONTENT)
    return str(p)

# Fixture per creare un file XML temporaneo MAL FORMATTATO
@pytest.fixture
def malformed_xml_file(tmp_path):
    d = tmp_path / "sub_malformed"
    d.mkdir()
    p = d / "malformed.xml"
    p.write_text(MOCK_XML_MALFORMED_CONTENT)
    return str(p)

def test_p01_parsing_xml_valido(valid_xml_file, mock_loggers):
    """Verifica l'estrazione corretta di itinerari e dettagli dal file XML valido."""
    
    defaultLogger, errorLogger = mock_loggers

    # Esecuzione della funzione da testare
    listaItinerari = Parser.parsing(valid_xml_file, defaultLogger, errorLogger)

    # ASSERZIONI (Verifica del Risultato Atteso)
    assert len(listaItinerari) == 2, "La lista deve contenere esattamente 2 itinerari."
    
    # Verifica dei dati del primo itinerario (ITIN_VAL_A)
    itin_a = listaItinerari[0]
    assert itin_a["id"] == '164'
    assert itin_a["name"] == 'ITIN_VAL_A'
    assert len(itin_a["trackCircuitList"]) == 2
    assert 'TC_A1' in itin_a["trackCircuitList"]
    assert itin_a["SwitchMotorId"] == 'SM_001'
    assert itin_a["SwitchMotorState"] == 'NORMAL'
    
    # Verifica dei dati del secondo itinerario (ITIN_VAL_B, con TrackCircuitList mancante)
    itin_b = listaItinerari[1]
    assert itin_b["id"] == '164'
    assert itin_b["name"] == 'ITIN_VAL_B'
    # Verifica che il campo mancante sia stato inizializzato correttamente a lista vuota
    assert itin_b["trackCircuitList"] == [] 
    assert itin_b["SwitchMotorId"] == 'SM_002'
    assert itin_b["SwitchMotorState"] == 'REVERSE'

    # Verifica che non ci siano stati errori di parsing
    errorLogger.error.assert_not_called()

# Nel file: tests/test_parser.py (dopo test_p01_parsing_xml_valido)

def test_p02_parsing_xml_no_valid_id(invalid_id_xml_file, mock_loggers):
    """Verifica che la lista sia vuota quando nessun itinerario ha plantId='164'."""
    
    defaultLogger, errorLogger = mock_loggers

    # Esecuzione della funzione da testare
    listaItinerari = Parser.parsing(invalid_id_xml_file, defaultLogger, errorLogger)

    # ASSERZIONI (Verifica del Risultato Atteso)
    
    # Test P02: Ci aspettiamo 0 itinerari
    assert len(listaItinerari) == 0, "La lista deve essere vuota poiché non ci sono itinerari con plantId='164'."
    
    # Verifica che non ci siano stati errori gravi durante l'apertura o il parsing
    errorLogger.error.assert_not_called()
    
    # Verifica che il defaultLogger abbia registrato l'inizio del parsing
    defaultLogger.info.assert_any_call("Inizio parsing degli itinerari con plantId '164'")

def test_p03_parsing_xml_malformed(malformed_xml_file, mock_loggers):
    """Verifica la gestione degli errori per un file XML mal formattato."""
    
    defaultLogger, errorLogger = mock_loggers

    # Esecuzione della funzione da testare
    listaItinerari = Parser.parsing(malformed_xml_file, defaultLogger, errorLogger)

    # ASSERZIONI
    
    # Valore di ritorno: Ci aspettiamo una lista vuota in caso di errore di parsing
    assert listaItinerari == [], "La lista deve essere vuota in caso di errore XML."
    
    # Gestione dell'errore (il risultato più critico per questo test)
    # Verifica che errorLogger.error sia stato chiamato esattamente una volta
    errorLogger.error.assert_called_once()
    
    # Verifica del messaggio di errore: Deve contenere la frase specifica del blocco 'try...except'
    # Usiamo assert_called_with per essere precisi
    call_args, _ = errorLogger.error.call_args
    assert "Errore durante il caricamento del file XML" in call_args[0]
    
