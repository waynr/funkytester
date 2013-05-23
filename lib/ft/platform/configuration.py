#!/usr/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# standard libraries
import re, sys
from os import path, walk

import logging, pprint

# installed libraries
import git, yaml
try:
        from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
        from yaml import Loader, Dumper

# local libraries

from ft.util.locker import (
        cls_locker_all
        )

##
# General configuration tool.
#
@cls_locker_all
class GenConfig(object):

    def __init__(self, file_name):
        self._load(file_name)
    
    def _load(self, file_name):
        with file(file_name, 'r+') as f:
            tmp = yaml.load(f, Loader=Loader)
            self.name = tmp["name"]
            self.shortdesc = tmp["shortdesc"]
            options = tmp["options"]

            self.__set_subattr(self, options)
    
    def __set_subattr(self, obj, dct):
        for key, val in dct.items():
            setattr(obj, key, val)

    def save(self, file_name):
        with file(file_name, 'w') as f:
            tmp = {
                    "name": self.name,
                    "shortdesc": self.shortdesc,
                    "options": self.options,
                    }
            yaml.dump(tmp, f, Dumper=Dumper)

    def is_valid(self, *args):
        return True

    def get(self, optname):
        return getattr(self, optname)

    def set(self, optname, value):
        return setattr(self, optname, value)

class GenConfig2(GenConfig):

    def __repr__(self):
        return pprint.pformat(self.__dict__)

    def _load(self, file_name):
        with file(file_name, 'r+') as f:
            tmp = yaml.load(f, Loader=Loader)
            self.__set_subattr(tmp)

    def __set_subattr(self, dct):
        for key, val in dct.items():
            setattr(self, key, val)

## Mixin intended to give subclassers access to nifty metadata directories.
#  
#  The purpose of this is to reduce code duplication and to provide consistent
#  access to meta data repositories which can be git, svn, or local
#  directory-based. The interface should remain agnostic to the actual directory
#  contents.
#
#  Obviously this needs a great deal of work before it is awesome.
#
class HasMetadata(object):

    def __init__(self):
        self.metadata_repo = ""
        self.metadata_version = ""
        self.relative_path = ""
        self.name = ""

    def set_info(self, metadata_dict):
        self.name = metadata_dict["name"]
        self.relative_path = metadata_dict["relative_path"]

    def _setup_repo(self):
        self.__setup_git_repo()

    def __setup_git_repo(self):
        self.repo = GitMetaDataRepo(self.metadata_repo_dict,
                self.relative_path, self.__metadata_type__)
        self.local_path = self.repo.local_path
        self.metadata_repo = self.repo.url
        self.metadata_version = self.repo.version
        self.repo.update()

class MetaDataDir(object):

    local_base_path = "./resources/"

    def __init__(self, relative_path):
        self.local_path = path.join( self.local_base_path, relative_path)
        self.repo = None
        self.version = ""

class GitMetaDataRepo(MetaDataDir):

    def __init__(self, repo_dict, relative_path, metadata_type=""):
        MetaDataDir.__init__(self, path.join( metadata_type, relative_path ))
        self.url = ( repo_dict['url'] + repo_dict['basepath'] + relative_path +
                '.git' )

    def update(self,):
        if path.isdir( path.join(self.local_path, '.git')) and not self.repo:
            self.repo = git.Repo(self.local_path)
            self.repo.remotes.origin.pull()
        else:
            self.checkout()

    def checkout(self, ref=None):
        if not self.repo:
            self.repo = git.Repo.clone_from(self.url, self.local_path)
        if ref:
            tmp = self.repo.git
            tmp.checkout(ref)
        return None
    
    def get_refs(self,):
        symbolic_refs = []
        branches = self.repo.branches
        for branch in branches:
            symbolic_refs.append({
                "name": branch.name,
                "shortdesc": branch.object.summary,
                })

        tags = self.repo.tags
        for tag in tags:
            symbolic_refs.append({
                "name": tag.name,
                "shortdesc": tag.tag.message,
                })
        return symbolic_refs
