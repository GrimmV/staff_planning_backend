from local_fetching.missy_fetching import get_distances, get_clients, get_mas, get_prio_assignments, get_vertretungen
from local_fetching.experience_logging import get_experience_log
from datetime import datetime, timedelta
from data_processing.data_processor import DataProcessor
import random
from data_processing.features_retrieval.retrieve_objects import get_objects_by_id
from learning.model import AbnormalityModel
from optimize.optimize import Optimizer
from typing import Dict

random.seed(42)

def get_recommendation(hard_constraints: Dict = {}):
    distances = get_distances()
    clients = get_clients()
    mas = get_mas()
    prio_assignments = get_prio_assignments()
    experience_log = get_experience_log()

    date = datetime(2025, 3, 21)
    vertretungen = get_vertretungen(date)

    data_processor = DataProcessor(mas, clients, prio_assignments, distances, experience_log)

    # Retrieve open clients from todays vertretungen
    open_clients_vertretung = data_processor.get_mabw_records(vertretungen)
    open_client_ids = [open_client["klientzubegleiten"]["id"] for open_client in open_clients_vertretung]
    open_clients = get_objects_by_id(clients, open_client_ids)

    known_mas = [experience["ma"] for experience in experience_log]
    # sample len(open_clients)-2 random elements from mas
    open_ma_ids = random.sample(known_mas, len(open_clients)-2)
    open_mas = get_objects_by_id(mas, open_ma_ids)

    clients_df, mas_df = data_processor.create_day_dataset(open_clients, open_mas, date)

    # iterate over the mas_df and add a column "available_until" based on the free_ma_ids in the form {"id": "123", "until": "2025-01-01"}
    # First, generate the column with the correct values and then add it to the dataframe
    mas_df["available_until"] = [date + timedelta(days=random.randint(1, 10)) for _ in range(len(mas_df))]
    clients_df["available_until"] = clients_df["id"].map(lambda x: next((datetime.strptime(item["enddatum"], "%Y-%m-%d") for item in open_clients_vertretung if item["klientzubegleiten"]["id"] == x), None))

    abnormality_model = AbnormalityModel()

    optimizer = Optimizer(mas_df, clients_df, hard_constraints, abnormality_model)
    optimizer.create_model()

    objective_value = optimizer.solve_model()
    print(f"Objective Value: {objective_value}")

    if objective_value is not None:
        results = optimizer.process_results()
        return {"assignment_info": results, "mas": mas_df.to_dict(orient="records"), "clients": clients_df.to_dict(orient="records")}
    else:
        print("No feasible solution found.")
        # return {"assignment_info": None, "mas": mas_df.to_dict(orient="records"), "clients": clients_df.to_dict(orient="records")}
        return None
    
if __name__ == "__main__":
    hard_constraints = {
        "forced_assignments": [("29df0d1c-9248-4fb1-a201-153fc8eea8b1", '9b932fa7-df20-4361-99bc-b7947e69960e')],
        # "forced_clients": ["0ba5e25a-e7de-4dee-aa1f-090160f6e380", "a29858e5-994d-4841-b038-ef5d6eecece7"],
    }
    output = get_recommendation(hard_constraints)
    print(f"Assignment Info: {output['assignment_info']}")
    print(f"MAS: {output['mas']}")
    print(f"Clients: {output['clients']}")