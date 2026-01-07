import os
import sys
from unittest.mock import patch

# Siccome test1 è dentro la cartella Tests, dobbiamo aggiungere la cartella principale al sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importo i moduli dalla cartella principale
import Logger
import FileWriter
import Parser

# --- SCENARIO 1: TUTTO OK ---
def test_scenario_ok():
    print("\n\n=== SCENARIO 1: TUTTO OK ===")
    
    loggers = Logger.setup_directory_and_logger()
    default_log = loggers[0]
    error_log = loggers[1]
    
    default_log.info("Inizio setup del Report")
    try:
        FileWriter.file_create()
        default_log.info("Report creato correttamente")
    except Exception as e:
        error_log.error(f"Errore durante la creazione del Report: {e}")
    
    default_log.info("Inizio parsing del file XML")
    try:
        listaItinerari = Parser.parsing()
        default_log.info(f"Trovati {len(listaItinerari)} itinerari.")
    except Exception as e:
        error_log.error(f"Errore durante il parsing del file XML: {e}")
        return
    
    for itinerario in listaItinerari:
        try:
            nome_itinerario = itinerario.get('name')
            FileWriter.write_existing_file(f"Nome itinerario: {nome_itinerario}")
        except Exception as e:
            error_log.error(f"Errore durante la scrittura del nome '{nome_itinerario}' nel Report: {e}")


# --- SCENARIO 2: ERRORE NELLA CREAZIONE DELLA CARTELLA (USANDO MOCK) ---
def test_scenario_cartella_non_creata():
    print("\n\n=== SCENARIO 2: CARTELLA NON CREATA ===")
    
    # Usa @patch per sostituire temporaneamente os.makedirs
    with patch('os.makedirs', side_effect=OSError(13, 'Permission denied')):
        try:
            Logger.setup_directory_and_logger()
        except OSError as e:
            # Il tuo codice ha gestito correttamente l'errore sollevato dal mock
            print(f"✔ Test passato: L'errore è stato gestito correttamente. Messaggio: {e}")


# --- SCENARIO 3: ERRORE NEL PARSING (USANDO MOCK) ---
def test_scenario_parsing_fallito():
    print("\n\n=== SCENARIO 3: PARSING FALLITO ===")
    
    # Simula la configurazione iniziale del logger
    loggers = Logger.setup_directory_and_logger()
    default_log = loggers[0]
    error_log = loggers[1]

    # Usa @patch per sostituire temporaneamente la funzione di parsing
    with patch('Parser.parsing', side_effect=ValueError("File XML non valido")):
        try:
            default_log.info("Inizio parsing (simulazione fallimento)")
            Parser.parsing()
        except Exception as e:
            error_log.error(f"Errore durante il parsing del file XML: {e}")
            print(f"✔ Test passato: L'errore di parsing è stato catturato e loggato.")

# --- SCENARIO 4: ERRORE DURANTE LA CREAZIONE DEI FILE DI LOG (USANDO MOCK) ---

def test_scenario_log_file_creation_failed():
    """Scenario 4: Errore durante la creazione dei file di log (simulazione)."""
    print("\n\n=== SCENARIO 4: CREAZIONE FILE DI LOG FALLITA ===")
    
    # Usiamo @patch per sostituire la funzione open()
    # L'argomento 'side_effect' fa sollevare un'eccezione quando viene chiamata open()
    with patch('builtins.open', side_effect=IOError(13, 'Permission denied')):
        try:
            # Chiamiamo la funzione di setup che tenterà di creare i file
            Logger.setup_directory_and_logger()
        except IOError as e:
            # Il tuo codice dovrebbe sollevare un IOError qui, che viene catturato dal tuo blocco try-except
            print(f"✔ Test passato: L'errore di I/O è stato gestito correttamente. Messaggio: {e}")
        except Exception as e:
            # Cattura qualsiasi altro errore imprevisto
            print(f"✘ Test fallito: Eccezione inattesa: {e}")            




# Esegui i test
if __name__ == "__main__":
    
    test_scenario_ok()
    #test_scenario_cartella_non_creata()
    #test_scenario_parsing_fallito()
    #test_scenario_log_file_creation_failed()