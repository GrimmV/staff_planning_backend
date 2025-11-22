import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import os


CACHE_FILE = "data/recommendation_cache.json"


def _normalize_hard_constraints(hard_constraints: Dict) -> Dict:
    """
    Normalize hard constraints for consistent comparison.
    Sorts lists and tuples to ensure consistent hashing.
    """
    normalized = {}
    
    # Sort forced_assignments (list of tuples)
    if "forced_assignments" in hard_constraints:
        normalized["forced_assignments"] = sorted(
            [tuple(sorted(assignment)) if isinstance(assignment, (list, tuple)) else assignment 
             for assignment in hard_constraints["forced_assignments"]]
        )
    
    # Sort forced_employees (list)
    if "forced_employees" in hard_constraints:
        normalized["forced_employees"] = sorted(hard_constraints["forced_employees"])
    
    # Sort forced_clients (list)
    if "forced_clients" in hard_constraints:
        normalized["forced_clients"] = sorted(hard_constraints["forced_clients"])
    
    # Sort banned_assignments (list of tuples)
    if "banned_assignments" in hard_constraints:
        normalized["banned_assignments"] = sorted(
            [tuple(sorted(assignment)) if isinstance(assignment, (list, tuple)) else assignment 
             for assignment in hard_constraints["banned_assignments"]]
        )
    
    return normalized


def _hash_hard_constraints(hard_constraints: Dict) -> str:
    """
    Create a hash of the normalized hard constraints for quick lookup.
    """
    normalized = _normalize_hard_constraints(hard_constraints)
    # Convert to JSON string and hash it
    constraints_str = json.dumps(normalized, sort_keys=True)
    return hashlib.md5(constraints_str.encode()).hexdigest()


def _load_cache() -> List[Dict]:
    """
    Load the cache from file. Returns empty list if file doesn't exist.
    """
    if not os.path.exists(CACHE_FILE):
        return []
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading cache: {e}")
        return []


def _save_cache(cache: List[Dict]) -> None:
    """
    Save the cache to file.
    """
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False, default=str)


def has_seen_constraints(hard_constraints: Dict) -> bool:
    """
    Check if the given hard constraints have been seen before.
    """
    cache = _load_cache()
    constraint_hash = _hash_hard_constraints(hard_constraints)
    
    for entry in cache:
        if entry.get("constraint_hash") == constraint_hash:
            return True
    
    return False


def get_cached_result(hard_constraints: Dict) -> Optional[Dict]:
    """
    Retrieve cached result for the given hard constraints.
    Returns None if not found.
    Updates last_access timestamp and moves entry to end of list.
    """
    cache = _load_cache()
    constraint_hash = _hash_hard_constraints(hard_constraints)
    
    for i, entry in enumerate(cache):
        if entry.get("constraint_hash") == constraint_hash:
            # Update last_access timestamp
            entry["last_access"] = datetime.now().isoformat()
            # Move entry to end of list
            cache.pop(i)
            cache.append(entry)
            _save_cache(cache)
            return entry.get("output")
    
    return None


def cache_result(hard_constraints: Dict, output: Dict) -> None:
    """
    Cache a new result with its associated hard constraints.
    If entry already exists, moves it to the end of the list and updates last_access.
    Appends new entries to the end of the cache list (newest at the end).
    """
    cache = _load_cache()
    constraint_hash = _hash_hard_constraints(hard_constraints)
    normalized_constraints = _normalize_hard_constraints(hard_constraints)
    current_time = datetime.now().isoformat()
    
    # Check if this exact constraint set already exists
    for i, entry in enumerate(cache):
        if entry.get("constraint_hash") == constraint_hash:
            # Update existing entry
            entry["output"] = output
            entry["hard_constraints"] = normalized_constraints
            entry["last_access"] = current_time
            # Preserve cached_at if it exists, otherwise set it
            if "cached_at" not in entry:
                entry["cached_at"] = current_time
            # Move entry to end of list
            cache.pop(i)
            cache.append(entry)
            _save_cache(cache)
            return
    
    # Create new cache entry
    new_entry = {
        "constraint_hash": constraint_hash,
        "hard_constraints": normalized_constraints,
        "output": output,
        "cached_at": current_time,
        "last_access": current_time
    }
    
    # Append to cache (newest at the end)
    cache.append(new_entry)
    _save_cache(cache)


def get_cache_history() -> List[Dict]:
    """
    Get the full cache history (ordered list, newest at the end).
    """
    return _load_cache()


def clear_cache() -> None:
    """
    Clear all cached results.
    """
    _save_cache([])

