import argparse
import subprocess
import warnings
from os import getcwd
from os.path import relpath, abspath, dirname
from typing import List, Optional

HELP = """
integer - traverse into that directory
? - show this help message
p - print current state
P - refresh
u - go up to parent directory
c - make current directory the base
x - relative or absolute paths 
s - sort by name or by size
q - quit
"""


class DirectoryDu:
    """Disk usage information for a single directory. Always store paths
    as absolute paths."""

    def __init__(self, path: str, size: int):
        self.path = abspath(path)
        self.size = size

    def str(self, base_directory=None):
        if base_directory:
            return f"{self.size:>10d}\t{relpath(self.path, base_directory)}"
        else:
            return f"{self.size:>10d}\t{abspath(self.path)}"

    def __str__(self):
        return self.str()


class IDu:
    """Interactive disk usage analyser."""

    def __init__(self, directory=None, base_directory=None):
        self.directory = abspath(directory) if directory else getcwd()
        self.base_directory = abspath(
            base_directory) if base_directory else getcwd()
        self.results = None
        self.sort_by_size = False
        self.rel = True

    def update(self, directory: Optional[str] = None, allow_rte: bool = True):
        if directory is None:
            directory = self.directory
        directory = abspath(directory)
        try:
            self.results = run_du(directory)
            self.resort()
            self.directory = directory

        except RuntimeError as exc:
            if not allow_rte:
                raise
            warnings.warn(exc.__str__())

        except KeyboardInterrupt:  # catch ctrl-C
            pass

    def resort(self):
        if self.sort_by_size:
            self.results = sorted(self.results, key=lambda x: x.size)
        else:
            self.results = sorted(self.results, key=lambda x: x.path)

    def prompt(self):
        ans = input('> ')
        try:
            if self.results is None:
                raise KeyError
            options = {n: r for n, r in enumerate(self.results)}
            self.update(options[int(ans)].path)
            print(self)
        except (KeyError, ValueError):
            if ans == '?':
                print(HELP)
            elif ans == 'q':
                exit(0)
            elif ans == 'p':
                print(self)
            elif ans == 'P':
                self.update()
                print(self)
            elif ans == 'u':
                self.update(dirname(abspath(self.directory)))
                print(self)
            elif ans == 'c':
                self.base_directory = self.directory
                print(self)
            elif ans == 'x':
                self.rel = not self.rel
                print(self)
            elif ans == 's':
                self.sort_by_size = not self.sort_by_size
                self.resort()
                print(self)
            else:
                print('?')

    def loop(self):
        self.update(allow_rte=False)
        print(self)
        while True:
            try:
                self.prompt()
            except (KeyboardInterrupt, EOFError):
                break

    def __str__(self):
        def fmt(n, r):
            if self.rel:
                return f"{n}\t{r.str(self.base_directory)}"
            else:
                return f"{n}\t{r.str()}"

        output = abspath(self.directory) + '\n' + '\n'.join(
            [fmt(n, r) for n, r in enumerate(self.results)]
        )

        return output

    __repr__ = __str__


def run_du(directory: str) -> List[DirectoryDu]:
    du_res = subprocess.run(['du', '-d1', directory], capture_output=True)
    if du_res.stderr:
        raise RuntimeError(du_res.stderr.decode())
    out = du_res.stdout.decode().split('\n')[:-1]
    out_2 = [o.split('\t') for o in out]
    return [DirectoryDu(path, int(size)) for size, path in out_2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='Directory to du', nargs='?', default='.')
    args = parser.parse_args()

    idu = IDu(directory=args.dir)
    idu.loop()

if __name__ == '__main__':
    main()
