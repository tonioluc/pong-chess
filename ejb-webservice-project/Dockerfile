FROM quay.io/wildfly/wildfly:latest

# Informations du mainteneur
LABEL maintainer="Antonio"
LABEL description="Application EJB Vie Web Service avec WildFly"

# Variables d'environnement
ENV WILDFLY_HOME /opt/jboss/wildfly
ENV DEPLOYMENT_DIR ${WILDFLY_HOME}/standalone/deployments
ENV CONFIGURATION_DIR ${WILDFLY_HOME}/standalone/configuration

# Passer en utilisateur root pour les installations
USER root

# Créer le répertoire pour le module MySQL
RUN mkdir -p ${WILDFLY_HOME}/modules/com/mysql/main

# Télécharger le driver MySQL
COPY --chown=jboss:jboss mysql-connector-java-8.0.18.jar ${WILDFLY_HOME}/modules/com/mysql/main/

# Copier le fichier de configuration du module MySQL
COPY --chown=jboss:jboss module.xml ${WILDFLY_HOME}/modules/com/mysql/main/

# Copier les scripts de configuration
COPY --chown=jboss:jboss configure-wildfly.cli ${WILDFLY_HOME}/

# Retourner à l'utilisateur jboss
USER jboss

# Copier l'application WAR
COPY --chown=jboss:jboss target/vie-webservice.war ${DEPLOYMENT_DIR}/

# Exposer les ports
# 8080: HTTP
# 9990: Administration Console
EXPOSE 8080 9990

RUN mkdir -p /opt/jboss/wildfly/standalone/log && chmod -R 755 /opt/jboss/wildfly/standalone/log
# Démarrer WildFly avec la configuration
CMD ["/bin/bash", "-c", "${WILDFLY_HOME}/bin/standalone.sh -b 0.0.0.0 -bmanagement 0.0.0.0 --debug *:8787"]
