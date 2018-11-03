## @file MuGit.py
# This module contains code that supports simple git operations.  This should 
# not be used as an extensive git lib but as what is needed for CI/CD builds
#
##
# Copyright (c) 2018, Microsoft Corporation
#
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##

import os
import logging
import subprocess
from UtilityFunctions import RunCmd

try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

class ObjectDict(object):
    def __init__(self):
        self.__values = list()
    def __setattr__(self,key,value):
        if not key.startswith("_"):
            self.__values.append(key)
        super().__setattr__(key,value)
    def __str__(self):
        result = list()
        result.append("ObjectDict:")
        for value in self.__values:
            result.append(value+":"+str(getattr(self,value)))
        return "\n".join(result)
    def set(self,key,value):
        self.__setattr__(key,value)

class Repo(object):

    def __init__(self,path=None):
        self._path = path #the path that the repo is pointed at
        self.active_branch = None #the active branch or none if detached
        self.bare = True #if the repo is bare
        self.exists = False # if the .git folder exists
        self.remotes = ObjectDict()
        self.initalized = False # if there is a git repo at the directory
        self.url = None # the origin remote
        self.dirty = False # if there are changes
        self.head = None # the head commit that this repo is at        
        self._update_from_git()

    # Updates the .git file
    def _update_from_git(self):

        if os.path.isdir(self._path):
            try:
                self.exists = True
                self.active_branch = self._get_branch()
                self.remotes = self._get_remotes()
                self.head = self._get_head()
                self.dirty = self._get_dirty()
                self.bare = self._get_bare()
                self.initalized = self._get_initalized()
            except Exception as e:
                logging.error("GIT ERROR for {0}".format(self._path))
                logging.error(e)
                raise e
                return False
            
    def _get_remotes(self):
        
        return_buffer = StringIO()
        cmd = "git remote"
        new_remotes = ObjectDict()
        RunCmd(cmd, workingdir=self._path,outstream=return_buffer)
        p1 = return_buffer.getvalue().strip()
        return_buffer.close()
        remote_list = p1.split("\n")
        for remote in remote_list:
            url = ObjectDict()
            url.set("url",self._get_url(remote))
            setattr(new_remotes, remote,url)        
        
        return new_remotes

    def _get_url(self,remote="origin"):
        return_buffer = StringIO()
        cmd = "git config --get remote.{0}.url".format(remote)
        RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        return_buffer.close()
        return p1

    def _get_dirty(self):
        return_buffer = StringIO()
        cmd = "git status --short"
        
        RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        return_buffer.close()
        
        if len(p1) > 0:
            return True

        return_buffer = StringIO()
        cmd = "git log --branches --not --remotes --decorate --oneline"

        RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        return_buffer.close()

        if len(p1) > 0:
            return True

       
        return False
    
    def _get_branch(self):
        return_buffer = StringIO()
        cmd = "git rev-parse --abbrev-ref HEAD"
        RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        return_buffer.close()        
        return p1
    
    def _get_head(self):        
        return_buffer = StringIO()
        cmd = "git rev-parse HEAD"
        RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        return_buffer.close()

        head = ObjectDict()
        head.set("commit",p1)

        return head

    def _get_bare(self):  
        return_buffer = StringIO()
        cmd = "git rev-parse --is-bare-repository"
        RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        return_buffer.close()
        if p1.lower() == "true":
            return True
        else: 
            return False

    def _get_initalized(self):
        return os.path.isdir(os.path.join(self._path,".git"))
    
    def submodule(self,command, *args):
        logging.debug("Calling command on submodule {0} with {1}".format(command,args))
        return_buffer = StringIO()
        flags = " ".join(args)
        cmd = "git submodule {0} {1}".format(command,flags)

        ret = RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        if ret != 0:
            logging.error(p1)
            return False

        return True

    def fetch(self):
        return_buffer = StringIO()
        
        cmd = "git fetch"
        
        ret = RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        if ret != 0:
            logging.error(p1)
            return False

        return True
    
    def pull(self):
        return_buffer = StringIO()
        
        cmd = "git pull"
        
        ret = RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        if ret != 0:
            logging.error(p1)
            return False

        return True

    def checkout(self,branch=None,commit=None):
        return_buffer = StringIO()
        if not branch is None:
            cmd = "git checkout %s" % branch
        elif not commit is None:
            cmd = "git checkout %s" % commit
        ret = RunCmd(cmd, workingdir=self._path,outstream=return_buffer)

        p1 = return_buffer.getvalue().strip()
        if ret != 0:
            logging.debug(p1)
            return False

        return True

    @classmethod
    def clone_from(self,url, to_path, progress=None, env=None,shallow =False, **kwargs):
        logging.debug("Cloning {0} into {1}".format(url,to_path))
        #make sure we get the commit if 
        # use run command from utilities
        cmd = ""
        if shallow:
            cmd = "git clone --depth 1 --shallow-submodules --recurse-submodules %s %s " % (url, to_path)
        else:
            cmd = "git clone --recurse-submodules %s %s " % (url, to_path)
        RunCmd(cmd)

        return Repo(to_path)
    
    def clone(self,url, shallow=False):
        logging.debug("Cloning {0} into {1}".format(url,to_path))
        #make sure we get the commit if 
        # use run command from utilities
        cmd = ""
        if shallow:
            cmd = "git clone --depth 1 --shallow-submodules --recurse-submodules %s %s " % (url, to_path)
        else:
            cmd = "git clone --recurse-submodules %s %s " % (url, to_path)
        RunCmd(cmd)

        self._update_from_git()

        return Repo(to_path)

    