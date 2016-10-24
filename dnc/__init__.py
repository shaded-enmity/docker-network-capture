""" Size of the buffer used to read from tcpdump pipe """
MAX_PACKET_SIZE = 2048

""" How many times we're gonna sleep waiting for producers to come online """
MAX_WAIT_RUNS = 10

class CaptureFlags(object):
    """ Which kind of traffic to capture """
    (Invalid, Ingress, Egress, Both) = (0, 1, 2, 3)


class ContainerError(Exception): pass


def start_pcap_parser(r, w, interface):
    """ Start parsing incoming packets """

    from pcapfile import savefile
    from pcapfile.protocols.transport import tcp
    from os import write, close, fdopen

    try:
        cap = savefile.load_savefile(fdopen(r, 'rb'), verbose=False, lazy=True, layers=3)

        # packets are loaded lazily via a generator, so we just iterate over them
        for p in cap.packets:
            payload = p.packet.payload

            # discard Ethernet and IP frames
            if isinstance(payload, bytes):
                continue


            l3 = payload.payload
            if isinstance(l3, tcp.TCP):
                seq = '{}-{}'.format(l3.acknum,l3.seqnum)
            else:
                seq = '-'

            src_port, dst_port = l3.src_port, l3.dst_port
            src, dst = payload.src.decode('utf-8'), payload.dst.decode('utf-8')
            # {src}:{src_port} {dst}:{dst_port} {interface} {seq} {payload}
            data_string = '{}:{} {}:{} {} {} {}\n'.format(src, src_port, dst, dst_port, interface,
                                                          seq, l3.payload.decode('utf-8'))

            # convert to byte buffer and write to the output pipe
            buf = bytes(data_string, 'utf-8')
            write(w, buf)
    except KeyboardInterrupt:
        pass

    close(w)
