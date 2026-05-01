"""
Flask application — serves the Wumpus World web UI and API.
"""

import json
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from wumpus.world import WumpusWorld
from wumpus.agent import KBAgent

app = Flask(__name__)
app.secret_key = 'wumpus-world-secret-key-2026'
CORS(app)

# In-memory game storage (keyed by simple counter)
games = {}
game_counter = 0


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/new-game', methods=['POST'])
def new_game():
    global game_counter
    data = request.get_json(force=True)
    rows = int(data.get('rows', 4))
    cols = int(data.get('cols', 4))
    rows = max(3, min(rows, 10))
    cols = max(3, min(cols, 10))

    world = WumpusWorld(rows, cols)
    agent = KBAgent(world)

    game_counter += 1
    game_id = str(game_counter)
    games[game_id] = {'world': world, 'agent': agent}

    state = agent.get_state()
    state['game_id'] = game_id
    return jsonify(state)


@app.route('/api/step', methods=['POST'])
def step():
    data = request.get_json(force=True)
    game_id = data.get('game_id')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    agent = games[game_id]['agent']
    state = agent.step()
    state['game_id'] = game_id
    return jsonify(state)


@app.route('/api/auto-play', methods=['POST'])
def auto_play():
    data = request.get_json(force=True)
    game_id = data.get('game_id')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    agent = games[game_id]['agent']
    history = []
    max_auto_steps = 100

    for _ in range(max_auto_steps):
        state = agent.step()
        history.append(state)
        if state['game_over']:
            break

    state['game_id'] = game_id
    state['history'] = history
    return jsonify(state)


@app.route('/api/state', methods=['POST'])
def get_state():
    data = request.get_json(force=True)
    game_id = data.get('game_id')

    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404

    agent = games[game_id]['agent']
    state = agent.get_state()
    state['game_id'] = game_id
    return jsonify(state)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
