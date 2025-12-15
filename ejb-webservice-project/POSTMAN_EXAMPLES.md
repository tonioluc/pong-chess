# Collection Postman pour tester le Web Service Vie

## Exemples de requêtes SOAP

### 1. Créer une Vie

**Méthode**: POST
**URL**: `http://localhost:8080/vie-webservice/VieWebService`
**Headers**:
- Content-Type: `text/xml; charset=utf-8`
- SOAPAction: `""`

**Body (XML)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:vie="http://ws.vie.com/">
  <soap:Body>
    <vie:createVie>
      <libelle>Vie Ultimate</libelle>
      <nombreVieInitiale>99</nombreVieInitiale>
    </vie:createVie>
  </soap:Body>
</soap:Envelope>
```

---

### 2. Récupérer toutes les Vies

**Méthode**: POST
**URL**: `http://localhost:8080/vie-webservice/VieWebService`
**Headers**:
- Content-Type: `text/xml; charset=utf-8`
- SOAPAction: `""`

**Body (XML)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:vie="http://ws.vie.com/">
  <soap:Body>
    <vie:getAllVies/>
  </soap:Body>
</soap:Envelope>
```

---

### 3. Récupérer une Vie par ID

**Méthode**: POST
**URL**: `http://localhost:8080/vie-webservice/VieWebService`
**Headers**:
- Content-Type: `text/xml; charset=utf-8`
- SOAPAction: `""`

**Body (XML)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:vie="http://ws.vie.com/">
  <soap:Body>
    <vie:getVieById>
      <id>1</id>
    </vie:getVieById>
  </soap:Body>
</soap:Envelope>
```

---

### 4. Mettre à jour une Vie

**Méthode**: POST
**URL**: `http://localhost:8080/vie-webservice/VieWebService`
**Headers**:
- Content-Type: `text/xml; charset=utf-8`
- SOAPAction: `""`

**Body (XML)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:vie="http://ws.vie.com/">
  <soap:Body>
    <vie:updateVie>
      <id>1</id>
      <libelle>Vie Modifiée</libelle>
      <nombreVieInitiale>15</nombreVieInitiale>
    </vie:updateVie>
  </soap:Body>
</soap:Envelope>
```

---

### 5. Supprimer une Vie

**Méthode**: POST
**URL**: `http://localhost:8080/vie-webservice/VieWebService`
**Headers**:
- Content-Type: `text/xml; charset=utf-8`
- SOAPAction: `""`

**Body (XML)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:vie="http://ws.vie.com/">
  <soap:Body>
    <vie:deleteVie>
      <id>1</id>
    </vie:deleteVie>
  </soap:Body>
</soap:Envelope>
```

---

### 6. Compter les Vies

**Méthode**: POST
**URL**: `http://localhost:8080/vie-webservice/VieWebService`
**Headers**:
- Content-Type: `text/xml; charset=utf-8`
- SOAPAction: `""`

**Body (XML)**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:vie="http://ws.vie.com/">
  <soap:Body>
    <vie:countVies/>
  </soap:Body>
</soap:Envelope>
```

---

## Import dans Postman

### Méthode 1: Import automatique du WSDL

1. Ouvrir Postman
2. Cliquer sur **Import**
3. Sélectionner l'onglet **Link**
4. Coller l'URL: `http://localhost:8080/vie-webservice/VieWebService?wsdl`
5. Cliquer sur **Continue** puis **Import**
6. Les requêtes seront automatiquement générées

### Méthode 2: Création manuelle

1. Créer une nouvelle requête POST
2. Entrer l'URL: `http://localhost:8080/vie-webservice/VieWebService`
3. Dans l'onglet **Headers**, ajouter:
   - `Content-Type: text/xml; charset=utf-8`
   - `SOAPAction: ""`
4. Dans l'onglet **Body**, sélectionner **raw** et **XML**
5. Coller le XML de la requête souhaitée

---

## Exemple de réponse

### Réponse pour getAllVies:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ns2:getAllViesResponse xmlns:ns2="http://ws.vie.com/">
      <return>
        <lid>1</lid>
        <libelle>Vie Standard</libelle>
        <nombreVieInitiale>3</nombreVieInitiale>
      </return>
      <return>
        <lid>2</lid>
        <libelle>Vie Bonus</libelle>
        <nombreVieInitiale>5</nombreVieInitiale>
      </return>
      <return>
        <lid>3</lid>
        <libelle>Vie Extra</libelle>
        <nombreVieInitiale>10</nombreVieInitiale>
      </return>
    </ns2:getAllViesResponse>
  </soap:Body>
</soap:Envelope>
```
