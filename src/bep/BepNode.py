import base64
import hashlib
import socket
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


class BepNode:
    irequest = 0
    client_id = None

    def __init__(self, cert, key):
        """Initial TLSv1.2 connection with certificate and key file"""

        self.client_id = certificate_id(cert)

        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.check_hostname = False
        context.load_cert_chain(cert, key)
        self.conn = context.wrap_socket(socket.socket(socket.AF_INET))

    def connect(self, endpoint):
        """Connect to endpoint"""

        self.conn.connect(endpoint)
        self.conn.do_handshake()

    def hello(self, name):
        """Exchange hello's"""

        HELLO_MAGIC_NUMBER = 0x2EA7D90B

        hello = protocol.Hello()
        hello.device_name = name
        hello.client_name = CLIENT_NAME
        hello.client_version = CLIENT_VERSION

        hello_str = hello.SerializeToString()

        self.conn.send(bytes([*pack_int(HELLO_MAGIC_NUMBER), *pack_short(len(hello_str)), *hello_str]))

        magic_nb = unpack_int(self.read(4))
        assert HELLO_MAGIC_NUMBER == magic_nb, 'Hello must be prefixed by magic number'

        msg_size = unpack_short(self.read(2))
        hello.ParseFromString(self.read(msg_size))
        return hello

    def cluster_config(self, folders):
        """Send our cluster configuration"""

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

        return self.send_msg(cluster_config, protocol.CLUSTER_CONFIG)

    def list_folder(self, folder='default'):
        """List a folder files"""

        index = protocol.IndexUpdate()
        index.folder = folder
        share = self.send_msg(index, protocol.INDEX_UPDATE)
        files = filter(lambda f: not f.deleted, share.files)
        return {'folder': share.folder, 'files': files}

    def download_file(self, file, folder='default'):
        """Download a file"""

        response = protocol.Response()
        file_content = b''

        request = protocol.Request()
        request.folder = folder
        request.name = file.name

        for block in file.Blocks:
            request.id = self.irequest
            request.offset = block.offset
            request.size = block.size
            self.irequest += 1
            res = self.send_msg(request, protocol.REQUEST, response)
            assert res.code == protocol.NO_ERROR, f'Failed to retrieve file: {res.code}'
            file_content += res.data

        return file_content

    def upload_file(self, file, filecontent, folder='default'):
        """Upload file"""

    def read(self, length):
        """Reads fixed length of bytes from connection"""

        BUFFER_SIZE = 2 ** 12

        buffer = b''
        while len(buffer) < length:
            buffer += self.conn.recv(min(length - len(buffer), BUFFER_SIZE))
        return buffer

    def send_msg(self, msg, msg_type, response=None):
        '''
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
        '''
        response = response or msg

        header = protocol.Header()
        header.type = msg_type
        header.compression = protocol.NONE
        header_str = header.SerializeToString()

        msg_str = msg.SerializeToString()
        self.conn.send(bytes([*pack_short(len(header_str)), *header_str, *pack_int(len(msg_str)), *msg_str]))

        header_size = unpack_short(self.read(2))
        header.ParseFromString(self.read(header_size))

        msg_size = unpack_int(self.read(4))
        res = self.read(msg_size)
        if header.compression == protocol.LZ4:
            res = res[3::-1] + res[4:]  # message int size header must be converted to little endian
            res = lz4.decompress(res)
        response.ParseFromString(res)
        return response

def certificate_id(certfile):
    'Calculates the client id based on the certificate'

    cert_content = open(certfile, 'rt').read()

    cert_pem = crypto.load_certificate(crypto.FILETYPE_PEM, cert_content)
    cert_der = crypto.dump_certificate(crypto.FILETYPE_ASN1, cert_pem)
    sig = hashlib.sha256(cert_der)
    b32 = base64.b32encode(sig.digest()).decode('ascii').rstrip('=')

    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
    alphabet_dict = {l: i for i, l in enumerate(alphabet)}

    def luhn_number(part):
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
