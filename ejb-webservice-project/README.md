# Vie Web Service - Application EJB avec MySQL

Application Java EE complète avec EJB, Web Service SOAP et MySQL, déployée avec Docker.

## 🏗️ Architecture

- **Backend**: Java EE 8 (EJB 3.2, JPA 2.2, JAX-WS)
- **Serveur d'application**: WildFly 26
- **Base de données**: MySQL 8.0
- **Conteneurisation**: Docker & Docker Compose

## 📁 Structure du projet

```
ejb-webservice-project/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/vie/
│   │   │       ├── entity/
│   │   │       │   └── Vie.java              # Entité JPA
│   │   │       ├── service/
│   │   │       │   ├── VieServiceRemote.java # Interface EJB Remote
│   │   │       │   └── VieServiceBean.java   # Implémentation EJB
│   │   │       └── ws/
│   │   │           ├── VieDTO.java           # Data Transfer Object
│   │   │           └── VieWebService.java    # Web Service SOAP
│   │   ├── resources/
│   │   │   └── META-INF/
│   │   │       └── persistence.xml           # Configuration JPA
│   │   └── webapp/
│   │       ├── WEB-INF/
│   │       │   └── web.xml
│   │       └── index.html
├── Dockerfile                                 # Image WildFly personnalisée
├── docker-compose.yml                         # Orchestration des services
├── module.xml                                 # Module MySQL pour WildFly
├── configure-wildfly.cli                      # Configuration automatique
├── init.sql                                   # Script d'initialisation DB
└── pom.xml                                    # Dépendances Maven
```

## 🚀 Démarrage rapide

### Prérequis
- Docker
- Docker Compose
- Maven (pour le build local)

### 1. Build de l'application

```bash
cd ejb-webservice-project
mvn clean package
```

### 2. Lancement avec Docker Compose

```bash
docker-compose up --build
```

### 3. Vérification

L'application sera accessible à :
- **Application**: http://localhost:8080/vie-webservice/
- **WSDL**: http://localhost:8080/vie-webservice/VieWebService?wsdl
- **MySQL**: localhost:3306

## 📡 API Web Service

### Opérations disponibles

1. **createVie** - Créer une nouvelle Vie
   - Paramètres: `libelle` (String), `nombreVieInitiale` (Integer)
   - Retour: `VieDTO`

2. **getVieById** - Récupérer une Vie
   - Paramètres: `id` (Long)
   - Retour: `VieDTO`

3. **getAllVies** - Lister toutes les Vies
   - Paramètres: Aucun
   - Retour: `List<VieDTO>`

4. **updateVie** - Mettre à jour une Vie
   - Paramètres: `id` (Long), `libelle` (String), `nombreVieInitiale` (Integer)
   - Retour: `VieDTO`

5. **deleteVie** - Supprimer une Vie
   - Paramètres: `id` (Long)
   - Retour: `boolean`

6. **countVies** - Compter les Vies
   - Paramètres: Aucun
   - Retour: `long`

## 🧪 Test avec Postman

### Méthode 1: Import du WSDL
1. Ouvrir Postman
2. File > Import > Link
3. Entrer l'URL: `http://localhost:8080/vie-webservice/VieWebService?wsdl`
4. Importer les opérations SOAP

### Méthode 2: Requête manuelle

**Endpoint**: `http://localhost:8080/vie-webservice/VieWebService`

**Exemple - Créer une Vie**:
```xml
POST /vie-webservice/VieWebService HTTP/1.1
Host: localhost:8080
Content-Type: text/xml; charset=utf-8
SOAPAction: ""

<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:vie="http://ws.vie.com/">
  <soap:Body>
    <vie:createVie>
      <libelle>Vie Test</libelle>
      <nombreVieInitiale>7</nombreVieInitiale>
    </vie:createVie>
  </soap:Body>
</soap:Envelope>
```

**Exemple - Récupérer toutes les Vies**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:vie="http://ws.vie.com/">
  <soap:Body>
    <vie:getAllVies/>
  </soap:Body>
</soap:Envelope>
```

## 🗄️ Base de données

### Configuration
- **Host**: mysql (dans Docker) / localhost (externe)
- **Port**: 3306
- **Database**: viedb
- **User**: vieuser
- **Password**: viepassword

### Schema
```sql
CREATE TABLE Vie (
    lid BIGINT PRIMARY KEY AUTO_INCREMENT,
    libelle VARCHAR(100) NOT NULL,
    nombreVieInitiale INT
);
```

### Données de test
Le script `init.sql` insère automatiquement 3 enregistrements au démarrage.

## ⚙️ Configuration

### Réinitialisation automatique (Développement)

Par défaut, les tables sont recréées à chaque démarrage grâce à :
```xml
<!-- Dans persistence.xml -->
<property name="hibernate.hbm2ddl.auto" value="update"/>
```

### Production

Pour la production, **commentez** la ligne ci-dessus dans `persistence.xml`:
```xml
<!-- <property name="hibernate.hbm2ddl.auto" value="update"/> -->
```

Ou changez la valeur en `validate` ou `none`.

## 🔧 Commandes utiles

### Docker

```bash
# Démarrer les services
docker-compose up -d

# Voir les logs
docker-compose logs -f wildfly
docker-compose logs -f mysql

# Arrêter les services
docker-compose down

# Arrêter et supprimer les volumes (reset complet)
docker-compose down -v

# Rebuild après modifications
docker-compose up --build --force-recreate
```

### Maven

```bash
# Build
mvn clean package

# Skip tests
mvn clean package -DskipTests

# Clean
mvn clean
```

## 🐛 Troubleshooting

### Le Web Service n'est pas accessible
- Vérifier que WildFly est démarré: `docker-compose logs wildfly`
- Attendre 30-60 secondes après le démarrage
- Vérifier l'URL: http://localhost:8080/vie-webservice/VieWebService?wsdl

### Erreur de connexion à MySQL
- Vérifier que MySQL est healthy: `docker-compose ps`
- Vérifier les logs: `docker-compose logs mysql`
- Attendre que le healthcheck passe au vert

### L'application ne démarre pas
- Vérifier que le WAR est bien buildé: `ls -lh target/vie-webservice.war`
- Rebuild l'image: `docker-compose up --build`
- Vérifier les logs WildFly pour les erreurs de déploiement

## 📊 Monitoring

### WildFly Admin Console
- URL: http://localhost:9990
- Pour activer, créer un utilisateur admin:
  ```bash
  docker exec -it vie-wildfly /opt/jboss/wildfly/bin/add-user.sh
  ```

### MySQL
```bash
# Se connecter à MySQL
docker exec -it vie-mysql mysql -u vieuser -pviepassword viedb

# Voir les données
mysql> SELECT * FROM Vie;
```

## 🔐 Sécurité

### Pour la production:
1. Changer les mots de passe dans `docker-compose.yml`
2. Utiliser des secrets Docker ou variables d'environnement
3. Activer HTTPS sur WildFly
4. Restreindre l'accès à la console d'administration
5. Configurer un firewall

## 📝 Licence

Projet éducatif - ITU S5

## 👨‍💻 Auteur

Antonio - ITU S5 - mr-tahina
