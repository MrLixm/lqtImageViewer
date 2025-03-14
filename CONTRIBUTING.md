# Contributing

Contributing guidelines and workflow for developers.

## pre-requisites

- `git` is available on your system
- `uv` is available on your system

## getting started

```shell
cd /some/place/to/develop
git clone https://github.com/MrLixm/lqtImageViewer.git
cd lqtImageViewer
# create the python venv
uv sync --all-group
# create and checkout new branch, DON'T work on main !
git checkout -b <branchname>
```
## code guidelines

- make sure the code is formatted with black before committing
  ```
  # reformat the python package 
  black lqtImageViewer
  ```
    

## building documentation

build once:

```shell
uv run --group doc mkdocs build
```

build with live changes detection:

```shell
uv run --group doc mkdocs serve --watch lqtImageViewer/
```
