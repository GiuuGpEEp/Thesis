
import xml.etree.ElementTree as ET
import Logger


def parsing(xml_path=None, defaultLogger=None, errorLogger=None):
    """Analizza l'XML fornito e restituisce una lista di itinerari per plantId '164'.

    La firma mette `xml_path` come primo argomento per permettere di chiamare
    `Parser.parsing()` nei test senza passare argomenti. Se i logger non vengono
    forniti, vengono ottenuti dal modulo `Logger`.
    """
    if defaultLogger is None:
        defaultLogger = Logger.get_default_logger()
    if errorLogger is None:
        errorLogger = Logger.get_error_logger()

    if not xml_path:
        errorLogger.error("Nessun percorso XML fornito a Parser.parsing.")
        return []

    defaultLogger.info(f"Parsing file: {xml_path}")
    # apri/parsa usando xml_path
    try:
        albero = ET.parse(xml_path)
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

                # Prossimo nodo a cui accedere: Switch - protezione contro elementi mancanti
                switch_element = None
                point_list = itinerario.find('PointList')
                if point_list is not None:
                    first_point = point_list.find('Point')
                    if first_point is not None:
                        switch_element = first_point.find('Switch')

                if switch_element is not None:
                    itinerario_dict["SwitchMotorId"] = switch_element.get('switchMotorId')
                    itinerario_dict["SwitchMotorName"] = switch_element.get('switchMotorName')
                    itinerario_dict["SwitchMotorState"] = switch_element.get('switchMotorState')

                listaItinerari.append(itinerario_dict)
                defaultLogger.info(f"Parsing itinerario: {itinerario_dict.get('name')} completato con successo.")

    except Exception as e:
        errorLogger.error(f"Errore durante il parsing degli itinerari: {e}")
    return listaItinerari


