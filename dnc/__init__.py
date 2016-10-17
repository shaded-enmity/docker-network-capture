""" Size of the buffer used to read from tcpdump pipe """
MAX_PACKET_SIZE = 2048


class CaptureFlags(object):
    """ Which kind of traffic to capture """
    (Invalid, Ingress, Egress, Both) = (0, 1, 2, 3)


class ContainerError(Exception): pass


def start_pcap_parser(r, w, interface):
    """ Start parsing incoming packets """

    from pcapfile import savefile
    from os import write, close, fdopen

    try:
        cap = savefile.load_savefile(fdopen(r, 'rb'), verbose=False, lazy=True, layers=3)

        # packets are loaded lazily via a generator, so we just iterate over them
        for p in cap.packets:
            payload = p.packet.payload

            # discard L1/L2 packets
            if isinstance(payload, bytes):
                continue

            src_port, dst_port = payload.payload.src_port, payload.payload.dst_port
            src, dst = payload.src.decode('utf-8'), payload.dst.decode('utf-8')
            # {src}:{src_port} {dst}:{dst_port} {interface} {payload}
            data_string = '{}:{} {}:{} {} {}\n'.format(src, src_port, dst, dst_port, interface,
                                                       payload.payload.payload.decode('utf-8'))

            # convert to byte buffer and write to the output pipe
            buf = bytes(data_string, 'utf-8')
            write(w, buf)
    except KeyboardInterrupt:
        pass

    close(w)
