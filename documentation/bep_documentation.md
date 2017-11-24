---
title: Block Exchange Protocol v1
author: Claudio Sousa
date: 2017
header-includes:
- \usepackage{pdfpages}
- \usepackage[english]{babel}
- \usepackage{hyperref}
- \hypersetup{  colorlinks = true,  linkcolor  = black }
- \setcounter{tocdepth}{5}
- \usepackage{fancyhdr}
- \pagestyle{fancy}
- \fancyhead{}
- \fancyhead[CO,CE]{Conception de protocoles réseau}
- \fancyfoot[LE,RO]{\thepage}
- \fancyfoot[CO,CE]{Claudio Sousa}
header: This is fancy
footer: So is this
bibliography: biblio.bib
geometry:
 - left=1.5cm
 - right=1.5cm
 - top=2.5cm
 - bottom=2.5cm
nocite:
abstract:
...

\ \

\begin{center}
Conception de protocoles réseau

HEPIA
\end{center}

\newpage

\newpage

\tableofcontents

\newpage

# Introduction

Ce document est le résultat de l'étude du protocole *Block Exchange Protocol*[^2] (BEP), développé et implémenté par Syncthing [^1].
L'étude se décompose en deux chapitres:

Le premier chapitre, *Block Exchange Protocol*, décrit l'analyse faite sur le protocole du nom du chapitre.
On modélise le protocole depuis trois approches différentes:

 * Le diagramme d'états
 * Le diagramme de séquences
 * Le diagramme de classes des messages échangées

Dans le deuxième chapitre, *BEP Client*, on décrit le mini-projet consistant à implémenter une partie le protocole décrit au premier chapitre.


# Block Exchange Protocol

## Diagramme d'états

Dans ce diagramme d'états on montre . La syntaxe utilisée est basée sur celle vue en cours, en particulier les notes sur les transitions ont la forme $\frac{condition}{action}$

Le diagramme proposé ici respecte la contrainte forte que, dans chaque état, une seule condition de transition ne peut être vrai à la fois. Ceci est important pour avoir un comportement d'exécution prévisible.


### *Actions* et *Conditions* communes

On définit ici quelques *actions* et *conditions* communes utilisées à plusieurs endroit du diagramme d'état. Les actions et conditions qui apparaissent une seule fois dans le diagramme sont décrites dans leur état respectif.

Data.req:
  : demande à la couche en dessous (couche transport) d'envoyer le message passé en paramètre. Exemple: Data.req(Hello) pour envoyer un message Hello

startTimer:
  : démarre le timer spécifié. Si le timer est en exécution, il est démarré

cancelTimer:
  : annule l'exécution du timer passé paramètre

### Conditions

timerExpired:
  : le timer spécifié a expiré

Data.ind:
  : un message du type spécifié a été reçu et son type est celui spécifié en paramètre.

      Exemples:

      * Data.ind(Hello) est vrai si le prochain message dans le buffer de réception est de type *Hello*.
      * Data.ind(msg != Hello) est vrai si le prochain message dans le buffer est de type différent de *Hello*.


### Les timers

Les timers décrits ici permettent de rajouter la dimension du temps dans le protocole. La valeur de leur temps n'est pas toujours précisée car dépendante de l'implémentation.

\textcolor{red}{même pour le ping timer???}

pingTimer:
  : determine le temps da attendre depuis le dernier message envoyé avant d'envoi du message ping au pair (*heartbeat*). Le protocole[^2] spécifie que la valeur de ce timer est de 90s.

downloadTimer:
  : vérifie si un *download* a toujours lieu afin de notifier la progression le cas échéant.


#### Timers d'exception

Lorsque ces timers expirent, un événement d'exception à lieu et on passe à l'état *handleException*.

waitingResponseTimer:
  : détermine le temps maximal d'attente de réception d'un message.

peerPingTimer:
  : de valeur supérieure pingTimer, ce timer compte le temps depuis la dernière réception du message *Ping*.

downloadTimer:
  : mesure la fréquence à laquelle des message DownloadProgress doivent être envoyés, si nécessaire

### Variables

Lors de l'exécution quelques variables *globales* maintient des information de synchronisation

newerBlocks:
 : cette variable représente tous les nouveaux blocks qui n'existent que localement et qui n'ont pas encore été annoncés au server. Souvent, ils résultent d'une modification du fichier effectuée par l'utilisateur (modification, ajout, suppression de fichier).

missingBlocks:
 : cette variable représente tous les nouveaux blocks qui existent chez le pair mais pas chez nous, et dont le contenu n'a pas encore été demandé par un message *Request*.


### État d'exception *handleException*

L'exécution de la machine d'état tombe dans cet état particulier lorsqu'un événement non attendu à lieu.

Quelques exemples:

  * On reçoit un message de type différent de *Hello* suite à l'envoi de notre *Hello*
  * On ne reçoit pas de réponse à notre message *Hello*

On spécifie dans notre diagramme d'états les conditions qui nous amènent dans cet état d'exception, mais on ne spécifie pas le traitement qui a lieu dans cet état.
On considère que le choix du traitement dépend de l'implémentation.


\includepdf[landscape]{rsc/StateDiagram.pdf}


### Les block et leurs états

#### Block *Initialization*

Dans ce block, le client est initialisé et essaye de joindre le pair.

**Actions initiales, exécutées sans condition**

* **useOrCreateNewClientId:** bien que pas partie du protocole, cette étape est cruciale car elle initialise, si besoin, la clé publique et le certificat à être utilisés par le client. L'identifiant du client est une information dérivée directement du certificat public.
* **Data.req(Hello):** On envoi le message *Hello* \textcolor{red}{rajouter ref chapitre class diagramme messages} au pair
* **startTimer(waitingResponseTimer)**

##### État *Waiting Hello*

Après l'envoi du message *Hello*, le client reste dans cet état jusqu'à que une de deux conditions soit remplie.

**Conditions de sortie:**

 #. **Data.ind(Hello): ** on reçoit le *Hello* du pair, on passe à l'état *Verify clientId* du prochain block
 #. **timerExpired(waitingResponseTimer) | Data.ind(msg != Hello): ** condition d'exception, a lieu si on ne reçoit pas de message dans le temps alloué (*waitingResponseTimer*) ou qu'on reçoit un message de type non attendu (*Hello*). Le client passe à l'état *handleException*


#### Block "Establish connection"

Après avoir réussit a attendre le client dans le block précédent, le client va ici essayer d'établir une connexion et échanger l'états de leurs folders.


##### État *Verify clientId*


Après avoir échangé les messages *Hello", le client va vérifier que le pair est un client connu en calculant le clientId du pair (depuis son certificat utilisé pour établir la connexion SSL) et en vérifiant que le clientId obtenu est dans la liste des pairs auxquels le client fait confiance.

Les détails concernant le maintient de la liste des clientIds connus ne fait pas partie du protocole et dépendra de l'implémentation.

**Conditions de sortie:**

 #. **knownClient:** le clientId du pair est reconnu comme valide.

    **Actions:**

    * **Data.req(ClusterConfig(Folders)):** le client envoi le message *ClusterConfig* contenant les informations des *Folders* partagés
    * **startTimer(waitingResponseTimer)**

 #. **timerExpired(waitingResponseTimer) | Data.ind(msg != Hello):** condition d'exception, a lieu si on ne reçoit pas de message dans le temps alloué (*waitingResponseTimer*) ou qu'on reçoit un message de type non attendu (*Hello*)



##### État *Waiting ClusterConfig*

Suite à l'envoi du message *Hello", le client doit atteindre la réception du message du même type de la part du pair.

**Conditions de sortie:**

  #. **Data.ind(ClusterConfig(Folders)):** on reçoit le message attendu avec les informations des *Folders* partagés

    **Actions:**

    * **Data.req(Index(Records)):** le client envoi le message *Index* contenant les informations des *Records* \textcolor{red}{ *Records* vs *blocks* ??}
    * **startTimer(waitingResponseTimer)**

 #. **timerExpired(waitingResponseTimer) | Data.ind(msg != ClusterConfig): ** condition d'exception, à lieu si on ne reçoit pas de message dans le temps alloué (*waitingResponseTimer*) ou qu'on reçoit un message de type non attendu (*ClusterConfig*)



##### État *Waiting Index*

Suite à l'envoi du message *Index", le client atteindre message *Index* du pair

**Conditions de sortie:**

  #. **Data.ind(Index(Records)):** on reçoit le message attendu avec les informations des *Records* partagés

    **Actions:**

    * **cancelTimer(waitingResponseTimer):** on n'attend plus une réponse immédiate.
    * **startTimer(pingTimer):** on veut se rappeler quand envoyer le ping au pair.
    * **startTimer(peerPingTimer):** on veut savoir quand l'attente du ping de la par du pair à expiré.
    * **updateMissingBlocks(records)):** on compare les *records* envoyés avec ceux reçus, afin de mettre à jour la variable *missingBlocks*. Ceux blocks seront demandés au pair ultérieurement.

 #. **timerExpired(waitingResponseTimer) | Data.ind(msg != Index): ** condition d'exception, à lieu si on ne reçoit pas de message dans le temps alloué (*waitingResponseTimer*) ou qu'on reçoit un message de type non attendu (*Index*)





#### Block *Main loop*

Ce block contient de la boucle d'exécution principale du programme. Dans les blocks précédents la connexion fut bien établie avec le client, et chaque pair a échangé l'état de leur *Folders* et *Records*.
Dans ce block on iterera sans fin afin de synchroniser tous les blocks qui n'existent pas chez tous les pairs dans leur version la plus récente. On sera a l'écoute aussi de nouveaux messages notifiant des nouvels records chez le pair, de demandes de *push* de blocks manquants chez le pair, de messages *Response* à nos messages *Request*, etc.


##### État *time to Ping?*

Lors de cet état on vérifie si le timer de notre *Ping* a expiré.

**Conditions de sortie:**

  #. **timerExpired(pingTimer):** il est temps d'envoyer un message *Ping*

    **Actions:**

    * **Data.req(Ping)**
    * **startTimer(pingTimer):** on veut se rappeler de quand envoyer le ping au pair.

  #. **!timerExpired(pingTimer):** on ne fait rien, on passe à l'état suivant


##### État *peer Ping missing?*

Lors de cet état on vérifie si le timer du *Ping* du pair a expiré.

**Conditions de sortie:**

  #. **!timerExpired(peerPingTimer):** on ne fait rien, on passe à l'état suivant
  #. **timerExpired(peerPingTimer):** le pair n'a pas envoyé de *Ping* dans le temps alloué, on passe à l'etat d'exception


##### État *download in progress?*

Lors de cet état on vérifie des messages *Réponse* sont encore en envoi

**Conditions de sortie:**

  #. **timerExpired(downloadTimer) & responseInProgress:** si un message *Response*  initié est toujours en envoi, on envoi un message *DownloadProgress* pour notifier le pair de l'avancement

    **Actions:**

    * **Data.req(DownloadProgress): ** envoi l'état de progrès du download
    * **startTimer(downloadTimer) **
    * **startTimer(pingTimer)**

  #. **!(timerExpired(downloadTimer) & responseInProgress):** on ne fait rien, on passe à l'état suivant


##### État *newerBlocks to notify?*

On vérifie dans cet état si notre client a des nouveaux blocks dont il doit notifié de pair.

**Conditions de sortie:**

  #. **newerBlocks:** il y a des nouveaux blocks

    **Actions:**

    * **Data.req(IndexUpdate(newerBlocks)):** on notifie le pair que des nouveaux blocks existent chez nous.
    * **newerBlocks = null:** on marque qu'il n'y a plus de newerBlocks
    * **startTimer(pingTimer)**

  #. **!newerBlocks:** on ne fait rien, on passe à l'état suivant



##### État *missingBlocks to request?*

On vérifie dans cet état si on connaît des nouveaux block chez le pair dont on a pas encore fait la demande.

**Conditions de sortie:**

  #. **missingBlocks & freeHD:** le pair a des block qu'on a pas encore et il y a suffisamment d'espace libre chez nous (client Syncthing exige 1% d'espace libre minimal)

    **Actions:**

    * **Data.req(Request(missingBlocks)):** on demande au pair de nous envoyer les blocks manquants
    * **missingBlocks = null:** on marque qu'il n'y a plus de missingBlocks
    * **startTimer(pingTimer)**

  #. **!(missingBlocks & freeH):** on ne fait rien, on passe à l'état suivant



##### État *message to handle?*

On vérifie dans cet état si un message a été reçu.

**Conditions de sortie:**

  #. **!Data.ind()** pas de message à traiter, on passe à l'état suivant

  #. **Data.ind(Request(missingBlock)):** le pair nous fait la demande de blocks qu'il n'a pas

    **Actions:**

    * **Data.req(Response(missingBlocks)):** on envoi les blocks manquants
    * **startTimer(downloadTimer):** on se rappelle de vérifier plus tard si des messages de *DownloadProgress* doivent être envoyées
    * **startTimer(pingTimer)**

  #. **Data.ind(DownloadProgress):** on reçoit la notification du progress d'un download
    **Actions:**

    * **handleDownloadProgress:** notification utilisateur ? dépend de l'implémentation


  #. **Data.ind(IndexUpdate(records)):** on reçoit la notification que des nouveaux records existent chez le pair
    **Actions:**

    * **updateMissingBlocks:** on met à jour la variable missingBlocks qui contient les blocks manquant chez nous


  #. **Data.ind(Response(blocks)):** on reçoit la réponse  à une *request* précédente
    **Actions:**

    * **saveReceivedBlocks(blocks):** on sauvegarde les nouveaux blocks reçus


  #. **Data.ind(Hello) | Data.ind(ClusterConfig) | Data.ind(Index):** on reçoit un message auquel on ne s'attend pas, on passe à l'état d'exception




##### État *messages checked*

État symbolique, atteint après la gestion d'un message reçu (ou son absence).

On boucle vers l'état initial du block *time to Ping?* sans autre condition



\newpage

## Diagramme de séquence

![Diagramme de séquence - connect to peer\label{seq1}](rsc/Seq1.png){width=50%}

Le diagramme de séquence de la figure \ref{seq1} montre les différentes échanges q8ui ont lieu lors de la phase initial de connection entre deux noeuds BEP (nommés ici *client*, et *Peer*).

Ce diagramme finit par le clock *Main loop*. Le diagramme de séquence de la figure \ref{seq2}

![Diagramme de séquence - main loop\label{seq2}](rsc/Seq2.png){width=50%}

\textcolor{red}{Commenter diagramme de séquence}



\newpage
## Diagram de classe des Messages

\includepdf[landscape]{rsc/classdiagram.pdf}

# Bep client

Nous avons implémenté une partie du protocole BEP dans un client nommé *Bep client* qui offre quesques fonctionalitées de base BEP.
Ces fonctionalitées sont disponibles en tant que executable en ligne de commandes, mais aussi en tant que librairie. Cette dernière pourrait être utilisée par une application souhaitant communiquer avec un server BEP sans avoir à re-implémenter le protocole.

L'énnoncé établi quelques limitations:
 * la synchronisation se fait avec un seul noeud Syncthing.
 * on suppose qu'on connaît  l'IP du noeud Syncthing, on ne fera pas de découvert dele protocole Global/Local Discovery


## Class diagramme

![bep client](rsc/bepclient.png)

\textcolor{red}{faire class diagram du client}


## Usage

\textcolor{red}{coller le help du programme, exempliquer }

### Examples


\textcolor{red}{Donner des exemples d'utilisation}

# Références

[^1]: @syncthing
[^2]: @bep