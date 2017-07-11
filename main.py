#!/usr/bin/env python3

from config import Config
from user import User
from organization import Organization
from repository import Repository

if __name__ == "__main__":
    cfg = Config()
    for entry in cfg.load_config()["repositories"]:
        with Repository(cfg.get_base_path(), entry["url"], entry["token"]) as r:
            r.update()
    for entry in cfg.load_config()["organizations"]:
        with Organization(cfg.get_base_path(), entry["url"], entry["token"]) as o:
            o.update()
            for repo in o.get_repositories():
                with Repository(cfg.get_base_path(), repo, entry["token"]) as r:
                    r.update()
    for entry in cfg.load_config()["users"]:
        with User(cfg.get_base_path(), entry["url"], entry["token"]) as u:
            for repo in u.get_repositories():
                with Repository(cfg.get_base_path(), repo, entry["token"]) as r:
                    r.update()

