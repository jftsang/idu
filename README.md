# idu - Interactive disk usage tool

J. M. F. Tsang (j.m.f.tsang@cantab.net)

---

`idu` is an interactive version of `du` that allows you to walk around
the directory structure. It is intended to be a lightweight, TUI
alternative to tools such as `baobab` or `WinDirStat`.


## Usage

Run `idu` on the working directory:
```
(idu) jmft2 @ blasius ~/PycharmProjects/idu (main)
└─ $ ▶ idu
/Users/jmft2/PycharmProjects/idu
0               400  (100.00%)  .
1               264  ( 66.00%)  .git
2                 4  (  1.00%)  .github
3                36  (  9.00%)  .idea
4                 4  (  1.00%)  __pycache__
5                12  (  3.00%)  build
6                16  (  4.00%)  dist
7                20  (  5.00%)  idu
8                20  (  5.00%)  idu.egg-info
of which         24     is from files in /Users/jmft2/PycharmProjects/idu
>
```
Then use `?` to get a list of possible commands:
```
> ?

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
```


## License

This software is released under the MIT Licence.
