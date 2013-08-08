# Just for python 3 compatibility
from __future__ import print_function

import ConfigParser
import hashlib
import os
import subprocess
import sys

COLORS = {
    'OFF': "\033[1;m",
    'RED': "\033[1;31m",
    'GRN': "\033[1;32m",
    'YLO': "\033[1;33m",
    'BLU': "\033[1;34m",
    'MGN': "\033[1;35m",
}


class Resource:
    """A pair of source and target with a shell command that defines
         how to generate the source from the target """

    cache = None

    def __init__(self, cmd, sources, target, hashcheck=False):
        self.cmd = cmd
        self.sources = sources
        self.target = target
        self.hashcheck = hashcheck

        if hashcheck and not Resource.cache:
            Resource.cache = ConfigParser.RawConfigParser()
            if os.path.exists('.bob-cache'):
                Resource.cache.read('.bob-cache')
            else:
                Resource.cache.add_section('hashes')

    def __cmdExists(self, cmd):
        exit_code = subprocess.call(['command', '-v', cmd],
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        return exit_code == 0

    def __isHashChanaged(self, path, hash):
        if not Resource.cache:
            return True

        if not Resource.cache.has_option('hashes', path):
            return True

        return Resource.cache.get('hashes', path) != hash

    def __setFileHash(self, path, hash):
        if not Resource.cache:
            return

        Resource.cache.set('hashes', path, hash)

        with open('.bob-cache', 'wb') as cache_file:
            Resource.cache.write(cache_file)

    def __removeFileHash(self, path):
        if not Resource.cache:
            return

        if Resource.cache.has_option('hashes', path):
            Resource.cache.remove_option('hashes', path)
            with open('.bob-cache', 'wb') as cache_file:
                Resource.cache.write(cache_file)

    def __filemd5(self, path):
        if not os.path.exists(path):
            return ""

        md5 = hashlib.new('md5')
        with open(path) as target:
            md5.update(target.read())

        return md5.hexdigest()

    def __requiresRebuild(self, path):
        if self.hashcheck:
            h = self.__filemd5(path)
            result = self.__isHashChanaged(path, h)
            return result
        else:
            return os.path.getmtime(path) > os.path.getmtime(self.target)

    def clean(self):
        if self.hashcheck:
            for path in self.sources:
                self.__removeFileHash(path)
        else:
            subprocess.call("rm -fr {0}".format(self.target),
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    def build(self):
        bin = self.cmd.split()[0]

        # Perform some smoke tests to ensure that we have everything we need
        # to complete the build. We also want to print all the potential
        # problems with the build rather than reporting one at a time.
        isBuildReady = True

        # Make sure the binary required to build this resource exists
        # on the current system. Abort if it doesn't exist
        if not self.__cmdExists(bin):
            print ("Fatal: Command '{0}' was not found.".format(bin))
            isBuildReady = False

        # Make sure that the source files exist before trying to build them
        for path in self.sources:
            if not os.path.exists(path):
                print ("Fatal: Source file '{0}' was not found.".format(path))
                isBuildReady = False

        if not isBuildReady:
            print ("Aborting build.")
            return False

        # Test that the file needs to be rebuilt before actually
        # rebuilding it.
        requiresRebuild = False

        if not os.path.exists(self.target):
            requiresRebuild = True
        else:
            for path in self.sources:
                requiresRebuild |= self.__requiresRebuild(path)

        if not requiresRebuild:
            print ("%(BLU)s[NOOP]%(OFF)s " % COLORS
                   + os.path.split(self.target)[-1])
            return True

        print ("%(YLO)s[MAKE]%(OFF)s " % COLORS
               + os.path.split(self.target)[-1], end='')
        sys.stdout.flush()

        exit_code = subprocess.call(self.cmd,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
        success = exit_code == 0

        if success:
            print ("\r%(GRN)s[DONE]%(OFF)s " % COLORS
                   + os.path.split(self.target)[-1] + " ")

            for path in self.sources:
                h = self.__filemd5(path)
                self.__setFileHash(path, h)
        else:
            print ("\r%(RED)s[FAIL]%(OFF)s " % COLORS
                   + os.path.split(self.target)[-1] + " ")
        sys.stdout.flush()
        return False
