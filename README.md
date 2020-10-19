<p align="center">
   
</p>

<h1 align="center">gilstats.py</h1>
<p align="center">
    Find out if <a href="https://opensource.com/article/17/4/grok-gil">CPython GIL</a> is slowing you down with a single script
</p>

![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square) 

## Introduction
`gilstats.py` is a utility for dumping per-thread statistics for CPython GIL using [eBPF](http://www.brendangregg.com/blog/2019-01-01/learn-ebpf-tracing.html) (Linux only). It only requires you to provide a ProcessID(`pid`) of your application to collect the data.

## Installation
`gilstats.py` uses [eBPF](http://www.brendangregg.com/blog/2019-01-01/learn-ebpf-tracing.html) technology under the hood, thus requires Linux.

The only thing prerequisite is to install `bcc-tools` on your system. 

You can follow the instructions here to install bcc-tools on your Linux system:
https://github.com/iovisor/bcc/blob/master/INSTALL.md

An example installation for Ubuntu 16.04:

```bash
> echo "deb [trusted=yes] https://repo.iovisor.org/apt/xenial xenial-nightly main" | sudo tee /etc/apt/sources.list.d/iovisor.list
> sudo apt-get update
> sudo apt-get install bcc-tools
```

And then you can run the `gilstats.py` script providing a process to profile.

## Examples

xxx

## How it works?

`gilstats.py` will first get your Python interpreter's major version. That is because the GIL implementation differs a lot between Python 2 and 3. You can find the reason on why here: https://www.youtube.com/watch?v=Obt-vMVdM8s. After retrieving the Python major version, we use eBPF to hook on following library functions:

```
pthread:sem_wait                # Python2
pthread:pthread_cond_timedwait  # Python3
```

These functions are the functions that actually _wait_ on GIL. On Python2, a GIL is a simple semaphore on Linux whereas on Python3 (3.2 and up) it is a condition variable. If we are able to track how much time a thread spent on these functions, we will be able to track how much time a thread waited to acquire the GIL. However, there is one more issue with this implementation. There might be some other code that might call these functions other than GIL. So, how to solve this? Well. While the idea I have used served me well for all the tests I have thrown at it, I am still not %100 sure this will work on every situation:
   
   1) Measure every `sem_wait`/`pthread_cond_timedwait` and record `call_count` and `total time spent` along with the first argument passed to these functions(via using `PT_REGS_PARM1` call eBPF provides). For `sem_wait` call, the first parameter will be a pointer to a `sem_t *` structure whereas for `pthread_cond_timedwait` it will be a `pthread_cond_t *` pointer.
   2) When probing finished, the GIL pointer will be the one with the maximum `call_count`. The reason this is true is because we assume for every other blocking call event GIL will be woken up. So, that means: there should be no more `sem_wait` call for a semaphore other than GIL itself. 
   
Again: although the idea seem to work for me well, I am still not sure if it is %100. Please open an issue where this assumption might actually be incorrect.
   
 
   



