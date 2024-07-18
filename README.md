# drumgizmo_genkit

Convenience scripts for generating DrumGizmo kits from sample libraries on the command line.
This was initially concieved for generating a kit from Jake Reed's "Super Dry Drums" packs.

Status is working but very fresh - the kit is not very refined yet. Contributions are very welcome!

## Usage

The core of the script can generate XML files compatible with DrumGizmo. To deal with the specific structure and filenames of your sample pack, you need to provide a config file which is a Python file itself.
That Python file should be able to parse the .wav paths of the sample pack and return the metadata needed for the XML generator to do its work.
For an example config, see `configs/jake_reed_sdd_3.py`.

Once your config is ready, run the tool. For the Jake Reed SDD 3 example:

```
python drumgizmo_genkit.py -c .\configs\jake_reed_sdd_3.py -r 'C:\Users\nx017926\Downloads\SDD VOL 3 ONE SHOTS' -o super_dead_drums_3 -a
```

The XML files should now be in the newly created `sdd3` folder. You can move it in the the `SDD VOL 3 ONE SHOTS` directory to use it.

## Generated Outputs

Some examples of generated kit files are in the **example_kits** folder, each with a README and midi mapping examples.

## Limitations

* Currently only tested and having config for Jake Reed Super Dead Drums Vol 3.
* Naive hit power mapping (linear scale directly taken from the V1-V16 suffixes of the files) - can be compensated with velocity curve in Gizmo plugin.
* Only a stereo channel mapping baked in at the moment.
* No MIDI map is generated, because that is simply a mapping from notes to instruments. Writing that down in a Python dictionary is equivalent to just writing the mapping XML yourself. Note however that some examples are included in the Generated Outputs.

Note however, that the resulting XMLs provide a great starting point for further manual tweaks. Or better yet, the config .py file can be tweaked to automatically re-generate the kit with different properties. For example, a multi-channel version wouldn't be hard to make this way.
