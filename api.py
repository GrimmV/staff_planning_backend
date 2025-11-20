from flask import Flask, request, jsonify
from get_recommendations import get_recommendation
from cors_handling import _build_cors_preflight_response, _corsify_actual_response

app = Flask(__name__)

@app.route('/recommendations', methods=['POST', 'OPTIONS'])
def recommendations():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    """
    Endpoint to get recommendations based on hard constraints.
    
    Expected JSON body:
    {
        "hard_constraints": {
            "forced_assignments": [["ma_id", "client_id"], ...],
            "forced_clients": ["client_id", ...]
        }
    }
    """
    try:
        # Get JSON data from request body
        data = request.get_json()
        
        # Extract hard_constraints, default to empty dict if not provided
        hard_constraints = data.get('hard_constraints', {}) if data else {}
        
        # Call the get_recommendation function
        result = get_recommendation(hard_constraints)
        
        print(f"Result: {result}")
        
        # Return the result as JSON
        if result:
            response = jsonify(result)
            return _corsify_actual_response(response)
        else:
            response = jsonify({"error": "No feasible solution found"})
            return _corsify_actual_response(response)
            
    except Exception as e:
        response = jsonify({"error": str(e)})
        return _corsify_actual_response(response)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
