#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

import yaml

try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

def load_manifest(manifest_file):
    with file(manifest_file, 'r+') as f:
        return yaml.load(f, Loader=Loader)

