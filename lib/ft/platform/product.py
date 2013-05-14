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

from ft.platform import HasMetadata, GenConfig, GenConfig2
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
    
        self.specification = None
        self.__specification_list = list()
    
        self.config = None

    def select(self, name):
        self.repo.checkout(name)
        self.configure()

    def configure(self):
        config_file = os.path.join(self.local_path, "config.yaml")
        self.config = GenConfig2(config_file)

    def get_product_versions(self):
        self._setup_repo()
        self.__specification_list = list()
        return self.repo.get_refs()

    def set_specification(self, name):
        if len(self.__specification_list) == 0:
            self.__load_specs()
        self.specification = self.__get_specification_by_name(name)
        return self.specification

    def __get_specification_by_name(self, name):
        for spec in self.__specification_list:
            if spec["name"] == name:
                return spec

    def get_spec_menu_list(self):
        if len(self.__specification_list) == 0:
            self.__load_specs()
        menu_info =  self.__get_spec_menu_info()
        print(menu_info)
        return menu_info

    def __get_spec_menu_info(self):
        specifications = list()
        for spec in self.__specification_list:
            specifications.append({
                "name": spec["name"],
                "shortdesc": spec["shortdesc"],
                })
        return specifications

    def __load_specs(self):
        spec_dir = os.path.join(self.local_path, 'spec')
        for root, dirs, files in os.walk(spec_dir):
            for file_name in files:
                file_name = os.path.join(root, file_name)
                self.__load_single_spec(file_name)

    def __load_single_spec(self, file_name):
        if file_name.endswith(".yaml"):
            spec = Specification(file_name)
            self.__specification_list.append(spec.test_spec)

