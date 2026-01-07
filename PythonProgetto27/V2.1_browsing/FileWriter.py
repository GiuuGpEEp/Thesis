import os
from datetime import datetime
import Logger
import sys


def _report_path():
    base = Logger.get_output_dir()
    return os.path.join(base, "Report.txt")


def file_create(defaultLogger=None, errorLogger=None):
    """
    Crea/ricrea il file Report.txt dentro la cartella di output (scelta dall'utente).
    Se i logger non sono forniti, vengono presi dal modulo `Logger`.
    """
    if defaultLogger is None:
        defaultLogger = Logger.get_default_logger()
    if errorLogger is None:
        errorLogger = Logger.get_error_logger()

    report = _report_path()
    try:
        # Assicurati che la cartella esista
        os.makedirs(os.path.dirname(report), exist_ok=True)
        if os.path.exists(report):
            os.remove(report)

        with open(report, "w", encoding='utf-8') as f:
            f.write("=====================================\n")
            f.write("         REPORT DELLE ATTIVITA'       \n")
            f.write("=====================================\n\n")
            f.write(f"Report generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        defaultLogger.info(f"File Report.txt creato con successo in: {report}")
    except Exception as e:
        # If errorLogger is None, try to get it (defensive)
        if errorLogger is None:
            errorLogger = Logger.get_error_logger()
        errorLogger.error(f"Errore durante la creazione del file Report.txt: {e}")
        raise


def write_existing_file(line: str, errorLogger=None, defaultLogger=None):
    """
    Appende una riga a Report.txt nella cartella di output.
    Se il file non esiste tenta di crearlo usando i logger disponibili.
    """
    if defaultLogger is None:
        defaultLogger = Logger.get_default_logger()
    if errorLogger is None:
        errorLogger = Logger.get_error_logger()

    report = _report_path()
    if not os.path.exists(report):
        errorLogger.error("Il file Report.txt non esiste... Tentativo di creazione in corso.")
        # crea il file con i logger correnti (defaultLogger e errorLogger)
        try:
            file_create(defaultLogger, errorLogger)
        except Exception:
            # se non riesce a creare il file, rilancia l'errore
            raise

    try:
        with open(report, "a", encoding='utf-8') as f:
            f.write(line + "\n")
    except Exception as e:
        errorLogger.error(f"Errore durante la scrittura nel file Report.txt: {e}")
        raise



