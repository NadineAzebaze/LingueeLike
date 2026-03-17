# LingueeLike

Un moteur de recherche bilingue (EN ↔ FR) inspiré de Linguee.
Recherchez un mot ou une expression et retrouvez sa traduction en contexte, extraite de livres bilingues alignés.

---

## Comment ça fonctionne

Le système est construit autour de trois couches :

**1. Couche données (SQLite + OpenSearch)**
Les paires de phrases EN/FR alignées sont stockées dans SQLite et indexées dans OpenSearch.
Chaque document OpenSearch représente une **paire bilingue complète** : la phrase source ET sa traduction sont dans le même document, ce qui évite toute requête secondaire lors de la recherche.

**2. Couche recherche (requête OpenSearch hybride)**
Les requêtes combinent deux stratégies :

- `match_phrase` (boost ×4, slop=1) — correspondance exacte ou quasi-exacte pour une haute précision
- `multi_match best_fields` (fuzziness AUTO) — correspondance approximative pour un large rappel

Le champ ciblé (`text_en` ou `text_fr`) détermine la langue de recherche — plus besoin de filtre `lang` explicite.
La traduction correspondante est retournée directement depuis le même document.

**3. Couche mise en évidence (pipeline NLP)**
Une fois la paire récupérée, le système met en évidence le ou les mots correspondants dans la traduction grâce à :

- Un index de traductions basé sur la co-occurrence (coefficient de Dice, construit à l'import dans SQLite)
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
│   │   │   └── index.py              # Mapping de l'index OpenSearch
│   │   └── templates/
│   │       └── search.html           # Interface de recherche (Tailwind CSS)
│   ├── tests/
│   │   ├── test_stemmer.py           # Tests NLP (racinisation, mots vides)
│   │   ├── test_highlighter.py       # Tests mise en évidence
│   │   ├── test_search_opensearch.py # Tests requête OpenSearch (client mocké)
│   │   ├── test_search_endpoint.py   # Tests endpoint FastAPI (OpenSearch + DB mockés)
│   │   └── test_index_mapping.py     # Tests structure du mapping
│   └── index_csv_opensearch.py       # Indexation du CSV dans OpenSearch (alternative dev)
│
├── logstash/
│   ├── pipeline/
│   │   └── linguee.conf          # Pipeline ETL : CSV → paires OpenSearch
│   ├── config/
│   │   └── logstash.yml          # workers: 1 (compteur Ruby thread-safe)
│   └── templates/
│       └── segments.json         # Template de mapping OpenSearch
│
├── data/
│   └── books/
│       ├── aligned_book.csv                                     # Paires de phrases EN/FR alignées
│       ├── thirty-six-reasons-for-winning-the-lost_interior.md  # Livre source EN
│       └── trente-six-raisons-de-gagner-les-perdus_interieur.md # Livre source FR
├── docker-compose.yml
└── README.md
```

---

## Modèle de données

### SQLite

| Table               | Description                                                            |
| ------------------- | ---------------------------------------------------------------------- |
| `books`             | Un enregistrement par version linguistique du livre (EN + FR)          |
| `segments`          | Une phrase par ligne, liée à un livre                                  |
| `alignments`        | Associe un segment EN à sa traduction FR                               |
| `word_translations` | Scores de traduction de mots par co-occurrence (coefficient de Dice)   |
| `stem_forms`        | Associe les racines à leurs formes de surface pour la mise en évidence |

### OpenSearch — document paire bilingue

Chaque document représente une paire alignée complète (1 document = 1 phrase EN + 1 phrase FR) :

```json
{
  "pair_id": 1,
  "book_id": 1,
  "position": 1,
  "segment_id_en": 1,
  "segment_id_fr": 2,
  "text_en": "The Lord Jesus came to seek and to save the lost.",
  "text_fr": "Le Seigneur Jésus est venu chercher et sauver les perdus."
}
```

`text_en` est analysé avec l'analyzer `english` (stemming, stopwords EN), `text_fr` avec l'analyzer `french`.
Chaque champ dispose d'un sous-champ `.normalized` (keyword lowercase+asciifolding) pour la recherche exacte.

---

## Installation

### Prérequis

- Python 3.11+
- Docker + Docker Compose

### 1. Cloner le projet

```bash
git clone <url>
cd linguee_like
```

### 2. Démarrer OpenSearch

```bash
docker compose up -d opensearch
```

Attendez que le healthcheck passe : `curl http://localhost:9200/_cluster/health`

### 3. Configurer l'environnement Python

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
```

### 4. Importer le livre dans SQLite

```bash
python app/scripts/import_md.py
```

Crée les livres, segments, alignements et l'index de traduction de mots. Les tables sont créées automatiquement au premier lancement.

### 5. Indexer dans OpenSearch via Logstash

```bash
docker compose run --rm logstash
```

Logstash lit `data/books/aligned_book.csv`, transforme chaque ligne en document paire bilingue et le pousse dans OpenSearch. Le mapping est appliqué automatiquement via le template `logstash/templates/segments.json`. Le conteneur quitte une fois le fichier entièrement traité.

> **Alternative sans Docker** (développement) : `cd backend && python index_csv_opensearch.py`

### 6. Lancer l'API

```bash
uvicorn app.main:app --reload
```

Ouvrez `http://localhost:8000` dans votre navigateur.

---

## Tests

```bash
cd backend
pip install pytest httpx
python -m pytest tests/ -v
```

30 tests couvrant le NLP, la mise en évidence, la requête OpenSearch et l'endpoint FastAPI.

---

## Ajouter un nouveau livre

1. Ajoutez le CSV aligné dans `data/books/` (colonnes : `en`, `fr`)
2. Modifiez le bloc `__main__` dans `app/scripts/import_md.py` avec les métadonnées du nouveau livre et exécutez-le
3. Mettez à jour `path` dans `logstash/pipeline/linguee.conf` si le nom du fichier change
4. Relancez `docker compose run --rm logstash` pour réindexer dans OpenSearch

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
      "book_title": "Thirty-six reasons for winning the lost",
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
