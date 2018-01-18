# Mini-projet *Block Exchange Protocol* (BEP)

Ce repo GIT contient le résultat de l'étude du protocole *Block Exchange Protocol*[^2] (BEP), développé et implémenté par Syncthing [^1].

L'étude se décompose en deux sections:

## Documentation

Le fichier [Bep documentation.pdf](https://githepia.hesge.ch/claudio.martinss/bep-client/raw/master/documentation/bep_documentation.pdf) contient l'analyse faite sur le *Block Exchange Protocol*.

On y modélise le protocole depuis trois approches différentes:

 * Le diagramme d'états
 * Le diagramme de séquences
 * Le diagramme de classes des messages échangées

Le coeur du BEP protocol est implémenté dans la class [BepNode.py](https://githepia.hesge.ch/claudio.martinss/bep-client/raw/master/src/bep/BepNode.py) et sa documentation est disponible en [html](https://githepia.hesge.ch/claudio.martinss/bep-client/raw/master/documentation/html/index.html).

## BEP Client

Le dossier *src* contient l'implémentation du protocole.

### Utilisation

L'executable *bepclient* à l'interface suivant:

~~~~~~~ {.bash }
$> bepclient.py -h
Bep client, can be used to download files from a BEP node.

Usage:
  bepclient.py [options] (showid | connect <host> [share <share_id> [download <remotefile> <localfile>]])

Examples:
  bepclient.py [options] showid
  bepclient.py [options] connect 129.194.186.177
  bepclient.py [options] connect 129.194.186.177 share hyperfacile
  bepclient.py [options] connect 129.194.186.177 share hyperfacile download plistlib.py /tmp/plistlib.py
  bepclient.py -h | --help

Options:
  --key=<keyfile>    Key file [default: config/key.pem].
  --cert=<certfile>  Certificate file [default: config/cert.pem].
  --port=<port>      Host port [default: 22000]
  --name=<name>      The client name [default: Claudio's BEP client].
  -h --help          Show this screen.
~~~~~~~


#### Exemples d'utilisation

**Montrer l'id du certificat utilisé:**

~~~~~~~ {.bash }
$> ./bepclient.py showid
Client id: HG3DI2F-JKKVY3Z-HL5ZCWN-FH53M35-CMGFGE5-WAPGTV6-5SBWC6W-4VZSFA
~~~~~~~

**Montrer les folders d'un noeud pair:**

~~~~~~~ {.bash }
$> ./bepclient.py connect 129.194.186.177
Connected to: redbox
Shared folders: 3
        -  (facile)
        -  (hyperfacile)
        -  (moins_facile)
~~~~~~~

**Montrer les fichiers d'un folder:**

~~~~~~~ {.bash }
$> ./bepclient.py connect 129.194.186.177 share hyperfacile
Connected to: redbox
Folder 'hyperfacile' files:
        - platform.py                    | size:  51.4K | modified:    Nov 02   | blocks: 1
        - platform.pyc                   | size:  36.8K | modified:    Nov 02   | blocks: 1
        - plistlib.py                    | size:  14.8K | modified:    Nov 02   | blocks: 1
        - plistlib.pyc                   | size:  18.7K | modified:    Nov 02   | blocks: 1
~~~~~~~

**Telécharger un fichier:**

~~~~~~~ {.bash }
$> ./bepclient.py connect 129.194.186.177 share hyperfacile download plistlib.py /tmp/plistlib.py
Connected to: redbox
File "/tmp/plistlib.py" downloaded
~~~~~~~

# Auteurs

Ce project est réalisé par *Claudio Sousa, ITI soir 2018*

# References

[^1]: https://syncthing.net"
[^2]: https://docs.syncthing.net/specs/bep-v1.html