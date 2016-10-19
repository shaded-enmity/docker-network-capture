# docker-network-capture

A small utility written in Python3 that can help you debug network problems of Docker containers.

## Prerequisites

Make sure you have `tcpdump` package installed, the execution requires root privileges

## Installation

Via PIP:
```
$ pip3 install docker-network-capture
```

## Usage

```
usage: docker-network-capture [-h] [--verbose] [-b BRIDGE] [-c CAPTURE] [-j]
                              [-d DOCKER]
                              container

positional arguments:
  container

optional arguments:
  -h, --help            show this help message and exit
  --verbose
  -b BRIDGE, --bridge BRIDGE
                        Docker bridge to use
  -c CAPTURE, --capture CAPTURE
                        Direction of traffic to capture [egress,ingress]
  -j, --json            buffer data and output JSON at the end
  -d DOCKER, --docker DOCKER
```

## Architecture & Security

![DNC ARCHITECTURE](https://github.com/shaded-enmity/docker-network-capture/blob/master/media/dnc_architecture.jpg "DNC ARCHITECTURE")

The main process starts off as `root` and creates two pipeline producers, one for the ethernet interface of the container and one for the namespaced loopback interface. Each pipeline launches it's own `tcpdump` capture process, after that is done, the main process deprivileges itself by changing it's UID/GID/Groups settings to nobody. After the `tcpdump` process is ready, a new process is forked, which is immediately deprivileged in the same way as the main process, and this process then handles the the parsing of raw byte stream into packets via PCAP and feeding them back to the main process via the `Queue`.

## Example

In the following example we see the output of `docker-network-capture` for a container
in which `curl google.com` was executed:

```
$ sudo docker-network-capture --capture=egress,ingress 92707a5e8369
OUT: 10.38.5.26:53
  00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
+-------------------------------------------------+----------------+
| 2F 59 01 00 00 01 00 00 00 00 00 00 06 67 6F 6F |/Y...........goo|
| 67 6C 65 03 63 6F 6D 00 00 01 00 01             |gle.com.....    |
+-------------------------------------------------+----------------+
OUT: 10.38.5.26:53
  00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
+-------------------------------------------------+----------------+
| CE B8 01 00 00 01 00 00 00 00 00 00 06 67 6F 6F |.............goo|
| 67 6C 65 03 63 6F 6D 00 00 1C 00 01             |gle.com.....    |
+-------------------------------------------------+----------------+
IN:  10.38.5.26:53
  00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
+-------------------------------------------------+----------------+
| 2F 59 81 80 00 01 00 01 00 00 00 00 06 67 6F 6F |/Y...........goo|
| 67 6C 65 03 63 6F 6D 00 00 01 00 01 C0 0C 00 01 |gle.com.........|
| 00 01 00 00 00 99 00 04 D8 3A D0 2E             |.........:..    |
+-------------------------------------------------+----------------+
IN:  10.38.5.26:53
  00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
+-------------------------------------------------+----------------+
| CE B8 81 80 00 01 00 01 00 00 00 00 06 67 6F 6F |.............goo|
| 67 6C 65 03 63 6F 6D 00 00 1C 00 01 C0 0C 00 1C |gle.com.........|
| 00 01 00 00 00 99 00 10 2A 00 14 50 40 01 08 15 |........*..P@...|
| 00 00 00 00 00 00 20 0E                         |...... .        |
+-------------------------------------------------+----------------+
OUT: 216.58.208.46:80
IN:  216.58.208.46:80
OUT: 216.58.208.46:80
OUT: 216.58.208.46:80
  00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
+-------------------------------------------------+----------------+
| 47 45 54 20 2F 20 48 54 54 50 2F 31 2E 31 0D 0A |GET / HTTP/1.1..|
| 48 6F 73 74 3A 20 67 6F 6F 67 6C 65 2E 63 6F 6D |Host: google.com|
| 0D 0A 55 73 65 72 2D 41 67 65 6E 74 3A 20 63 75 |..User-Agent: cu|
| 72 6C 2F 37 2E 34 37 2E 31 0D 0A 41 63 63 65 70 |rl/7.47.1..Accep|
| 74 3A 20 2A 2F 2A 0D 0A 0D 0A                   |t: */*....      |
+-------------------------------------------------+----------------+
IN:  216.58.208.46:80
IN:  216.58.208.46:80
  00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15
+-------------------------------------------------+----------------+
| 48 54 54 50 2F 31 2E 31 20 33 30 32 20 46 6F 75 |HTTP/1.1 302 Fou|
| 6E 64 0D 0A 43 61 63 68 65 2D 43 6F 6E 74 72 6F |nd..Cache-Contro|
| 6C 3A 20 70 72 69 76 61 74 65 0D 0A 43 6F 6E 74 |l: private..Cont|
| 65 6E 74 2D 54 79 70 65 3A 20 74 65 78 74 2F 68 |ent-Type: text/h|
| 74 6D 6C 3B 20 63 68 61 72 73 65 74 3D 55 54 46 |tml; charset=UTF|
| 2D 38 0D 0A 4C 6F 63 61 74 69 6F 6E 3A 20 68 74 |-8..Location: ht|
| 74 70 3A 2F 2F 77 77 77 2E 67 6F 6F 67 6C 65 2E |tp://www.google.|
| 63 7A 2F 3F 67 66 65 5F 72 64 3D 63 72 26 65 69 |cz/?gfe_rd=cr&ei|
| 3D 50 72 63 45 57 49 4F 64 49 34 4C 62 38 41 66 |=PrcEWIOdI4Lb8Af|
| 52 34 62 76 67 44 51 0D 0A 43 6F 6E 74 65 6E 74 |R4bvgDQ..Content|
| 2D 4C 65 6E 67 74 68 3A 20 32 35 38 0D 0A 44 61 |-Length: 258..Da|
| 74 65 3A 20 4D 6F 6E 2C 20 31 37 20 4F 63 74 20 |te: Mon, 17 Oct |
| 32 30 31 36 20 31 31 3A 33 34 3A 32 32 20 47 4D |2016 11:34:22 GM|
| 54 0D 0A 0D 0A 3C 48 54 4D 4C 3E 3C 48 45 41 44 |T....<HTML><HEAD|
| 3E 3C 6D 65 74 61 20 68 74 74 70 2D 65 71 75 69 |><meta http-equi|
| 76 3D 22 63 6F 6E 74 65 6E 74 2D 74 79 70 65 22 |v="content-type"|
| 20 63 6F 6E 74 65 6E 74 3D 22 74 65 78 74 2F 68 | content="text/h|
| 74 6D 6C 3B 63 68 61 72 73 65 74 3D 75 74 66 2D |tml;charset=utf-|
| 38 22 3E 0A 3C 54 49 54 4C 45 3E 33 30 32 20 4D |8">.<TITLE>302 M|
| 6F 76 65 64 3C 2F 54 49 54 4C 45 3E 3C 2F 48 45 |oved</TITLE></HE|
| 41 44 3E 3C 42 4F 44 59 3E 0A 3C 48 31 3E 33 30 |AD><BODY>.<H1>30|
| 32 20 4D 6F 76 65 64 3C 2F 48 31 3E 0A 54 68 65 |2 Moved</H1>.The|
| 20 64 6F 63 75 6D 65 6E 74 20 68 61 73 20 6D 6F | document has mo|
| 76 65 64 0A 3C 41 20 48 52 45 46 3D 22 68 74 74 |ved.<A HREF="htt|
| 70 3A 2F 2F 77 77 77 2E 67 6F 6F 67 6C 65 2E 63 |p://www.google.c|
| 7A 2F 3F 67 66 65 5F 72 64 3D 63 72 26 61 6D 70 |z/?gfe_rd=cr&amp|
| 3B 65 69 3D 50 72 63 45 57 49 4F 64 49 34 4C 62 |;ei=PrcEWIOdI4Lb|
| 38 41 66 52 34 62 76 67 44 51 22 3E 68 65 72 65 |8AfR4bvgDQ">here|
| 3C 2F 41 3E 2E 0D 0A 3C 2F 42 4F 44 59 3E 3C 2F |</A>...</BODY></|
| 48 54 4D 4C 3E 0D 0A                            |HTML>..         |
+-------------------------------------------------+----------------+
OUT: 216.58.208.46:80
OUT: 216.58.208.46:80
IN:  216.58.208.46:80
OUT: 216.58.208.46:80
```

And here's the same request but with a JSON formatted output:

```
[
   {
      "payload": "5be60100000100000000000006676f6f676c6503636f6d0000010001",
      "src_port": "36838",
      "interface": "docker0",
      "src": "172.17.0.2",
      "dst": "10.38.5.26",
      "dst_port": "53"
   },
   {
      "payload": "1dd30100000100000000000006676f6f676c6503636f6d00001c0001",
      "src_port": "36838",
      "interface": "docker0",
      "src": "172.17.0.2",
      "dst": "10.38.5.26",
      "dst_port": "53"
   },
   {
      "payload": "5be68180000100010000000006676f6f676c6503636f6d0000010001c00c00010001000000890004d83ad02e",
      "src_port": "53",
      "interface": "docker0",
      "src": "10.38.5.26",
      "dst": "172.17.0.2",
      "dst_port": "36838"
   },
   {
      "payload": "1dd38180000100010000000006676f6f676c6503636f6d00001c0001c00c001c00010000008900102a00145040010815000000000000200e",
      "src_port": "53",
      "interface": "docker0",
      "src": "10.38.5.26",
      "dst": "172.17.0.2",
      "dst_port": "36838"
   },
   {
      "payload": "",
      "src_port": "46094",
      "interface": "docker0",
      "src": "172.17.0.2",
      "dst": "216.58.208.46",
      "dst_port": "80"
   },
   {
      "payload": "",
      "src_port": "80",
      "interface": "docker0",
      "src": "216.58.208.46",
      "dst": "172.17.0.2",
      "dst_port": "46094"
   },
   {
      "payload": "",
      "src_port": "46094",
      "interface": "docker0",
      "src": "172.17.0.2",
      "dst": "216.58.208.46",
      "dst_port": "80"
   },
   {
      "payload": "474554202f20485454502f312e310d0a486f73743a20676f6f676c652e636f6d0d0a557365722d4167656e743a206375726c2f372e34372e310d0a4163636570743a202a2f2a0d0a0d0a",
      "src_port": "46094",
      "interface": "docker0",
      "src": "172.17.0.2",
      "dst": "216.58.208.46",
      "dst_port": "80"
   },
   {
      "payload": "",
      "src_port": "80",
      "interface": "docker0",
      "src": "216.58.208.46",
      "dst": "172.17.0.2",
      "dst_port": "46094"
   },
   {
      "payload": "485454502f312e312033303220466f756e640d0a43616368652d436f6e74726f6c3a20707269766174650d0a436f6e74656e742d547970653a20746578742f68746d6c3b20636861727365743d5554462d380d0a4c6f636174696f6e3a20687474703a2f2f7777772e676f6f676c652e637a2f3f6766655f72643d63722665693d54726345574e7a5247596a6238416648376f4b6f42510d0a436f6e74656e742d4c656e6774683a203235380d0a446174653a204d6f6e2c203137204f637420323031362031313a33343a333820474d540d0a0d0a3c48544d4c3e3c484541443e3c6d65746120687474702d65717569763d22636f6e74656e742d747970652220636f6e74656e743d22746578742f68746d6c3b636861727365743d7574662d38223e0a3c5449544c453e333032204d6f7665643c2f5449544c453e3c2f484541443e3c424f44593e0a3c48313e333032204d6f7665643c2f48313e0a54686520646f63756d656e7420686173206d6f7665640a3c4120485245463d22687474703a2f2f7777772e676f6f676c652e637a2f3f6766655f72643d637226616d703b65693d54726345574e7a5247596a6238416648376f4b6f4251223e686572653c2f413e2e0d0a3c2f424f44593e3c2f48544d4c3e0d0a",
      "src_port": "80",
      "interface": "docker0",
      "src": "216.58.208.46",
      "dst": "172.17.0.2",
      "dst_port": "46094"
   },
   {
      "payload": "",
      "src_port": "46094",
      "interface": "docker0",
      "src": "172.17.0.2",
      "dst": "216.58.208.46",
      "dst_port": "80"
   },
   {
      "payload": "",
      "src_port": "46094",
      "interface": "docker0",
      "src": "172.17.0.2",
      "dst": "216.58.208.46",
      "dst_port": "80"
   },
   {
      "payload": "",
      "src_port": "80",
      "interface": "docker0",
      "src": "216.58.208.46",
      "dst": "172.17.0.2",
      "dst_port": "46094"
   },
   {
      "payload": "",
      "src_port": "46094",
      "interface": "docker0",
      "src": "172.17.0.2",
      "dst": "216.58.208.46",
      "dst_port": "80"
   }
]

```

## License

GNU/GPL 2.0
