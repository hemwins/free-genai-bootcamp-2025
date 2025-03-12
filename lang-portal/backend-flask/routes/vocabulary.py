from flask import request, jsonify, g
from flask_cors import cross_origin
import json
from math import ceil

def load(app):
    @app.route('/api/vocabulary', methods=['POST'])
    @cross_origin()
    def post_vocabulary():
        app.logger.info("Route hit: /api/vocabulary POST")
        try:
            data = request.get_json()
            category = data.get('category')
            vocabulary = data.get('data')

            if not category or not vocabulary:
                return jsonify({"error": "Category and vocabulary data are required"}), 400
            # Validate required fields
            for item in vocabulary:
                kanji = item.get('kanji')
                romaji = item.get('romaji')
                english = item.get('english')
                parts = json.dumps(item.get('parts'))
                if not all([kanji, romaji, english, parts]):
                    app.logger.warning(f"kanji in vocabulary fields: {kanji}")
                    app.logger.warning(f"romaji in vocabulary fields: {romaji}")
                    app.logger.warning(f"english in vocabulary fields: {english}")
                    app.logger.warning(f"parts in vocabulary fields: {parts}")
                    app.logger.warning(f"Missing required vocabulary fields in request: {vocabulary}")
                    return jsonify({"error": "Missing required vocabulary fields"}), 400

            cursor = app.db.cursor()

            # Check if the group exists
            cursor.execute('SELECT id, words_count FROM groups WHERE name = ?', (category,))
            group = cursor.fetchone()
            if group:
                group_id = group['id']
                existing_word_count = group['words_count']
            else:
                group_id = None
                existing_word_count = 0

            # If the group doesn't exist, create it
            if not group_id:
                cursor.execute('INSERT INTO groups (name, words_count) VALUES (?, 0)', (category,))
                group_id = cursor.lastrowid
                app.logger.info(f"Created new group: {category} with id {group_id}")
                app.db.commit()

            new_words_added = 0
            
            # Process each word in the vocabulary
            for item in vocabulary:
                kanji = item.get('kanji')
                romaji = item.get('romaji')
                english = item.get('english')
                parts = json.dumps(item.get('parts'))

                # Check if the word exists
                cursor.execute('SELECT id FROM words WHERE kanji = ? AND romaji = ? AND english = ?', (kanji, romaji, english))
                word = cursor.fetchone()
                word_id = word['id'] if word else None

                # If the word doesn't exist, create it
                if not word_id:
                    cursor.execute('''
                        INSERT INTO words (kanji, romaji, english, parts)
                        VALUES (?, ?, ?, ?)
                    ''', (kanji, romaji, english, parts))
                    word_id = cursor.lastrowid
                    app.logger.info(f"Created new word: {kanji} with id {word_id}")
                    app.db.commit()

                # Create a relationship between the word and the group in word_groups
                cursor.execute('SELECT * FROM word_groups WHERE word_id = ? AND group_id = ?', (word_id, group_id))
                existing_relation = cursor.fetchone()

                if not existing_relation:
                    cursor.execute('INSERT INTO word_groups (word_id, group_id) VALUES (?, ?)', (word_id, group_id))
                    app.logger.info(f"Added word {word_id} to group {group_id}")
                    app.db.commit()
                    new_words_added += 1

            # Update the group's word count
            new_word_count = existing_word_count + new_words_added
            cursor.execute('UPDATE groups SET words_count = ? WHERE id = ?', (new_word_count, group_id))
            app.db.commit()
            app.logger.info(f"Updated group {category} word count to {new_word_count}")

            return jsonify({"count": new_words_added}), 200

        except Exception as e:
            app.logger.error(f"Error processing vocabulary: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

