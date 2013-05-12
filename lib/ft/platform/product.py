#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

## @package product
#
#  Abstracts the testset metadata stored in a git repository and provideds
#  capability-querying utilities to facilitate run-time enabled or disabling of
#  UI widgets.
#

import sys, os

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ft import Base

from ft.platform import HasMetadata
from ft.util.yaml_util import load_manifest
from ft.test import Specification

class ProductDB(Base):

    __tablename__ = "pyft_product"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    hardware_rev = Column(String(20))
    metadata_repo = Column(String(100))
    metadata_rev = Column(String(100))

    uuts = relationship("UnitUnderTest")
    
    def __repr__(self,):
        rstring = "<Product('%s','%s','%s':'%s')>" 
        rtuple = ( self.name, self.hardware_rev, self.metadata['repo'], 
                self.metadata['rev'], )
        return rstring % rtuple

class Product(ProductDB, HasMetadata):

    __metadata_type__ = "products"

    def __init__(self, manifest_file):
        self.manifest = load_manifest(manifest_file)
        self.metadata_repo_dict = self.manifest["metadata_repo"]
        self.repo = None

    def get_product_versions(self):
        self._setup_repo()
        return self.repo.get_refs()

    def get_specifications(self):
        spec_dir = os.path.join(self.local_path, 'spec')
        specifications = list()
        for root, dirs, files in os.walk(spec_dir):
            for file_name in files:
                if file_name.endswith(".yaml"):
                    spec = Specification(os.path.join(root, file_name))
                    spec = spec.test_spec
                    specifications.append({
                        "name": spec["name"],
                        "shortdesc": spec["shortdesc"],
                        })
        return specifications

