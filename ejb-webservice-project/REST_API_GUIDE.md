# 🚀 API REST - Guide d'utilisation Postman

## 📍 URL de base
```
http://localhost:8080/vie-webservice/api/vies
```

---

## 📋 Endpoints disponibles

### 1️⃣ **GET /api/vies** - Récupérer toutes les vies

**URL** : `http://localhost:8080/vie-webservice/api/vies`  
**Méthode** : GET  
**Headers** : Aucun requis  

**Réponse (200 OK)** :
```json
[
  {
    "lid": 1,
    "libelle": "Vie Standard",
    "nombreVieInitiale": 3
  },
  {
    "lid": 2,
    "libelle": "Vie Bonus",
    "nombreVieInitiale": 5
  },
  {
    "lid": 3,
    "libelle": "Vie Extra",
    "nombreVieInitiale": 10
  }
]
```

---

### 2️⃣ **GET /api/vies/{id}** - Récupérer une vie par ID

**URL** : `http://localhost:8080/vie-webservice/api/vies/1`  
**Méthode** : GET  
**Headers** : Aucun requis  

**Réponse (200 OK)** :
```json
{
  "lid": 1,
  "libelle": "Vie Standard",
  "nombreVieInitiale": 3
}
```

**Réponse (404 NOT FOUND)** :
```json
{
  "error": "Vie non trouvée avec l'ID: 99"
}
```

---

### 3️⃣ **POST /api/vies** - Créer une nouvelle vie

**URL** : `http://localhost:8080/vie-webservice/api/vies`  
**Méthode** : POST  
**Headers** :
- `Content-Type: application/json`

**Body (JSON)** :
```json
{
  "libelle": "Vie Premium",
  "nombreVieInitiale": 50
}
```

**Réponse (201 CREATED)** :
```json
{
  "lid": 4,
  "libelle": "Vie Premium",
  "nombreVieInitiale": 50
}
```

---

### 4️⃣ **PUT /api/vies/{id}** - Mettre à jour une vie

**URL** : `http://localhost:8080/vie-webservice/api/vies/1`  
**Méthode** : PUT  
**Headers** :
- `Content-Type: application/json`

**Body (JSON)** :
```json
{
  "libelle": "Vie Standard Modifiée",
  "nombreVieInitiale": 10
}
```

**Réponse (200 OK)** :
```json
{
  "lid": 1,
  "libelle": "Vie Standard Modifiée",
  "nombreVieInitiale": 10
}
```

---

### 5️⃣ **DELETE /api/vies/{id}** - Supprimer une vie

**URL** : `http://localhost:8080/vie-webservice/api/vies/1`  
**Méthode** : DELETE  
**Headers** : Aucun requis  

**Réponse (200 OK)** :
```json
{
  "message": "Vie supprimée avec succès"
}
```

**Réponse (404 NOT FOUND)** :
```json
{
  "error": "Vie non trouvée avec l'ID: 99"
}
```

---

### 6️⃣ **GET /api/vies/count** - Compter les vies

**URL** : `http://localhost:8080/vie-webservice/api/vies/count`  
**Méthode** : GET  
**Headers** : Aucun requis  

**Réponse (200 OK)** :
```json
{
  "count": 3
}
```

---

## 🎯 Comment tester dans Postman

### Configuration rapide :

1. **Ouvrir Postman**
2. **Créer une nouvelle requête**
3. **Sélectionner la méthode** (GET, POST, PUT, DELETE)
4. **Entrer l'URL complète**
5. Pour POST/PUT : 
   - Aller dans l'onglet **Body**
   - Sélectionner **raw**
   - Choisir **JSON** dans le menu déroulant
   - Coller le JSON

---

## 📝 Exemples de test complets

### Test 1 : Lister toutes les vies
```
GET http://localhost:8080/vie-webservice/api/vies
```

### Test 2 : Créer une nouvelle vie
```
POST http://localhost:8080/vie-webservice/api/vies
Content-Type: application/json

{
  "libelle": "Vie Test",
  "nombreVieInitiale": 25
}
```

### Test 3 : Récupérer la vie créée (ID = 4)
```
GET http://localhost:8080/vie-webservice/api/vies/4
```

### Test 4 : Modifier la vie
```
PUT http://localhost:8080/vie-webservice/api/vies/4
Content-Type: application/json

{
  "libelle": "Vie Test Modifiée",
  "nombreVieInitiale": 30
}
```

### Test 5 : Compter les vies
```
GET http://localhost:8080/vie-webservice/api/vies/count
```

### Test 6 : Supprimer la vie
```
DELETE http://localhost:8080/vie-webservice/api/vies/4
```

---

## 🔥 Collection Postman prête à l'emploi

### Import rapide dans Postman :

1. Créer une **nouvelle collection** nommée "Vie REST API"
2. Ajouter ces 6 requêtes avec les configurations ci-dessus
3. Sauvegarder la collection pour réutilisation

---

## ✅ Codes de statut HTTP

| Code | Signification |
|------|--------------|
| 200 | OK - Succès |
| 201 | Created - Ressource créée |
| 400 | Bad Request - Données invalides |
| 404 | Not Found - Ressource non trouvée |
| 500 | Internal Server Error - Erreur serveur |

---

## 💡 Avantages de REST vs SOAP

✅ **Plus simple** - Pas de XML complexe  
✅ **Format JSON** - Plus lisible et léger  
✅ **URLs intuitives** - `/api/vies/1` au lieu de SOAP envelope  
✅ **Méthodes HTTP standard** - GET, POST, PUT, DELETE  
✅ **Facile à tester** - Directement dans le navigateur pour GET  

---

## 🌐 Test rapide dans le navigateur

Vous pouvez tester les requêtes GET directement dans votre navigateur :

- http://localhost:8080/vie-webservice/api/vies
- http://localhost:8080/vie-webservice/api/vies/1
- http://localhost:8080/vie-webservice/api/vies/count
