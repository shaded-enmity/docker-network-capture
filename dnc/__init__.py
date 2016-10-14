""" Size of the buffer used to read from tcpdump pipe """
MAX_PACKET_SIZE = 2048


class CaptureFlags(object):
    """ Which kind of traffic to capture """
    (Invalid, Ingress, Egress, Both) = (0, 1, 2, 3)


class ContainerError(Exception): pass
