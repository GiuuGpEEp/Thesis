import xml.etree.ElementTree as ET


def parsing(defaultLogger, errorLogger):
    
    # Caricamento del file XML
    try:
        defaultLogger.info("Caricamento del file XML")
        albero = ET.parse('Input/ITINERARI.xml')
        root = albero.getroot()
    except Exception as e:
        errorLogger.error(f"Errore durante il caricamento del file XML: {e}")
        return []

    listaItinerari = []

    # Navigo tutto il percorso: per trovare 'IXLItemList' e poi i vari 'IXLItem'
    try:
        defaultLogger.info("Inizio parsing degli itinerari con plantId '164'")
        for itinerario in root.findall('./IXLItemList/IXLItem'):

            # Accedo all'attributo 'plantId' con .get()
            if itinerario.get('plantId') == '164':
                itinerario_dict = {
                    "id": itinerario.get('plantId'),
                    "name": itinerario.get('name'),
                    "trackCircuitList": [],
                    "SwitchMotorId": None,
                    "SwitchMotorName": None,
                    "SwitchMotorState": None
                }

                # Prossimo nodo a cui accedere: 'TrackCircuitList' - Ci interessano solo i nomi dei vari trackCircuit   
                trackCircuitList = itinerario.find('TrackCircuitList')  
                if trackCircuitList is not None:
                    for trackCircuit in trackCircuitList.findall('TrackCircuit'):
                        trackCircuit_name = trackCircuit.get('name')
                        itinerario_dict["trackCircuitList"].append(trackCircuit_name)

                #Prossimo nodo a cui accedere: Switch - Navigo di elemento in elmento finchè non lo trovo
                switch_element = itinerario.find('PointList').find('Point').find('Switch')      
                if switch_element is not None:
                    itinerario_dict["SwitchMotorId"] = switch_element.get('switchMotorId')
                    itinerario_dict["SwitchMotorName"] = switch_element.get('switchMotorName')
                    itinerario_dict["SwitchMotorState"] = switch_element.get('switchMotorState')
                
                listaItinerari.append(itinerario_dict)
                defaultLogger.info(f"Parsing itinerario: {itinerario_dict['name']} completato con successo.")

    except Exception as e:
        errorLogger.error(f"Errore durante il parsing degli itinerari: {e}")
    return listaItinerari        


