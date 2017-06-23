#!/usr/bin/env python3

import unittest
import os
import glob
import py_compile

class Compile(unittest.TestCase):

    files = []

    def setUp(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        self.files = glob.glob("{}/**/*.py".format(cwd), recursive=True)
        print(self.files)

    def test_compile(self):
        for f in self.files:
            py_compile.compile(f, doraise=True)
