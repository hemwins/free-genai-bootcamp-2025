from flask import request, jsonify, g
from flask_cors import cross_origin
import json
from math import ceil

def load(app):
  # Endpoint: GET /api/words with pagination (50 words per page)
  @app.route('/api/words', methods=['GET'])
  @cross_origin()
  def get_words():
    app.logger.info("Route hit: /api/words GET")
    try:
      cursor = app.db.cursor()

      # First, let's check the actual table structure
      cursor.execute("PRAGMA table_info(words)")
      columns = cursor.fetchall()
      app.logger.debug(f"Words table columns: {[col['name'] for col in columns]}")
        
      # Get the current page number from query parameters (default is 1)
      page = int(request.args.get('page', 1))
      # Ensure page number is positive
      page = max(1, page)
      words_per_page = request.args.get('words_per_page', 50)
      offset = (page - 1) * words_per_page

      # Get sorting parameters from the query string
      sort_by = request.args.get('sort_by', 'kanji')  # Default to sorting by 'kanji'
      order = request.args.get('order', 'asc').upper()  # Default to ascending order

      # Define valid columns mapping
      valid_columns = {
        'kanji': 'w.kanji',
        'romaji': 'w.romaji',
        'english': 'w.english',
        'correct_count': 'COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0)',
        'wrong_count': 'COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0)'
      }
        
      # Validate sort_by parameter
      if sort_by not in valid_columns:
        app.logger.warning(f"Invalid sort field: {sort_by}, defaulting to kanji")
        sort_by = 'kanji'
        
      # Validate order parameter
      if order not in ['ASC', 'DESC']:
        app.logger.warning(f"Invalid sort order: {order}, defaulting to ASC")
        order = 'ASC'
        

      # Get total count for pagination
      cursor.execute('SELECT COUNT(*) as count FROM words')
      total_count = cursor.fetchone()['count']
      total_pages = ceil(total_count / words_per_page)
        
      # Build the query with review statistics
      query = f'''
        SELECT 
          w.id,
          w.kanji,
          w.romaji,
          w.english,
          COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0) as correct_count,
          COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0) as wrong_count,
          COALESCE(MAX(wri.created_at), '') as last_reviewed,
          GROUP_CONCAT(DISTINCT g.id || '::' || g.name) as groups
        FROM words w
        LEFT JOIN word_review_items wri ON w.id = wri.word_id
        LEFT JOIN word_groups wg ON w.id = wg.word_id
        LEFT JOIN groups g ON wg.group_id = g.id
        GROUP BY w.id, w.kanji, w.romaji, w.english
        ORDER BY {valid_columns[sort_by]} {order}
        LIMIT ? OFFSET ?
      '''
        
      app.logger.debug(f"Executing query with sort_by={sort_by}, order={order}, "
                      f"limit={words_per_page}, offset={offset}")
        
      cursor.execute(query, (words_per_page, offset))
      words = cursor.fetchall()

      # Process the results
      words_data = []
      for word in words:
        # Convert SQLite Row to dict
        word_dict = dict(word)
        # Process groups
        groups = []
        if word_dict.get('groups'):  # Use get() with default None
          for group_str in word_dict['groups'].split(','):
            try:
              group_id, group_name = group_str.split('::')
              groups.append({
                'id': int(group_id),
                'name': group_name
              })
            except ValueError as e:
              app.logger.error(f"Error splitting group string: {group_str}, error: {str(e)}")
              continue # Skip malformed group data
        # Build word data
        word_data = {
          'id': word_dict.get('id'),
          'kanji': word_dict.get('kanji'),
          'romaji': word_dict.get('romaji'),
          'english': word_dict.get('english'),
          'stats': {
            'correct_count': word_dict.get('correct_count', 0),
            'wrong_count': word_dict.get('wrong_count', 0),
            'accuracy': round(word_dict.get('correct_count', 0) / 
              (word_dict.get('correct_count', 0) + word_dict.get('wrong_count', 0)) * 100, 2) 
              if (word_dict.get('correct_count', 0) + word_dict.get('wrong_count', 0)) > 0 else 0,
            'last_reviewed': word_dict.get('last_reviewed', '')
          },
          'groups': groups
        }
        words_data.append(word_data)
      app.logger.info(f"Retrieved {len(words_data)} words (page {page} of {total_pages})")
      return jsonify({
            'words': words_data,
            'pagination': {
                'total_items': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'per_page': words_per_page
            },
            'sorting': {
                'sort_by': sort_by,
                'order': order
            }
        }) 
    except Exception as e:
      app.logger.error(f"Error retrieving words: {str(e)}", exc_info=True)
      return jsonify({"error": str(e)}), 500
    finally:
      app.db.close()

  # Endpoint: GET /words/:id to get a single word with its details
  @app.route('/api/words/<int:word_id>', methods=['GET'])
  @cross_origin()
  def get_word(word_id):
    try:
      cursor = app.db.cursor()
      
      # Query to fetch the word and its details
      cursor.execute('''
        SELECT w.id, w.kanji, w.romaji, w.english,
               COALESCE(r.correct_count, 0) AS correct_count,
               COALESCE(r.wrong_count, 0) AS wrong_count,
               GROUP_CONCAT(DISTINCT g.id || '::' || g.name) as groups
        FROM words w
        LEFT JOIN word_reviews r ON w.id = r.word_id
        LEFT JOIN word_groups wg ON w.id = wg.word_id
        LEFT JOIN groups g ON wg.group_id = g.id
        WHERE w.id = ?
        GROUP BY w.id
      ''', (word_id,))
      
      word = cursor.fetchone()
      
      if not word:
        return jsonify({"error": "Word not found"}), 404
      
      # Parse the groups string into a list of group objects
      groups = []
      if word["groups"]:
        for group_str in word["groups"].split(','):
          group_id, group_name = group_str.split('::')
          groups.append({
            "id": int(group_id),
            "name": group_name
          })
      
      return jsonify({
        "word": {
          "id": word["id"],
          "kanji": word["kanji"],
          "romaji": word["romaji"],
          "english": word["english"],
          "correct_count": word["correct_count"],
          "wrong_count": word["wrong_count"],
          "groups": groups
        }
      })
      
    except Exception as e:
      return jsonify({"error": str(e)}), 500