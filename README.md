
# Pong Chess (Pong-Échecs)

Petit jeu hybride « Pong » / « Échecs » en Python (Tkinter). Deux joueurs contrôlent chacun une barre et doivent lancer une balle parmi des pions inspirés des pièces d'échecs. Le jeu supporte un mode local et un mode réseau (serveur + 2 clients).

## Résumé rapide
- Langage : Python 3
- UI : Tkinter (canvas)
- Communication réseau : sockets TCP (JSON par ligne)

## Fonctionnalités
- Mode `local` : tout en un, pour tester rapidement
- Mode `network` : serveur dédié + deux clients connectés
- Choix de la trajectoire initiale par le joueur 1 (flèche, gauche/droite + Entrée)
- Dimensions : possibilité de réduire la zone active via la variable d'environnement `EXTRA_DIMENSIONS` (2,4,6,8)
- Collisions multi-pièces : la balle peut endommager plusieurs pièces en un même impact

## Prérequis
- Python 3.8+ installé (Ubuntu : `sudo apt install python3 python3-tk`)

## Fichiers importants
- `server.py` : boucle serveur / autorité de jeu
- `client/client.py` : client Tkinter (mode `local` ou `network`)
- `game.py` : logique du jeu, collisions, génération de plateaux réduits
- `client/renderer.py` : rendu canvas
- `entities/` : `ball.py`, `paddle.py` et autres entités

## Installation / exécution

Ouvrez un terminal dans le dossier du projet (exemple : `$HOME/Bureau/S5/mr-tahina/pong-chess`)

### Mode local (test rapide, tout en un)
```bash
python3 ./client/client.py --mode local
```

### Mode réseau (serveur et clients séparés)

Lancer le serveur :
```bash
python3 ./server.py
```

Lancer deux clients (sur la même machine ou depuis d'autres machines pointant sur l'IP du serveur) :
```bash
python3 ./client/client.py --mode network
```

## Contrôles
- Joueur 1 (haut) : touches `A` / `D` (ou Flèche gauche / droite)
- Joueur 2 (bas) : touches Flèche gauche / Flèche droite
- Au début d'une partie, le Joueur 1 choisit la trajectoire initiale :
	- utiliser Gauche / Droite pour orienter la flèche
	- appuyer sur `Entrée` pour lancer la balle

## Paramètres et options
- Pour réduire le nombre de colonnes actives (2,4,6,8) :
```bash
export EXTRA_DIMENSIONS=4
python3 ./client/client.py --mode local
```

## Optimisations réseau
- Le serveur et les clients désactivent Nagle (`TCP_NODELAY`) et augmentent les buffers socket pour réduire la latence sur petits paquets.
- Si vous constatez encore des lags, réduire `FRAME_RATE` dans `server.py` (par défaut 20.0) peut aider à diminuer la charge réseau.

## Dépannage
- Si la balle ne part pas après avoir pressé `Entrée` :
	- En mode `local`, vérifiez la console du client : elle doit afficher `Local: player 1 chose trajectory: <angle>` puis `Ball trajectory chosen by player 1: <angle> ...`.
	- En mode `network`, vérifiez les logs du serveur pour confirmer la réception du contrôle `trajectory` et son application.
- Si un client ne se connecte pas, vérifiez l'adresse/port (`config.py` dans `client/` contient `SERVER_HOST` et `SERVER_PORT`).

## Contribuer
- Le code est volontairement simple et conçu pour être modifié. Proposez des améliorations via des commits ou ouvrez des issues.

## Licence
- Code fourni tel quel (pas de licence explicite). Utilisez-le et modifiez-le selon vos besoins.

## Améliorations possibles
- Interpolation client-side pour des updates serveur moins fréquentes
- Passage à UDP ou messages différentiels pour réduire la bande passante
- Interface utilisateur plus complète (HP, scores détaillés, menu)

---
Pour toute question ou suggestion, ouvrez une issue ou contactez l’auteur.

Optimisations réseau
---------------------
- Le serveur et les clients désactivent Nagle (`TCP_NODELAY`) et augmentent les buffers socket pour réduire la latence sur petits paquets.
- Si vous constatez encore des lags, réduire `FRAME_RATE` dans `server.py` (par défaut 20.0) peut aider à diminuer la charge réseau.

Dépannage
---------
- Si la balle ne part pas après avoir pressé `Entrée` :
	- En mode `local`, vérifiez la console du client : elle doit afficher `Local: player 1 chose trajectory: <angle>` puis `Ball trajectory chosen by player 1: <angle> ...`.
	- En mode `network`, vérifiez les logs du serveur pour confirmer la réception du contrôle `trajectory` et son application.
- Si un client ne se connecte pas, vérifiez l'adresse/port (`config.py` dans `client/` contient `SERVER_HOST` et `SERVER_PORT`).

Contribuer
---------
- Le code est volontairement simple et conçu pour être modifié. Proposez des améliorations via des commits ou ouvrez des issues.

Licence
-------
- Code fourni tel quel (pas de licence explicite). Utilisez-le et modifiez-le selon vos besoins.

Améliorations possibles
----------------------
- Interpolation client-side pour des updates serveur moins fréquentes
- Passage à UDP ou messages différentiels pour réduire la bande passante
- Interface utilisateur plus complète (HP, scores détaillés, menu)

Si vous voulez, je peux ajouter des instructions de test automatique ou un petit script pour lancer serveur+2 clients en local.
