#!/usr/bin/env python3

import unittest
import os
import glob
import py_compile
from subprocess import Popen, PIPE

from config import ConfigBase, Config
from git import Git
from repository import Repository
from organization import Organization
from github import GitHubBase, GitHub, TemporaryError

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

    def test_inst(self):
        Config()
        baseconfig = ConfigBase()
        self.assertRaises(NotImplementedError, baseconfig.get_base_path)

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
        
        self.login_defs = ["SYS_UID_MAX\t \t400\n", "UID_MIN \t   450\n"]  
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
        Popen(['git', 'init',  '--bare'], cwd=self.bare, stdout=PIPE).communicate()

    def test_inst(self):
        Git("")

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
        os.mkdir(self.repo + '/testdir/')
        with open(self.repo + '/testdir/testfile2', 'w') as testfile:
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

    def test_push(self):
        repo = Git.clone(self.bare, self.basepath + 'pushtest', instantiate=True)
        with open(self.basepath + 'pushtest/data', 'w') as testfile:
            testfile.write('data\n')
        repo.add()
        repo.commit('testcommit')
        repo.push()
        p = Popen(['git', 'log', '-1', '--oneline'], cwd=self.bare, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise RuntimeError(err)
        self.assertEqual('testcommit', out.decode('utf-8').split(' ')[1].strip())

    def test_fetch(self):
        repo = Git.mirror(self.bare, self.basepath + 'fetchtest', instantiate=True)
        work_clone = self.basepath + 'tmpfetch'
        Popen(['git', 'clone', self.bare, work_clone], stdout=PIPE, stderr=PIPE).communicate()
        Popen(['git', 'checkout', '-b', 'fetchtest'], cwd=work_clone, stdout=PIPE, stderr=PIPE).communicate()
        with open(work_clone + '/fetchfile', 'w') as fetchfile:
            fetchfile.write("fetch\n")
        Popen(['git', 'add', 'fetchfile'], cwd=work_clone, stdout=PIPE, stderr=PIPE).communicate()
        Popen(['git', 'commit', '-a', '-m', 'fetchtest'], cwd=work_clone, stdout=PIPE, stderr=PIPE).communicate()
        Popen(['git', 'push', '--set-upstream', 'origin', 'fetchtest'], cwd=work_clone, stdout=PIPE, stderr=PIPE).communicate()
        repo.fetch()
        p = Popen(['git', 'branch'], cwd=self.basepath + 'fetchtest', stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise RuntimeError(err)
        self.assertIn('fetchtest', [branch.strip() for branch in out.decode('utf-8').split('\n')])
        p = Popen(['git', 'log', 'fetchtest', '-1', '--oneline'], cwd=self.basepath + 'fetchtest', stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        self.assertEqual('fetchtest', out.decode('utf-8').split(' ')[1].strip())



class OrgTest(unittest.TestCase):

    def test_inst(self):
        o = Organization("/tmp/safehub_organization_test.{}".format(os.getpid()), "https://github.com/jklmnn", "")
        self.assertEqual(o.user, "jklmnn")
        self.assertEqual(o.repo, None)

    def test_parse_url(self):
        self.assertEqual("jklmnn", Organization._parse_url("https://github.com/jklmnn"))
        self.assertRaises(ValueError, Organization._parse_url, "https.//github.com/jklmnn/safehub")

class RepoTest(unittest.TestCase):

    def test_inst(self):
        r = Repository("/tmp/safehub_repository_test.{}".format(os.getpid()), "https://github.com/jklmnn/safehub", "")
        self.assertEqual(r.user, "jklmnn")
        self.assertEqual(r.repo, "safehub")
        r = Repository("/tmp/safehub_repository_test.{}".format(os.getpid()), "https://github.com/jklmnn/safehub", "")
        self.assertEqual(r.user, "jklmnn")
        self.assertEqual(r.repo, "safehub")

    def test_parse_url(self):
        self.assertEqual(("jklmnn", "safehub"), Repository._parse_url("https://github.com/jklmnn/safehub"))
        self.assertEqual(("jklmnn", "safehub"), Repository._parse_url("https://github.com/jklmnn/safehub.git"))
        self.assertRaises(ValueError, Repository._parse_url, "https://github.com/jklmnn")
        self.assertRaises(ValueError, Repository._parse_url, "https:/github.com/jklmnn/safehub.git")
        self.assertRaises(ValueError, Repository._parse_url, "https//github.com/jklmnn/safehub.git")

    def test_gen_repo_git_url(self):
        self.assertEqual("git://github.com/jklmnn/safehub.git", Repository._gen_code_git_url("jklmnn", "safehub"))

    def test_gen_wiki_git_url(self):
        self.assertEqual("git://github.com/jklmnn/safehub.wiki.git", Repository._gen_wiki_git_url("jklmnn", "safehub"))

    def test_gen_path(self):
        base = "/base/"
        self.assertEqual("/base", Repository._gen_path(base))
        self.assertEqual("/base/jklmnn", Repository._gen_path(base, "jklmnn"))
        self.assertEqual("/base/jklmnn/safehub", Repository._gen_path(base, "jklmnn", "safehub"))
        self.assertEqual("/base/jklmnn/safehub/wiki.git", Repository._gen_path(base, "jklmnn", "safehub", "wiki"))
        self.assertEqual("/base/jklmnn/meta.git", Repository._gen_path(base, "jklmnn", None, "meta"))
        self.assertRaises(ValueError, Repository._gen_path, base, "jklmnn", "safehub", "test")
        self.assertRaises(RuntimeError, Repository._gen_path, base, None, "safehub", "code")
        self.assertRaises(RuntimeError, Repository._gen_path, base, "jklmnn", None, "wiki")

class GitHubTest(unittest.TestCase, GitHubBase):

    def setUp(self):
        self.basepath = '/tmp/safehub_fetch_test.{}/'.format(os.getpid())

    def _get(self, url):
        tdata = {"one": "[1]", "two": "[2,2]", "three": "[3,3,3]"}
        first = "one"
        last = "three"
        nxt = {"one": "two", "two": "three"}
        prev = {"two": "one", "three": "two"}
        if url in tdata:
            return (tdata[url],
                    {"Link": '<one>; rel="first", <three>; rel="last"' +
                        ', <{}>; rel="next"'.format(nxt[url]) if url in nxt else '' +
                        ', <{}>; rel="prev"'.format(prev[url]) if url in prev else '' })

    def get_data(self, user, repo, path):
        if not user:
            raise TemporaryError
        return []


    def test_inst(self):
        GitHub("")
        ghb = GitHubBase()
        self.assertRaises(NotImplementedError, ghb.get_data, "", "", "")
        self.assertRaises(NotImplementedError, ghb._get, "")

    def test_paging(self):
        first, last, nxt, prev = GitHubBase._parse_link('<https://api.github.com/repositories/test/forks?page=3>; rel="next", <https://api.github.com/repositories/test/forks?page=495>; rel="last", <https://api.github.com/repositories/test/forks?page=1>; rel="first", <https://api.github.com/repositories/test/forks?page=1>; rel="prev"')
        self.assertEqual("https://api.github.com/repositories/test/forks?page=3", nxt)
        self.assertEqual("https://api.github.com/repositories/test/forks?page=495", last)
        self.assertEqual("https://api.github.com/repositories/test/forks?page=1", first)
        self.assertEqual("https://api.github.com/repositories/test/forks?page=1", prev)
        first, last, nxt, prev = GitHubBase._parse_link('<https://api.github.com/repositories/test/forks?page=2>; rel="next", <https://api.github.com/repositories/test/forks?page=495>; rel="last", <https://api.github.com/repositories/test/forks?page=1>; rel="first"')
        self.assertIsNone(prev)

    def test_page_gen(self):
        self.assertEqual([1,2,2,3,3,3], self.gen_data("one"))

    def test_fetch(self):
        self.fetch_repository("user", "repo", self.basepath, "/", ["file1", "file2"])
        self.fetch_repository("user", "repo", self.basepath, "/dir/", ["file3", "file4"])
        self.fetch_repository(None, "repo", self.basepath, "/", ["file5", "file6"])
        for f in ["/file1.json", "/file2.json", "/dir/file3.json", "/dir/file4.json"]:
            with open(self.basepath + f, 'r') as tf:
                self.assertEqual("[]", tf.read())
        self.assertFalse(os.path.isfile(self.basepath + "/file5"))
        self.assertFalse(os.path.isfile(self.basepath + "/file6"))

