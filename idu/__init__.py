import argparse
import subprocess
import warnings
from pathlib import Path
from os import getcwd
from os.path import relpath, abspath, dirname
from typing import List, Optional, Union

HELP = """
integer - traverse into that directory
? - show this help message
p - print current state
P - refresh
u or .. - go up to parent directory
c - make current directory the base
g /foo - go to a new directory
r - switch between relative or absolute paths 
s - switch between sorting by name or by size
q - quit
"""

OUPs = Optional[Union[Path, str]]

class DirectoryDu:
    """Disk usage information for a single directory. All paths are
    resolved as absolute paths using Path.resolve().
    """

    def __init__(self, path: OUPs, size: int):
        self.path = Path(path).resolve()
        self.size = size

    def str(self, base_directory: OUPs = None):
        if base_directory:
            pathstr = relpath(self.path, Path(base_directory).resolve())
        else:
            pathstr = self.path

        return f'{self.size:>10d}\t{pathstr}'

    def __str__(self):
        return self.str()


class IDu:
    """Interactive disk usage analyser."""

    def __init__(self, directory: OUPs = None, base_directory: OUPs = None):
        self.directory = Path(directory).resolve() if directory else Path.getcwd()
        self.base_directory = Path(base_directory).resolve() if base_directory else Path.cwd()
        self.results = []
        self.sort_by_size = False
        self.rel = True

    def update(
        self,
        directory: OUPs = None,
        cached: bool = True,
        allow_rte: bool = True,
    ):
        if directory is None:
            directory = self.directory

        directory = Path(directory).resolve()
        try:
            if not cached or (directory not in [r.path for r in self.results]):
                self.results = run_du(directory)
                self.resort()

            self.directory = directory

        except RuntimeError as exc:
            if not allow_rte:
                raise
            warnings.warn(exc.__str__())

        except KeyboardInterrupt:  # catch ctrl-C
            pass

    def here(self):
        return [r for r in self.results
                if r.path == self.directory or r.path.parent == self.directory]

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
            options = {n: r for n, r in enumerate(self.here())}
            self.update(options[int(ans)].path, cached=True)
            print(self)
        except (KeyError, ValueError):
            if ans == '?':
                print(HELP)
            elif ans == 'q':
                exit(0)
            elif ans == 'p':
                print(self)
            elif ans == 'P':
                self.update(cached=False)
                print(self)
            elif ans in {'..', 'u'}:
                self.update(self.directory.parent, cached=True)
                print(self)
            elif ans == 'c':
                self.base_directory = self.directory
                print(self)
            elif ans[:2] == 'g ':
                self.update(self.base_directory / Path(ans[2:]))
                print(self)
            elif ans == 'r':
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
                return f'{n}\t{r.str(self.base_directory)}'
            else:
                return f'{n}\t{r.str()}'

        # Show only immediate children
        output = str(self.base_directory.resolve()) + '\n' + '\n'.join(
            [fmt(n, r) for n, r in enumerate(self.here())]
        )

        return output

    __repr__ = __str__


def run_du(directory: Union[str, Path]) -> List[DirectoryDu]:
    directory = str(directory)
    du_res = subprocess.run(['du', directory], capture_output=True)
    if du_res.stderr:
        raise RuntimeError(du_res.stderr.decode())
    out = du_res.stdout.decode().split('\n')[:-1]
    out_2 = [o.split('\t') for o in out]
    return [DirectoryDu(path, int(size)) for size, path in out_2]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='Directory to du', nargs='?', default='.')
    args = parser.parse_args()

    idu = IDu(directory=Path(args.dir), base_directory=Path(args.dir))
    idu.loop()

if __name__ == '__main__':
    main()
