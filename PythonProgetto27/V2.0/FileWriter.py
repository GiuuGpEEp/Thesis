import os
from datetime import datetime
import Logger
import sys


def file_create(defaultLogger, errorLogger):
    if os.path.exists("Results/Report.txt"):
        os.remove("Results/Report.txt")

    try:    
        f = open("Results/Report.txt", "w")
        f.write("=====================================\n")
        f.write("         REPORT DELLE ATTIVITA'       \n")
        f.write("=====================================\n\n")
        f.write(f"Report generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        defaultLogger.info("File Report.txt creato con successo.")
    except Exception as e:
        errorLogger.error(f"Errore durante la creazione del file Report.txt: {e}")
        raise

def write_existing_file(line: str, errorLogger):
    if not os.path.exists("Results/Report.txt"):
        errorLogger.error("Il file Report.txt non esiste... Tentativo di creazione in corso.")
        file_create()
    try:
        f = open("Results/Report.txt", "a")
        f.write(line + "\n")
        f.close() 
    except Exception as e:
        errorLogger.error(f"Errore durante la scrittura nel file Report.txt: {e}")
        raise



