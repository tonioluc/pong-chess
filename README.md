
# Guide d'installation et d'exécution (déploiement sur une autre machine)

Objectif
--------
Ce document explique clairement et pas-à-pas comment exécuter le projet sur une machine différente (prérequis, build, lancement des services et des clients).

Prérequis
---------
- Docker & Docker Compose (v2+) installés
- Maven (commande `mvn` disponible)
- Python 3.x installé

Étapes pour démarrer le projet (single-machine)
-----------------------------------------------
1. Construire l'application Java (génère le WAR) :

```bash
cd ejb-webservice-project
mvn clean package
```

2. Démarrer les services backend (MySQL + WildFly) :

```bash
docker compose up --build
```

Notes:
- Le conteneur MySQL exécutera `ejb-webservice-project/init.sql` lors de la première initialisation pour créer la base `viedb` et insérer les valeurs par défaut.
- Le script `ejb-webservice-project/configure-wildfly.cli` configure le driver JDBC et la datasource. Il est conçu pour être idempotent afin d'éviter des erreurs de type "Duplicate resource" lors de redémarrages.

3. Dans un nouveau terminal (toujours sur la même machine), lancer le serveur du jeu Python :

```bash
# depuis la racine du projet
python3 server.py
```

4. Lancer le client en mode local (test rapide et rendu) :

```bash
cd client
python3 client.py --mode local
```

Mode réseau (serveur et clients sur des machines séparées)
-------------------------------------------------------
1. Sur la machine serveur (hébergeant WildFly + MySQL + `server.py`), suivez les étapes 1–3 ci‑dessus.
2. Sur chaque machine cliente, ouvrez `client/config.py` et modifiez la variable `SERVER_HOST` pour qu'elle contienne l'adresse IP de la machine serveur (où `server.py` tourne). Ne modifiez pas `config.py` sur la machine qui exécute le serveur.
3. Lancez le client en mode réseau :

```bash
cd client
python3 client.py --mode network
```

Remarques & dépannage rapide
----------------------------
- Si WildFly échoue avec `WFLYCTL0212: Duplicate resource`, n'exécutez pas systématiquement `docker compose down -v` — la configuration a été rendue idempotente. En dernier recours pour réinitialiser complètement la base de données :

```bash
docker compose down -v
docker compose up --build
```

- Si le client réseau ne parvient pas à se connecter : vérifiez que
  - `server.py` est démarré et écoute (par défaut port `9999`),
  - le pare-feu sur la machine serveur autorise le port `9999`,
  - `client/config.py` contient la bonne IP (`SERVER_HOST`).

- Pour forcer une ré-initialisation des données MySQL (perd toutes les données), supprimez le volume MySQL :

```bash
docker compose down -v
```

Fichiers importants
-------------------
- `ejb-webservice-project/`: code Java (Maven), `Dockerfile`, `docker-compose.yml`, `configure-wildfly.cli`, `init.sql`.
- `server.py`: serveur de jeu Python (autorité de jeu et interface vers l'API REST).
- `client/`: code client (Tkinter) — `client/client.py`, `client/config.py`, `client/renderer.py`.

Support
-------
Pour aider quelqu'un à reproduire l'environnement, fournir :
- versions de Docker, Maven et Python
- logs pertinents (`docker compose logs`, sortie de `server.py`)

