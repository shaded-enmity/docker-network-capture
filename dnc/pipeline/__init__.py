from os import read, pipe, close, dup
from threading import Thread
from queue import Queue, Empty
from sys import stderr
from subprocess import Popen, PIPE, TimeoutExpired
from dnc.utils import has_flag, is_tcpdump_header, not_none, net_ns, format_buffer
from dnc import CaptureFlags, MAX_PACKET_SIZE


class PipelineComponent(object):
    """ Base class for a `tcpdump` pipeline component functor """
    def __init__(self, capture, context=None):
        self.capture = capture
        self.pipeline = None
        self.rx = None
        self.child = None

    def _init_tcpdump(self, interface, address=None, flags=CaptureFlags.Ingress):
        """ Initialize `tcpdump` and set child process info and the `read` pipe of the process"""
        direction, proto = [], None
        if address:
            proto = "ether"
            if has_flag(flags, CaptureFlags.Ingress):
                direction += ["dst"]
            if has_flag(flags, CaptureFlags.Both):
                direction += ["or"]
            if has_flag(flags, CaptureFlags.Egress):
                direction += ["src"]

        args = not_none(["tcpdump", "-i", interface, "-w-", "-U", proto] + direction + [address])
        rx, tx = pipe()
        # pipes are not inheritable by children processes, so we need
        # to duplicate the tx pipe, then close it
        write2 = dup(tx)
        close(tx)

        process = Popen(args, stdin=PIPE, stdout=write2, stderr=PIPE)

        close(write2)
        self.rx = rx
        self.child = process

    def init_tcpdump(self):
        """ Subclasses override this with specific way how to call `_init_tcpdump` """
        raise NotImplementedError()

    def __call__(self):
        """ Starts reading from the `read` pipe as long as the pipeline is running """
        self.init_tcpdump()
        packets = 1
        while self.pipeline.running:
            try:
                code = self.child.wait(0)
                if code == 1:
                    print('[!] Tcpdump execution **failed**, are you a superuser?', file=stderr)
                return
            except TimeoutExpired:
                pass

            data = read(self.rx, MAX_PACKET_SIZE)
            if not data:
                continue

            if is_tcpdump_header(data):
                continue

            if self.pipeline.context.get("verbose", False):
                print("Packet: {}".format(packets))
                print(format_buffer(data))

            if self.pipeline.queue:
                self.pipeline.queue.put(data)

            packets += 1


class InterfaceProducer(PipelineComponent):
    """ Subclass to capture on a specific interface and address """
    def __init__(self, bridge, mac, capture):
        super().__init__(capture)
        self.bridge = bridge
        self.mac = mac

    def init_tcpdump(self):
        self._init_tcpdump(self.bridge, self.mac, self.capture)


class LoopbackProducer(PipelineComponent):
    """ Subclass to capture on the namespaced local loopback """
    def __init__(self, pid, capture):
        super().__init__(capture)
        self.pid = pid

    def init_tcpdump(self):
        net_ns(self.pid)
        self._init_tcpdump("lo", flags=self.capture)


class PipelineError(Exception):
    pass


class Pipeline(object):
    """ Provides simple interface for running multiple producers and consumers and synchronizing them via queue """
    def __init__(self, **kwargs):
        self.producers = []
        self.queue = Queue()
        self.consumers = []
        self.running = False
        self.context = kwargs

    def add_producer(self, target):
        """ Adds a new producers, an error is thrown if the pipeline is already running """
        if not self.running:
            target.pipeline = self
            self.producers.append(target)
        else:
            raise PipelineError("Pipeline already running")

    def add_consumer(self, target):
        """ Adds a new consumer target """
        self.consumers.append(target)

    def run(self):
        """ Start running the pipeline """
        self.running = True

        threads = []
        for p in self.producers:
            threads.append(Thread(target=p))
            threads[-1].start()

        while any(t.is_alive() for t in threads):
            try:
                data = self.queue.get()
                for c in self.consumers:
                    c(data)
                self.queue.task_done()
            except Empty:
                pass
