from flask import request, jsonify, g
from flask_cors import cross_origin
import json
from lib.db import Db

def load(app):
  @app.route('/api/groups', methods=['GET'])
  @cross_origin()
  def get_groups():
    app.logger.info(f"Route hit: /api/groups GET")
    try:
      cursor = app.db.cursor()

      # Get the current page number from query parameters (default is 1)
      page = int(request.args.get('page', 1))
      groups_per_page = int(request.args.get('per_page', 10))
      offset = (page - 1) * groups_per_page
      app.logger.debug(f"Pagination params: page={page}, {groups_per_page}, Offset: {offset}")

      # Get sorting parameters from the query string
      sort_by = request.args.get('sort_by', 'name')  # Default to sorting by 'name'
      order = request.args.get('order', 'asc')  # Default to ascending order

      # Validate sort_by and order
      valid_columns = ['name', 'words_count']
      if sort_by not in valid_columns:
        sort_by = 'name'
      if order not in ['asc', 'desc']:
        order = 'asc'

      # Query to fetch groups with sorting and the cached word count
      cursor.execute(f'''
        SELECT id, name, words_count
        FROM groups
        ORDER BY {sort_by} {order}
        LIMIT ? OFFSET ?
      ''', (groups_per_page, offset))

      groups = cursor.fetchall()

      # Query the total number of groups
      cursor.execute('SELECT COUNT(*) as count FROM groups')
      total_groups = cursor.fetchone()['count']
      total_pages = (total_groups + groups_per_page - 1) // groups_per_page

      # Format the response
      groups_data = []
      for group in groups:
        groups_data.append({
          "id": group["id"],
          "group_name": group["name"],
          "word_count": group["words_count"]
        })

      # Return groups and pagination metadata
      return jsonify({
        'groups': groups_data,
        'total_pages': total_pages,
        'current_page': page
      })
    except Exception as e:
      app.logger.error(f"Error getting groups: {str(e)}", exc_info=True)
      return jsonify({"error": str(e)}), 500
    
  @app.route('/api/groups', methods=['POST'])
  @cross_origin()
  def create_group():
    app.logger.info("Route hit: /api/groups POST")
    try:
      data = request.get_json()
      app.logger.debug(f"Received data: {data}")
      
      if not data or 'name' not in data:
        return jsonify({"error": "Name is required"}), 400
      
      cursor = app.db.cursor()
      
      cursor.execute('''
        INSERT INTO groups (name, words_count)
        VALUES (?, 0)
      ''', (data['name'],))
      
      app.db.commit()
      group_id = cursor.lastrowid
      
      return jsonify({
        "id": group_id,
        "name": data['name'],
        "words_count": 0
      }), 201
      
    except Exception as e:
      app.logger.error(f"Error creating group: {str(e)}", exc_info=True)
      return jsonify({"error": str(e)}), 500

  @app.route('/api/groups/<int:group_id>', methods=['PUT'])
  @cross_origin()
  def update_group(group_id):
    app.logger.info(f"Route hit: /api/groups/{group_id} PUT")
    try:
      data = request.get_json()
      app.logger.debug(f"Received data: {data}")
            
      if 'name' not in data:
        app.logger.warning("Missing name in request")
        return jsonify({"error": "Name is required"}), 400
                
      if not isinstance(data['name'], str):
        app.logger.warning(f"Invalid name type: {type(data['name'])}")
        return jsonify({"error": "Name must be a string"}), 400
                
      cursor = app.db.cursor()
            
      # Check if group exists
      cursor.execute('SELECT COUNT(*) as count FROM groups WHERE id = ?', (group_id,))
      if cursor.fetchone()['count'] == 0:
        app.logger.warning(f"Group not found: {group_id}")
        return jsonify({"error": "Group not found"}), 404
                
      # Check if new name already exists for different group
      cursor.execute('''
        SELECT COUNT(*) as count 
        FROM groups 
        WHERE name = ? AND id != ?
      ''', (data['name'], group_id))
      if cursor.fetchone()['count'] > 0:
        app.logger.warning(f"Group name already exists: {data['name']}")
        return jsonify({"error": "Group name already exists"}), 409
                
      try:
        # Start transaction
        cursor.execute('BEGIN')
                
        # Update group
        cursor.execute('''
          UPDATE groups 
          SET name = ?
          WHERE id = ?
        ''', (data['name'], group_id))
                
        # Get updated group
        cursor.execute('''
          SELECT g.*, 
          COUNT(DISTINCT wg.word_id) as word_count,
          COUNT(DISTINCT ss.id) as session_count
          FROM groups g
          LEFT JOIN word_groups wg ON g.id = wg.group_id
          LEFT JOIN study_sessions ss ON g.id = ss.group_id
          WHERE g.id = ?
          GROUP BY g.id
        ''', (group_id,))
                
        group = cursor.fetchone()
        app.db.commit()
                
        app.logger.info(f"Updated group: {group_id}")
        return jsonify({'group': dict(group)})
                
      except Exception as e:
        app.db.get().rollback()
        raise e
                
    except Exception as e:
      app.logger.error(f"Error updating group: {str(e)}", exc_info=True)
      return jsonify({"error": str(e)}), 500

  @app.route('/api/groups/<int:group_id>', methods=['DELETE'])
  @cross_origin()
  def delete_group(group_id):
    app.logger.info(f"Route hit: /api/groups/{group_id} DELETE")
    try:
      cursor = app.db.cursor()
            
      # Check if group exists
      cursor.execute('SELECT COUNT(*) as count FROM groups WHERE id = ?', (group_id,))
      if cursor.fetchone()['count'] == 0:
        app.logger.warning(f"Group not found: {group_id}")
        return jsonify({"error": "Group not found"}), 404
                
      try:
        # Start transaction
        cursor.execute('BEGIN')
                
        # Delete related records first
        cursor.execute('DELETE FROM word_groups WHERE group_id = ?', (group_id,))
        cursor.execute('DELETE FROM study_sessions WHERE group_id = ?', (group_id,))
                
        # Delete group
        cursor.execute('DELETE FROM groups WHERE id = ?', (group_id,))
                
        app.db.commit()
                
        app.logger.info(f"Deleted group: {group_id}")
        return '', 204
                
      except Exception as e:
        app.db.get().rollback()
        raise e
                
    except Exception as e:
      app.logger.error(f"Error deleting group: {str(e)}", exc_info=True)
      return jsonify({"error": str(e)}), 500


  @app.route('/api/groups/<int:group_id>', methods=['GET'])
  @cross_origin()
  def get_group(group_id):
    try:
      cursor = app.db.cursor()

      # Get group details
      cursor.execute('''
        SELECT id, name, words_count
        FROM groups
        WHERE id = ?
      ''', (group_id,))
      
      group = cursor.fetchone()
      if not group:
        return jsonify({"error": "Group not found"}), 404

      return jsonify({
        "id": group["id"],
        "group_name": group["name"],
        "word_count": group["words_count"]
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/groups/<int:id>/words', methods=['GET'])
  @cross_origin()
  def get_group_words(id):
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = int(request.args.get('page', 1))
      words_per_page = 10
      offset = (page - 1) * words_per_page

      # Get sorting parameters
      sort_by = request.args.get('sort_by', 'kanji')
      order = request.args.get('order', 'asc')

      # Validate sort parameters
      valid_columns = ['kanji', 'romaji', 'english', 'correct_count', 'wrong_count']
      if sort_by not in valid_columns:
        sort_by = 'kanji'
      if order not in ['asc', 'desc']:
        order = 'asc'

      # First, check if the group exists
      cursor.execute('SELECT name FROM groups WHERE id = ?', (id,))
      group = cursor.fetchone()
      if not group:
        return jsonify({"error": "Group not found"}), 404

      # Query to fetch words with pagination and sorting
      cursor.execute(f'''
        SELECT w.*, 
               COALESCE(wr.correct_count, 0) as correct_count,
               COALESCE(wr.wrong_count, 0) as wrong_count
        FROM words w
        JOIN word_groups wg ON w.id = wg.word_id
        LEFT JOIN word_reviews wr ON w.id = wr.word_id
        WHERE wg.group_id = ?
        ORDER BY {sort_by} {order}
        LIMIT ? OFFSET ?
      ''', (id, words_per_page, offset))
      
      words = cursor.fetchall()

      # Get total words count for pagination
      cursor.execute('''
        SELECT COUNT(*) 
        FROM word_groups 
        WHERE group_id = ?
      ''', (id,))
      total_words = cursor.fetchone()[0]
      total_pages = (total_words + words_per_page - 1) // words_per_page

      # Format the response
      words_data = []
      for word in words:
        words_data.append({
          "id": word["id"],
          "kanji": word["kanji"],
          "romaji": word["romaji"],
          "english": word["english"],
          "correct_count": word["correct_count"],
          "wrong_count": word["wrong_count"]
        })

      return jsonify({
        'words': words_data,
        'total_pages': total_pages,
        'current_page': page
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  # todo GET /groups/:id/words/raw
  @app.route('/api/groups/<int:id>/words/raw', methods=['GET'])
  @cross_origin()
  def get_group_words_raw(id):
    app.logger.info(f"Route hit: /api/groups/{id}/words/raw GET")
    try:
      cursor = app.db.cursor()
        
      # First check if group exists
      cursor.execute('SELECT COUNT(*) as count FROM groups WHERE id = ?', (id,))
      if cursor.fetchone()['count'] == 0:
        app.logger.warning(f"Group not found: {id}")
        return jsonify({"error": "Group not found"}), 404
        
      # Get all words for the group
      cursor.execute('''
        SELECT 
        w.id,
        w.kanji,
        w.english,
        w.romaji,
        w.parts
        FROM words w
        JOIN word_groups wg ON w.id = wg.word_id
        WHERE wg.group_id = ?
      ''', (id,))
        
      words = cursor.fetchall()
        
      # Convert to list of dictionaries
      words_data = [{
        'id': word['id'],
        'kanji': word['kanji'],
        'english': word['english'],
        'romaji': word['romaji'],
        'parts': word['parts']
      } for word in words]
        
      app.logger.info(f"Retrieved {len(words_data)} words for group {id}")
        
      return jsonify({
        'words': words_data,
        'count': len(words_data)
      })
        
    except Exception as e:
        app.logger.error(f"Error getting raw words for group {id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
      
  

  @app.route('/api/groups/<int:id>/study-sessions', methods=['GET'])
  @cross_origin()
  def get_group_study_sessions(id):
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = int(request.args.get('page', 1))
      sessions_per_page = 10
      offset = (page - 1) * sessions_per_page

      # Get sorting parameters
      sort_by = request.args.get('sort_by', 'created_at')
      order = request.args.get('order', 'desc')  # Default to newest first

      # Map frontend sort keys to database columns
      sort_mapping = {
        'startTime': 'created_at',
        'endTime': 'last_activity_time',
        'activityName': 'a.name',
        'groupName': 'g.name',
        'reviewItemsCount': 'review_count'
      }

      # Use mapped sort column or default to created_at
      sort_column = sort_mapping.get(sort_by, 'created_at')

      # Get total count for pagination
      cursor.execute('''
        SELECT COUNT(*)
        FROM study_sessions
        WHERE group_id = ?
      ''', (id,))
      total_sessions = cursor.fetchone()[0]
      total_pages = (total_sessions + sessions_per_page - 1) // sessions_per_page

      # Get study sessions for this group with dynamic calculations
      cursor.execute(f'''
        SELECT 
          s.id,
          s.group_id,
          s.study_activity_id,
          s.created_at as start_time,
          (
            SELECT MAX(created_at)
            FROM word_review_items
            WHERE study_session_id = s.id
          ) as last_activity_time,
          a.name as activity_name,
          g.name as group_name,
          (
            SELECT COUNT(*)
            FROM word_review_items
            WHERE study_session_id = s.id
          ) as review_count
        FROM study_sessions s
        JOIN study_activities a ON s.study_activity_id = a.id
        JOIN groups g ON s.group_id = g.id
        WHERE s.group_id = ?
        ORDER BY {sort_column} {order}
        LIMIT ? OFFSET ?
      ''', (id, sessions_per_page, offset))
      
      sessions = cursor.fetchall()
      sessions_data = []
      
      for session in sessions:
        # If there's no last_activity_time, use start_time + 30 minutes
        end_time = session["last_activity_time"]
        if not end_time:
            end_time = cursor.execute('SELECT datetime(?, "+30 minutes")', (session["start_time"],)).fetchone()[0]
        
        sessions_data.append({
          "id": session["id"],
          "group_id": session["group_id"],
          "group_name": session["group_name"],
          "study_activity_id": session["study_activity_id"],
          "activity_name": session["activity_name"],
          "start_time": session["start_time"],
          "end_time": end_time,
          "review_items_count": session["review_count"]
        })

      return jsonify({
        'study_sessions': sessions_data,
        'total_pages': total_pages,
        'current_page': page
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500