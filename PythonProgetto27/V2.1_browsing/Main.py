import FileWriter
import Parser
import Logger
import Comparer
import DbExtractor
import datetime
import os

# Importa il modulo per caricare i file tramite dialog
from utils.file_dialog import choose_xml_file, choose_output_directory

# --- CONFIGURAZIONE ---
CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=Stroncone_TC_2102_01;Trusted_Connection=Yes;Encrypt=Yes;TrustServerCertificate=Yes;"
REPORT_PATH = ""
# ----------------------

# Setup iniziale della cartella e dei logger
output_path = choose_output_directory(initial_dir=os.getcwd())
loggers = Logger.setup_directory_and_logger(output_path)
defaultLogger = loggers[0]
errorLogger = loggers[1]

if not output_path:
    errorLogger.error("Nessuna directory di output selezionata. Uscita dal programma.")
    raise SystemExit(1)

# --- SCRITTURA INTESTAZIONE REPORT INIZIALE ---
# Questa funzione sovrascrive il file e aggiunge l'intestazione
FileWriter.file_create(defaultLogger, errorLogger)

# Parsing del file XML
xml_path = choose_xml_file(initial_dir=os.getcwd())
if not xml_path or not os.path.isfile(xml_path):
    errorLogger.error("Nessun file XML selezionato o il percorso non è valido. Uscita dal programma.")
    raise SystemExit(1)

listaItinerari = Parser.parsing(xml_path, defaultLogger, errorLogger)
defaultLogger.info(f"Trovati {len(listaItinerari)} itinerari con plantId '164' nel file XML.")

# Estrazione dati dal DB
db_itinerari = DbExtractor.get_data(CONNECTION_STRING, defaultLogger, errorLogger)
defaultLogger.info(f"Trovati {len(db_itinerari)} itinerari nel database.")


# --- CONFRONTO E STAMPA RISULTATI ---
if db_itinerari:
    defaultLogger.info("Inizio confronto tra XML e database...")
    
    # 1. Intestazione 'Confronto itinerari'
    FileWriter.write_existing_file("\n=== CONFRONTO ITINERARI ===", errorLogger)
    
    # 2. Esegui il confronto principale
    ok_count, diff_count = Comparer.compare_data(listaItinerari, db_itinerari, defaultLogger, errorLogger)

    # 3. Scrivi il riepilogo
    FileWriter.write_existing_file("\n=== RIEPILOGO ITINERARI ===", errorLogger)
    Comparer.write_summary(ok_count, diff_count, errorLogger)

    # 4. Esegui le verifiche aggiuntive
    FileWriter.write_existing_file("\n=== VERIFICHE AGGIUNTIVE ===", errorLogger)
    Comparer.check_missing_itinerari(listaItinerari, db_itinerari, defaultLogger, errorLogger)

    defaultLogger.info("Confronto completato con successo.")
else:
    errorLogger.error("Il confronto non è stato eseguito a causa di errori di connessione al database.")

# Alla fine il root logger stampa un messaggio di completamento su console
Logger.termination_message()