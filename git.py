
import subprocess
    
def _exec(args, cwd=None):
    proc = subprocess.Popen(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    if not proc.returncode == 0:
        if err:
            raise RuntimeError(err)
        else:
            raise RuntimeError(out)
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
    def init(cls, path, instantiate=False):
        _exec(['git', 'init', '--bare', path])
        if instantiate:
            return cls(path)

    def fetch(self):
        _exec(['git', 'fetch'], self.cwd)

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
        _exec(['git', 'commit', '-m', message, '-a'], self.cwd)

    def push(self):
        _exec(['git', 'push', 'origin', 'master'], self.cwd)
        

