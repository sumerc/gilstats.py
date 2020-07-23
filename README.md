<p align="center">
   
</p>

<h1 align="center">gilstats.py</h1>
<p align="center">
    Find out if <a href="https://opensource.com/article/17/4/grok-gil">CPython GIL</a> is a friend or enemy
</p>

![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square) 

## Introduction
gilstats.py is a utility for dumping per-thread statistics for CPython GIL using eBPF (Linux only)

## Installation
`gilstats.py` uses eBPF technology under the hood, thus requires Linux.

The only thing prerequisite is to install `bcc-tools` on your system. 

You can follow the instructions here to install bcc-tools on your Linux system:
https://github.com/iovisor/bcc/blob/master/INSTALL.md

An example installtion for Ubuntu 18.04:

```bash
> echo "deb [trusted=yes] https://repo.iovisor.org/apt/xenial xenial-nightly main" | sudo tee /etc/apt/sources.list.d/iovisor.list
> sudo apt-get update
> sudo apt-get install bcc-tools
```

## Examples

xxx

## How it works?
xxx

## Usage
xxx
