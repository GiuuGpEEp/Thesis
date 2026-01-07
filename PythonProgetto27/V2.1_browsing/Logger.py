import os
import logging
import sys

# Setup del root logger - ovvero quello principale
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Module-level state to allow other modules to get loggers/output dir when they don't pass them explicitly
_output_dir = ""
_default_logger = None
_error_logger = None


def setup_directory_and_logger(output_dir=None):
    """Crea o reimposta gli handler di logging e restituisce (defaultLogger, errorLogger).

    Se `output_dir` è None viene usata una stringa vuota e i file di log vengono
    creati nella directory di lavoro corrente. I logger creati vengono memorizzati
    in variabili a livello di modulo così che altri moduli possano recuperarli
    tramite le funzioni getter.
    """
    global _output_dir, _default_logger, _error_logger

    # Setup della directory
    results_dir = ""
    try:
        if output_dir:
            results_dir = output_dir
            _output_dir = output_dir

        # Setup del file di log (if results_dir is empty this will be relative to cwd)
        log_file_path = os.path.join(results_dir, "logging.log")
        if os.path.exists(log_file_path):
            os.remove(log_file_path)
            logging.info(f"File di log '{log_file_path}' resettato con successo.")
    except Exception as e:
        logging.error(f"Errore durante la creazione della directory o del file di log: {e}")
        raise e

    try:
        # Setup del logger
        defaultLogger = logging.getLogger("DefaultLogger")
        defaultLogger.setLevel(logging.INFO)
        defaultLogger.propagate = False

        # Setup del primo handler per il file di log
        fileHandler = logging.FileHandler(log_file_path)
        fileHandler.setLevel(logging.INFO)
        fileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fileHandler.setFormatter(fileFormatter)

        # Remove existing handlers to avoid duplicates when reinitializing
        defaultLogger.handlers = []
        defaultLogger.addHandler(fileHandler)

        # Creazione del secondo logger per gli errori
        errorLogger = logging.getLogger("ErrorLogger")
        errorLogger.setLevel(logging.ERROR)
        errorLogger.propagate = False

        # Creazione del handler per il file di log degli errori
        errorFileHandler = logging.FileHandler(log_file_path, mode='a')
        errorFileHandler.setLevel(logging.ERROR)
        errorFileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        errorFileHandler.setFormatter(errorFileFormatter)

        errorLogger.handlers = []
        errorLogger.addHandler(errorFileHandler)

        # Store to module-level variables so other modules can get them later if they don't pass loggers explicitly
        _default_logger = defaultLogger
        _error_logger = errorLogger

    except Exception as e:
        logging.error(f"Errore durante la creazione dei logger: {e}")
        raise e

    return defaultLogger, errorLogger


def get_output_dir():
    """Restituisce l'ultima directory di output configurata (o stringa vuota per cwd)."""
    return _output_dir


def get_default_logger():
    """Restituisce il logger di default se configurato, altrimenti lo crea e lo restituisce."""
    global _default_logger, _error_logger
    if _default_logger is None or _error_logger is None:
        _default_logger, _error_logger = setup_directory_and_logger()
    return _default_logger


def get_error_logger():
    global _default_logger, _error_logger
    if _default_logger is None or _error_logger is None:
        _default_logger, _error_logger = setup_directory_and_logger()
    return _error_logger


# Messaggio di completamento da parte del root logger
def termination_message():
    logging.info("Tutte le operazioni sono state completate... Controllare Report e log per i dettagli.")