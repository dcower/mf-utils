#! /usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import os
import struct
import wave

# i  -> zip_longest in Python 3.
try:
    from itertools import zip_longest
except ImportError:
    from itertools import izip_longest as zip_longest

from firmware import FirmwareImage, zero_padding_bytes


SIZE_TO_STRUCT_FORMAT = {1: "B", 2: "h", 4: "i"}

# Wave_read/Wave_write isn't a context manager in Python 2.
wave.Wave_read.__enter__ = wave.Wave_write.__enter__ = \
  lambda self: self
wave.Wave_read.__exit__ = wave.Wave_write.__exit__ = \
  lambda self, *_: self.close()

class Wavetables:
  NUM_TABLES = 16
  CYCLES_PER_TABLE = 32
  SAMPLES_PER_CYCLE = 256
  # 16-bit samples -- 2 bytes per sample.
  SAMPLE_SIZE = 2
  # Mono samples.
  NUM_CHANNELS = 1
  # This is a guess. At this sample rate, playing D#4 on the MF keyboard sounds
  # ~identical to the sample played without pitching.
  SAMPLE_RATE_HZ = 40000

  # Size in bytes of wavetables FirmwareImage header.
  IMAGE_HEADER_SIZE = 64
  # Size in bytes of wavetables FirmwareImage footer.
  IMAGE_FOOTER_SIZE = 16
  # Size of header padding. Excludes image num + magic bytes.
  IMAGE_HEADER_PADDING_SIZE = IMAGE_HEADER_SIZE - 2
  # Size of footer padding. Excludes magic byte.
  IMAGE_FOOTER_PADDING_SIZE = IMAGE_FOOTER_SIZE - 1

  # Struct for encoding/decoding a single wavetable.
  wavetable_struct = struct.Struct("<{}h".format(SAMPLES_PER_CYCLE))
  # Struct for encoding/decoding all wavetables together.
  wavetables_struct = struct.Struct("<{}h".format(
    SAMPLES_PER_CYCLE * CYCLES_PER_TABLE * NUM_TABLES))

  def __init__(self):
    self.tables = [[[0 for sample in range(Wavetables.SAMPLES_PER_CYCLE)]
                       for cycle in range(Wavetables.CYCLES_PER_TABLE)]
                       for table in range(Wavetables.NUM_TABLES)]
    self.image = None

  def to_image(self):
    image = self.image

    flattened = list(itertools.chain(*self.tables))
    flattened = list(itertools.chain(*flattened))
    tables_data = Wavetables.wavetables_struct.pack(*flattened)

    # Add header: image num, magic, and padding.
    image_num_byte = struct.pack("B", image.image_num)
    magic_byte = struct.pack("B", image.magic)
    header_padding = zero_padding_bytes(Wavetables.IMAGE_HEADER_PADDING_SIZE)
    data = image_num_byte + magic_byte + header_padding

    # Add tables.
    data = data + tables_data

    # Add footer: padding + magic.
    footer_padding = zero_padding_bytes(Wavetables.IMAGE_FOOTER_PADDING_SIZE)
    data = data + footer_padding + magic_byte

    image.data = data

    return image

  @classmethod
  def get_table_wav_path(cls, table_index, dir):
    name = "wavetable_{}.wav".format(table_index)
    return os.path.join(dir, name)

  def replace_tables_with_wavs(self, dir):
    NUM_FRAMES = Wavetables.SAMPLES_PER_CYCLE * Wavetables.CYCLES_PER_TABLE

    for table_index in range(Wavetables.NUM_TABLES):
      path = Wavetables.get_table_wav_path(table_index, dir)

      with wave.open(path, "rb") as wav_file:
        if wav_file.getnchannels() != Wavetables.NUM_CHANNELS:
          raise Exception(
            "WAV {} must have {} channels; got {}".format(
              path, Wavetables.NUM_CHANNELS, wav_file.getnchannels()))

        if wav_file.getsampwidth() != Wavetables.SAMPLE_SIZE:
          raise Exception(
            "WAV {} must have sample size of {} bytes; got {}".format(
              path, Wavetables.SAMPLE_SIZE, wav_file.getsampwidth()))

        if wav_file.getnframes() < NUM_FRAMES:
          raise Exception(
            "WAV {} must have at least {} frames; got {}".format(
              path, NUM_FRAMES, wav_file.getnframes()))

        frames = wav_file.readframes(NUM_FRAMES)

        struct_format = SIZE_TO_STRUCT_FORMAT[wav_file.getsampwidth()]
        table = struct.unpack(("<{}{}".format(NUM_FRAMES, struct_format)), frames)
        table_split_into_cycles = list(zip_longest(*[iter(table)] * Wavetables.SAMPLES_PER_CYCLE))
        self.tables[table_index] = table_split_into_cycles
        # Convert to list of lists.
        self.tables[table_index] = [list(cycle) for cycle in self.tables[table_index]]

  def write_tables_to_wavs(self, dir):
    for table_index in range(Wavetables.NUM_TABLES):
      path = Wavetables.get_table_wav_path(table_index, dir)

      with wave.open(path, "wb") as wav_file:
        wav_file.setnchannels(Wavetables.NUM_CHANNELS)
        wav_file.setsampwidth(Wavetables.SAMPLE_SIZE)
        wav_file.setframerate(Wavetables.SAMPLE_RATE_HZ)

        for cycle_index in range(Wavetables.CYCLES_PER_TABLE):
          wav_file.writeframes(
            Wavetables.wavetable_struct.pack(
              *self.tables[table_index][cycle_index]))

  def replace_with_wav(self, table_index, path):
    with wave.open(path, "rb") as wav_file:
      assert(wav_file.getnchannels() == Wavetables.NUM_CHANNELS)

      NUM_FRAMES = Wavetables.SAMPLES_PER_CYCLE * Wavetables.CYCLES_PER_TABLE
      frames = wav_file.readframes(NUM_FRAMES)

      struct_format = SIZE_TO_STRUCT_FORMAT[wav_file.getsampwidth()]
      table = struct.unpack(("<{}{}".format(NUM_FRAMES, struct_format)), frames)
      table_split_into_cycles = list(zip_longest(*[iter(table)] * Wavetables.SAMPLES_PER_CYCLE))
      self.tables[table_index] = table_split_into_cycles
      # Convert to list of lists.
      self.tables[table_index] = [list(cycle) for cycle in self.tables[table_index]]


  def write_to_wav(self, path):
    with wave.open(path, "wb") as wav_file:
      wav_file.setnchannels(Wavetables.NUM_CHANNELS)
      wav_file.setsampwidth(Wavetables.SAMPLE_SIZE)
      wav_file.setframerate(Wavetables.SAMPLE_RATE_HZ)

      for table_index in range(Wavetables.NUM_TABLES):
        for cycle_index in range(Wavetables.CYCLES_PER_TABLE):
          wav_file.writeframes(
            Wavetables.wavetable_struct.pack(
              *self.tables[table_index][cycle_index]))

  def write_cycles_to_wavs(self, dir):
    for table_index in range(Wavetables.NUM_TABLES):
        for cycle_index in range(Wavetables.CYCLES_PER_TABLE):
          name = "wavetable_{}_{}.wav".format(table_index, cycle_index)
          path = os.path.join(dir, name)

          with wave.open(path, "wb") as wav_file:
            wav_file.setnchannels(Wavetables.NUM_CHANNELS)
            wav_file.setsampwidth(Wavetables.SAMPLE_SIZE)
            wav_file.setframerate(Wavetables.SAMPLE_RATE_HZ)  
            wav_file.writeframes(
              Wavetables.wavetable_struct.pack(
                *self.tables[table_index][cycle_index]))

  @classmethod
  def from_image(cls, image):
    assert(image.type == FirmwareImage.Type.WAVETABLES)

    wt = Wavetables()
    wt.image = image

    data_index = 0
    # Skip magic + padding.
    data_index += Wavetables.IMAGE_HEADER_SIZE

    for table_index in range(Wavetables.NUM_TABLES):
      for cycle_index in range(Wavetables.CYCLES_PER_TABLE):
        size = Wavetables.SAMPLES_PER_CYCLE * Wavetables.SAMPLE_SIZE
        wt.tables[table_index][cycle_index] = list(Wavetables.wavetable_struct.unpack(image.data[data_index : data_index + size]))
        data_index += size

    # Skip end padding.
    data_index += Wavetables.IMAGE_FOOTER_SIZE

    return wt