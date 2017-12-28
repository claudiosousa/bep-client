#!/usr/bin/env python3.6

"""
Bep client, can be used to download & upload files to a BEP node.

Usage:
  bepclient.py [options] (showid | connect <host> [share <share_id> [(download|upload) <file>]])

Examples:
  bepclient.py [options] showid
  bepclient.py [options] connect 129.194.186.177
  bepclient.py [options] connect 129.194.186.177 share hyperfacile
  bepclient.py [options] connect 129.194.186.177 share hyperfacile download plistlib.py
  bepclient.py [options] connect 129.194.186.177 share hyperfacile upload filename.py
  bepclient.py -h | --help

Options:
  -h --help          Show this screen.
  --key=<keyfile>    Key file [default: config/key.pem].
  --cert=<certfile>  Certificate file [default: config/cert.pem].
  --port=<port>      Host port [default: 22000]
  --name=<name>      The client name [default: Claudio's BEP client].
"""


from datetime import datetime
from pprint import pprint

from docopt import docopt

import humanize
from bep.BepNode import BepNode

args = docopt(__doc__)


def main():
    keyfile = args.get('--key')
    certfile = args.get('--cert')
    client = BepNode(cert=certfile, key=keyfile)

    if args['showid']:  # just want to show clientid
        print(f'Client id: {client.client_id}')
        return

    host = args.get('<host>')
    port = int(args.get('--port'))
    client.connect((host, port))

    name = args.get('--name')
    peerinfo = client.hello(name)
    print(f'Connected to: {peerinfo.device_name}')

    if not args['share']:
        # we want to list shares
        peer_cluster = client.cluster_config(folders=[])
        print(f'Shared folders: {len(peer_cluster.folders)}')
        for folder in peer_cluster.folders:
            print(f'\t- {folder.label} ({folder.id})')
        print()
        return

    share_id = args['<share_id>']
    client.cluster_config(folders=[share_id])
    share = client.list_folder(folder=share_id)

    if not args['download']:
        # we want to list shares
        print(f"Folder '{share['folder']}' files:")
        for file in share['files']:
            print(f'\t- {file.name:40} | size: {humanize.naturalsize(file.size, gnu=True):>6} | modified: {humanize.naturaldate(datetime.fromtimestamp(file.modified_s)):^12}| blocks: {len(file.Blocks)}')
        print()
        return

    # download file
    file = args['<file>']
    files = {f.name: f for f in share['files']}
    assert file in files, f'could not find file {file}'
    res = client.download_file(file=files[file], folder=share['folder'])
    filename = file.split('/')[-1]
    with open(filename, "wb") as f:
        f.write(res)

    print(f'File {filename} downloaded')


if __name__ == '__main__':
    main()
