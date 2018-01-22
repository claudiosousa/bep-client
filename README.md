# Mini-projet *Block Exchange Protocol* (BEP)

Ce repo GIT contient le résultat de l'étude du protocole *Block Exchange Protocol*[^2] (BEP), développé et implémenté par Syncthing [^1].

L'étude se décompose en deux sections:

## Documentation

Le fichier [Bep documentation.pdf](https://githepia.hesge.ch/claudio.martinss/bep-client/raw/master/documentation/bep_documentation.pdf) contient l'analyse faite sur le *Block Exchange Protocol*.

On y modélise le protocole depuis trois approches différentes:

 * Le diagramme d'états
 * Le diagramme de séquences
 * Le diagramme de classes des messages échangées

Le coeur du BEP protocol est implémenté dans la class [BepNode.py](https://githepia.hesge.ch/claudio.martinss/bep-client/blob/master/src/bep/BepNode.py) et sa documentation est disponible en [html](http://claudio.sousa.gitlab.io/bep-client/classBepNode_1_1BepNode.html).

## BEP Client

Le dossier *src* contient l'implémentation du protocole.

### Utilisation

L'executable *bepclient* à l'interface suivant:

~~~~~~~ {.bash }
$> bepclient.py -h
Bep client, can be used to download files from a BEP node.

Usage:
  bepclient.py [options] (showid | connect <host> [share <share_id> [download <destination>]])

Examples:
  bepclient.py [options] showid
  bepclient.py [options] connect 129.194.186.177
  bepclient.py [options] connect 129.194.186.177 share facile
  bepclient.py [options] connect 129.194.186.177 share facile download /tmp/destination
  bepclient.py -h | --help

Options:
  --key=<keyfile>    Key file [default: config/key.pem].
  --cert=<certfile>  Certificate file [default: config/cert.pem].
  --port=<port>      Host port [default: 22000]
  --name=<name>      The client name [default: Claudio's BEP client].
  -h --help          Show this screen.
~~~~~~~


#### Exemples d'utilisation

**Montrer l'id du certificat utilisé :**

~~~~~~~ {.bash }
$> ./bepclient.py showid
Client id: HG3DI2F-JKKVY3Z-HL5ZCWN-FH53M35-CMGFGE5-WAPGTV6-5SBWC6W-4VZSFA
~~~~~~~

**Montrer les folders d'un noeud pair :**

~~~~~~~ {.bash }
$> ./bepclient.py connect 129.194.186.177
Connected to: redbox
Shared folders: 3
        -  (facile)
        -  (hyperfacile)
        -  (moins_facile)
~~~~~~~

**Montrer les fichiers du folder `facile` :**

~~~~~~~ {.bash }
$> ./bepclient.py connect 129.194.186.177 share facile
Connected to: redbox
Folder 'facile' content:
File                                       |    Size  |   Modified   | Blocks
platform.py                                |    51.4K |    Oct 20    | 1
platform.pyc                               |    36.8K |    Oct 20    | 1
plistlib.py                                |    14.8K |    Oct 20    | 1
plistlib.pyc                               |    18.7K |    Oct 20    | 1
~~~~~~~

**Telécharger le folder `facile` :**

~~~~~~~ {.bash }
$> ./bepclient.py connect 129.194.186.177 share facile download /tmp/facile
Connected to: redbox
Share "facile" downloaded into /tmp/facile
~~~~~~~

# Auteurs

Ce project est réalisé par *Claudio Sousa, ITI soir 2018*

# References

[^1]: https://syncthing.net"
[^2]: https://docs.syncthing.net/specs/bep-v1.html