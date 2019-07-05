# mf-utils

Utilities for the [Arturia MicroFreak](https://www.arturia.com/products/hardware-synths/microfreak) synthesizer.

| WARNING: Flashing your MicroFreak with custom firmware not from Arturia -- firmware created with these tools -- may void your warranty or brick your MicroFreak. I am not responsible if your MicroFreak is bricked by this process. |
| --- |

## wavetabula
Extract, replace, and modify wavetables in MicroFreak firmware files (.mff).

### Requirements
You need Python 2.7 or later, or Python 3.4 or later, to run this tool. If you don't have Python installed, you can get it here: http://www.python.org/getit/

### Usage
1. Clone or download the repository.

2. Download a MicroFreak firmware file (.mff) from [Arturia's Resources page for MicroFreak](https://www.arturia.com/products/hardware-synths/microfreak/resources).

3. Extract wavetables from the firmware:

```
python wavetabula.py --out_wav_dir out_wavetables/ extract MicroFreak_Firmware_Update_1_1_2_390.mff
```

4. Modify the newly extracted wavetables as you see fit. For this example, we'll use the supplied sample wavetables I made.

5. Replace the wavetables in the firmware with our fancy new wavetables:

```
python wavetabula.py --wav_dir sample_wavetables/ replace MicroFreak_Firmware_Update_1_1_2_390.mff
```

6. Voila! You should now have a file named `new_firmware.mff` (by default), which you can flash via Arturia's MIDI Control Center. Read the giant **WARNING** above before doing so; be aware that you could brick your device by doing this.

Run `python wavetabula.py -h` or see below for more options.

### Commands

#### Extract
Extracts wavetables from the specified MicroFreak firmware file (.mff) and writes the wavetables to separate WAV files, one for each table.

Example:
```
python wavetabula.py --out_wav_dir out_wavetables/ extract MicroFreak_Firmware_Update_1_1_2_390.mff
```

Run `python wavetabula.py extract -h` for more details.

#### Replace
Replaces wavetables in the specified MicroFreak firmware file (.mff) with wavetables (stored as WAVs in the same format as output from the `extract` command) in the specified directory.

Example:
```
python wavetabula.py --wav_dir sample_wavetables/ replace --out_firmware my_custom_firmware.mff MicroFreak_Firmware_Update_1_1_2_390.mff
```

Run `python wavetabula.py replace -h` for more details.

#### Smooth
Smooths MicroFreak-style wavetables (stored as WAVs in the same format as output from the `extract` command) in the specified directory. This can be used to reduce pops, clicks, and other artifacts you may hear when experimenting with your own wavetables.

Example:
```
python wavetabula.py --wav_dir sample_wavetables/ --out_wav_dir fade_wavetables/ smooth --fade_distance 16 --fade_target zero --rotate
```

Run `python wavetabula.py smooth -h` for more details.

### Notes
* There are 16 wavetables on the device; each wavetable contains 32 cycles, and each cycle is 256 samples long.
* I believe the sample format is 16-bit mono @ 40kHz. Yes, 40000Hz. Each sample is tuned to D#4.
* The tool only supports 16-bit mono WAV files; each wavetable must contain at least 8192 samples, and the first 8192 will be used. They should be encoded at 40kHz if you want them to sound correct.

## Libraries

* [firmware.py](https://github.com/dcower/mf-utils/blob/master/firmware.py): Load and write MicroFreak firmware files (.mff).
* [wavetables.py](https://github.com/dcower/mf-utils/blob/master/wavetables.py): Load, write, and modify the wavetables in MicroFreak firmware files (.mff). E.g., write the tables to WAV files, replace select tables in the firmware with WAV files on disk, etc.
