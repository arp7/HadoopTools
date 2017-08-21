#!/usr/bin/env python

import os
import re
import shutil
import sys

""" Automate updating multiple HDP jars for debugging/hotfix purposes.
Agnostic to the target directory layout which can differ across HDP versions.
"""

if (len(sys.argv) != 4):
  print("Usage: replace-jars.py <source-dir> <source-version> <dst-version>")
  print("       source-dir     : Directory containing the new jar versions.")
  print("       source-version : Version string of the new jars.")
  print("       dst-version    : Installed HDP version to be updated.")
  sys.exit(1)


src, src_ver, dst_ver = sys.argv[1:]

# Canonicalize and validate the source directory exists.
#
src = os.path.realpath(src)
if not os.path.isdir(src):
  print("Source directory {} does not exist".format(src))
  sys.exit(1)

# Strip out the first three digits which are the Apache version
# from dst_ver.
#
ver_pattern = re.compile('^\d+\.\d+\.\d+\.')
dst = os.path.join("/usr", "hdp", re.sub(ver_pattern, "", dst_ver))

if not os.path.isdir(dst):
  print("HDP directory {} does not exist. Is HDP version {} installed?".format(dst, dst_ver))
  sys.exit(1)

# Build a map of source jar name to its full absolute path under
# the source directory.
#
sources = {}
for root, dirs, files in os.walk(src):
  for f in files:
    if f.endswith('.jar') and f not in sources:
      sources[f] = os.path.join(root, f)

print("Got {} source jars.".format(len(sources)))

# List destination jars, and replace each with the corresponding
# source jar.
# TODO: Create a backup of the jars being replaced.
#
jars_replaced = 0
for root, dirs, files in os.walk(dst):
  for f in files:
    if f.endswith('.jar') and f.startswith('hadoop'):
      dest = os.path.join(root, f)
      src_jar_name = f.replace(dst_ver, src_ver, 1)
      if src_jar_name in sources and os.path.isfile(dest):
        print("{} -> {}".format(dest, sources[src_jar_name]))
        shutil.copy2(sources[src_jar_name], dest)
        jars_replaced += 1


print("Replaced {} jars.".format(jars_replaced))

