# drumgizmo_genkit

Convenience scripts for generating DrumGizmo kits from sample libraries on the command line.
This was initially concieved for generating a kit from Jake Reed's "Super Dry Drums" packs.

Not tested yet.

## Usage

The core of the script can generate XML files compatible with DrumGizmo. To deal with the specific structure and filenames of your sample pack, you need to provide a config file which is a Python file itself.
That Python file should be able to parse the .wav paths of the sample pack and return the metadata needed for the XML generator to do its work.
For an example config, see `configs/jake_reed_sdd_3.py`.

Once your config is ready, run the tool. For the Jake Reed SDD 3 example:

```
python .\drumgizmo_genkit\drumgizmo_genkit.py -c .\configs\jake_reed_sdd_3.py -r 'C:\Users\nx017926\Downloads\SDD VOL 3 ONE SHOTS' -o sdd3
```

The XML files should now be in the newly created `sdd3` folder. You can move it in the the `SDD VOL 3 ONE SHOTS` directory to use it.

## Limitations

* Currently untested (soon to change at least for the SDD3 kit)
* Naive hit power mapping (linear scale directly taken from the V1-V16 suffixes of the files)
* Stereo channel mapping baked in at the moment

Note that although these are limiting, the script can still provide a good starting point after which manual editing can improve further.
