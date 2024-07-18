"""
Configuration for generating kit from Jake Reed Super Dead Drums 3 pack.
Maps all instruments onto common L and R channels.
"""
from typing import List
import os
import re
import glob

def split_path_recursive(path):
    head, tail = os.path.split(path)
    if not head:
        return [tail] if tail else []
    if head == path:
        return [head]
    return split_path_recursive(head) + [tail]

def parse_path(path : str) -> List[Sample]:
    path_parts = split_path_recursive(path)
    if len(path_parts) < 2:
        raise Exception(f"Jake reed SDD 3 audio file path not deep enough: {path}")

    instrument_name = (
        path_parts[-2] if len(path_parts) < 3 or not re.match(rf'{path_parts[-3]} V[0-9]+', path_parts[-2]) # Instrument subfolder
        else path_parts[-3]                                                                                 # Velocity subfolder
    ).replace('SDD 3 ', '').replace(' ', '_').strip()
    sample_name = path_parts[-1].strip().replace(' ', '_')
    filename = path_parts[-1].strip()

    match = re.match(r'.*_([a-z])\.wav', filename)
    if match:
        sample_name = sample_name + f' {match.group(1)}'
    
    sample_power = 1.0
    match_v_pattern = r'.*V([0-9])+(?:_[a-z])?.wav'
    match = re.match(match_v_pattern, filename)
    if match:
        # Set the power to the V number, can be recalculated later.
        sample_power = float(int(match.group(1)))

    return [{
        'instrument': instrument_name,
        'name':       sample_name,
        'power':      sample_power,
        'files':      [{
            'path':         path,
            'file_channel': chan,
            'channel':      ['L', 'R'][chan - 1],
        } for chan in [1, 2]],
    }]                    

def genkit_config() -> GenKitConfig:
    return {
        'default_name': 'Jake Reed Super Dry Drums 3',
        'default_description': "Jake Reed Super Dry Drums 3, generated by drumgizmo_genkit",
        'parse_path': parse_path
    }