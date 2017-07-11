#!/usr/bin/env python3

import logging
import logging.handlers
import argparse
import time
import sys
from config import Config
from user import User
from organization import Organization
from repository import Repository
from github import RateLimitExceeded
from setproctitle import setproctitle

def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="print debug output", action="store_true")
    parser.add_argument("-q", "--quiet", help="print less output", action="store_true")
    parser.add_argument("-s", "--syslog", help="log to syslog", action="store_true")
    return parser

if __name__ == "__main__":
    setproctitle("safehub")
    args = get_parser().parse_args()
    logger = logging.getLogger(__name__)
    if args.verbose and args.quiet:
        print("verbose and quiet cannot be used together")
        exit(1)
    if args.verbose:
        logl = logging.DEBUG
    elif args.quiet:
        logl = logging.WARN
    else:
        logl = logging.INFO
    if args.syslog:
        handler = logging.handlers.SysLogHandler(address='/dev/log', facility=logging.handlers.SysLogHandler.LOG_USER)
#        logger.addHandler(handler)
        logging.basicConfig(format='[safehub] %(levelname)s: %(message)s', level=logl, handlers=[handler])
    else:
        handler = logging.StreamHandler(sys.stdout)
#        logger.addHandler(handler)
        logging.basicConfig(format='%(asctime)s [%(name)s] %(levelname)s: %(message)s', level=logl, handlers=[handler])
    cfg = Config()
    try:
        for entry in cfg.load_config()["repositories"]:
            with Repository(cfg.get_base_path(), entry["url"], entry["token"]) as r:
                logger.info("Pulling {}".format(r.get_github_url()))
                r.update()
        for entry in cfg.load_config()["organizations"]:
            with Organization(cfg.get_base_path(), entry["url"], entry["token"]) as o:
                o.update()
                for repo in o.get_repositories():
                    with Repository(cfg.get_base_path(), repo, entry["token"]) as r:
                        logger.info("Pulling {}".format(r.get_github_url()))
                        r.update()
        for entry in cfg.load_config()["users"]:
            with User(cfg.get_base_path(), entry["url"], entry["token"]) as u:
                for repo in u.get_repositories():
                    with Repository(cfg.get_base_path(), repo, entry["token"]) as r:
                        logger.info("Pulling {}".format(r.get_github_url()))
                        r.update()
    except RateLimitExceeded as re:
        logger.fatal("Ratelimit exceeded. Reset at {}".format(time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(int(str(re))))))
