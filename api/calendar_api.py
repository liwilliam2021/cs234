from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory calendar storage (for simplicity)
calendar_events = []

@app.route('/events', methods=['GET'])
def get_events():
    """Retrieve all calendar events"""
    return jsonify(calendar_events), 200

@app.route('/events', methods=['POST'])
def add_event():
    """Add a new event to the calendar"""
    event_data = request.json
    try:
        event = {
            "title": event_data['title'],
            "date": datetime.strptime(event_data['date'], '%Y-%m-%d'),
            "description": event_data.get('description', '')
        }
        calendar_events.append(event)
        return jsonify(event), 201
    except (KeyError, ValueError):
        return jsonify({"error": "Invalid event data"}), 400

@app.route('/events/<date>', methods=['GET'])
def get_events_by_date(date):
    """Retrieve calendar events for a specific date"""
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        events_on_date = [event for event in calendar_events if event['date'] == date_obj]
        return jsonify(events_on_date), 200
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

if __name__ == '__main__':
    app.run(debug=True)
