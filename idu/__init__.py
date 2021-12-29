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
c - show directories relative to this one
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
    ):
        if directory is None:
            directory = self.directory

        directory = Path(directory).resolve()
        try:
            cached_paths = [r.path for r in self.results]
            if not (cached and directory in cached_paths):
                self.results, stderr = run_du(directory)
                if stderr:
                    warnings.warn(stderr)
                self.resort()

            self.directory = directory

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
        self.update()
        print(self)
        while True:
            try:
                self.prompt()
            except (KeyboardInterrupt, EOFError):
                break

    def __str__(self):
        # Show only the current directory and its immediate children
        here = self.here()
        children_size = sum(r.size for r in here if r.path.parent == self.directory)
        my_size = sum(r.size for r in here if r.path == self.directory)
        output = str(self.base_directory.resolve()) + '\n'

        def fmt(n, r):
            percentage = r.size / my_size * 100
            if self.rel:
                return f'{n:<9d}{r.size:>10d}  ({percentage:>6.2f}%)\t{relpath(r.path, self.base_directory)}'
            else:
                return f'{n:<9d}{r.size:>10d}  ({percentage:>6.2f}%)\t{r.path}'

        output += '\n'.join([fmt(n, r) for n, r in enumerate(here)])
        output += '\n'
        output += f'of which {my_size - children_size:>10d}\tis from files in {self.directory}'


        return output

    __repr__ = __str__


def run_du(directory: Union[str, Path]) -> (List[DirectoryDu], str):
    directory = str(directory)
    du_res = subprocess.run(['du', '-k', directory], capture_output=True)
    out = du_res.stdout.decode().split('\n')[:-1]
    out_2 = [o.split('\t') for o in out]
    return (
        [DirectoryDu(path, int(size)) for size, path in out_2],
        du_res.stderr.decode()
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dir', help='Directory to du', nargs='?', default='.')
    args = parser.parse_args()

    idu = IDu(directory=Path(args.dir), base_directory=Path(args.dir))
    idu.loop()

if __name__ == '__main__':
    main()
