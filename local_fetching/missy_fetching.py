from utils.read_file import read_file
from typing import List, Any
from datetime import datetime

def get_vertretungen(date: datetime) -> List[Any]:
    
    endpoint_key = 'vertretungsfall_all'
    
    vertretungen = read_file(endpoint_key)
    
    sub_vertretungen = [vertretung for vertretung in vertretungen if datetime.strptime(vertretung["startdatum"], "%Y-%m-%d") <= date and datetime.strptime(vertretung["enddatum"], "%Y-%m-%d") >= date]
    
    return sub_vertretungen

def get_clients() -> List[Any]:
    
    endpoint_key = 'klient'
    
    clients = read_file(endpoint_key)
    
    return clients

def get_mas() -> List[Any]:
    
    endpoint_key = 'ma'
    
    mas = read_file(endpoint_key)
    
    return mas

def get_prio_assignments() -> List[Any]:
    
    endpoint_key = 'prio_assignment'
    
    assignments = read_file(endpoint_key)
    
    return assignments

def get_distances() -> List[Any]:
    
    endpoint_key = 'dist_ma_sch'
    
    distances = read_file(endpoint_key)
    
    return distances