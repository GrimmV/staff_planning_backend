from typing import Tuple, List, Dict

def filter_mabw_records(records: List) -> Tuple[List]:
    
    open_clients = []
    
    for record in records:
        if record["typ"] == "mabw" and 'klientzubegleiten' in record:
            open_clients.append(record)
                
    return open_clients