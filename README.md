# LingueeLike

Un moteur de recherche bilingue (EN ↔ FR) inspiré de Linguee.
Recherchez un mot ou une expression et retrouvez sa traduction en contexte, extraite de livres bilingues alignés.

---

## Comment ça fonctionne

Le système est construit autour de trois couches :

**1. Couche données (SQLite + OpenSearch)**
Les paires de phrases EN/FR alignées sont stockées dans SQLite et indexées dans OpenSearch.
Chaque phrase est reliée à sa traduction via un identifiant d'alignement bidirectionnel.

**2. Couche recherche (requête OpenSearch hybride)**
Les requêtes combinent deux stratégies :

- `match_phrase` (boost ×4) — correspondance exacte ou quasi-exacte pour une haute précision
- `multi_match best_fields` (fuzziness AUTO) — correspondance de mots approximative pour un large rappel

Le filtre restreint les résultats à la langue et au livre corrects, puis trie par score de pertinence.

**3. Couche mise en évidence (pipeline NLP)**
Une fois la phrase source et sa traduction récupérées, le système met en évidence le ou les mots correspondants dans la traduction grâce à :

- Un index de traductions de mots basé sur la co-occurrence (coefficient de Dice, construit à l'import)
- Un alignement positionnel en secours pour les mots absents du dictionnaire
- Un filtrage des mots vides et une détection des mots composés (ex. `soul` → `soul-winning`)

---

## Architecture

```
linguee_like/
├── backend/
│   ├── app/
│   │   ├── main.py                   # Point d'entrée FastAPI
│   │   ├── api/
│   │   │   └── dictionary.py         # Endpoint /search
│   │   ├── core/
│   │   │   └── config.py             # Paramètres (DB, OpenSearch)
│   │   ├── db/
│   │   │   ├── models.py             # Book, Segment, Alignment, WordTranslation, StemForm
│   │   │   └── database.py           # Session SQLAlchemy
│   │   ├── nlp/
│   │   │   ├── highlighter.py        # Mise en évidence des traductions
│   │   │   ├── stemmer.py            # Racinisation EN/FR + mots vides
│   │   │   └── indexer.py            # Construction de l'index de co-occurrence WordTranslation
│   │   ├── scripts/
│   │   │   └── import_md.py          # Pipeline d'import CSV
│   │   ├── search/
│   │   │   ├── client.py             # Client OpenSearch singleton
│   │   │   └── index.py              # Mapping de l'index + helpers création/suppression
│   │   └── templates/
│   │       └── search.html           # Interface de recherche (Tailwind CSS)
│   ├── scripts/
│   │   └── align_books.py            # Extrait les paires alignées des livres markdown
│   ├── index_csv_opensearch.py       # Indexation du CSV dans OpenSearch
│   └── import_md_runner.py           # Import du CSV dans SQLite
│
├── data/
│   └── books/
│       ├── aligned_book.csv                                     # Paires de phrases EN/FR alignées
│       ├── thirty-six-reasons-for-winning-the-lost_interior.md  # Livre source EN
│       └── trente-six-raisons-de-gagner-les-perdus_interieur.md # Livre source FR
└── README.md
```

---

## Modèle de données

| Table               | Description                                                            |
| ------------------- | ---------------------------------------------------------------------- |
| `books`             | Un enregistrement par version linguistique du livre (EN + FR)          |
| `segments`          | Une phrase par ligne, liée à un livre                                  |
| `alignments`        | Associe un segment EN à sa traduction FR                               |
| `word_translations` | Scores de traduction de mots par co-occurrence (coefficient de Dice)   |
| `stem_forms`        | Associe les racines à leurs formes de surface pour la mise en évidence |

OpenSearch reflète les segments avec la structure de document suivante :

```json
{
  "segment_id": 1,
  "book_id": 1,
  "position": 1,
  "lang": "en",
  "text": "The Lord Jesus came to seek and to save the lost.",
  "text_normalized": "the lord jesus came to seek and to save the lost.",
  "aligned_id": 2
}
```

`aligned_id` pointe vers l'identifiant du document de traduction dans le même index (`fr-2` dans l'exemple ci-dessus).

---

## Installation

### Prérequis

- Python 3.11+
- Docker (pour OpenSearch)

### 1. Cloner le projet

```bash
git clone <url>
cd linguee_like
```

### 2. Démarrer OpenSearch

```bash
docker compose up -d
```

Attendez quelques secondes puis vérifiez : `curl http://localhost:9200`

### 3. Configurer l'environnement Python

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
```

### 4. Initialiser la base de données

```bash
python data/scripts/init_db.py
```

### 5. Importer le livre dans SQLite

```bash
python import_md_runner.py
```

Cela crée les livres, segments, alignements et l'index de traduction de mots.

### 6. Indexer dans OpenSearch

Créer d'abord l'index :

```bash
python -c "from app.search.index import create_index; create_index()"
```

Puis indexer le CSV :

```bash
python index_csv_opensearch.py
```

### 7. Lancer l'API

```bash
uvicorn app.main:app --reload
```

Ouvrez `http://localhost:8000` dans votre navigateur.

---

## Ajouter un nouveau livre

1. Ajoutez le CSV aligné dans `data/books/` (colonnes : `en`, `fr`)
2. Modifiez `import_md_runner.py` avec les métadonnées du nouveau livre et exécutez-le
3. Relancez `index_csv_opensearch.py` pour indexer dans OpenSearch

Pour générer un CSV aligné à partir d'une paire de fichiers markdown, exécutez :

```bash
python scripts/align_books.py
```

---

## API

### `GET /search`

| Paramètre | Type          | Défaut      | Description                    |
| --------- | ------------- | ----------- | ------------------------------ |
| `q`       | string        | obligatoire | Mot ou expression à rechercher |
| `lang`    | `en` ou `fr`  | `en`        | Langue source                  |
| `limit`   | entier        | 20          | Nombre maximum de résultats    |

**Exemple de réponse :**

```json
{
  "query": "Lord",
  "lang": "en",
  "count": 3,
  "results": [
    {
      "segment_id": 1,
      "book_id": 1,
      "book_title": "Thirty Six Reasons for Winning the Lost (EN)",
      "language": "en",
      "text": "The Lord Jesus came to seek and to save the lost.",
      "alignment_text": "Le Seigneur Jésus est venu chercher et sauver les perdus.",
      "alignment_language": "fr",
      "alignment_id": 2,
      "alignment_highlights": ["Seigneur"]
    }
  ]
}
```

`alignment_highlights` contient le ou les mots dans la traduction qui correspondent à la requête de recherche.

---

## Qualité de la recherche

| Requête   | Phrase source                        | Traduction                               | Mot mis en évidence |
| --------- | ------------------------------------ | ---------------------------------------- | ------------------- |
| `Lord`    | The **Lord** Jesus came...           | Le **Seigneur** Jésus est venu...        | Seigneur            |
| `soul`    | A **soul**-winning church...         | Une église qui gagne les **âmes**...     | âmes                |
| `church`  | A soul-winning **church**...         | Une **église** qui gagne...              | église              |
| `perdus`  | ...sauver les **perdus**             | ...to save the **lost**                  | lost                |

La recherche bascule automatiquement sur SQLite ILIKE si OpenSearch est indisponible.
