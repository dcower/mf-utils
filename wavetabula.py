#! /usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import errno
import math
import os
import sys

from firmware import Firmware, FirmwareImage
from wavetables import Wavetables


def mkdir_p(path):
  try:
    os.makedirs(path)
  except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise

def clamp_short(x):
  return min(32767, max(-32768, x))

def extract_parser_handler(args):
  print("Extracting wavetables from {} to {}".format(
    args.firmware, os.path.abspath(args.out_wav_dir)))

  firmware = Firmware.load_from_mff(args.firmware)
  if args.verbose:
    firmware.log()

  wavetables_image = firmware.get_image(FirmwareImage.Type.WAVETABLES)
  wavetables = Wavetables.from_image(wavetables_image)
  mkdir_p(args.out_wav_dir)
  wavetables.write_tables_to_wavs(args.out_wav_dir)

def replace_parser_handler(args):
  print(
    "Replacing wavetables from {} with those in {} and writing result to {}".
    format(
      args.firmware,
      os.path.abspath(args.wav_dir),
      os.path.abspath(args.out_firmware)))

  firmware = Firmware.load_from_mff(args.firmware)

  wavetables = Wavetables.from_image(firmware.get_image(FirmwareImage.Type.WAVETABLES))
  wavetables.replace_tables_with_wavs(args.wav_dir)

  firmware.put_image(wavetables.to_image())

  if args.verbose:
    firmware.log()

  firmware.write_to_mff(args.out_firmware)

  # Sanity check that the file was written.
  assert(Firmware.load_from_mff(args.out_firmware) is not None)

def smooth_parser_handler(args):
  print(
    "Adding {}-sample cycle fade to {} to wavetables in {} and writing to {}".
    format(
      args.fade_distance,
      args.fade_target,
      os.path.abspath(args.wav_dir),
      os.path.abspath(args.out_wav_dir)))

  wavetables = Wavetables()
  wavetables.replace_tables_with_wavs(args.wav_dir)

  for table_index in range(Wavetables.NUM_TABLES):
      for cycle_index in range(Wavetables.CYCLES_PER_TABLE):
        cycle = wavetables.tables[table_index][cycle_index]

        # If enabled, rotate to minimize distance to fade target.
        if args.rotate:
          rotate_amount = -1
          distance_min = 0.0
          for i in range(len(cycle)):
            if args.fade_target == "zero":
              distance = abs(cycle[i] - 0)
            elif args.fade_target == "mean":
              distance = abs(cycle[i] - cycle[i - 1])

            if rotate_amount == -1 or distance < distance_min:
              distance_min = distance
              rotate_amount = i

          print("Rotated: {}".format(rotate_amount))
          cycle = cycle[rotate_amount:] + cycle[:rotate_amount]
          wavetables.tables[table_index][cycle_index] = cycle

        # Target value to fade to.
        # TODO: Use mean of power instead? Or average over a window?
        if args.fade_target == "zero":
          fade_target = 0
        elif args.fade_target == "mean":
          fade_target = (cycle[0] + cycle[-1]) // 2
        else:
          raise Exception("Unknown fade target: {}".format(args.fade_target))

        for i in range(args.fade_distance):
          t = float(i) / args.fade_distance
          # Equal power crossfade:
          # https://dsp.stackexchange.com/questions/14754/equal-power-crossfade
          fade_cycle_amount = math.sqrt(t)
          fade_target_amount = math.sqrt(1.0 - t)
          # TODO: Clamp these to within short range?
          cycle[i] = clamp_short(int(cycle[i] * fade_cycle_amount + fade_target * fade_target_amount))
          cycle[-1 - i] = clamp_short(int(cycle[-1 - i] * fade_cycle_amount + fade_target * fade_target_amount))

  mkdir_p(args.out_wav_dir)
  wavetables.write_tables_to_wavs(args.out_wav_dir)

def main():
  parser = argparse.ArgumentParser(description=
    "Tools for modifying MicroFreak wavetables.")

  subparsers = parser.add_subparsers()
  subparsers.required = True
  subparsers.dest = "command"

  parser.add_argument(
    "--wav_dir",
    action="store",
    default="wavetables",
    help="directory to read input wavetable .wav's from")
  parser.add_argument(
    "--out_wav_dir",
    action="store",
    default="out_wavetables",
    help="directory to write output wavetable .wav's into")
  parser.add_argument(
    "--verbose",
    action="store_true",
    default=False,
    help="enables verbose logging")

  extract_parser = subparsers.add_parser(
    "extract",
    add_help=True,
    help=
    "extracts wavetables from the specified firmware .mff and saves them to "
    ".wav file(s) in --out_wav_dir")
  extract_parser.set_defaults(func=extract_parser_handler)

  replace_parser = subparsers.add_parser(
    "replace",
    add_help=True,
    help=
    "replaces wavetables in the specified firmware .mff with ones in --wav_dir "
    "and saves a new .mff")
  replace_parser.add_argument(
    "--out_firmware",
    action="store",
    default="new_firmware.mff",
    help="output firmware image (.mff file)")
  replace_parser.set_defaults(func=replace_parser_handler)

  for p in extract_parser, replace_parser:
    p.add_argument(
      "firmware",
      action="store",
      help="firmware image (.mff file)")

  smooth_parser = subparsers.add_parser(
    "smooth",
    add_help=True,
    help=
    "loads the the .wav files in the --wav_dir directory, smooths each cycle "
    "using fading, rotating, etc., and outputs them to --out_wav_dir")
  smooth_parser.add_argument(
    "--fade_distance",
    type=int,
    action="store",
    default=16,
    help="sample distance to fade at start and end of each cycle")
  smooth_parser.add_argument(
    "--fade_target",
    choices=["zero", "mean"],
    action="store",
    default="zero",
    help="value to fade to. 'mean' fades to the average of samples at both "
    "ends of the cycle. 'zero' fades to zero.")
  smooth_parser.add_argument(
    "--rotate",
    action="store_true",
    default=False,
    help="rotate each cycle before fading to minimize distance to fade target. "
    "This will reduce (or remove) clicks or pops when switching between cycles "
    "in wavetable synthesizers that do not fade between cycles/wavetables.")
  smooth_parser.set_defaults(func=smooth_parser_handler)
  
  args = parser.parse_args()
  args.func(args)

  return


if __name__ == "__main__":
  main()