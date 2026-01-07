import os 
import logging
import sys

#Setup del root logger - ovvero quello principale
logging.basicConfig(
    level = logging.INFO,
    stream = sys.stdout,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

#Setup della cartella, del file di log e dei logger
def setup_directory_and_logger():
    
    #Setup della directory
    results_dir = "Results"
    try:
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            logging.info(f"Directory '{results_dir}' creata con successo.")
        
        #Setup del file di log
        log_file_path = os.path.join(results_dir, "logging.log")
        if os.path.exists(log_file_path):
            os.remove(log_file_path)
            logging.info(f"File di log '{log_file_path}' resettato con successo.")
    
    except Exception as e:
        logging.error(f"Errore durante la creazione della directory o del file di log: {e}")
        raise e
        
    try:

        #Setup del logger
        defaultLogger = logging.getLogger("DefaultLogger")
        defaultLogger.setLevel(logging.INFO)
        defaultLogger.propagate = False  # Evita la propagazione al root logger - in questo modo evito che questo logger usi la stessa configurazione del root logger e non mandi quindi messaggi anche su terminale

        #Setup del primo handler per il file di log
        fileHandler = logging.FileHandler(log_file_path)
        fileHandler.setLevel(logging.INFO)
        fileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fileHandler.setFormatter(fileFormatter)
        
        #Aggiunta degli handler al logger
        defaultLogger.addHandler(fileHandler)
        
        #Creazione del secondo logger per gli errori
        errorLogger = logging.getLogger("ErrorLogger")
        errorLogger.setLevel(logging.ERROR)
        errorLogger.propagate = False  # Evita la propagazione al root logger - in questo modo evito che questo logger usi la stessa configurazione del root logger e non mandi quindi messaggi anche su terminale

        #Creazione del handler per il file di log degli errori
        errorFileHandler = logging.FileHandler(log_file_path, mode = 'a')
        errorFileHandler.setLevel(logging.ERROR)
        errorFileFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        errorFileHandler.setFormatter(errorFileFormatter)

        #Aggiunta dell'handler al logger degli errori
        errorLogger.addHandler(errorFileHandler)
    
    except Exception as e:
        logging.error(f"Errore durante la creazione dei logger: {e}")
        raise e    

    return defaultLogger, errorLogger 

# Messaggio di completamento da parte del root logger
def termination_message():
    logging.info("Tutte le operazioni sono state completate... Controllare Report e log per i dettagli.")