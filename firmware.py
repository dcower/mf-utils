#! /usr/bin/env python
# -*- coding: utf-8 -*-

import itertools
import json
import os
import struct
import zipfile


def zero_padding_bytes(size):
  padding_zeroes = itertools.repeat(0, size)
  return struct.pack("{}B".format(size), *padding_zeroes)

class FirmwareImage:
  class Type:
    UNKNOWN = -1
    MAIN = 0
    OLED = 1
    MATRIX = 2
    KEYBOARD = 3
    WAVETABLES = 4

  def __init__(self, file_name, image_num, data):
    self.file_name = file_name
    self.image_num = image_num
    self.data = data
    self.magic = struct.unpack("B", data[1:2])[0]

    if file_name.startswith("nanowave_main"):
      self.type = FirmwareImage.Type.MAIN
    elif file_name.startswith("nanowave_iochip_oled"):
      self.type = FirmwareImage.Type.OLED
    elif file_name.startswith("nanowave_iochip_matrix"):
      self.type = FirmwareImage.Type.MATRIX
    elif file_name.startswith("nanowave_iochip_kbd"):
      self.type = FirmwareImage.Type.KEYBOARD
    elif file_name.startswith("nanowave_wavetables"):
      self.type = FirmwareImage.Type.WAVETABLES
    else:
      self.type = FirmwareImage.Type.UNKNOWN

    assert(self.type != FirmwareImage.Type.UNKNOWN)

    # Verify that the first byte matches the image_num.
    assert(struct.unpack("B", data[:1])[0] == image_num)

    # Verify that the second byte (magic) and last byte (magic #2) match.
    assert(struct.unpack("B", data[1:2])[0] == 
           struct.unpack("B", data[-1:])[0])

    # Verify that the padding at the start and end of the file, excluding magic
    # bytes and image num, is all 0's.
    # TODO: Determine actual end padding amount.
    assert(data[2:64] == zero_padding_bytes(62))
    assert(data[-10:-1] == zero_padding_bytes(9))

  def log(self):
    print("FirmwareImage:", self.image_num, ":", self.file_name,
          "- magic =", self.magic, "- data size =", len(self.data))


class Firmware:
  def __init__(self, images=dict(), version_number="", date=""):
    self.images = images
    self.version_number = version_number
    self.date = date

  def log(self):
    print("Firmware:", self.version_number, "-", self.date)
    for type, image in self.images.items():
      image.log()

  def get_image(self, type):
    return self.images[type]

  def put_image(self, image):
    self.images[image.type] = image

  def write_to_mff(self, path):
    with zipfile.ZipFile(path, "w") as zf:
      zf.writestr("info.json", self.build_json())
      for type, image in self.images.items():
        zf.writestr(image.file_name, image.data)

  def build_json(self):
    info = {}
    info["version_number"] = self.version_number
    info["date"] = self.date
    info["images"] = []

    for type, image in self.images.items():
      image_info = {}
      image_info["image_num"] = image.image_num
      image_info["file_name"] = image.file_name
      info["images"].append(image_info)

    return json.dumps(info)

  @classmethod
  def load_from_mff(cls, path):
    with zipfile.ZipFile(path, "r") as zf:
      zipped_names = set(zf.namelist())

      image_names = set(
        filter(lambda s: os.path.splitext(s)[1] == ".bin",zipped_names))
      zipped_names = zipped_names - image_names

      info_name = "info.json"
      assert(info_name in zipped_names)
      zipped_names = zipped_names - set([info_name])

      if len(zipped_names) > 0:
        print("Unknown files in firmware:", zipped_names)

      info = json.loads(zf.read(info_name))

      images = {}

      for image_entry in info["images"]:
        image_num = image_entry["image_num"]
        file_name = image_entry["file_name"]
        assert(file_name in image_names)

        data = zf.read(file_name)
        image = FirmwareImage(file_name, image_num, data)
        images[image.type] = image

    return Firmware(images=images, version_number=info["version_number"],
                    date=info["date"])
