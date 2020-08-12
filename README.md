<p align="center">
   
</p>

<h1 align="center">gilstats.py</h1>
<p align="center">
    Find out if <a href="https://opensource.com/article/17/4/grok-gil">CPython GIL</a> is slowing you down using eBPF
</p>

![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square) 

## Introduction
`gilstats.py` is a utility for dumping per-thread statistics for CPython GIL using [eBPF](http://www.brendangregg.com/blog/2019-01-01/learn-ebpf-tracing.html) (Linux only)

## Installation
`gilstats.py` uses [eBPF](http://www.brendangregg.com/blog/2019-01-01/learn-ebpf-tracing.html) technology under the hood, thus requires Linux.

The only thing prerequisite is to install `bcc-tools` on your system. 

You can follow the instructions here to install bcc-tools on your Linux system:
https://github.com/iovisor/bcc/blob/master/INSTALL.md

An example installation for Ubuntu 18.04:

```bash
> echo "deb [trusted=yes] https://repo.iovisor.org/apt/xenial xenial-nightly main" | sudo tee /etc/apt/sources.list.d/iovisor.list
> sudo apt-get update
> sudo apt-get install bcc-tools
```

And then you can run the `gilstats.py` script providing a process to profile.

## Examples

xxx

## How it works?

xxx

