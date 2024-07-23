from typing import TypedDict, Callable, List, Union
import argparse
import glob
import os
import xml.dom.minidom
import copy
from dataclasses import dataclass

class SampleFile(TypedDict):
    path: str
    file_channel: int
    channel: str

class Sample(TypedDict):
    instrument: str
    name: str
    power: float
    openness: float
    files: List[SampleFile]

ParsePathCallable = Callable[[str], List[Sample]]

@dataclass
class InstrumentChokesOthers:
    instrument: str
    chokes: List[str]

class ContinuousHihatEntry(TypedDict):
    instrument: str
    openness: float

@dataclass
class ContinuousHihat:
    hihat_steps: List[ContinuousHihatEntry]
    combined_instrument_name: str

InstrumentFeature = Union[InstrumentChokesOthers, ContinuousHihat]

class GenKitConfig(TypedDict):
    default_name: str
    default_description: str
    parse_path_fn: ParsePathCallable
    instrument_features: List[InstrumentFeature]
    
plugin_script_types = {
    'Sample': Sample,
    'SampleFile': SampleFile,
    'ParsePathCallable': ParsePathCallable,
    'GenKitConfig': GenKitConfig,
    'InstrumentChokesOthers': InstrumentChokesOthers,
    'InstrumentFeature': InstrumentFeature,
    'ContinuousHihatEntry': ContinuousHihatEntry,
    'ContinuousHihat': ContinuousHihat,
}

def instrument_to_xml(instrument, name):
    doc = xml.dom.minidom.Document()

    top = doc.createElement('instrument')
    top.setAttribute('name', name)
    top.setAttribute('version', '2.0')
    doc.appendChild(top)

    samples = doc.createElement('samples')
    top.appendChild(samples)

    for skey,sval in instrument['samples'].items():
        sample = doc.createElement('sample')
        sample.setAttribute('name', skey)
        sample.setAttribute('power', str(sval['power']))
        if 'openness' in sval and sval['openness'] is not None:
            sample.setAttribute('openness', str(sval['openness']))

        for f in sval['files']:
            file = doc.createElement('audiofile')
            file.setAttribute('channel', str(f['channel']))
            file.setAttribute('file', str(f['path']))
            file.setAttribute('filechannel', str(f['file_channel']))
            sample.appendChild(file)
        
        samples.appendChild(sample)
    return doc

def generate_drumkit_xml(name, description, instruments, instruments_dir):
    doc = xml.dom.minidom.Document()

    top = doc.createElement('drumkit')
    top.setAttribute('name', name)
    top.setAttribute('description', description)
    doc.appendChild(top)

    channels = doc.createElement('channels')
    top.appendChild(channels)

    for channel in ["L", "R"]:
        chan = doc.createElement('channel')
        chan.setAttribute('name', channel)
        channels.appendChild(chan)
    
    instruments_node = doc.createElement('instruments')
    top.appendChild(instruments_node)

    for instrument_name,instrument in instruments.items():
        inst = doc.createElement('instrument')
        inst.setAttribute('name', instrument_name)
        inst.setAttribute('file', f'{instruments_dir}/{instrument_name}.xml')
        instruments_node.appendChild(inst)
        
        if 'chokes' in instrument and len(instrument['chokes']) > 0:
            chokes = doc.createElement('chokes')
            inst.appendChild(chokes)
            for choke in instrument['chokes']:
                choke_node = doc.createElement('choke')
                choke_node.setAttribute('instrument', choke)
                chokes.appendChild(choke_node)

        for channel_name in ['L', 'R']:
            chan = doc.createElement('channelmap')
            chan.setAttribute('in', channel_name)
            chan.setAttribute('out', channel_name)
            inst.appendChild(chan)
    return doc

def apply_instrument_choke(instruments, feature : InstrumentChokesOthers):
    if feature.instrument in instruments:
        instrument = instruments[feature.instrument]
        for chokes in feature.chokes:
            instrument['chokes'].add(chokes)
            
def create_continuous_hihat(instruments, feature : ContinuousHihat):
    combined_instrument = {
        'samples': {},
        'chokes': set(),
    }
    for entry in feature.hihat_steps:
        if entry['instrument'] not in instruments:
            raise Exception(f"Continuous hihat entry instrument {entry['instrument']} not found.")
        from_inst = instruments[entry['instrument']]
        for skey,sval in from_inst['samples'].items():
            if skey not in combined_instrument['samples']:
                combined_instrument['samples'][skey] = sval
                combined_instrument['samples'][skey]['openness'] = entry['openness']
    instruments[feature.combined_instrument_name] = combined_instrument

def apply_instrument_feature(instruments, feature : InstrumentFeature):
    if isinstance(feature, InstrumentChokesOthers):
        apply_instrument_choke(instruments, feature)
    elif isinstance(feature, ContinuousHihat):
        create_continuous_hihat(instruments, feature)
    else:
        raise Exception(f"Unknown instrument feature type: {type(feature)}")

def main():
    parser = argparse.ArgumentParser(
        description = "Generate DrumGizmo kits from sample folders."
    )

    parser.add_argument('-c', '--config', type=str, required=True, help="The config .py file to use")
    parser.add_argument('-r', '--root', type=str, required=True, help="The root path of the sample library")
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose output for debugging")
    parser.add_argument('-o', '--output-dir', type=str, help="Output directory in which to store the XML files")
    parser.add_argument('-a', '--auto-relative', action='store_true', help="Automatically make paths relative to the root")

    args = parser.parse_args()

    config_file_code = None
    with open(args.config, 'r') as config_file:
        config_file_code = config_file.read()

    exec_globals = copy.copy(plugin_script_types)
    exec(config_file_code, exec_globals)

    if not 'genkit_config' in exec_globals:
        raise Exception("No genkit_config function defined in config file.")

    config : GenKitConfig = exec_globals['genkit_config']()

    sample_files = [os.path.relpath(p, args.root) for p in glob.glob(f'{args.root}/**/*.wav', recursive=True)]
    sample_lists = []
    failed = 0
    success = 0
    for f in sample_files:
        try:
            sample_lists.append(config['parse_path'](f))
            success = success + 1
        except Exception as e:
            print(f'Failed to parse path {f}: {e}')
            failed = failed + 1


    instruments = {}

    for s in [sample for sublist in sample_lists for sample in sublist]:
        instrument_name = s['instrument']
        if instrument_name not in instruments:
            instruments[instrument_name] = {
                'samples': {},
                'chokes': set(),
            }
        instrument = instruments[instrument_name]

        sample_name = s['name']
        if sample_name not in instrument['samples']:
            instrument['samples'][sample_name] = {
                'power': s['power'],
                'files': []
            }
        sample = instrument['samples'][sample_name]
        
        for f in s['files']:
            sample['files'].append(f)

    print("Remapping power values to linear scale")
    for name,inst in instruments.items():
        max_power = max(1.0, max([s['power'] for s in inst['samples'].values()]))
        for s in inst['samples'].values():
            s['power'] = s['power'] / max_power
    
    print("Applying instrument features")
    for feature in config['instrument_features']:
        apply_instrument_feature(instruments, feature)

    if args.verbose:
        print("All found instruments:")
        for name,inst in instruments.items():
            print(instrument_to_xml(inst, name).toprettyxml(indent='  '))
    
    print(f'Parsed {len(instruments.keys())} instruments from {success} paths successfully, {failed} paths failed')

    if not args.output_dir:
        print("No output directory specified, exiting.")
        exit(0)
    if os.path.exists(args.output_dir):
        print("Output dir already exists, please delete it first.")
        exit(1)
    
    instruments_dir = os.path.join(args.output_dir, f"{config['default_name']}_instruments")
        
    if args.auto_relative:
        print("Resolving relative paths")
        for name,inst in instruments.items():
            for s in inst['samples'].values():
                for f in s['files']:
                    f['path'] = os.path.relpath(os.path.join(args.root, f['path']), instruments_dir)
    
    os.makedirs(args.output_dir)
    os.makedirs(instruments_dir)

    drumkit_name = config['default_name']
    drumkit_description = config['default_description']
    
    for name,inst in instruments.items():
        with open(os.path.join(instruments_dir, f'{name}.xml'), 'w') as file:
            file.write(instrument_to_xml(inst, name).toprettyxml(indent='  '))
    
    with open(os.path.join(args.output_dir, f'{drumkit_name}.xml'), 'w') as file:
        file.write(generate_drumkit_xml(drumkit_name, drumkit_description, instruments, os.path.relpath(instruments_dir, args.output_dir)).toprettyxml(indent='  '))

if __name__ == "__main__":
    main()