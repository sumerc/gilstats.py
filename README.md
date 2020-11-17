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

```
> sudo /usr/bin/python gilstats.py -p 19402
Attaching /lib/x86_64-linux-gnu/libpthread.so.0:^pthread_cond_timedwait$. Hit Ctrl+C to stop.
^C
*** Per-thread Results
[
    {
        "tid": 19437, 
        "ttot_secs": 7, 
        "ncall": 2191
    }, 
    {
        "tid": 19438, 
        "ttot_secs": 7, 
        "ncall": 2191
    }, 
    {
        "tid": 19436, 
        "ttot_secs": 7, 
        "ncall": 2190
    }, 
    {
        "tid": 19435, 
        "ttot_secs": 0, 
        "ncall": 14
    }
]

*** Total elapsed: 11.4190039635 secs
```

You can see the `time spent in secs` for every thread probed. 

`tid` is the thread id. See [here](https://github.com/iovisor/bcc/blob/master/docs/reference_guide.md#4-bpf_get_current_pid_tgid) for more details.
`ttot_secs` is the number of seconds this thread waited to acquire the GIL.
`ncall` is the number of times this thread tried to acquire the GIL.

## How it works?

`gilstats.py` will first get your Python interpreter's major version. That is because the GIL implementation differs a lot between Python 2 and 3. You can find the reason on why here: https://www.youtube.com/watch?v=Obt-vMVdM8s. After retrieving the Python major version, we use eBPF to hook on following library functions:

```
pthread:sem_wait                # Python2
pthread:pthread_cond_timedwait  # Python3
```

These functions are the functions that actually _wait_ on GIL. On Python2, a GIL is a simple semaphore on Linux whereas on Python3 (3.2 and up) it is a condition variable. If we are able to track how much time a thread spent on these functions, we will be able to track how much time a thread waited to acquire the GIL. However, there is one more issue with this implementation. There might be some other code that might call these functions other than GIL. So, how to solve this? Well. Here is my idea:
   
   1) Measure every `sem_wait`/`pthread_cond_timedwait` and record `call_count` and `total time spent` along with the first argument passed to these functions(via using `PT_REGS_PARM1` call eBPF provides). For `sem_wait` call, the first parameter will be a pointer to a `sem_t *` structure whereas for `pthread_cond_timedwait` it will be a `pthread_cond_t *` pointer.
   2) When probing finished, the GIL pointer will be the one with the maximum `call_count`. The reason this is true is because we assume for every other blocking call event GIL will be woken up. So, that means: there should be no more `sem_wait` call for a semaphore other than GIL itself. 

## Performance

Since we are using `eBPF`, the performance overhead during monitoring is minimal.

## Future

While I am no expert on the subject, I think with a little bit of help, `gilstats.py` can be used to monitor the Ruby MRI GIL, too.
   



