"""Scenarios for this experiment.

The apron questions use the frozen M1 replay through backend.evidence. The tower replay
(tower1.json) needs five extra fields; they are registered in backend.evidence.FIELDS for
the running process only. No backend source file changes, so the frozen-source integrity
check is unaffected.
"""
import json
from pathlib import Path
from backend import evidence

HERE = Path(__file__).resolve().parent
TOWER_ID = 'T1-tower-clearances-01'
TOWER_FIELDS = {
    'taxi_clearance': 'Taxi clearance', 'lineup_clearance': 'Line-up clearance',
    'takeoff_clearance': 'Take-off clearance', 'readback': 'Pilot readback', 'runway': 'Runway assigned',
}


def register_tower_fields():
    for name, label in TOWER_FIELDS.items():
        evidence.FIELDS.setdefault(name, label)


def load(scenario_id):
    if scenario_id == TOWER_ID:
        register_tower_fields()
        data = json.loads((HERE / 'tower1.json').read_text())
        evidence.validate_scenario(data)
        return data
    return evidence.load_scenario(scenario_id)
