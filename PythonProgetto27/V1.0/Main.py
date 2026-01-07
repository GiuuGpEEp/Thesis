import FileWriter
import Parser
import Logger
import Comparer
import DbExtractor

CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=Stroncone_TC_2102_01;Trusted_Connection=Yes;Encrypt=Yes;TrustServerCertificate=Yes;"

# Setup iniziale della cartella e dei logger
loggers = Logger.setup_directory_and_logger()
defaultLogger = loggers[0]
errorLogger = loggers[1]

# Generazione del report
FileWriter.file_create(defaultLogger, errorLogger)

# Parsing del file XML
listaItinerari = Parser.parsing(defaultLogger, errorLogger)
defaultLogger.info(f"Trovati {len(listaItinerari)} itinerari con plantId '164'.")

# Stampa finale
errorFound = False
for itinerario_dict in listaItinerari:
    try:
        # Crea una riga di separazione per ogni itinerario
        report_line = "---" * 15 + "\n"
        
        # Aggiungi un titolo per l'itinerario
        report_line += f"| Itinerario: {itinerario_dict['name']}\n"
        report_line += f"| ID: {itinerario_dict['id']}\n"
        
        # Aggiungi i TrackCircuit se la lista non è vuota
        if itinerario_dict['trackCircuitList']:
            report_line += "|   Dettagli TrackCircuit:\n"
            for trackCircuit in itinerario_dict['trackCircuitList']:
                report_line += f"|     - Nome: {trackCircuit}\n"

        # Aggiungi i dettagli dello Switch se presenti
        if itinerario_dict.get('SwitchMotorId'): # Controlla che la chiave esista
            report_line += "|   Dettagli Switch:\n"
            report_line += f"|     - Motor ID: {itinerario_dict['SwitchMotorId']}\n"
            report_line += f"|     - Nome: {itinerario_dict['SwitchMotorName']}\n"
            report_line += f"|     - Stato: {itinerario_dict['SwitchMotorState']}\n"

        report_line += "---" * 15 + "\n" # Chiusura del blocco
        
        FileWriter.write_existing_file(report_line, errorLogger) # Scrittura nel report
        defaultLogger.info(f"Itinerario '{itinerario_dict['name']}' scritto correttamente nel Report.")
    
    except Exception as e:
        errorFound = True
        errorLogger.error(f"Errore durante la scrittura dell'itinerario '{itinerario_dict.get('name', 'N/A')}' nel Report: {e}")

# Estrazione dati dal DB
db_itinerari = DbExtractor.get_data(CONNECTION_STRING, defaultLogger, errorLogger)
defaultLogger.info(f"Trovati {len(db_itinerari)} itinerari nel database.")

# Scrittura degli itinerari dal DB nel Report
try:
    if db_itinerari:
        FileWriter.write_existing_file("\n=== ITINERARI DAL DATABASE ===", errorLogger)
        for it in db_itinerari:
            try:
                report_line_db = "---" * 15 + "\n"
                report_line_db += f"| Itinerario (DB): {it.get('nome') or it.get('name')}\n"
                report_line_db += f"| ID: {it.get('id')}\n"

                # Track circuits se presenti
                tc_list = it.get('trackCircuits') or it.get('trackCircuitList') or []
                if tc_list:
                    report_line_db += "|   Dettagli TrackCircuit (DB):\n"
                    for tc in tc_list:
                        report_line_db += f"|     - Nome: {tc}\n"

                # Switch se presente
                switch_info = it.get('switch')
                if switch_info:
                    report_line_db += "|   Dettagli Switch (DB):\n"
                    if isinstance(switch_info, dict):
                        if 'SwitchMotorId' in switch_info or 'switchMotorId' in switch_info:
                            report_line_db += f"|     - Motor ID: {switch_info.get('SwitchMotorId') or switch_info.get('switchMotorId')}\n"
                        if 'SwitchMotorName' in switch_info or 'switchMotorName' in switch_info:
                            report_line_db += f"|     - Nome: {switch_info.get('SwitchMotorName') or switch_info.get('switchMotorName')}\n"
                        if 'SwitchMotorState' in switch_info or 'switchMotorState' in switch_info:
                            report_line_db += f"|     - Stato: {switch_info.get('SwitchMotorState') or switch_info.get('switchMotorState')}\n"
                    else:
                        report_line_db += f"|     - Dettagli: {switch_info}\n"

                report_line_db += "---" * 15 + "\n"
                FileWriter.write_existing_file(report_line_db, errorLogger)
                defaultLogger.info(f"Itinerario DB '{it.get('nome') or it.get('name')}' scritto correttamente nel Report.")
            except Exception as e:
                errorLogger.error(f"Errore durante la scrittura dell'itinerario DB '{it.get('nome') or it.get('name')}' nel Report: {e}")
    else:
        FileWriter.write_existing_file("\n(Nessun itinerario trovato nel database)", errorLogger)
except Exception as e:
    errorLogger.error(f"Errore generale durante la scrittura degli itinerari DB nel Report: {e}")

# Se l'estrazione è andata bene, procedi al confronto e al report
if db_itinerari:
    defaultLogger.info("Inizio confronto tra XML e database...")

    # Esegui il confronto principale
    ok_count, diff_count = Comparer.compare_data(listaItinerari, db_itinerari, defaultLogger, errorLogger)

    # Scrivi il riepilogo
    FileWriter.write_existing_file("\n=== RIEPILOGO ITINERARI ===", errorLogger)
    Comparer.write_summary(ok_count, diff_count, errorLogger)

    # Esegui le verifiche aggiuntive
    FileWriter.write_existing_file("\n=== VERIFICHE AGGIUNTIVE ===", errorLogger)
    Comparer.check_missing_itinerari(listaItinerari, db_itinerari, defaultLogger, errorLogger)

    defaultLogger.info("Confronto completato con successo.")
else:
    errorLogger.error("Il confronto non è stato eseguito a causa di errori di connessione al database.")


# Alla fine il root logger stampa un messaggio di completamento su console
Logger.termination_message()