import pyodbc
import logging 

STATE_MAP = {'R' : 2, 'N' : 1} # Mappa per convertire lo stato da stringa a intero

def get_data(conn_string, defaultLogger, errorLogger):
    db_itinerari = {}
    conn = None
    cursor = None

    defaultLogger.info("Connessione al database in corso...")
    try:
        # Connessione al database
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()
        defaultLogger.info("Connessione al database avvenuta con successo.")

        # --- QUERY 1: Recupero degli itinerari dalla tabella dbo.itinerari ---
        defaultLogger.info("Recupero degli itinerari dal database...")
        cursor.execute("SELECT id_itine, nome FROM dbo.itinerari WHERE id_itine IS NOT NULL;")
        for row in cursor.fetchall():  # tramite fetchall() ottengo una lista di tuple, ovvero tutte quelle risultanti dalla query
            id_itine = row[0]
            nome_itine = row[1].strip()
            db_itinerari[nome_itine] = {
                'id': id_itine,
                'nome': nome_itine,
                'trackCircuits': [],
                'switch': None
            }
        defaultLogger.info(f"Operazione completata con successo. Sono stati caricati: {len(db_itinerari)} itinerari.")

        # --- QUERY 2: Recupero delle informazioni sui vari blocchi nella tabella dbo.tc_bloccamenti_dv_itine ---
        cursor.execute("SELECT id_itine, cdb, ente, id_ente FROM dbo.tc_bloccamenti_dv_itine;")
        blocchi_per_itine = {}
        for row in cursor.fetchall():
            id_itine_b = row[0]
            cdb = row[1].strip() 
            ente = row[2].strip()
            id_ente = row[3]
            
            # associo ad ogni id una lista di elementi (cdb, ente, id_ente)
            # usare setdefault mi permette di inizializzare la lista se la chiave non esiste
            blocchi_per_itine.setdefault(id_itine_b, []).append({
                'cdb': cdb,
                'ente': ente,
                'id_ente': id_ente
            })

        # --- QUERY 3: Recupero info switch (tc_it_lib_dev_percorso) ---
        cursor.execute("SELECT id_itine, id_cassa, nome, statocassa FROM dbo.tc_it_lib_dev_percorso;")
        percorsi_switch = {}
        for row in cursor.fetchall():
            ps_id_itine = row[0]
            id_cassa = row[1]
            nome = row[2].strip() if row[2] else None
            stato_symbol = row[3].strip() if row[3] else None
            stato = STATE_MAP.get(stato_symbol, None)
            # Usiamo (id_itine, id_ente) come chiave; qui id_cassa funge da id_ente per il join
            percorsi_switch[(ps_id_itine, id_cassa)] = {'name': nome, 'state': stato}

        # Merge: blocchi e switch sugli itinerari
        for _, itine_dict in db_itinerari.items():
            id_itine = itine_dict['id']
            for blocco in blocchi_per_itine.get(id_itine, []):
                
                # Track circuits
                cdb_name = blocco.get('cdb')
                if cdb_name:
                    itine_dict['trackCircuits'].append(cdb_name)

                # Switch: se cdb != ente, prova join su (id_itine, id_ente)
                if blocco.get('cdb') != blocco.get('ente'):
                    key = (id_itine, blocco.get('id_ente'))
                    percorso_data = percorsi_switch.get(key)
                    if percorso_data:
                        itine_dict['switch'] = {
                            'SwitchMotorId': blocco.get('id_ente'),
                            'SwitchMotorName': percorso_data.get('name'),
                            'SwitchMotorState': percorso_data.get('state')
                        }

            # Deduplica mantenendo l'ordine
            if itine_dict['trackCircuits']:
                itine_dict['trackCircuits'] = list(dict.fromkeys(itine_dict['trackCircuits']))

        defaultLogger.info("Recupero e merge dei dati completato con successo.")
        return list(db_itinerari.values())

    except pyodbc.Error as err:
        msg = err.args if getattr(err, 'args', None) else str(err)
        errorLogger.error(f"Errore durante l'accesso al database: {msg}", exc_info=True)
        return []
    except Exception as e:
        errorLogger.error(
            f"Errore inaspettato durante l'estrazione dei dati: {type(e).__name__}: {e} | args={getattr(e, 'args', None)}",
            exc_info=True
        )
        return []
    finally:
        try:
            if cursor is not None:
                cursor.close()
            if conn is not None:
                conn.close()
            defaultLogger.info("Connessione al database chiusa.")
        except Exception as close_err:
            errorLogger.error(f"Errore durante la chiusura della connessione al database: {close_err}")
