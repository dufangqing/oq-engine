# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2010-2022 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
"""\
The Starmap API
====================================

There are several good libraries to manage parallel programming in Python, both
in the standard library and in third party packages. Since we are not
interested in reinventing the wheel, OpenQuake does not provide any new
parallel library; however, it does offer some glue code so that you
can use over your library of choice. Currently threading, multiprocessing,
and zmq are supported. Moreover,
:mod:`openquake.baselib.parallel` offers some additional facilities
that make it easier to parallelize scientific computations,
i.e. embarrassingly parallel problems.

Typically one wants to apply a callable to a list of arguments in
parallel, and then combine together the results. This is known as a
`MapReduce` problem. As a simple example, we will consider the problem
of counting the letters in a text, by using the following `count`
function:

.. code-block:: python

  def count(word):
      return collections.Counter(word)

The `collections.Counter` class works sequentially, and can
solve the problem in parallel by using
:class:`openquake.baselib.parallel.Starmap`:

>>> arglist = [('hello',), ('world',)]  # list of arguments
>>> smap = Starmap(count, arglist)  # Starmap instance, nothing started yet
>>> sorted(smap.reduce().items())  # build the counts per letter
[('d', 1), ('e', 1), ('h', 1), ('l', 3), ('o', 2), ('r', 1), ('w', 1)]

A `Starmap` object is an iterable: when iterating over it produces
task results. It also has a `reduce` method similar to `functools.reduce`
with sensible defaults:

1. the default aggregation function is `add`, so there is no need to specify it
2. the default accumulator is an empty accumulation dictionary (see
   :class:`openquake.baselib.AccumDict`) working as a `Counter`, so there
   is no need to specify it.

You can of course override the defaults, so if you really want to
return a `Counter` you can do

>>> res = Starmap(count, arglist).reduce(acc=collections.Counter())

In the engine we use nearly always callables that return dictionaries
and we aggregate nearly always with the addition operator, so such
defaults are very convenient. You are encouraged to do the same, since we
found that approach to be very flexible. Typically in a scientific
application you will return a dictionary of numpy arrays.

The parallelization algorithm used by `Starmap` will depend on the
environment variable `OQ_DISTRIBUTE`. Here are the possibilities
available at the moment:

`OQ_DISTRIBUTE` not set or set to "processpool":
  use multiprocessing
`OQ_DISTRIBUTE` set to "no":
  disable the parallelization, useful for debugging
`OQ_DISTRIBUTE` set tp "zmq"
   use the zmq concurrency mechanism (experimental)

There is also an `OQ_DISTRIBUTE` = "threadpool"; however the
performance of using threads instead of processes is normally bad for the
kind of applications we are interested in (CPU-dominated, which large
tasks such that the time to spawn a new process is negligible with
respect to the time to perform the task), so it is not recommended.

If you are using a pool, is always a good idea to cleanup resources at the end
with

>>> Starmap.shutdown()

`Starmap.shutdown` is always defined. It does nothing if there is
no pool, but it is still better to call it: in the future, you may change
idea and use another parallelization strategy requiring cleanup. In this
way your code is future-proof.

Monitoring
=============================

A major feature of the Starmap API is the ability to monitor the time spent
in each task and the memory allocated. Such information is written into an
HDF5 file that can be provided by the user or autogenerated. To autogenerate
the file you can use :func:`openquake.commonlib.datastore.hdf5new` which
will create a file named ``calc_XXX.hdf5`` in your $OQ_DATA directory
(if the environment variable is not set, the engine will use $HOME/oqdata).
Here is an example of usage:

>>> from openquake.commonlib.datastore import hdf5new
>>> h5 = hdf5new()
>>> smap = Starmap(count, [['hello'], ['world']], h5=h5)
>>> print(sorted(smap.reduce().items()))
[('d', 1), ('e', 1), ('h', 1), ('l', 3), ('o', 2), ('r', 1), ('w', 1)]

After the calculation, or even while the calculation is running, you can
open the calculation file for reading and extract the performance information
for it. The engine provides a command to do that, `oq show performance`,
but you can also get it manually, with a call to
`openquake.baselib.performance.performance_view(h5)` which will return
the performance information as a numpy array:

>>> from openquake.baselib.performance import performance_view
>>> performance_view(h5).dtype.names
('operation', 'time_sec', 'memory_mb', 'counts')
>>> h5.close()

The four columns are as follows:

operation:
  the name of the function running in parallel (in this case 'count')
time_sec:
  the cumulative time in second spent running the function
memory_mb:
  the maximum allocated memory per core
counts:
  the number of times the function was called (in this case 2)

The Starmap.apply API
====================================

The `Starmap` class has a very convenient classmethod `Starmap.apply`
which is used in several places in the engine. `Starmap.apply` is useful
when you have a sequence of objects that you want to split in homogenous chunks
and then apply a callable to each chunk (in parallel). For instance, in the
letter counting example discussed before, `Starmap.apply` could
be used as follows:

>>> text = 'helloworld'  # sequence of characters
>>> res3 = Starmap.apply(count, (text,)).reduce()
>>> assert res3 == res

The API of `Starmap.apply` is designed to extend the one of `apply`,
a builtin of Python 2; the second argument is the tuple of arguments
passed to the first argument. The difference with `apply` is that
`Starmap.apply` returns a :class:`Starmap` object so that nothing is
actually done until you iterate on it (`reduce` is doing that).

How many chunks will be produced? That depends on the parameter
`concurrent_tasks`; it it is not passed, it has a default of 5 times
the number of cores in your machine - as returned by `os.cpu_count()` -
and `Starmap.apply` will try to produce a number of chunks close to
that number. The nice thing is that it is also possible to pass a
`weight` function. Suppose for instance that instead of a list of
letters you have a list of seismic sources: some sources requires a
long computation time (such as `ComplexFaultSources`), some requires a
short computation time (such as `PointSources`). By giving an heuristic
weight to the different sources it is possible to produce chunks with
nearly homogeneous weight; in particular `PointSource` tasks will
contain a lot more sources than tasks with `ComplexFaultSources`.

It is *essential* in large computations to have a homogeneous task
distribution, otherwise you will end up having a big task dominating
the computation time (i.e. you may have 1000 cores of which 999 are free,
having finished all the short tasks, but you have to wait for days for
the single core processing the slow task). The OpenQuake engine does
a great deal of work trying to split slow sources in more manageable
fast sources.

"""
import os
import re
import ast
import sys
import time
import socket
import signal
import pickle
import inspect
import logging
import operator
import traceback
import itertools
import collections
from unittest import mock
import multiprocessing.dummy
import multiprocessing.shared_memory as shmem
from multiprocessing.connection import wait
import psutil
import numpy
try:
    from setproctitle import setproctitle
except ImportError:
    def setproctitle(title):
        "Do nothing"

from openquake.baselib import config, hdf5, workerpool
from openquake.baselib.python3compat import decode
from openquake.baselib.zeromq import zmq, Socket
from openquake.baselib.performance import (
    Monitor, memory_rss, init_performance)
from openquake.baselib.general import (
    split_in_blocks, block_splitter, AccumDict, humansize, CallableDict,
    gettemp, engine_version, mp as mp_context)

sys.setrecursionlimit(2000)  # raised to make pickle happier
# see https://github.com/gem/oq-engine/issues/5230
submit = CallableDict()
GB = 1024 ** 3
hosts = [hc.split()[0] for hc in config.zworkers.host_cores.split(',')]
ihost = itertools.cycle(hosts)


def debug(msg, mon):
    """
    Trivial task useful for debugging
    """
    print(msg)


@submit.add('no')
def no_submit(self, func, args, monitor):
    return safely_call(func, args, self.task_no, monitor)


@submit.add('processpool')
def processpool_submit(self, func, args, monitor):
    return self.pool.apply_async(
        safely_call, (func, args, self.task_no, monitor))


@submit.add('threadpool')
def threadpool_submit(self, func, args, monitor):
    return self.pool.apply_async(
        safely_call, (func, args, self.task_no, monitor))


@submit.add('zmq')
def zmq_submit(self, func, args, monitor):
    host = getattr(monitor, 'host', None)
    if host is None:
        host = next(ihost)
    else:
        logging.debug('Sending task %d to %s', self.task_no, host)
    if not hasattr(self, 'sender'):  # the first time
        port = int(config.zworkers.ctrl_port)
        self.sender = {
            host: Socket(
                'tcp://%s:%d' % (host, port), zmq.REQ, 'connect'
            ).__enter__() for host in hosts}
    return self.sender[host].send((func, args, self.task_no, monitor))


@submit.add('ipp')
def ipp_submit(self, func, args, monitor):
    return self.executor.submit(
        safely_call, func, args, self.task_no, monitor)


def oq_distribute(task=None):
    """
    :returns: the value of OQ_DISTRIBUTE or config.distribution.oq_distribute
    """
    dist = os.environ.get('OQ_DISTRIBUTE', config.distribution.oq_distribute)
    if dist not in ('no', 'processpool', 'threadpool', 'zmq', 'ipp'):
        raise ValueError('Invalid oq_distribute=%s' % dist)
    return dist


class Pickled(object):
    """
    An utility to manually pickling/unpickling objects. Pickled instances
    have a nice string representation and length giving the size
    of the pickled bytestring.

    :param obj: the object to pickle
    """
    def __init__(self, obj):
        self.clsname = obj.__class__.__name__
        self.calc_id = str(getattr(obj, 'calc_id', ''))  # for monitors
        try:
            self.pik = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
        except TypeError as exc:  # can't pickle, show the obj in the message
            raise TypeError('%s: %s' % (exc, obj))

    def __repr__(self):
        """String representation of the pickled object"""
        return '<Pickled %s #%s %s>' % (
            self.clsname, self.calc_id, humansize(len(self)))

    def __len__(self):
        """Length of the pickled bytestring"""
        return len(self.pik)

    def unpickle(self):
        """Unpickle the underlying object"""
        return pickle.loads(self.pik)


def get_pickled_sizes(obj):
    """
    Return the pickled sizes of an object and its direct attributes,
    ordered by decreasing size. Here is an example:

    >> total_size, partial_sizes = get_pickled_sizes(Monitor(''))
    >> total_size
    345
    >> partial_sizes
    [('_procs', 214), ('exc', 4), ('mem', 4), ('start_time', 4),
    ('_start_time', 4), ('duration', 4)]

    Notice that the sizes depend on the operating system and the machine.
    """
    sizes = []
    attrs = getattr(obj, '__dict__',  {})
    for name, value in attrs.items():
        sizes.append((name, len(Pickled(value))))
    return len(Pickled(obj)), sorted(
        sizes, key=lambda pair: pair[1], reverse=True)


def pickle_sequence(objects):
    """
    Convert an iterable of objects into a list of pickled objects.
    If the iterable contains copies, the pickling will be done only once.
    If the iterable contains objects already pickled, they will not be
    pickled again.

    :param objects: a sequence of objects to pickle
    """
    cache = {}
    out = []
    for obj in objects:
        obj_id = id(obj)
        if obj_id not in cache:
            if isinstance(obj, Pickled):  # already pickled
                cache[obj_id] = obj
            else:  # pickle the object
                cache[obj_id] = Pickled(obj)
        out.append(cache[obj_id])
    return out


class FakePickle:
    def __init__(self, sentbytes):
        self.sentbytes = sentbytes

    def unpickle(self):
        pass

    def __len__(self):
        return self.sentbytes


class Result(object):
    """
    :param val: value to return or exception instance
    :param mon: Monitor instance
    :param tb_str: traceback string (empty if there was no exception)
    :param msg: message string (default empty)
    """
    func = None

    def __init__(self, val, mon, tb_str='', msg=''):
        if isinstance(val, dict):
            self.pik = Pickled(val)
            self.nbytes = {k: len(Pickled(v)) for k, v in val.items()}
        elif isinstance(val, tuple) and callable(val[0]):
            self.func = val[0]
            self.pik = pickle_sequence(val[1:])
            self.nbytes = {'args': sum(len(p) for p in self.pik)}
        elif msg == 'TASK_ENDED':
            self.pik = Pickled(None)
            self.nbytes = {}
        else:
            self.pik = Pickled(val)
            self.nbytes = {'tot': len(self.pik)}
        self.mon = mon
        self.tb_str = tb_str
        self.msg = msg
        # host_ip = socket.gethostbyname(socket.gethostname())
        self.workerid = (socket.gethostname(), os.getpid())

    def get(self):
        """
        Returns the underlying value or raise the underlying exception
        """
        val = self.pik.unpickle()
        if self.tb_str:
            etype = val.__class__
            msg = '\n%s%s: %s' % (self.tb_str, etype.__name__, val)
            if issubclass(etype, KeyError):
                raise RuntimeError(msg)  # nicer message
            else:
                raise etype(msg)
        return val

    def __repr__(self):
        nbytes = ['%s: %s' % (k, humansize(v)) for k, v in self.nbytes.items()]
        return '<%s %s>' % (self.__class__.__name__, ' '.join(nbytes))

    @classmethod
    def new(cls, func, args, mon, sentbytes=0):
        """
        :returns: a new Result instance
        """
        try:
            if mon.version and mon.version != engine_version():
                raise RuntimeError(
                    'The master is at version %s while the worker %s is at '
                    'version %s' % (mon.version, socket.gethostname(),
                                    engine_version()))
            if mon.config.dbserver.host != config.dbserver.host:
                raise RuntimeError(
                    'The master has dbserver.host=%s while the worker has %s'
                    % (mon.config.dbserver.host, config.dbserver.host))
            with mon:
                val = func(*args)
        except StopIteration:
            mon.counts -= 1  # StopIteration does not count
            res = Result(None, mon, msg='TASK_ENDED')
            res.pik = FakePickle(sentbytes)
        except Exception:
            _etype, exc, tb = sys.exc_info()
            res = Result(exc, mon, ''.join(traceback.format_tb(tb)))
        else:
            res = Result(val, mon)
        return res


def check_mem_usage(soft_percent=None, hard_percent=None):
    """
    Display a warning if we are running out of memory
    """
    soft_percent = soft_percent or config.memory.soft_mem_limit
    hard_percent = hard_percent or config.memory.hard_mem_limit
    used_mem_percent = psutil.virtual_memory().percent
    if used_mem_percent > hard_percent:
        raise MemoryError('Using more memory than allowed by configuration '
                          '(Used: %d%% / Allowed: %d%%)! Shutting down.' %
                          (used_mem_percent, hard_percent))
    elif used_mem_percent > soft_percent:
        msg = 'Using over %d%% of the memory in %s!'
        return msg % (used_mem_percent, socket.gethostname())


dummy_mon = Monitor()
dummy_mon.config = config
dummy_mon.backurl = None


def safely_call(func, args, task_no=0, mon=dummy_mon):
    """
    Call the given function with the given arguments safely, i.e.
    by trapping the exceptions. Return a pair (result, exc_type)
    where exc_type is None if no exceptions occur, otherwise it
    is the exception class and the result is a string containing
    error message and traceback.

    :param func: the function to call
    :param args: the arguments
    :param task_no: the task number
    :param mon: a monitor
    """
    isgenfunc = inspect.isgeneratorfunction(func)
    if hasattr(args[0], 'unpickle'):
        # args is a list of Pickled objects
        args = [a.unpickle() for a in args]
    if mon is dummy_mon:  # in the DbServer
        assert not isgenfunc, func
        return Result.new(func, args, mon)
    if mon.operation.endswith('_'):
        name = mon.operation[:-1]
    elif func is split_task:
        name = args[1].__name__
    else:
        name = func.__name__
    mon = mon.new(operation='total ' + name, measuremem=True)
    mon.weight = getattr(args[0], 'weight', 1.)  # used in task_info
    mon.task_no = task_no
    if mon.inject:
        args += (mon,)
    sentbytes = 0
    with Socket(mon.backurl, zmq.PUSH, 'connect') as zsocket:
        msg = check_mem_usage()  # warn if too much memory is used
        if msg:
            zsocket.send(Result(None, mon, msg=msg))
        if inspect.isgeneratorfunction(func):
            it = func(*args)
        else:
            def gen(*args):
                yield func(*args)
            it = gen(*args)
        while True:
            # StopIteration -> TASK_ENDED
            res = Result.new(next, (it,), mon, sentbytes)
            try:
                zsocket.send(res)
            except Exception:  # like OverflowError
                _etype, exc, tb = sys.exc_info()
                err = Result(exc, mon, ''.join(traceback.format_tb(tb)))
                zsocket.send(err)
            sentbytes += len(res.pik)
            if res.msg == 'TASK_ENDED':
                break


if oq_distribute() == 'ipp':
    from ipyparallel import Cluster


class IterResult(object):
    """
    :param iresults:
        an iterator over Result objects
    :param taskname:
        the name of the task
    :param done_total:
        a function returning the number of done tasks and the total
    :param sent:
        a nested dictionary name -> {argname: number of bytes sent}
    :param progress:
        a logging function for the progress report
    :param hdf5path:
        a path where to store persistently the performance info
     """
    def __init__(self, iresults, taskname, argnames, sent, h5):
        self.iresults = iresults
        self.name = taskname
        self.argnames = ' '.join(argnames)
        self.sent = sent
        self.h5 = h5

    def _iter(self):
        first_time = True
        for result in self.iresults:
            msg = check_mem_usage()
            # log a warning if too much memory is used
            if msg and first_time:
                logging.warning(msg)
                first_time = False  # warn only once
            if isinstance(result, BaseException):
                # this happens with WorkerLostError with celery
                raise result
            elif isinstance(result, Result):
                val = result.get()
                self.nbytes += result.nbytes
            else:  # this should never happen
                raise ValueError(result)
            if sys.platform != 'darwin':
                # it normally works on macOS, but not in notebooks calling
                # notebooks, which is the case relevant for Marco Pagani
                mem_gb = (memory_rss(os.getpid()) + sum(
                    memory_rss(pid) for pid in Starmap.pids)) / GB
            else:
                # measure only the memory used by the main process
                mem_gb = memory_rss(os.getpid()) / GB
            if result.msg == 'TASK_ENDED':
                task_sent = ast.literal_eval(decode(self.h5['task_sent'][()]))
                task_sent.update(self.sent)
                del self.h5['task_sent']
                self.h5['task_sent'] = str(task_sent)
                name = result.mon.operation[6:]  # strip 'total '
                n = self.name + ':' + name if name == 'split_task' else name
                result.mon.save_task_info(self.h5, result, n, mem_gb)
                result.mon.flush(self.h5)
            elif not result.func:  # real output
                yield val

    def __iter__(self):
        if self.iresults == ():
            return ()
        t0 = time.time()
        self.nbytes = AccumDict()
        try:
            yield from self._iter()
        finally:
            items = sorted(self.nbytes.items(), key=operator.itemgetter(1))
            nb = {k: humansize(v) for k, v in reversed(items)}
            msg = nb if len(nb) < 10 else {
                'tot': humansize(sum(self.nbytes.values()))}
            logging.info('Received %s in %d seconds from %s',
                         msg, time.time() - t0, self.name)

    def reduce(self, agg=operator.add, acc=None):
        if acc is None:
            acc = AccumDict()
        for result in self:
            acc = agg(acc, result)
        return acc

    @classmethod
    def sum(cls, iresults):
        """
        Sum the data transfer information of a set of results
        """
        res = object.__new__(cls)
        res.sent = 0
        for iresult in iresults:
            res.sent += iresult.sent
            name = iresult.name.split('#', 1)[0]
            if hasattr(res, 'name'):
                assert res.name.split('#', 1)[0] == name, (res.name, name)
            else:
                res.name = iresult.name.split('#')[0]
        return res


def init_workers():
    """Waiting function, used to wake up the process pool"""
    setproctitle('oq-worker')


def getargnames(task_func):
    # a task can be a function, a method, a class or a callable instance
    if inspect.isfunction(task_func):
        return inspect.getfullargspec(task_func).args
    elif inspect.ismethod(task_func):
        return inspect.getfullargspec(task_func).args[1:]
    elif inspect.isclass(task_func):
        return inspect.getfullargspec(task_func.__init__).args[1:]
    else:  # instance with a __call__ method
        return inspect.getfullargspec(task_func.__call__).args[1:]


class SharedArray(object):
    """
    Wrapper over a SharedMemory object to be used as a context manager.
    """
    def __init__(self, shape, dtype, value):
        nbytes = numpy.zeros(1, dtype).nbytes * numpy.prod(shape)
        sm = shmem.SharedMemory(create=True, size=nbytes)
        self.name = sm.name
        self.shape = shape
        self.dtype = dtype
        # fill the SharedMemory buffer with the value
        arr = numpy.ndarray(shape, dtype, buffer=sm.buf)
        arr[:] = value

    def __enter__(self):
        self.sm = shmem.SharedMemory(self.name)
        return numpy.ndarray(self.shape, self.dtype, buffer=self.sm.buf)

    def __exit__(self, etype, exc, tb):
        self.sm.close()

    def unlink(self):
        shmem.SharedMemory(self.name).unlink()


class Starmap(object):
    pids = ()
    running_tasks = []  # currently running tasks
    shared = []  # SharedArrays
    maxtasksperchild = None  # with 1 it hangs on the EUR calculation!
    num_cores = int(config.distribution.get('num_cores', '0'))
    if not num_cores:
        # use only the "visible" cores, not the total system cores
        # if the underlying OS supports it (macOS does not)
        try:
            num_cores = len(psutil.Process().cpu_affinity())
        except AttributeError:
            num_cores = psutil.cpu_count()
    CT = num_cores * 2

    @classmethod
    def init(cls, distribute=None):
        cls.distribute = distribute or oq_distribute()
        if cls.distribute == 'processpool' and not hasattr(cls, 'pool'):
            # unregister custom handlers before starting the processpool
            term_handler = signal.signal(signal.SIGTERM, signal.SIG_DFL)
            int_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            # we use spawn here to avoid deadlocks with logging, see
            # https://github.com/gem/oq-engine/pull/3923 and
            # https://codewithoutrules.com/2018/09/04/python-multiprocessing/
            cls.pool = mp_context.Pool(
                cls.num_cores, init_workers,
                maxtasksperchild=cls.maxtasksperchild)
            cls.pids = [proc.pid for proc in cls.pool._pool]
            cls.shared = []
            # after spawning the processes restore the original handlers
            # i.e. the ones defined in openquake.engine.engine
            signal.signal(signal.SIGTERM, term_handler)
            signal.signal(signal.SIGINT, int_handler)
        elif cls.distribute == 'threadpool' and not hasattr(cls, 'pool'):
            cls.pool = multiprocessing.dummy.Pool(cls.num_cores)
        elif cls.distribute == 'ipp' and not hasattr(cls, 'executor'):
            rc = Cluster(n=cls.num_cores).start_and_connect_sync()
            cls.executor = rc.executor()

    @classmethod
    def shutdown(cls):
        for shared in cls.shared:
            shmem.SharedMemory(shared.name).unlink()
        # shutting down the pool during the runtime causes mysterious
        # race conditions with errors inside atexit._run_exitfuncs
        if hasattr(cls, 'pool'):
            cls.pool.close()
            cls.pool.terminate()
            cls.pool.join()
            del cls.pool
            cls.pids = []
        elif hasattr(cls, 'executor'):
            cls.executor.shutdown()

    @classmethod
    def apply(cls, task, allargs, concurrent_tasks=None,
              maxweight=None, weight=lambda item: 1,
              key=lambda item: 'Unspecified',
              distribute=None, progress=logging.info, h5=None):
        r"""
        Apply a task to a tuple of the form (sequence, \*other_args)
        by first splitting the sequence in chunks, according to the weight
        of the elements and possibly to a key (see :func:
        `openquake.baselib.general.split_in_blocks`).

        :param task: a task to run in parallel
        :param args: the arguments to be passed to the task function
        :param concurrent_tasks: hint about how many tasks to generate
        :param maxweight: if not None, used to split the tasks
        :param weight: function to extract the weight of an item in arg0
        :param key: function to extract the kind of an item in arg0
        :param distribute: if not given, inferred from OQ_DISTRIBUTE
        :param progress: logging function to use (default logging.info)
        :param h5: an open hdf5.File where to store the performance info
        :returns: an :class:`IterResult` object
        """
        arg0, *args = allargs
        if maxweight:  # block_splitter is lazy
            taskargs = ([blk] + args for blk in block_splitter(
                arg0, maxweight, weight, key))
        else:  # split_in_blocks is eager
            if concurrent_tasks is None:
                concurrent_tasks = cls.CT
            taskargs = [[blk] + args for blk in split_in_blocks(
                arg0, concurrent_tasks or 1, weight, key)]
        return cls(task, taskargs, distribute, progress, h5)

    @classmethod
    def apply_split(cls, task, allargs, concurrent_tasks=None,
                    maxweight=None, weight=lambda item: 1,
                    key=lambda item: 'Unspecified',
                    distribute=None, progress=logging.info, h5=None,
                    duration=300, outs_per_task=5):
        """
        Same as Starmap.apply, but possibly produces subtasks
        """
        args = (allargs[0], task, allargs[1:], duration, outs_per_task)
        return cls.apply(split_task, args, concurrent_tasks or 2*cls.num_cores,
                         maxweight, weight, key, distribute, progress, h5)

    def __init__(self, task_func, task_args=(), distribute=None,
                 progress=logging.info, h5=None):
        self.__class__.init(distribute=distribute)
        self.task_func = task_func
        if h5:
            match = re.search(r'(\d+)', os.path.basename(h5.filename))
            self.calc_id = int(match.group(1))
        else:
            self.calc_id = None
            h5 = hdf5.File(gettemp(suffix='.hdf5'), 'w')
            init_performance(h5)
        if task_func is split_task:
            self.name = task_args[0][1].__name__
        else:
            self.name = task_func.__name__
        self.monitor = Monitor(self.name)
        self.monitor.filename = h5.filename
        self.monitor.calc_id = self.calc_id
        self.task_args = task_args
        self.progress = progress
        self.h5 = h5
        self.task_queue = []
        try:
            self.num_tasks = len(self.task_args)
        except TypeError:  # generators have no len
            self.num_tasks = None
        self.argnames = getargnames(task_func)
        self.sent = AccumDict(accum=AccumDict())  # fname -> argname -> nbytes
        self.monitor.inject = (self.argnames[-1].startswith('mon') or
                               self.argnames[-1].endswith('mon'))
        self.receiver = 'tcp://0.0.0.0:%s' % config.dbserver.receiver_ports
        if self.distribute in ('no', 'processpool'):
            self.return_ip = '127.0.0.1'  # zmq returns data to localhost
        else:  # zmq returns data to the receiver_host
            self.return_ip = socket.gethostbyname(
                config.dbserver.receiver_host or socket.gethostname())
        self.monitor.backurl = None  # overridden later
        self.tasks = []  # populated by .submit
        self.task_no = 0
        self.t0 = time.time()
        if self.distribute == 'zmq':  # add a check
            master = workerpool.WorkerMaster(config.zworkers)
            errors = ['The workerpool on %s is down' % host
                      for host, run, tot in master.status() if tot == 0]
            if errors:
                raise RuntimeError('\n'.join(errors))

    def log_percent(self):
        """
        Log the progress of the computation in percentage
        """
        submitted = len(self.tasks)
        queued = len(self.task_queue)
        total = submitted + queued
        done = submitted - self.todo
        percent = int(float(done) / total * 100)
        if not hasattr(self, 'prev_percent'):  # first time
            self.prev_percent = 0
        elif percent > self.prev_percent:
            self.progress('%s %3d%% [%d submitted, %d queued]',
                          self.name, percent, submitted, queued)
            self.prev_percent = percent
        return done

    def submit(self, args, func=None, host=None):
        """
        Submit the given arguments to the underlying task
        """
        func = func or self.task_func
        if not hasattr(self, 'socket'):  # first time
            self.t0 = time.time()
            self.__class__.running_tasks = self.tasks
            self.socket = Socket(self.receiver, zmq.PULL, 'bind').__enter__()
            self.monitor.backurl = 'tcp://%s:%s' % (
                self.return_ip, self.socket.port)
            self.monitor.config = config
        OQ_TASK_NO = os.environ.get('OQ_TASK_NO')
        if OQ_TASK_NO is not None and self.task_no != int(OQ_TASK_NO):
            self.task_no += 1
            return
        dist = 'no' if self.num_tasks == 1 or OQ_TASK_NO else self.distribute
        if dist != 'no':
            pickled = isinstance(args[0], Pickled)
            if not pickled:
                assert not isinstance(args[-1], Monitor)  # sanity check
                args = pickle_sequence(args)
            if func is None:
                fname = self.task_func.__name__
                argnames = self.argnames[:-1]
            else:
                fname = func.__name__
                argnames = getargnames(func)[:-1]
            self.sent[fname] += {a: len(p) for a, p in zip(argnames, args)}
        if host is not None:
            self.monitor.host = host
        res = submit[dist](self, func, args, self.monitor)
        self.task_no += 1
        self.tasks.append(res)

    def submit_split(self, args,  duration, outs_per_task):
        """
        Submit the given arguments to the underlying task
        """
        self.monitor.operation = self.task_func.__name__ + '_'
        self.submit(
            (args[0], self.task_func, args[1:], duration, outs_per_task),
            split_task)

    def submit_all(self):
        """
        :returns: an IterResult object
        """
        if self.num_tasks is None:  # loop on the iterator
            for args in self.task_args:
                self.submit(args)
        else:  # build a task queue in advance
            self.task_queue = [(self.task_func, args)
                               for args in self.task_args]
        return self.get_results()

    def get_results(self):
        """
        :returns: an :class:`IterResult` instance
        """
        return IterResult(self._loop(), self.name, self.argnames,
                          self.sent, self.h5)

    def reduce(self, agg=operator.add, acc=None):
        """
        Submit all tasks and reduce the results
        """
        return self.submit_all().reduce(agg, acc)

    def __iter__(self):
        return iter(self.submit_all())

    def _submit_many(self, howmany, host=None):
        for _ in range(howmany):
            if self.task_queue:
                # remove in LIFO order
                func, args = self.task_queue[0]
                del self.task_queue[0]
                self.submit(args, func, host)
                self.todo += 1

    def _loop(self):
        self.busytime = AccumDict(accum=[])  # pid -> time
        if self.task_queue:
            first_args = self.task_queue[:self.num_cores]
            self.task_queue[:] = self.task_queue[self.num_cores:]
            for func, args in first_args:
                self.submit(args, func=func)
        if not hasattr(self, 'socket'):  # no submit was ever made
            return ()

        nbytes = sum(self.sent[self.task_func.__name__].values())
        if nbytes > 1E6:
            logging.info('Sent %d %s tasks, %s in %d seconds', len(self.tasks),
                         self.name, humansize(nbytes), time.time() - self.t0)

        isocket = iter(self.socket)
        self.todo = len(self.tasks)
        while self.todo:
            self.log_percent()
            res = next(isocket)
            if self.calc_id != res.mon.calc_id:
                logging.warning('Discarding a result from job %s, since this '
                                'is job %s', res.mon.calc_id, self.calc_id)
            elif res.msg == 'TASK_ENDED':
                self.busytime += {res.workerid: res.mon.duration}
                self.todo -= 1
                self._submit_many(1, res.workerid[0])
                logging.debug('%d tasks running, %d in queue',
                              self.todo, len(self.task_queue))
                yield res
            elif res.func:  # add subtask
                self.task_queue.append((res.func, res.pik))
                self._submit_many(1)
            else:
                yield res
        self.log_percent()
        self.socket.__exit__(None, None, None)
        self.tasks.clear()
        if len(self.busytime) > 1:
            times = numpy.array(list(self.busytime.values()))
            logging.info(
                'Mean time per core=%ds, std=%.1fs, min=%ds, max=%ds',
                times.mean(), times.std(), times.min(), times.max())

    def create_shared(self, shape, dtype=float, value=0.):
        """
        Create an array backed by a SharedMemory buffer.

        :param shape: shape of the array
        :param dtype: dtype of the array (default float)
        :param value: initialization value (default 0.)
        :returns: a SharedArray instance
        """
        shared = SharedArray(shape, dtype, value)
        self.shared.append(shared)
        return shared


def sequential_apply(task, args, concurrent_tasks=Starmap.CT,
                     maxweight=None, weight=lambda item: 1,
                     key=lambda item: 'Unspecified',
                     progress=logging.info):
    """
    Apply sequentially task to args by splitting args[0] in blocks
    """
    with mock.patch.dict('os.environ', {'OQ_DISTRIBUTE': 'no'}):
        return Starmap.apply(task, args, concurrent_tasks, maxweight, weight,
                             key, progress=progress)


def count(word):
    """
    Used as example in the documentation
    """
    return collections.Counter(word)


class List(list):
    weight = 0


def split_task(elements, func, args, duration, outs_per_task, monitor):
    """
    :param func: a task function with a monitor as last argument
    :param args: arguments of the task function, with args[0] being a sequence
    :param duration: split the task if it exceeds the duration
    :param outs_per_task: number of splits to try (ex. 5)
    :yields: a partial result, 0 or more task objects
    """
    n = len(elements)
    if outs_per_task > n:  # too many splits
        outs_per_task = n
    elements = numpy.array(elements)  # from WeightedSequence to array
    idxs = numpy.arange(n)
    split_elems = [elements[idxs % outs_per_task == i]
                   for i in range(outs_per_task)]
    # see how long it takes to run the first slice
    t0 = time.time()
    for i, elems in enumerate(split_elems):
        monitor.out_no = monitor.task_no + i * 65536
        res = func(elems, *args, monitor=monitor)
        dt = time.time() - t0
        yield res
        if dt > duration:
            # spawn subtasks for the rest and exit, used in classical/case_14
            for els in split_elems[i + 1:]:
                ls = List(els)
                ls.weight = sum(getattr(el, 'weight', 1.) for el in els)
                yield (func, ls) + args
            break


def multispawn(func, allargs, num_cores=Starmap.num_cores):
    """
    Spawn processes with the given arguments
    """
    allargs = allargs[::-1]  # so that the first argument is submitted first
    procs = {}  # sentinel -> process
    while allargs:
        args = allargs.pop()
        proc = mp_context.Process(target=func, args=args)
        proc.start()
        procs[proc.sentinel] = proc
        while len(procs) >= num_cores:  # wait for something to finish
            for finished in wait(procs):
                del procs[finished]
    while procs:
        for finished in wait(procs):
            del procs[finished]
