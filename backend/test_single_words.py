from app.nlp.highlighter import find_highlights_in_text

# Test data from aligned_book.csv
test_cases = [
    # Single words from each sentence - EN to FR
    ('Lord', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['Seigneur']),
    ('Jesus', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['Jésus']),
    ('reason', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['raison']),
    ('coming', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['descendre']),
    ('heaven', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['ciel']),
    ('world', 'en', 'The Lord Jesus had one reason for coming down from heaven into our world.', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', ['monde']),

    ('came', 'en', 'He came to seek and save the lost.', 'Il est venu chercher et sauver les perdus.', ['venu']),
    ('seek', 'en', 'He came to seek and save the lost.', 'Il est venu chercher et sauver les perdus.', ['chercher']),
    ('save', 'en', 'He came to seek and save the lost.', 'Il est venu chercher et sauver les perdus.', ['sauver']),
    ('lost', 'en', 'He came to seek and save the lost.', 'Il est venu chercher et sauver les perdus.', ['perdus']),

    ('most', 'en', 'This is the most important task of the church.', "C'est la tâche la plus importante de l'église.", ['plus']),
    ('important', 'en', 'This is the most important task of the church.', "C'est la tâche la plus importante de l'église.", ['importante']),
    ('task', 'en', 'This is the most important task of the church.', "C'est la tâche la plus importante de l'église.", ['tâche']),
    ('church', 'en', 'This is the most important task of the church.', "C'est la tâche la plus importante de l'église.", ["l'église"]),

    ('must', 'en', 'We must win souls for Christ.', 'Nous devons gagner des âmes pour Christ.', ['devons']),
    ('win', 'en', 'We must win souls for Christ.', 'Nous devons gagner des âmes pour Christ.', ['gagner']),
    ('souls', 'en', 'We must win souls for Christ.', 'Nous devons gagner des âmes pour Christ.', ['âmes']),
    ('Christ', 'en', 'We must win souls for Christ.', 'Nous devons gagner des âmes pour Christ.', ['Christ']),

    ('Bible', 'en', 'The Bible says: He who wins souls is wise.', 'La Bible dit : Celui qui gagne des âmes est sage.', ['Bible']),
    ('says', 'en', 'The Bible says: He who wins souls is wise.', 'La Bible dit : Celui qui gagne des âmes est sage.', ['dit']),
    ('wins', 'en', 'The Bible says: He who wins souls is wise.', 'La Bible dit : Celui qui gagne des âmes est sage.', ['gagne']),
    ('wise', 'en', 'The Bible says: He who wins souls is wise.', 'La Bible dit : Celui qui gagne des âmes est sage.', ['sage']),

    # FR to EN
    ('Seigneur', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', 'The Lord Jesus had one reason for coming down from heaven into our world.', ['Lord']),
    ('Jésus', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', 'The Lord Jesus had one reason for coming down from heaven into our world.', ['Jesus']),
    ('raison', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', 'The Lord Jesus had one reason for coming down from heaven into our world.', ['reason']),
    ('descendre', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', 'The Lord Jesus had one reason for coming down from heaven into our world.', ['coming']),
    ('ciel', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', 'The Lord Jesus had one reason for coming down from heaven into our world.', ['heaven']),
    ('monde', 'fr', 'Le Seigneur Jésus avait une raison de descendre du ciel dans notre monde.', 'The Lord Jesus had one reason for coming down from heaven into our world.', ['world']),

    ('venu', 'fr', 'Il est venu chercher et sauver les perdus.', 'He came to seek and save the lost.', ['came']),
    ('chercher', 'fr', 'Il est venu chercher et sauver les perdus.', 'He came to seek and save the lost.', ['seek']),
    ('sauver', 'fr', 'Il est venu chercher et sauver les perdus.', 'He came to seek and save the lost.', ['save']),
    ('perdus', 'fr', 'Il est venu chercher et sauver les perdus.', 'He came to seek and save the lost.', ['lost']),

    ('plus', 'fr', "C'est la tâche la plus importante de l'église.", 'This is the most important task of the church.', ['most']),
    ('importante', 'fr', "C'est la tâche la plus importante de l'église.", 'This is the most important task of the church.', ['important']),
    ('tâche', 'fr', "C'est la tâche la plus importante de l'église.", 'This is the most important task of the church.', ['task']),
    ('église', 'fr', "C'est la tâche la plus importante de l'église.", 'This is the most important task of the church.', ['church']),

    ('devons', 'fr', 'Nous devons gagner des âmes pour Christ.', 'We must win souls for Christ.', ['must']),
    ('gagner', 'fr', 'Nous devons gagner des âmes pour Christ.', 'We must win souls for Christ.', ['win']),
    ('âmes', 'fr', 'Nous devons gagner des âmes pour Christ.', 'We must win souls for Christ.', ['souls']),
    ('Christ', 'fr', 'Nous devons gagner des âmes pour Christ.', 'We must win souls for Christ.', ['Christ']),

    ('Bible', 'fr', 'La Bible dit : Celui qui gagne des âmes est sage.', 'The Bible says: He who wins souls is wise.', ['Bible']),
    ('dit', 'fr', 'La Bible dit : Celui qui gagne des âmes est sage.', 'The Bible says: He who wins souls is wise.', ['says']),
    ('gagne', 'fr', 'La Bible dit : Celui qui gagne des âmes est sage.', 'The Bible says: He who wins souls is wise.', ['wins']),
    ('sage', 'fr', 'La Bible dit : Celui qui gagne des âmes est sage.', 'The Bible says: He who wins souls is wise.', ['wise']),
]

passed = 0
failed = 0

for query, lang, source, target, expected in test_cases:
    result = find_highlights_in_text(query, source, target, lang)

    # Normalize for comparison (handle accents, case)
    result_normalized = [r.lower().replace('é', 'e').replace('â', 'a').replace('î', 'i').replace("'", "'") for r in result]
    expected_normalized = [e.lower().replace('é', 'e').replace('â', 'a').replace('î', 'i').replace("'", "'") for e in expected]

    # Check if results match (order doesn't matter for single words)
    if set(result_normalized) == set(expected_normalized):
        print(f'[PASS] {query:12} -> {result}')
        passed += 1
    else:
        print(f'[FAIL] {query:12} -> {result} (expected {expected})')
        failed += 1

print(f'\n=== Results: {passed}/{len(test_cases)} PASS ({100*passed//len(test_cases)}%) ===')
