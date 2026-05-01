"""
Vercel Serverless Entry Point — Flask API for Wumpus World.
Handles all /api/* routes as a single serverless function.
"""

import sys
import os
import json

# Add project root to path so 'wumpus' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from wumpus.world import WumpusWorld
from wumpus.agent import KBAgent

app = Flask(__name__)

# In-memory game storage
games = {}
game_counter = 0


@app.route('/api/new-game', methods=['POST'])
def new_game():
    global game_counter
    data = request.get_json(force=True)
    rows = max(3, min(int(data.get('rows', 4)), 10))
    cols = max(3, min(int(data.get('cols', 4)), 10))

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
    for _ in range(100):
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
