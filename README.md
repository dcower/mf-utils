# mf-utils

Utilities for the [Arturia MicroFreak](https://www.arturia.com/products/hardware-synths/microfreak) synthesizer.

| WARNING: Flashing your MicroFreak with custom firmware not from Arturia -- firmware created with these tools -- may void your warranty or brick your MicroFreak. I am not responsible if your MicroFreak is bricked by this process. |
| --- |

## Utilities

### [wavetable_tool.py](https://github.com/dcower/mf-utils/blob/master/wavetable_tool.py)
Extract and replace wavetables in MicroFreak firmware files (.mff).

#### Requirements
You need Python 2.7 or later, or Python 3.4 or later, to run this tool. If you don't have Python installed, you can get it here: http://www.python.org/getit/

#### Usage
1. Clone or download the repository.

2. Download a MicroFreak firmware file (.mff) from [Arturia's Resources page for MicroFreak](https://www.arturia.com/products/hardware-synths/microfreak/resources).

3. Extract wavetables from the firmware:

```
python wavetable_tool.py --out_wav_dir out_wavetables/ extract MicroFreak_Firmware_Update_1_1_2_390.mff
```

4. Modify the newly extracted wavetables as you see fit. For this example, we'll use the supplied sample wavetables I made.

5. Replace the wavetables in the firmware with our fancy new wavetables:

```
python wavetable_tool.py --wav_dir sample_wavetables/ replace MicroFreak_Firmware_Update_1_1_2_390.mff
```

6. Voila! You should now have a file named `new_firmware.mff` (by default), which you can flash via Arturia's MIDI Control Center. Read the giant **WARNING** above before doing so; be aware that you could brick your device by doing this.

Run `python wavetable_tool.py -h` for more options.

#### Notes
* There are 16 wavetables on the device; each wavetable contains 32 cycles, and each cycle is 256 samples long.
* I believe the sample format is 16-bit mono @ 40kHz. Yes, 40000Hz. Each sample is tuned to D#4.
* The tool only supports 16-bit mono WAV files; each wavetable must contain at least 8192 samples, and the first 8192 will be used. They should be encoded at 40kHz if you want them to sound correct.

## Libraries

* [firmware.py](https://github.com/dcower/mf-utils/blob/master/firmware.py): Load and write MicroFreak firmware files (.mff).
* [wavetables.py](https://github.com/dcower/mf-utils/blob/master/wavetables.py): Load, write, and modify the wavetables in MicroFreak firmware files (.mff). E.g., write the tables to WAV files, replace select tables in the firmware with WAV files on disk, etc.
