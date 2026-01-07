import logging
import FileWriter

N_ITINERARI_ATTESI = 8 

def compare_data(xml_itine, db_itine, defaultLogger, errorLogger):

    # Per evitare ogni volta di accedere all'elemento del dizionario
    # creo delle mappe che associno il nome dell'itinerario al suo dizionario
    xml_itine_map = {it['name']: it for it in xml_itine}
    db_itine_map = {it['nome']: it for it in db_itine}

    ok_count = 0
    diff_count = 0

    for xml_name, xml_item in xml_itine_map.items():
        
        # Prima controllo i nomi degli itinerari
        if xml_name not in db_itine_map:
            FileWriter.write_existing_file(f"• Itinerario {xml_name}\n", errorLogger)
            FileWriter.write_existing_file("    Stato: MANCANTE (presente in XML ma assente nel DB)\n\n", errorLogger)
            defaultLogger.warning(f"Itinerario '{xml_name}' presente in XML ma assente nel DB.")
            continue

        # Ora confronto i dettagli dei vari itinerari
        db_item = db_itine_map[xml_name] # prende l'elemento corrispondende dal db cercando per nome
        differences = []

        # Confronto TrackCircuitList (normalizzazione: possono essere stringhe o dict)
        xml_tc_raw = xml_item.get('trackCircuitList', [])
        db_tc_raw = db_item.get('trackCircuits', [])

        xml_trackcircuits = [
            (tc if isinstance(tc, str) else tc.get('name'))
            for tc in xml_tc_raw
        ]
        xml_trackcircuits = [tc for tc in xml_trackcircuits if tc is not None]

        db_trackcircuits = [
            (tc if isinstance(tc, str) else tc.get('cdb'))
            for tc in db_tc_raw
        ]
        db_trackcircuits = [tc for tc in db_trackcircuits if tc is not None]

        if xml_trackcircuits != db_trackcircuits:
            differences.append(f"TrackCircuits non corrispondenti. XML: {xml_trackcircuits}, DB: {db_trackcircuits}")

        # Confronto Switch
        # Normalizzazione per evitare mismatch di tipo (str vs int)
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
        db_switch_raw = db_item.get('switch') or {}
        db_switch = {
            'SwitchMotorId': _norm(db_switch_raw.get('SwitchMotorId')),
            'SwitchMotorName': _norm(db_switch_raw.get('SwitchMotorName')),
            'SwitchMotorState': _norm(db_switch_raw.get('SwitchMotorState')),
        }

        if xml_switch['SwitchMotorId'] != db_switch['SwitchMotorId']:
            differences.append(
                f"SwitchMotorId non corrispondente. XML: {xml_switch['SwitchMotorId']}, DB: {db_switch['SwitchMotorId']}"
            )
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
                FileWriter.write_existing_file(f"      - {diff}\n", errorLogger)
                errorLogger.error(f"DIFF. Itinerario '{xml_name}': {diff}")
            FileWriter.write_existing_file("\n", errorLogger)
            diff_count += 1
            
    return ok_count, diff_count

def write_summary(ok_count, diff_count, errorLogger):
    FileWriter.write_existing_file("  - OK: {}".format(ok_count), errorLogger)
    FileWriter.write_existing_file("  - Con differenze: {}".format(diff_count), errorLogger)

def check_missing_itinerari(xml_items, db_items, defaultLogger, errorLogger):
    # Nel DB la chiave è 'nome', nell'XML è 'name'
    db_map = {item['nome']: item for item in db_items}
    xml_map = {item['name']: item for item in xml_items}

    FileWriter.write_existing_file("\nVerifiche aggiuntive", errorLogger)

    # 1. Itinerari nel DB ma non nell'XML
    for db_name in db_map.keys():
        if db_name not in xml_map:
            FileWriter.write_existing_file(f"  - [MANCANTE] Itinerario {db_name}: presente nel DB ma assente nel XML.", errorLogger)
            defaultLogger.warning(f"Itinerario '{db_name}' presente nel DB ma assente nell'XML.")
    
    # 2. Confronto conteggi totali
    db_count = len(db_items)
    xml_count = len(xml_items)
    
    if db_count > xml_count:
        FileWriter.write_existing_file(f"  - [WARNING] Il DB ha più itinerari ({db_count}) del XML ({xml_count})!", errorLogger)
    elif xml_count > db_count:
        FileWriter.write_existing_file(f"  - [ERRORE] XML ha più itinerari ({xml_count}) del DB ({db_count})!", errorLogger)

    # 3. Check sul numero atteso di itinerari
    if db_count != N_ITINERARI_ATTESI:
        FileWriter.write_existing_file(f"  - [ANOMALIA] Numero itinerari trovati nel DB: {db_count}, aspettati: {N_ITINERARI_ATTESI}", errorLogger)





