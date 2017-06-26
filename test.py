#!/usr/bin/env python3

import unittest
import os
import glob
import py_compile

from config import _get_base_path
from repository import _parse_url, _gen_repo_git_url, _gen_wiki_git_url, _gen_path

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
        self.assertEqual("/home/test/.safehub", _get_base_path([], "/home/test", 1000))
        self.assertEqual("/var/lib/safehub", _get_base_path([], "/var/lib/safehub", 499))
        self.assertEqual("/var/lib/safehub", _get_base_path(["UID_MIN     2000\n", "SYS_UID_MAX\t\t\t1999\n"], "/var/lib/safehub", 1500))
        self.assertEqual("/home/test/.safehub", _get_base_path(["SYS_UID_MAX        400\n", "UID_MIN\t\t450\n"], "/home/test", 450))
        self.assertEqual("/var/lib/safehub", _get_base_path(["UID_MIN\t\t\t2000\n", "SYS_UID_MAX     1999\n"], "/var/lib/safehub", 1500))
        self.assertEqual("/home/test/.safehub", _get_base_path(["SYS_UID_MAX\t\t400\n", "UID_MIN    450\n"], "/home/test", 450))
        self.assertEqual("/root/.safehub", _get_base_path([], "/root", 0))
        self.assertRaises(ValueError, _get_base_path, ["UID_MIN   2000\n"], "/", 1000)

class Github(unittest.TestCase):

    def test_parse_url(self):
        self.assertEqual(("jklmnn", "safehub"), _parse_url("https://github.com/jklmnn/safehub"))
        self.assertEqual(("jklmnn", "safehub"), _parse_url("https://github.com/jklmnn/safehub.git"))
        self.assertRaises(ValueError, _parse_url, "https://github.com/jklmnn")
        self.assertRaises(ValueError, _parse_url, "https:/github.com/jklmnn/safehub.git")
        self.assertRaises(ValueError, _parse_url, "https//github.com/jklmnn/safehub.git")

    def test_gen_repo_git_url(self):
        self.assertEqual("https://github.com/jklmnn/safehub.git", _gen_repo_git_url("jklmnn", "safehub"))

    def test_gen_wiki_git_url(self):
        self.assertEqual("https://github.com/jklmnn/safehub.wiki.git", _gen_wiki_git_url("jklmnn", "safehub"))

    def test_gen_path(self):
        base = "/base/"
        self.assertEqual("/base", _gen_path(base))
        self.assertEqual("/base/jklmnn", _gen_path(base, "jklmnn"))
        self.assertEqual("/base/jklmnn/safehub", _gen_path(base, "jklmnn", "safehub"))
        self.assertEqual("/base/jklmnn/safehub/wiki.git", _gen_path(base, "jklmnn", "safehub", "wiki"))
