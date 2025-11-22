from typing import List, Dict, Any, Tuple
from read_file import read_file
from name_generator import load_name_mappings
import statistics
import json


Z_THRESHOLD = 2.0  # flag added values with |z| >= Z_THRESHOLD as 'significantly different'

feature_mapping_dr = {
    "timeToSchool": "Fahrtzeit / 1000 in Minuten",
    "cl_experience": "Erfahrung mit Klient",
    "short_term_cl_experience": "Erfahrung mit Klient in letzten zwei Wochen",
    "school_experience": "Erfahrung mit Schule",
    "priority": "Klienten-Priorität (10 = sehr hoch, 100 = sehr niedrig)",
    "mobility": "Mobilität",
    "geschlecht_relevant": "Geschlecht relevant",
    "availability_gap": "Verfügbarkeit des Mitarbeiters im Vergleich zum Klienten in Tagen",
    "abnormality_score": "Abnormalität (-1 = abnormal, 1 = normal)",
}

name_mappings = load_name_mappings()

def key_of(item: Dict) -> Tuple[str, str]:
    return item['ma'], item['klient']


def is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def gather_numeric_fields(items: List[Dict]) -> List[str]:
    fields = set()
    for it in items:
        for k, v in it.items():
            if is_number(v):
                fields.add(k)
    return sorted(fields)


def compute_basic_stats(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {'anzahl': 0, 'mittelwert': None, 'median': None, 'standardabweichung': None}
    count = len(values)
    mean = statistics.mean(values)
    median = statistics.median(values)
    std = None
    if count >= 2:
        # sample standard deviation
        try:
            std = statistics.pstdev(values)  # population stdev is fine here; use stdev() if you prefer sample
        except Exception:
            std = None
    return {'anzahl': count, 'mittelwert': mean, 'median': median, 'standardabweichung': std}


def field_values(items: List[Dict], field: str) -> List[float]:
    vals = []
    for it in items:
        v = it.get(field)
        if is_number(v):
            vals.append(float(v))
    return vals


def analyze_added_removed(old: List[Dict], new: List[Dict], z_threshold: float = Z_THRESHOLD) -> Dict:
    # Build maps and lists (same as your simplified diff)
    old_map = {key_of(x): x for x in old}
    new_map = {key_of(x): x for x in new}

    added = []
    removed = []
    all_keys = set(old_map.keys()) | set(new_map.keys())

    for k in all_keys:
        if k in old_map and k not in new_map:
            transformed_old_map = {feature_mapping_dr.get(k, k): v for k, v in old_map[k].items() if k in feature_mapping_dr}
            transformed_old_map["ma"] = name_mappings[old_map[k]['ma']]
            transformed_old_map["klient"] = name_mappings[old_map[k]['klient']]
            removed.append(transformed_old_map)
        elif k not in old_map and k in new_map:
            transformed_new_map = {feature_mapping_dr.get(k, k): v for k, v in new_map[k].items() if k in feature_mapping_dr}
            transformed_new_map["ma"] = name_mappings[new_map[k]['ma']]
            transformed_new_map["klient"] = name_mappings[new_map[k]['klient']]
            added.append(transformed_new_map)

    # Gather numeric fields across both sets (and old/new to compute totals)
    numeric_fields = gather_numeric_fields(old + new)

    # Prepare stats containers
    stats = {
        'felder': {},
        'abnormalitat': {
            'hinzugefügt': {'anzahl': 0, 'anteil': 0.0},
            'entfernt': {'anzahl': 0, 'anteil': 0.0}
        },
        'anzahl': {
            'alt': len(old),
            'neu': len(new),
            'hinzugefügt': len(added),
            'entfernt': len(removed)
        }
    }

    # Abnormality counts
    def count_abnormal(items_list: List[Dict]) -> int:
        return sum(1 for it in items_list if it.get(feature_mapping_dr['abnormality_score']) == -1)

    n_ab_added = count_abnormal(added)
    n_ab_removed = count_abnormal(removed)
    stats['abnormalitat']['hinzugefügt']['anzahl'] = n_ab_added
    stats['abnormalitat']['entfernt']['anzahl'] = n_ab_removed
    stats['abnormalitat']['hinzugefügt']['anteil'] = (n_ab_added / len(added)) if added else None
    stats['abnormalitat']['entfernt']['anteil'] = (n_ab_removed / len(removed)) if removed else None

    # Per-field basic stats for old, new, added, removed
    for field in numeric_fields:
        transformed_field = feature_mapping_dr.get(field, field)
        vals_added = field_values(added, transformed_field)
        vals_removed = field_values(removed, transformed_field)

        stats['felder'][transformed_field] = {
            'hinzugefügt': compute_basic_stats(vals_added),
            'entfernt': compute_basic_stats(vals_removed),
            # change in mean added - removed
            'mittelwert_änderung_hinzugefügt_minus_entfernt': None if (not vals_added or not vals_removed) else statistics.mean(vals_added) - statistics.mean(vals_removed)
        }

    return {
        'hinzugefügt': added,
        'entfernt': removed,
        'stats': stats,
    }


if __name__ == "__main__":
    recommendations = read_file("recommendation_cache")
    # Use the two consecutive recommendation dumps like in your script (guard for length)
    if len(recommendations) < 2:
        raise SystemExit("Need at least two recommendation snapshots in 'recommendation_cache'")

    first_set = recommendations[0]["output"]["assignment_info"]["assigned_pairs"]
    second_set = recommendations[1]["output"]["assignment_info"]["assigned_pairs"]

    result = analyze_added_removed(first_set, second_set, z_threshold=Z_THRESHOLD)

    print(json.dumps(result, indent=4))
