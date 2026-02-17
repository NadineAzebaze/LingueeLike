"""
Comprehensive test suite with 75 test cases from the enriched dataset.
Tests single words, phrases, and various linguistic patterns.
"""
from app.nlp.highlighter import find_highlights_in_text


def normalize(text):
    """Normalize for comparison."""
    return text.lower().replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('ë', 'e') \
               .replace('à', 'a').replace('â', 'a').replace('ä', 'a') \
               .replace('ù', 'u').replace('û', 'u').replace('ü', 'u') \
               .replace('ô', 'o').replace('ö', 'o') \
               .replace('î', 'i').replace('ï', 'i') \
               .replace('ç', 'c').replace("'", "'").replace("\u2019", "'")


# Test cases: (query, lang, source, target, expected_highlight)
test_cases = [
    # === SINGLE WORDS - Common nouns ===
    ('Lord', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.',
     'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['Seigneur']),

    ('Jesus', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.',
     'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['Jésus']),

    ('reason', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.',
     'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['raison']),

    ('heaven', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.',
     'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['ciel']),

    ('world', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.',
     'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['monde']),

    # === SINGLE WORDS - Verbs ===
    ('came', 'en', 'He came to seek and save the lost.',
     'Il est venu chercher et sauver les perdus.', ['venu']),

    ('seek', 'en', 'He came to seek and save the lost.',
     'Il est venu chercher et sauver les perdus.', ['chercher']),

    ('save', 'en', 'He came to seek and save the lost.',
     'Il est venu chercher et sauver les perdus.', ['sauver']),

    ('lost', 'en', 'He came to seek and save the lost.',
     'Il est venu chercher et sauver les perdus.', ['perdus']),

    # === SINGLE WORDS - Adjectives (word order tests) ===
    ('important', 'en', 'This is the most important task of the church.',
     "C'est la tâche la plus importante de l'église.", ['importante']),

    ('most', 'en', 'This is the most important task of the church.',
     "C'est la tâche la plus importante de l'église.", ['plus']),

    # === SINGLE WORDS - Stop words as valid translations ===
    ('must', 'en', 'We must win souls for Christ.',
     'Nous devons gagner des âmes pour Christ.', ['devons']),

    # === SINGLE WORDS - Common words ===
    ('souls', 'en', 'We must win souls for Christ.',
     'Nous devons gagner des âmes pour Christ.', ['âmes']),

    ('Christ', 'en', 'We must win souls for Christ.',
     'Nous devons gagner des âmes pour Christ.', ['Christ']),

    ('Bible', 'en', 'The Bible says: He who wins souls is wise.',
     'La Bible dit : Celui qui gagne des âmes est sage.', ['Bible']),

    ('says', 'en', 'The Bible says: He who wins souls is wise.',
     'La Bible dit : Celui qui gagne des âmes est sage.', ['dit']),

    ('wins', 'en', 'The Bible says: He who wins souls is wise.',
     'La Bible dit : Celui qui gagne des âmes est sage.', ['gagne']),

    ('wise', 'en', 'The Bible says: He who wins souls is wise.',
     'La Bible dit : Celui qui gagne des âmes est sage.', ['sage']),

    # === FRENCH TO ENGLISH ===
    ('Seigneur', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.',
     'The Lord Jesus had one reason for coming down from heaven into our world.', ['Lord']),

    ('Jésus', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.',
     'The Lord Jesus had one reason for coming down from heaven into our world.', ['Jesus']),

    ('raison', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.',
     'The Lord Jesus had one reason for coming down from heaven into our world.', ['reason']),

    ('ciel', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.',
     'The Lord Jesus had one reason for coming down from heaven into our world.', ['heaven']),

    ('monde', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.',
     'The Lord Jesus had one reason for coming down from heaven into our world.', ['world']),

    ('venu', 'fr', 'Il est venu chercher et sauver les perdus.',
     'He came to seek and save the lost.', ['came']),

    ('chercher', 'fr', 'Il est venu chercher et sauver les perdus.',
     'He came to seek and save the lost.', ['seek']),

    ('sauver', 'fr', 'Il est venu chercher et sauver les perdus.',
     'He came to seek and save the lost.', ['save']),

    ('perdus', 'fr', 'Il est venu chercher et sauver les perdus.',
     'He came to seek and save the lost.', ['lost']),

    ('importante', 'fr', "C'est la tâche la plus importante de l'église.",
     'This is the most important task of the church.', ['important']),

    ('devons', 'fr', 'Nous devons gagner des âmes pour Christ.',
     'We must win souls for Christ.', ['must']),

    ('gagner', 'fr', 'Nous devons gagner des âmes pour Christ.',
     'We must win souls for Christ.', ['win']),

    ('âmes', 'fr', 'Nous devons gagner des âmes pour Christ.',
     'We must win souls for Christ.', ['souls']),

    # === MORE VOCABULARY - Gospel/Evangelism ===
    ('gospel', 'en', 'The gospel is the power of God.',
     "L'Évangile est la puissance de Dieu.", ['Évangile']),

    ('power', 'en', 'The gospel is the power of God.',
     "L'Évangile est la puissance de Dieu.", ['puissance']),

    ('believe', 'en', 'Everyone who believes in the Lord Jesus is saved.',
     'Quiconque croit au Seigneur Jésus est sauvé.', ['croit']),

    ('saved', 'en', 'Everyone who believes in the Lord Jesus is saved.',
     'Quiconque croit au Seigneur Jésus est sauvé.', ['sauvé']),

    ('church', 'en', 'This is the most important task of the church.',
     "C'est la tâche la plus importante de l'église.", ["l'église"]),

    # === THEOLOGICAL TERMS ===
    ('sin', 'en', 'He died on the cross for all sinners.',
     'Il mourut sur la croix pour tous les pécheurs.', ['pécheurs']),

    ('cross', 'en', 'He died on the cross for all sinners.',
     'Il mourut sur la croix pour tous les pécheurs.', ['croix']),

    ('died', 'en', 'He died on the cross for all sinners.',
     'Il mourut sur la croix pour tous les pécheurs.', ['mourut']),

    ('blood', 'en', 'He shed His blood for all men.',
     'Il versa Son sang pour tous les hommes.', ['sang']),

    ('hell', 'en', 'Everyone who does not believe in the Lord Jesus will go to hell.',
     'Quiconque ne croit pas au Seigneur Jésus ira en enfer.', ['enfer']),

    # === FRENCH THEOLOGICAL TERMS ===
    ('Évangile', 'fr', "L'Évangile est la puissance de Dieu.",
     'The gospel is the power of God.', ['gospel']),

    ('puissance', 'fr', "L'Évangile est la puissance de Dieu.",
     'The gospel is the power of God.', ['power']),

    ('croit', 'fr', 'Quiconque croit au Seigneur Jésus est sauvé.',
     'Everyone who believes in the Lord Jesus is saved.', ['believes']),

    ('sauvé', 'fr', 'Quiconque croit au Seigneur Jésus est sauvé.',
     'Everyone who believes in the Lord Jesus is saved.', ['saved']),

    ('église', 'fr', "C'est la tâche la plus importante de l'église.",
     'This is the most important task of the church.', ['church']),

    ('pécheurs', 'fr', 'Il mourut sur la croix pour tous les pécheurs.',
     'He died on the cross for all sinners.', ['sinners']),

    ('croix', 'fr', 'Il mourut sur la croix pour tous les pécheurs.',
     'He died on the cross for all sinners.', ['cross']),

    # === PRONOUNS AND ARTICLES ===
    ('He', 'en', 'He came to seek and save the lost.',
     'Il est venu chercher et sauver les perdus.', ['Il']),

    # === ACTION VERBS ===
    ('win', 'en', 'We must win souls for Christ.',
     'Nous devons gagner des âmes pour Christ.', ['gagner']),

    ('preach', 'en', 'You must preach the gospel.',
     "Il faut que tu prêches l'Évangile.", ['prêches']),

    # === NUMBERS AND QUANTIFIERS ===
    ('one', 'en', 'The Lord Jesus had one reason for coming down from heaven.',
     'Le Seigneur Jésus avait une raison de descendre du ciel.', ['une']),

    ('all', 'en', 'He shed His blood for all men.',
     'Il versa Son sang pour tous les hommes.', ['tous']),

    # === SPIRITUAL CONCEPTS ===
    ('heart', 'en', 'May the Holy Spirit set your heart on fire.',
     'Puisse le Saint-Esprit enflammer ton cœur.', ['cœur']),

    ('fire', 'en', 'May the Holy Spirit set your heart on fire.',
     'Puisse le Saint-Esprit enflammer ton cœur.', ['enflammer']),

    ('Spirit', 'en', 'May the Holy Spirit set your heart on fire.',
     'Puisse le Saint-Esprit enflammer ton cœur.', ['Saint-Esprit']),

    # === MULTI-WORD PHRASES ===
    ('Holy Spirit', 'en', 'May the Holy Spirit set your heart on fire.',
     'Puisse le Saint-Esprit enflammer ton cœur.', ['Saint-Esprit', 'enflammer']),

    ('win souls', 'en', 'We must win souls for Christ.',
     'Nous devons gagner des âmes pour Christ.', ['gagner', 'âmes']),

    ('seek and save', 'en', 'He came to seek and save the lost.',
     'Il est venu chercher et sauver les perdus.', ['chercher', 'sauver']),

    ('Lord Jesus', 'en', 'The Lord Jesus had one reason.',
     'Le Seigneur Jésus avait une raison.', ['Seigneur', 'Jésus']),

    # === COMPLEX PHRASES ===
    ('most important task', 'en', 'This is the most important task of the church.',
     "C'est la tâche la plus importante de l'église.", ['tâche', 'plus', 'importante']),

    ('coming down from heaven', 'en', 'He had one reason for coming down from heaven.',
     'Il avait une raison de descendre du ciel.', ['descendre', 'ciel']),

    # === FRENCH PHRASES ===
    ('gagner des âmes', 'fr', 'Nous devons gagner des âmes pour Christ.',
     'We must win souls for Christ.', ['win', 'souls']),

    ('Saint-Esprit', 'fr', 'Puisse le Saint-Esprit enflammer ton cœur.',
     'May the Holy Spirit set your heart on fire.', ['Holy', 'Spirit']),

    ('chercher et sauver', 'fr', 'Il est venu chercher et sauver les perdus.',
     'He came to seek and save the lost.', ['seek', 'save']),

    # === ADDITIONAL VOCABULARY ===
    ('earth', 'en', 'You should stay on earth.',
     'Tu dois rester sur terre.', ['terre']),

    ('partner', 'en', 'Be His partner in winning the lost.',
     'Être son partenaire dans le gagnement des perdus.', ['partenaire']),

    ('book', 'en', 'In this book we have given you reasons.',
     'Dans ce livre nous avons donné des raisons.', ['livre']),

    ('give', 'en', 'In this book we have given you reasons.',
     'Dans ce livre nous avons donné des raisons.', ['donné']),

    ('read', 'en', 'As you read the book.',
     'Pendant que tu lis ce livre.', ['lis']),

    ('rest', 'en', 'You will take no rest.',
     'Tu ne prendras aucun repos.', ['repos']),

    ('task', 'en', 'The supreme task of winning the lost.',
     'La tâche suprême de gagner les perdus.', ['tâche']),
]

print(f"Running comprehensive test suite with {len(test_cases)} tests...\n")

passed = 0
failed = 0
categories = {
    'single_word_en_fr': {'passed': 0, 'total': 0},
    'single_word_fr_en': {'passed': 0, 'total': 0},
    'phrases': {'passed': 0, 'total': 0},
    'adjectives': {'passed': 0, 'total': 0},
    'stop_words': {'passed': 0, 'total': 0},
}

for i, (query, lang, source, target, expected) in enumerate(test_cases, 1):
    result = find_highlights_in_text(query, source, target, lang)

    # Normalize for comparison
    result_normalized = [normalize(r) for r in result]
    expected_normalized = [normalize(e) for e in expected]

    # Check if results match
    match = set(result_normalized) == set(expected_normalized)

    # Categorize test
    is_phrase = ' ' in query
    is_adjective = query.lower() in ['most', 'important', 'importante', 'plus']
    is_stop_word = query.lower() in ['must', 'devons', 'he', 'il']

    if match:
        passed += 1
        status = '[PASS]'

        if is_phrase:
            categories['phrases']['passed'] += 1
        elif lang == 'en':
            categories['single_word_en_fr']['passed'] += 1
        else:
            categories['single_word_fr_en']['passed'] += 1

        if is_adjective:
            categories['adjectives']['passed'] += 1
        if is_stop_word:
            categories['stop_words']['passed'] += 1
    else:
        failed += 1
        status = '[FAIL]'

    # Update totals
    if is_phrase:
        categories['phrases']['total'] += 1
    elif lang == 'en':
        categories['single_word_en_fr']['total'] += 1
    else:
        categories['single_word_fr_en']['total'] += 1

    if is_adjective:
        categories['adjectives']['total'] += 1
    if is_stop_word:
        categories['stop_words']['total'] += 1

    # Print result
    result_str = ', '.join(result[:3]) + ('...' if len(result) > 3 else '')
    expected_str = ', '.join(expected[:3]) + ('...' if len(expected) > 3 else '')

    if status == '[FAIL]':
        print(f"{status} Test {i:2d}: '{query}' -> {result_str} (expected: {expected_str})")

print(f"\n{'='*70}")
print(f"OVERALL RESULTS: {passed}/{len(test_cases)} PASS ({100*passed//len(test_cases)}%)")
print(f"{'='*70}")

print("\nBREAKDOWN BY CATEGORY:")
for category, stats in categories.items():
    if stats['total'] > 0:
        pct = 100 * stats['passed'] // stats['total']
        print(f"  {category:20s}: {stats['passed']:2d}/{stats['total']:2d} ({pct:3d}%)")
