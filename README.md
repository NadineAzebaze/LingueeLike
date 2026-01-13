# 🌍 **Linguee‑Like – MVP**  
### *Un moteur de recherche bilingue basé sur l’alignement de phrases (EN ↔ FR)*

Ce projet est un **prototype fonctionnel** inspiré de Linguee.  
Il permet d’importer des fichiers TMX (traductions alignées), de les transformer en segments bilingues, puis de les exposer via une API pour construire un moteur de recherche bilingue.

L’objectif du MVP est simple :  
👉 **Importer un corpus bilingue et permettre de retrouver les phrases alignées.**

---

# 🧭 **Objectifs fonctionnels (pour non‑techniques)**

Ce projet répond à plusieurs besoins concrets :

### ✔ Importer des traductions existantes  
À partir d’un fichier TMX (format standard utilisé par les traducteurs), le système extrait automatiquement les phrases anglaises et françaises.

### ✔ Aligner les phrases  
Chaque phrase anglaise est reliée à sa traduction française.  
Cela permet de retrouver rapidement la phrase correspondante dans l’autre langue.

### ✔ Stocker les données proprement  
Les phrases sont organisées dans une base de données structurée, prête pour la recherche.

### ✔ Exposer une API simple  
L’API permet de :
- récupérer les phrases
- naviguer dans les alignements
- préparer une future recherche bilingue

### ✔ Préparer un futur moteur de recherche  
Le MVP pose les fondations pour :
- une interface utilisateur
- une recherche intelligente
- l’ajout de nouveaux corpus

---

# 🏗️ **Architecture technique**

```
linguee_like/
│
├── backend/
│   ├── app/
│   │   ├── main.py          → API FastAPI
│   │   ├── db/
│   │   │   ├── models.py    → Modèles SQLAlchemy (Book, Segment, Alignment)
│   │   │   ├── database.py  → Connexion DB
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── venv/                → Environnement virtuel Python
│
├── data/
│   ├── scripts/
│   │   ├── init_db.py       → Création des tables
│   │   └── import_tmx.py    → Import TMX → Segments alignés
│   └── tmx/
│       └── test.tmx         → Exemple de fichier TMX
│
└── README.md
```

---

# 🗄️ **Modèle de données**

Le projet repose sur trois entités principales :

### 📘 **Book**
Représente un document source (anglais ou français).

### 🧩 **Segment**
Une phrase extraite du document.

### 🔗 **Alignment**
Lien entre un segment anglais et son segment français correspondant.

Ce modèle permet de reconstruire un corpus bilingue aligné, comme dans Linguee.

---

# ⚙️ **Installation**

### 1. Cloner le projet

```bash
git clone <url>
cd linguee_like
```

### 2. Créer l’environnement virtuel

```bash
cd backend
python -m venv venv
venv\Scripts\activate
```

### 3. Installer les dépendances

```bash
pip install fastapi sqlalchemy uvicorn pydantic-settings
```

---

# 🛠️ **Initialiser la base de données**

Depuis la racine du projet :

```bash
python data/scripts/init_db.py
```

Cela crée les tables nécessaires.

---

# 📥 **Importer un fichier TMX**

Place ton fichier dans :

```
data/tmx/
```

Puis lance :

```bash
python data/scripts/import_tmx.py
```

Le script :
- crée deux livres (EN et FR)
- extrait les phrases
- crée les alignements

---

# 🌐 **Lancer l’API**

Depuis `backend/` :

```bash
venv\Scripts\activate
uvicorn app.main:app --reload
```

Endpoints disponibles :

- Documentation interactive :  
  👉 `http://127.0.0.1:8000/docs`  
- Page d’accueil :  
  👉 `http://127.0.0.1:8000/`

---

# 🚀 **Fonctionnalités actuelles du MVP**

### ✔ Import TMX → Segments alignés  
### ✔ Base de données structurée  
### ✔ API FastAPI opérationnelle  
### ✔ Architecture prête pour la recherche bilingue  
### ✔ Pipeline complet fonctionnel

---

# 🔮 **Prochaines étapes (Roadmap)**

### 🟦 1. Route de recherche bilingue  
Permettre de taper un mot ou une phrase et retrouver les segments alignés.

### 🟩 2. Interface utilisateur simple  
Un champ de recherche + affichage des résultats.

### 🟧 3. Import de plusieurs TMX  
Automatiser l’ingestion de corpus.

### 🟪 4. Amélioration de la qualité des alignements  
Ajout d’un score de similarité ou d’un modèle linguistique.

---

# 📝 **Résumé pour reprendre le projet plus tard**

> *Le backend est fonctionnel, la base est initialisée, les TMX sont importés en Books/Segments/Alignments, et la prochaine étape est d’ajouter la recherche bilingue.*
