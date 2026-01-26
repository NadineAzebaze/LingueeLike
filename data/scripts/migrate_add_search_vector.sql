-- data/scripts/migrate_add_search_vector.sql
ALTER TABLE IF EXISTS segments ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE INDEX IF NOT EXISTS idx_segments_search ON segments USING GIN(search_vector);

-- remplir pour les lignes existantes
UPDATE segments SET search_vector = to_tsvector('english', text) WHERE language = 'en';
UPDATE segments SET search_vector = to_tsvector('french', text) WHERE language = 'fr';