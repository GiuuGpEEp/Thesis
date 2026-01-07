import logging
import FileWriter

N_ITINERARI_ATTESI = 8 

def compare_data(xml_itine, db_itine, defaultLogger, errorLogger):
    """
    Confronta i dati estratti dall'XML e dal DB e scrive i dettagli delle differenze.
    """
    # Per evitare ogni volta di accedere all'elemento del dizionario
    # creo delle mappe che associano il nome dell'itinerario al suo dizionario
    xml_itine_map = {it['name']: it for it in xml_itine}
    db_itine_map = {it['nome']: it for it in db_itine} # Assumendo che 'nome' sia la chiave DB
    
    ok_count = 0
    diff_count = 0

    for xml_name, xml_item in xml_itine_map.items():
        
        # 1. Prima controllo i nomi degli itinerari (XML -> DB)
        if xml_name not in db_itine_map:
            # Qui non ci preoccupiamo della formattazione estesa dei separatori, 
            # usiamo solo la scrittura di base come fai tu.
            FileWriter.write_existing_file(f"• Itinerario {xml_name}\n", errorLogger)
            FileWriter.write_existing_file("    Stato: MANCANTE (presente in XML ma assente nel DB)\n\n", errorLogger)
            defaultLogger.warning(f"Itinerario '{xml_name}' presente in XML ma assente nel DB.")
            continue

        # Ora confronto i dettagli dei vari itinerari
        db_item = db_itine_map[xml_name]
        differences = []

        # 2. Confronto TrackCircuitList: LOGICA DI SET PER ISOLARE I MANCANTI
        
        # Normalizzazione dei nomi TC per XML (possono essere dict con chiave 'name' o stringhe)
        xml_tc_raw = xml_item.get('trackCircuitList', [])
        xml_tc_names = set(
            (tc if isinstance(tc, str) else tc.get('name'))
            for tc in xml_tc_raw
            if (tc if isinstance(tc, str) else tc.get('name')) is not None
        )

        # Normalizzazione dei nomi TC per DB (possono essere dict con chiave 'cdb' o stringhe)
        db_tc_raw = db_item.get('trackCircuits', [])
        db_tc_names = set(
            (tc if isinstance(tc, str) else tc.get('cdb'))
            for tc in db_tc_raw
            if (tc if isinstance(tc, str) else tc.get('cdb')) is not None
        )

        # Calcola le differenze
        missing_in_db = xml_tc_names - db_tc_names # TC presenti in XML ma non nel DB
        missing_in_xml = db_tc_names - xml_tc_names # TC presenti in DB ma non nell'XML
        
        if missing_in_db:
            for tc_name in missing_in_db:
                # Genera il messaggio specifico richiesto
                differences.append(f"TrackCircuit {tc_name} non trovato nel DB.")
        
        if missing_in_xml:
            for tc_name in missing_in_xml:
                 # Genera un messaggio specifico per la direzione opposta
                differences.append(f"TrackCircuit {tc_name} non trovato nell'XML.")
        

        # 3. Confronto Switch (Normalizzazione mantenuta)
        def _norm(v):
            if v is None:
                return None
            s = str(v).strip()
            return s if s != '' else None

        xml_switch = {
            'SwitchMotorId': _norm(xml_item.get('SwitchMotorId')),
            'SwitchMotorName': _norm(xml_item.get('SwitchMotorName')),
            'SwitchMotorState': _norm(xml_item.get('SwitchMotorState')),
        }
        # Il DB_extractor popola la chiave 'switch' e può usare due formati:
        # 1) {'id': ..., 'name': ..., 'state': ...}
        # 2) {'SwitchMotorId': ..., 'SwitchMotorName': ..., 'SwitchMotorState': ...}
        db_switch_raw = db_item.get('switch') or {}

        # Rileva il formato e normalizza ai campi usati dall'XML-side
        if 'SwitchMotorId' in db_switch_raw or 'SwitchMotorName' in db_switch_raw or 'SwitchMotorState' in db_switch_raw:
            db_switch = {
                'SwitchMotorId': _norm(db_switch_raw.get('SwitchMotorId')),
                'SwitchMotorName': _norm(db_switch_raw.get('SwitchMotorName')),
                'SwitchMotorState': _norm(db_switch_raw.get('SwitchMotorState')),
            }
        else:
            db_switch = {
                'SwitchMotorId': _norm(db_switch_raw.get('id')),
                'SwitchMotorName': _norm(db_switch_raw.get('name')),
                'SwitchMotorState': _norm(db_switch_raw.get('state')),
            }
        
        # Confronto
        if xml_switch['SwitchMotorId'] != db_switch['SwitchMotorId']:
            differences.append(
                f"SwitchMotorId non corrispondente. XML: {xml_switch['SwitchMotorId']}, DB: {db_switch['SwitchMotorId']}"
            )
        # Il nome dello switch è meno critico e spesso è lo stesso, ma lo teniamo per completezza
        if xml_switch['SwitchMotorName'] != db_switch['SwitchMotorName']:
            differences.append(
                f"SwitchMotorName non corrispondente. XML: {xml_switch['SwitchMotorName']}, DB: {db_switch['SwitchMotorName']}"
            )
        if xml_switch['SwitchMotorState'] != db_switch['SwitchMotorState']:
            differences.append(
                f"SwitchMotorState non corrispondente. XML: {xml_switch['SwitchMotorState']}, DB: {db_switch['SwitchMotorState']}"
            )
        
        # --- Scrittura nel report ---
        FileWriter.write_existing_file(f"• Itinerario {xml_name}\n", errorLogger)
        if not differences:
            FileWriter.write_existing_file("    Stato: OK\n\n", errorLogger)
            ok_count += 1
        else:
            FileWriter.write_existing_file("    Stato: DIFFERENZE\n", errorLogger)
            FileWriter.write_existing_file("    Dettagli:\n", errorLogger)
            for diff in differences:
                # Nota: qui ho usato 5 spazi e un trattino per allineare l'output al tuo esempio
                FileWriter.write_existing_file(f"      - {diff}\n", errorLogger) 
                errorLogger.error(f"DIFF. Itinerario '{xml_name}': {diff}")
            FileWriter.write_existing_file("\n", errorLogger)
            diff_count += 1
            
    return ok_count, diff_count

def write_summary(ok_count, diff_count, errorLogger):
    """Scrive il riepilogo nel formato richiesto."""
    FileWriter.write_existing_file(f" - OK: {ok_count}\n", errorLogger)
    FileWriter.write_existing_file(f" - Con differenze: {diff_count}\n", errorLogger)

def check_missing_itinerari(xml_items, db_items, defaultLogger, errorLogger):
    """Verifica la presenza bidirezionale e i conteggi totali."""
    db_map = {item['nome']: item for item in db_items}
    xml_map = {item['name']: item for item in xml_items}

    FileWriter.write_existing_file("\n", errorLogger) # Riga vuota dopo l'intestazione
    
    # 1. Itinerari nel DB ma non nell'XML
    for db_name in db_map.keys():
        if db_name not in xml_map:
            FileWriter.write_existing_file(f"  - [MANCANTE] Itinerario {db_name}: presente nel DB ma assente nel XML.\n", errorLogger)
            defaultLogger.warning(f"Itinerario '{db_name}' presente nel DB ma assente nell'XML.")
    
    # 2. Confronto conteggi totali
    db_count = len(db_items)
    xml_count = len(xml_items)
    
    if db_count > xml_count:
        FileWriter.write_existing_file(f"  - [WARNING] Il DB ha più itinerari ({db_count}) del XML ({xml_count})!\n", errorLogger)
    elif xml_count > db_count:
        FileWriter.write_existing_file(f"  - [ERRORE] XML ha più itinerari ({xml_count}) del DB ({db_count})!\n", errorLogger)

    # 3. Check sul numero atteso di itinerari
    if db_count != N_ITINERARI_ATTESI:
        FileWriter.write_existing_file(f"  - [ANOMALIA] Numero itinerari trovati nel DB: {db_count}, aspettati: {N_ITINERARI_ATTESI}\n", errorLogger)