"""
Bla bla
"""

import base64
import hashlib
import socket
import select
import ssl
import struct
from collections import namedtuple
from functools import partial

import bep.protocol.bep_protocol_pb2 as protocol
import lz4.block as lz4
import OpenSSL.crypto as crypto

Endpoint = namedtuple('Endpoint', ['hostname', 'port'])

CLIENT_NAME = 'claudio_bep-client'
CLIENT_VERSION = 'v0.1'

pack_int = partial(struct.pack, '>I')
pack_short = partial(struct.pack, '>H')
def unpack_int(buf): return struct.unpack('>I', buf)[0]
def unpack_short(buf): return struct.unpack('>H', buf)[0]


# proto buff message types indexed by MessageType enum value
ResponsesByTypeValue = [
    protocol.ClusterConfig,  # MessageType 0
    protocol.Index,  # MessageType 1
    protocol.IndexUpdate,  # MessageType 2
    protocol.Request,  # MessageType 3
    protocol.Response,  # MessageType 4
    protocol.DownloadProgress,  # MessageType 5
    protocol.Ping,  # MessageType 6
    protocol.Close  # MessageType 7
]

class BepNode:
    """
    Implements the BEP protocol.

    Provides the behavior to connect to a BEP peer node, get the list of shares, the files of a share and download files.
    """
    def __init__(self, cert, key):
        """Initial TLSv1.2 connection with certificate and key file"""

        self.__irequest = 0
        self.client_id = certificate_id(cert)

        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.check_hostname = False
        context.load_cert_chain(cert, key)
        self.__conn = context.wrap_socket(socket.socket(socket.AF_INET))

    def connect(self, endpoint):
        """Connects to a peer BEP node endpoint"""

        self.__conn.connect(endpoint)
        self.__conn.do_handshake()

    def hello(self, name):
        """Exchange hello's messages"""

        HELLO_MAGIC_NUMBER = 0x2EA7D90B

        hello = protocol.Hello()
        hello.device_name = name
        hello.client_name = CLIENT_NAME
        hello.client_version = CLIENT_VERSION

        hello_str = hello.SerializeToString()

        self.__conn.send(bytes([*pack_int(HELLO_MAGIC_NUMBER), *pack_short(len(hello_str)), *hello_str]))

        magic_nb = unpack_int(self._read(4))
        assert HELLO_MAGIC_NUMBER == magic_nb, 'Hello must be prefixed by magic number'

        msg_size = unpack_short(self._read(2))
        hello.ParseFromString(self._read(msg_size))
        return hello

    def cluster_config(self, folders):
        """Exchange cluster configuration messages"""

        f_name = folders or []

        cluster_config = protocol.ClusterConfig()
        for f_name in folders:
            folder = cluster_config.folders.add()
            folder.id = f_name
            folder.label = f_name
            folder.read_only = False
            folder.ignore_permissions = True
            folder.ignore_delete = True
            folder.disable_temp_indexes = True

        self._send_msg(cluster_config, protocol.CLUSTER_CONFIG)
        res = self._read_msg()
        assert res.DESCRIPTOR.name == 'ClusterConfig', 'Expected msg of type ClusterConfig'
        return res

    def list_folder(self, folder='default'):
        """Lists a folder files"""

        index = protocol.IndexUpdate()
        index.folder = folder
        self._send_msg(index, protocol.INDEX_UPDATE)
        files = []

        # while there are messages to be read, keep reading it them
        # useful if share data is too big to fit in 1 message
        while select.select([self.__conn], [], [], 1)[0]:
            share = self._read_msg()
            assert share.DESCRIPTOR.name in ('Index', 'IndexUpdate'), 'Expected msg of type Index(Update)'
            files += filter(lambda f: not f.deleted, share.files)

        return {'folder': share.folder, 'files': files}

    def download_file(self, file, folder='default'):
        """Download a file"""

        file_content = b''

        request = protocol.Request()
        request.folder = folder
        request.name = file.name

        for block in file.Blocks:
            request.id = self.__irequest
            request.offset = block.offset
            request.size = block.size
            self.__irequest += 1
            self._send_msg(request, protocol.REQUEST)
            res = self._read_msg()
            assert res.DESCRIPTOR.name == 'Response', 'Expected msg of type Response'
            assert res.code == protocol.NO_ERROR, f'Failed to retrieve file: {res.code}'
            file_content += res.data

        return file_content

    def _read(self, length):
        """Reads fixed length of bytes from connection"""

        BUFFER_SIZE = 2 ** 12

        buffer = b''
        while len(buffer) < length:
            buffer += self.__conn.recv(min(length - len(buffer), BUFFER_SIZE))
        return buffer

    def _send_msg(self, msg, msg_type):
        """
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |         Header Length         |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        /                               /
        \            Header             \
        /                               /
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        |         Message Length        |
        |           (32 bits)           |
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        /                               /
        \            Message            \
        /                               /
        +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
        """
        header = protocol.Header()
        header.type = msg_type
        header.compression = protocol.NONE
        header_str = header.SerializeToString()

        msg_str = msg.SerializeToString()
        self.__conn.send(bytes([*pack_short(len(header_str)), *header_str, *pack_int(len(msg_str)), *msg_str]))

    def _read_msg(self):
        """Reads a message from peer BEP node"""

        header = protocol.Header()
        header_size = unpack_short(self._read(2))
        header.ParseFromString(self._read(header_size))

        response = ResponsesByTypeValue[header.type]()

        msg_size = unpack_int(self._read(4))
        res = self._read(msg_size)

        if header.compression == protocol.LZ4:
            res = res[3::-1] + res[4:]  # message int size header must be converted to little endian
            res = lz4.decompress(res)
        response.ParseFromString(res)
        return response

def certificate_id(certfile):
    """Calculates the client id based on the certificate"""

    cert_content = open(certfile, 'rt').read()

    cert_pem = crypto.load_certificate(crypto.FILETYPE_PEM, cert_content)
    cert_der = crypto.dump_certificate(crypto.FILETYPE_ASN1, cert_pem)
    sig = hashlib.sha256(cert_der)
    b32 = base64.b32encode(sig.digest()).decode('ascii').rstrip('=')

    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
    alphabet_dict = {l: i for i, l in enumerate(alphabet)}

    def luhn_number(part):
        """https://en.wikipedia.org/wiki/Luhn_algorithm"""
        total = 0
        for i, v in enumerate(alphabet_dict[x] for x in part):
            if i % 2:
                v *= 2
            if v > 31:
                v -= 31
            total += v
        return alphabet[32 - total % 32]

    parts = [b32[i:i + 13] for i in range(0, len(b32), 13)]
    return '-'.join(part[:7] + '-' + part[7:] + luhn_number(part) for part in parts)
