
import os
import re
import json


def get_base_path():
    with open('/etc/login.defs', 'r') as login_defs:
        return _get_base_path(login_defs.readlines(),
                              lambda: os.getenv("HOME"),
                              lambda: os.getuid())

class ConfigBase:

    cfg = {}

    def get_login_defs(self):
        raise NotImplementedError("get_login_defs")

    def get_home(self):
        raise NotImplementedError("get_home")

    def get_uid(self):
        raise NotImplementedError("get_uid")

    def get_base_path(self):
        login_defs = self.get_login_defs()
        home = self.get_home()
        uid = self.get_uid()
        UID_MIN = 1000
        UID_MAX = 60000
        SYS_UID_MIN = 100
        SYS_UID_MAX = 999
        if uid == 0:
            return "/" + home.strip("/") + "/.safehub"
        tabsplit = re.compile("[\t ]+")
        for line in login_defs:
            line = line.strip('\n')
            if line.startswith("UID_MIN"):
                UID_MIN = int(tabsplit.split(line)[1])
            elif line.startswith("UID_MAX"):
                UID_MAX = int(tabsplit.split(line)[1])
            elif line.startswith("SYS_UID_MIN"):
                SYS_UID_MIN = int(tabsplit.split(line)[1])
            elif line.startswith("SYS_UID_MAX"):
                SYS_UID_MAX = int(tabsplit.split(line)[1])
        if uid <= UID_MAX and uid >= UID_MIN:
            return "/" + home.strip("/") + "/.safehub"
        elif uid <= SYS_UID_MAX and uid >= SYS_UID_MIN:
            return "/" + home.strip("/")
        else:
            raise ValueError("UID outside defined UID ranges.")


    def load_config(self):
        try:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            self.cfg = open(dir_path + "/safehub.json", "r")
        except FileNotFoundError:
            try:
                self.cfg = open(os.getenv("HOME") + "/.safehub.json", "r")
            except FileNotFoundError:
                try:
                    self.cfg = open("/etc/safehub/safehub.json", "r")
                except FileNotFoundError:
                    raise FileNotFoundError("Failed to find configuration file.")
        return json.load(self.cfg)

class Config(ConfigBase):

    def get_login_defs(self):
        with open('/etc/login.defs', 'r') as login_defs:
            return login_defs.readlines()

    def get_home(self):
        return os.getenv("HOME")

    def get_uid(self):
        return os.getuid()
