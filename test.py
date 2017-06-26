#!/usr/bin/env python3

import unittest
import os
import glob
import py_compile

from config import _get_base_path

class Compile(unittest.TestCase):

    files = []

    def setUp(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        self.files = glob.glob("{}/**/*.py".format(cwd), recursive=True)

    def test_compile(self):
        for f in self.files:
            py_compile.compile(f, doraise=True)

class Config(unittest.TestCase):

    def test_base(self):
        assert("/home/test/.safehub/" == _get_base_path([], "/home/test", 1000))
        assert("/var/lib/safehub/" == _get_base_path([], "/var/lib/safehub", 499))
        assert("/var/lib/safehub/" == _get_base_path(["UID_MIN     2000\n", "SYS_UID_MAX\t\t\t1999\n"], "/var/lib/safehub", 1500))
        assert("/home/test/.safehub/" == _get_base_path(["SYS_UID_MAX        400\n", "UID_MIN\t\t450\n"], "/home/test", 450))
        assert("/var/lib/safehub/" == _get_base_path(["UID_MIN\t\t\t2000\n", "SYS_UID_MAX     1999\n"], "/var/lib/safehub", 1500))
        assert("/home/test/.safehub/" == _get_base_path(["SYS_UID_MAX\t\t400\n", "UID_MIN    450\n"], "/home/test", 450))
        assert("/root/.safehub/" == _get_base_path([], "/root", 0))
