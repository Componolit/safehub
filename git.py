
import subprocess
import logging
    
logger = logging.getLogger(__name__)

def _exec(args, cwd=None, ok_codes=[0]):
    proc = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    logger.debug("{} : {}".format(" ".join(args), proc.returncode))
    out_log = out.decode('utf-8').strip("\n").replace("\n", "\ ")
    err_log = err.decode('utf-8').strip("\n").replace("\n", "\ ")
    if proc.returncode:
        logger.warn("{} returned with unusual code {} but was allowed to do so".format(" ".join(args), proc.returncode))
        logger.info("Output was: {}".format(out_log if out_log else err_log))
    if proc.returncode not in ok_codes:
        raise RuntimeError("{} failed with status {} :{}".format(" ".join(args), proc.returncode, out_log if out_log else err_log))
    return out

class Git:

    def __init__(self, path):
        self.cwd = path

    @classmethod
    def clone(cls, url, path, instantiate=False, mirror=False):
        if mirror:
            _exec(['git', 'clone', '--mirror', url, path])
        else:
            _exec(['git', 'clone', url, path])
        if instantiate:
            return cls(path)

    @classmethod
    def mirror(cls, url, path, instantiate=False):
        return cls.clone(url, path, instantiate=instantiate, mirror=True)

    @classmethod
    def init(cls, path, instantiate=False):
        _exec(['git', 'init', '--bare', path])
        if instantiate:
            return cls(path)

    def fetch(self):
        try:
            _exec(['git', 'fetch', '--all'], self.cwd)
        except FileNotFoundError as e:
            logger.warn("Failed to fetch: {}".format(str(e)))

    def gen_file_list(self):
        filelist = _exec(['git', 'status', '-s'], self.cwd).decode('utf-8')
        files = []
        for f in filelist.split('\n'):
            if f.startswith('??'):
                files.append(f.split(' ')[1])
        return files

    def add(self):
        fl = self.gen_file_list()
        args = ['git', 'add']
        args.extend(fl)
        _exec(args, self.cwd)

    def commit(self, message):
        _exec(['git', 'commit', '-m', message, '-a'], self.cwd, ok_codes=[0,1])

    def push(self):
        _exec(['git', 'push', 'origin', 'master'], self.cwd, ok_codes=[0,1])
        

