#!/usr/bin/env python3

from config import Config
from repository import Repository

if __name__ == "__main__":
    cfg = Config()
    for entry in cfg.load_config()["repositories"]:
        with Repository(cfg.get_base_path(), entry["url"], entry["token"]) as r:
            r.update()
