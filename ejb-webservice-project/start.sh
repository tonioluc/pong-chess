#!/bin/bash

# Script de démarrage rapide pour l'application Vie Web Service

echo "=================================="
echo "  Vie Web Service - Démarrage"
echo "=================================="
echo ""

# Vérifier si Docker est installé
# if ! command -v docker &> /dev/null; then
#     echo "❌ Docker n'est pas installé. Veuillez installer Docker d'abord."
#     exit 1
# fi

# Vérifier si Docker Compose est installé
# if ! command -v docker compose &> /dev/null; then
#     echo "❌ Docker Compose n'est pas installé. Veuillez installer Docker Compose d'abord."
#     exit 1
# fi

echo "✅ Docker et Docker Compose sont installés"
echo ""

# Build Maven si le WAR n'existe pas
if [ ! -f "target/vie-webservice.war" ]; then
    echo "📦 Build de l'application avec Maven..."
    
    if command -v mvn &> /dev/null; then
        mvn clean package
        if [ $? -ne 0 ]; then
            echo "❌ Erreur lors du build Maven"
            exit 1
        fi
    else
        echo "⚠️  Maven n'est pas installé. Tentative de build avec Docker..."
        docker run -it --rm \
            -v "$(pwd)":/usr/src/app \
            -w /usr/src/app \
            maven:3.8.6-openjdk-11 \
            mvn clean package
        
        if [ $? -ne 0 ]; then
            echo "❌ Erreur lors du build Maven avec Docker"
            exit 1
        fi
    fi
    echo "✅ Build Maven réussi"
else
    echo "✅ Le fichier WAR existe déjà"
fi

echo ""
echo "🚀 Démarrage des conteneurs Docker..."
docker compose up --build -d

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du démarrage des conteneurs"
    exit 1
fi

echo ""
echo "⏳ Attente du démarrage des services (cela peut prendre 30-60 secondes)..."
sleep 10

# Attendre que MySQL soit prêt
echo "⏳ Vérification de MySQL..."
for i in {1..30}; do
    if docker compose exec -T mysql mysqladmin ping -h localhost -u root -prootpassword &> /dev/null; then
        echo "✅ MySQL est prêt"
        break
    fi
    echo "   Attente de MySQL... ($i/30)"
    sleep 2
done

echo ""
echo "⏳ Vérification de WildFly..."
sleep 15

# Vérifier si WildFly répond
for i in {1..20}; do
    if curl -s http://localhost:8080 &> /dev/null; then
        echo "✅ WildFly est prêt"
        break
    fi
    echo "   Attente de WildFly... ($i/20)"
    sleep 3
done

echo ""
echo "=================================="
echo "  ✅ Démarrage terminé !"
echo "=================================="
echo ""
echo "📡 Liens utiles:"
echo "   - Application: http://localhost:8080/vie-webservice/"
echo "   - WSDL: http://localhost:8080/vie-webservice/VieWebService?wsdl"
echo ""
echo "🔧 Commandes utiles:"
echo "   - Voir les logs: docker compose logs -f wildfly"
echo "   - Arrêter: docker compose down"
echo "   - Redémarrer: docker compose restart"
echo ""
echo "📝 Consultez le README.md pour plus d'informations"
echo ""
