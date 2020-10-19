#!/usr/bin/python

import sys
import time
import signal
import json
import os
import argparse
import subprocess
from bcc import BPF

IS_PY3 = sys.version_info > (3, 0)

examples = """examples:
    ./gilstats -p 1234              # trace process 1234
"""
parser = argparse.ArgumentParser(
    description="Time/Print GIL stats per-thread",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples,
)
parser.add_argument(
    "-p", "--pid", type=int, required=True, help="trace this PID only"
)
args = parser.parse_args()

code = """
#include <uapi/linux/ptrace.h>

struct key_t {
    u64 tid;
};

struct data_t {
    u64 t0;

    // hold the lock_ptr, uretprobe cannot access it, so we save it in uprobe
    // and as a single thread can only hold a single lock per any time we use
    // the last one in uretprobe.
    uintptr_t lock_ptr;
};

struct lock_key_t {
    u64 tid;
    uintptr_t ptr;
};

struct lock_data_t {
    u64 ttot;
    u64 ncall;
};

BPF_HASH(fn_stats, struct key_t, struct data_t);
BPF_HASH(lock_stats, struct lock_key_t, struct lock_data_t);

int lock_enter(struct pt_regs *ctx) {
    u64 curr_tid = bpf_get_current_pid_tgid() & 0x00000000FFFFFFFF;

    //bpf_trace_printk("curr_tid=%x\\n", curr_tid);
    
    u64 now = bpf_ktime_get_ns();

    struct key_t key = {curr_tid};
    struct data_t zero = {0, 0};
    struct data_t *data = fn_stats.lookup_or_init(&key, &zero);
    data->t0 = now;
    data->lock_ptr = (uintptr_t)PT_REGS_PARM1(ctx);

    return 0;
};

int lock_exit(struct pt_regs *ctx) {
    u64 curr_tid = bpf_get_current_pid_tgid() & 0x00000000FFFFFFFF;
    u64 now = bpf_ktime_get_ns();

    //bpf_trace_printk("gil ptr=%x %x\\n", (void *)PT_REGS_PARM1(ctx), PT_REGS_PARM2(ctx));

    struct key_t key = {curr_tid};
    struct data_t *data = fn_stats.lookup(&key);
    if (data) {
        u64 elapsed = now - data->t0;

        // initialize per-lock data
        struct lock_key_t akey = {curr_tid, data->lock_ptr};
        struct lock_data_t zero = {0, 0};
        struct lock_data_t *adata = lock_stats.lookup_or_init(&akey, &zero);
        adata->ttot += elapsed;
        adata->ncall += 1;
    }
    
    return 0;
};

"""


# signal handler
def signal_ignore(signal, frame):
    print()


def get_py_major_version(exec_path):
    if IS_PY3:
        py_version = subprocess.run(
            [exec_path, '--version'],
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE
        ).stdout
    else:
        py_version = subprocess.check_output(
            [exec_path, '--version'],
            stderr=subprocess.STDOUT,
        )

    assert py_version.startswith(b'Python')

    if IS_PY3:
        py_version = py_version.decode("utf-8")
    r = int(py_version.split()[1][0])
    assert r in [2, 3]
    return r


start_time = time.time()

try:
    exec_path = os.readlink("/proc/%d/exe" % (args.pid))
except:
    raise Exception("No Process with PID %d found." % (args.pid))

# get python version
try:
    py_maj_version = get_py_major_version(exec_path)
except Exception as e:
    raise Exception(
        'Could not retrieve the Python version from the binary %s [%s]' %
        (exec_path, e)
    )

if py_maj_version == 2:
    exec_path = BPF.find_library("pthread")
    sym_re = "^sem_wait$"
elif py_maj_version == 3:
    exec_path = BPF.find_library("pthread")
    sym_re = "^pthread_cond_timedwait$"

if exec_path is None or len(exec_path) == 0:
    raise Exception("unable to find library %s" % exec_path)

print('Attaching %s:%s. Hit Ctrl+C to stop.' % (exec_path, sym_re))

b = BPF(text=code)
b.attach_uprobe(
    name=exec_path,
    sym_re=sym_re,
    fn_name="lock_enter",
    pid=args.pid,
    #addr=sym,
)

b.attach_uretprobe(
    name=exec_path,
    #addr=sym,
    sym_re=sym_re,
    fn_name="lock_exit",
    pid=args.pid
)

lock_stats = b.get_table("lock_stats")
exiting = False
while (1):
    try:
        time.sleep(0.1)
    except KeyboardInterrupt:
        exiting = True
        signal.signal(signal.SIGINT, signal_ignore)

    import ctypes

    if exiting:
        # we look at possible GIL wait points in Python binaries with holding the
        # lock pointer. GIL is the one that is called the most. The logic is some other
        # locks can use the same system calls we intercepted(e.g: sem_wait and pthread_cond_wait)
        # but even in that case, GIL would at least have the same amount of call counts because
        # every blocking op. including acquiring a lock involves GIL, too.
        lock_elapsed = {}
        max_lock_ncall = 0
        gil_candidate = None
        for k, v in lock_stats.items():
            #print((k.tid, hex(k.ptr)), (v.ttot, v.ncall))
            lock_ptr = hex(k.ptr)
            if lock_ptr not in lock_elapsed:
                lock_elapsed[lock_ptr] = {"ttot_ns": v.ttot, "ncall": v.ncall}
            else:
                lock_elapsed[lock_ptr]["ttot_ns"] += v.ttot
                lock_elapsed[lock_ptr]["ncall"] += v.ncall

                if lock_elapsed[lock_ptr]["ncall"] > max_lock_ncall:
                    gil_candidate = lock_ptr
                    max_lock_ncall = lock_elapsed[lock_ptr]["ncall"]

        if not gil_candidate:
            raise Exception(
                'No gil candidate found. Maybe symbols are not intercepted properly? [%d]'
                % (len(lock_stats))
            )

        result = []
        for k, v in lock_stats.items():
            if hex(k.ptr) == gil_candidate:
                result.append(
                    {
                        "tid": k.tid,
                        "ttot_secs": v.ttot / 1000000000,
                        "ncall": v.ncall,
                    }
                )

        print("\n*** Per-thread Results")
        print(json.dumps(result, indent=4))
        print("\n*** Total elapsed: %s secs" % (time.time() - start_time))

        sys.exit(0)

    #b.trace_print()
