#!/usr/bin/env python3

import unittest
import os
import glob
import py_compile
from subprocess import Popen, PIPE

from config import ConfigBase
from git import Git
from repository import _parse_url, _gen_repo_git_url, _gen_wiki_git_url, _gen_path

class Compile(unittest.TestCase):

    files = []

    def setUp(self):
        cwd = os.path.dirname(os.path.realpath(__file__))
        self.files = glob.glob("{}/**/*.py".format(cwd), recursive=True)

    def test_compile(self):
        for f in self.files:
            py_compile.compile(f, doraise=True)

class ConfigTest(unittest.TestCase, ConfigBase):

    def get_login_defs(self):
        return self.login_defs

    def get_home(self):
        return self.home

    def get_uid(self):
        return self.uid

    def test_base(self):

        self.login_defs = []  
        self.home = "/home/test"  
        self.uid = 1000 
        self.assertEqual("/home/test/.safehub", self.get_base_path())
            
        self.login_defs = []  
        self.home = "/var/lib/safehub"  
        self.uid = 499 
        self.assertEqual("/var/lib/safehub", self.get_base_path())
        
        self.login_defs = ["UID_MIN     2000\n", "SYS_UID_MAX\t\t\t1999\n"]  
        self.home = "/var/lib/safehub"  
        self.uid = 1500 
        self.assertEqual("/var/lib/safehub", self.get_base_path())
        
        self.login_defs = ["SYS_UID_MAX        400\n", "UID_MIN\t\t450\n"]  
        self.home = "/home/test"  
        self.uid = 450 
        self.assertEqual("/home/test/.safehub", self.get_base_path())
        
        self.login_defs = ["UID_MIN\t\t\t2000\n", "SYS_UID_MAX     1999\n"]  
        self.home = "/var/lib/safehub"  
        self.uid = 1500 
        self.assertEqual("/var/lib/safehub", self.get_base_path())
        
        self.login_defs = ["SYS_UID_MAX\t\t400\n", "UID_MIN    450\n"]  
        self.home = "/home/test"  
        self.uid = 450 
        self.assertEqual("/home/test/.safehub", self.get_base_path())
        
        self.login_defs = []  
        self.home = "/root"  
        self.uid = 0 
        self.assertEqual("/root/.safehub", self.get_base_path())
       
        self.login_defs = ["UID_MIN   2000\n"]
        self.home = "/"
        self.uid = 1000
        self.assertRaises(ValueError, self.get_base_path)
    
    def test_impl(self):
        baseconfig = ConfigBase()
        self.assertRaises(NotImplementedError, baseconfig.get_base_path)

class GitTest(unittest.TestCase):

    def setUp(self):
        self.basepath = '/tmp/safehub_git_test.{}/'.format(os.getpid())
        if not os.path.isdir(self.basepath):
            os.mkdir(self.basepath)
        self.repo = self.basepath + 'repo'
        self.bare = self.basepath + 'bare'
        if not os.path.isdir(self.repo):
            os.mkdir(self.repo)
        if not os.path.isdir(self.bare):
            os.mkdir(self.bare)
        Popen(['git', 'init'], cwd=self.repo, stdout=PIPE).communicate()
        Popen(['git', 'init'], cwd=self.bare, stdout=PIPE).communicate()

    def test_init(self):
        Git.init(self.basepath + 'inittest')
        p = Popen(['git', 'branch'], cwd=self.basepath+'inittest', stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if not p.returncode == 0:
            raise RuntimeError("Failed to init repository: {}".format(err))

    def test_clone(self):
        Git.clone(self.bare, self.basepath + 'clonetest')
        p = Popen(['git', 'status'], cwd=self.basepath+'clonetest', stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if not p.returncode == 0:
            raise RuntimeError("Failed to clone repository: {}".format(err))


    def test_add(self):
        with open(self.repo + '/testfile', 'w') as testfile:
            testfile.write('test\n')
        repo = Git(self.repo)
        repo.add()
        p = Popen(['git', 'status', '-s'], cwd=self.repo, stdout=PIPE, stderr=PIPE)
        out, err =  p.communicate()
        out = out.decode('utf-8')
        repo.commit("testcommit")
        for entry in out.split('\n'):
            if entry.startswith('??'):
                raise ValueError("No untracked files should exist: {}".format(err))




class Github(unittest.TestCase):

    def test_parse_url(self):
        self.assertEqual(("jklmnn", "safehub"), _parse_url("https://github.com/jklmnn/safehub"))
        self.assertEqual(("jklmnn", "safehub"), _parse_url("https://github.com/jklmnn/safehub.git"))
        self.assertRaises(ValueError, _parse_url, "https://github.com/jklmnn")
        self.assertRaises(ValueError, _parse_url, "https:/github.com/jklmnn/safehub.git")
        self.assertRaises(ValueError, _parse_url, "https//github.com/jklmnn/safehub.git")

    def test_gen_repo_git_url(self):
        self.assertEqual("git://github.com/jklmnn/safehub.git", _gen_repo_git_url("jklmnn", "safehub"))

    def test_gen_wiki_git_url(self):
        self.assertEqual("git://github.com/jklmnn/safehub.wiki.git", _gen_wiki_git_url("jklmnn", "safehub"))

    def test_gen_path(self):
        base = "/base/"
        self.assertEqual("/base", _gen_path(base))
        self.assertEqual("/base/jklmnn", _gen_path(base, "jklmnn"))
        self.assertEqual("/base/jklmnn/safehub", _gen_path(base, "jklmnn", "safehub"))
        self.assertEqual("/base/jklmnn/safehub/wiki.git", _gen_path(base, "jklmnn", "safehub", "wiki"))
        self.assertRaises(ValueError, _gen_path, base, "jklmnn", "safehub", "test")
        self.assertRaises(RuntimeError, _gen_path, base, None, "safehub", "code")
        self.assertRaises(RuntimeError, _gen_path, base, "jklmnn", None, "wiki")
