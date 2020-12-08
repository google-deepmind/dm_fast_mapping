# `dm_fast_mapping`: DeepMind Fast Language Learning Tasks

The *DeepMind Fast Language Learning Tasks* is a set of machine-learning tasks
that requires agents to learn the meaning of instruction words either slowly
(i.e. across many episodes), quickly (i.e. within a single episode) or both.

The tasks in this repo are [Unity-based](http://unity3d.com/).

## Overview

These tasks are provided through pre-packaged
[Docker containers](http://www.docker.com).

This package consists of support code to run these Docker containers. You
interact with the task environment via a
[`dm_env`](http://www.github.com/deepmind/dm_env) Python interface.

Please see the [documentation](docs/index.md) for more detailed information on
the available tasks, actions and observations.

## Requirements

`dm_fast_mapping` requires [Docker](https://www.docker.com),
[Python](https://www.python.org/) 3.6.1 or later and a x86-64 CPU with SSE4.2
support. We do not attempt to maintain a working version for Python 2.

Note: We recommend using
[Python virtual environment](https://docs.python.org/3/tutorial/venv.html) to
mitigate conflicts with your system's Python environment.

Download and install Docker:

*   For Linux, install [Docker-CE](https://docs.docker.com/install/)
*   Install Docker Desktop for
    [OSX](https://docs.docker.com/docker-for-mac/install/) or
    [Windows](https://docs.docker.com/docker-for-windows/install/).

## Installation

You can install `dm_fast_mapping` by cloning a local copy of our GitHub
repository:

```bash
$ git clone https://github.com/deepmind/dm_fast_mapping.git
$ pip install ./dm_fast_mapping
```

You can install the dependencies for the `examples/` with:

```bash
$ pip install ./dm-fast-mapping[examples]
```

## Usage

Once `dm_fast_mapping` is installed, to instantiate a `dm_env` instance run the
following:

```python
import dm_fast_mapping

settings = dm_fast_mapping.EnvironmentSettings(seed=123,
    level_name='fast_slow/fast_map_three_objs')
env = dm_fast_mapping.load_from_docker(settings)
```

## Citing

If you use `dm_fast_mapping` in your work, please cite the accompanying paper:

```bibtex
@misc{hill2020grounded,
      title={Grounded Language Learning Fast and Slow},
      author={Felix Hill and
              Olivier Tieleman and
              Tamara von Glehn and
              Nathaniel Wong and
              Hamza Merzic and
              Stephen Clark},
      year={2020},
      eprint={2009.01719},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```

## Notice

This is not an officially supported Google product.
