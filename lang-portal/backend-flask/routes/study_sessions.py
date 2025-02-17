from flask import request, jsonify, g
from flask_cors import cross_origin
from datetime import datetime
import math
import json

def load(app):
  @app.route('/api/study-sessions', methods=['GET'])
  @cross_origin()
  def get_study_sessions():
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      offset = (page - 1) * per_page

      # Get sorting parameters from the query string
      sort_by = request.args.get('sort_by', 'id')  # Default to sorting by 'kanji'
      order = request.args.get('order', 'asc').upper()  # Default to ascending order

      # Define valid columns mapping
      valid_columns = {
        'id': 'ss.id',
        'group_name': 'g.name',
        'activity_name': 'sa.name',
        'start_time': 'ss.created_at',
        'end_time': 'ss.created_at',
        'review_items_count': 'review_items_count'
      }
      
      # Validate sort_by parameter
      if sort_by not in valid_columns:
        app.logger.warning(f"Invalid sort field: {sort_by}, defaulting to Id")
        sort_by = 'id'
        
      # Validate order parameter
      if order not in ['ASC', 'DESC']:
        app.logger.warning(f"Invalid sort order: {order}, defaulting to ASC")
        order = 'ASC'
        

        
      # Get total count
      cursor.execute('''
        SELECT COUNT(*) as count 
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
      ''')
      total_count = cursor.fetchone()['count']

      # Get paginated sessions
      query = f'''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as study_activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        GROUP BY ss.id
        ORDER BY {valid_columns[sort_by]} {order}
        LIMIT ? OFFSET ?
      '''
      cursor.execute(query, (per_page, offset))
      sessions = cursor.fetchall()

      return jsonify({
        'items': [{
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'study_activity_id': session['study_activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],  # For now, just use the same time since we don't track end time
          'review_items_count': session['review_items_count']
        } for session in sessions],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_count / per_page)
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/<id>', methods=['GET'])
  @cross_origin()
  def get_study_session(id):
    try:
      cursor = app.db.cursor()
      
      # Get session details
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as study_activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        WHERE ss.id = ?
        GROUP BY ss.id
      ''', (id,))
      
      session = cursor.fetchone()
      if not session:
        return jsonify({"error": "Study session not found"}), 404

      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      offset = (page - 1) * per_page

      # Get the words reviewed in this session with their review status
      cursor.execute('''
        SELECT 
          w.*,
          COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0) as session_correct_count,
          COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0) as session_wrong_count
        FROM words w
        JOIN word_review_items wri ON wri.word_id = w.id
        WHERE wri.study_session_id = ?
        GROUP BY w.id
        ORDER BY w.kanji
        LIMIT ? OFFSET ?
      ''', (id, per_page, offset))
      
      words = cursor.fetchall()

      # Get total count of words
      cursor.execute('''
        SELECT COUNT(DISTINCT w.id) as count
        FROM words w
        JOIN word_review_items wri ON wri.word_id = w.id
        WHERE wri.study_session_id = ?
      ''', (id,))
      
      total_count = cursor.fetchone()['count']

      return jsonify({
        'session': {
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'study_activity_id': session['study_activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],  # For now, just use the same time
          'review_items_count': session['review_items_count']
        },
        'words': [{
          'id': word['id'],
          'kanji': word['kanji'],
          'romaji': word['romaji'],
          'english': word['english'],
          'correct_count': word['session_correct_count'],
          'wrong_count': word['session_wrong_count']
        } for word in words],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_count / per_page)
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/reset', methods=['POST'])
  @cross_origin()
  def reset_study_sessions():
    try:
      cursor = app.db.cursor()
      
      # First delete all word review items since they have foreign key constraints
      cursor.execute('DELETE FROM word_review_items')
      
      # Then delete all study sessions
      cursor.execute('DELETE FROM study_sessions')
      
      app.db.commit()
      
      return jsonify({"message": "Study history cleared successfully"}), 200
    except Exception as e:
      return jsonify({"error": str(e)}), 500
    
    # todo /api/study_sessions POST
  @app.route('/api/study-sessions', methods=['POST'])
  @cross_origin()
  def create_study_session():
    app.logger.info("Route hit: /api/study-sessions POST")
    try:
      data = request.get_json() # Get JSON data from request
      app.logger.debug(f"Received data: {data}")
      
      # Validate required fields
      required_fields = ['group_id', 'study_activity_id']
      if not all(field in data for field in required_fields):
        app.logger.warning(f"Missing required fields in request: {data}")
        return jsonify({"error": "Missing required fields"}), 400
      # Add to existing validation
      if not isinstance(data.get('group_id'), int) or not isinstance(data.get('study_activity_id'), int):
        app.logger.warning(f"group_id and study_activity_id must be integers: {data}")
        return jsonify({"error": "group_id and study_activity_id must be integers"}), 400      
      cursor = app.db.cursor()           
      # Add validation for group_id and activity_id
      cursor.execute('SELECT COUNT(*) as count FROM groups WHERE id = ?', (data['group_id'],))
      if cursor.fetchone()['count'] == 0:
        app.logger.error(f"Group not found: {data['group_id']}")
        return jsonify({"error": "Group not found"}), 404

      cursor.execute('SELECT COUNT(*) as count FROM study_activities WHERE id = ?', (data['study_activity_id'],))
      if cursor.fetchone()['count'] == 0:
        app.logger.error(f"Activity not found: {data['study_activity_id']}")
        return jsonify({"error": "Activity not found"}), 404

      # Insert new study session
      cursor.execute('''
        INSERT INTO study_sessions (group_id, study_activity_id, created_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (data['group_id'], data['study_activity_id']))
            
      session_id = cursor.lastrowid
      app.db.commit()
            
      # Return the created session
      cursor.execute('''
        SELECT s.*, g.name as group_name, a.name as activity_name
        FROM study_sessions s
        JOIN groups g ON s.group_id = g.id
        JOIN study_activities a ON s.study_activity_id = a.id
        WHERE s.id = ?
        ''', (session_id,))
            
      session = cursor.fetchone()
            
      return jsonify({
        'session': {
        'id': session['id'],
        'group_id': session['group_id'],
        'group_name': session['group_name'],
        'study_activity_id': session['study_activity_id'],
        'activity_name': session['activity_name'],
        'start_time': session['created_at'],
        'end_time': session['created_at'],
        'review_items_count': 0
         }
      }), 201
            
    except Exception as e:
      # app.db.rollback()
      app.db.get().rollback()
      app.logger.error(f"Error creating study session: {str(e)}")
      return jsonify({"error": str(e)}), 500
    
  # todo POST /api/study_sessions/:id/
  @app.route('/api/study-sessions/<int:session_id>', methods=['PUT'])
  @cross_origin()
  def update_study_session(session_id):
    app.logger.info(f"Route hit: /api/study-sessions/{session_id} PUT")
    try:
      data = request.get_json()
      app.logger.debug(f"Received data: {data}")
      # Input validation
      if not isinstance(data.get('group_id'), int):
        app.logger.warning(f"Invalid group_id type: {type(data.get('group_id'))}")
        return jsonify({
          "error": "group_id must be an integer"
        }), 400

      if not isinstance(data.get('study_activity_id'), int):
        app.logger.warning(f"Invalid study_activity_id type: {type(data.get('study_activity_id'))}")
        return jsonify({
          "error": "study_activity_id must be an integer"
        }), 400

      
      cursor = app.db.cursor()
            
      # Check if session exists
      cursor.execute('''
        SELECT COUNT(*) as count 
        FROM study_sessions 
        WHERE id = ?
      ''', (session_id,))
      session = cursor.fetchone()
       
      if session['count'] == 0:
        app.logger.error(f"Session not found: {session_id}")
        return jsonify({"error": "Session not found"}), 404
                
      # Validate foreign keys
      cursor.execute('SELECT id FROM groups WHERE id = ?', (data['group_id'],))
      if not cursor.fetchone():
        app.logger.error(f"Group not found: {data['group_id']}")
        return jsonify({"error": "Group not found"}), 404

      cursor.execute('SELECT id FROM study_activities WHERE id = ?', (data['study_activity_id'],))
      if not cursor.fetchone():
        app.logger.error(f"Activity not found: {data['study_activity_id']}")
        return jsonify({"error": "Activity not found"}), 404
            
      # Update session
      cursor.execute('''
        UPDATE study_sessions 
        SET group_id = ?, study_activity_id = ?
        WHERE id = ?
      ''', (data['group_id'], data['study_activity_id'], session_id))
      app.db.commit()
      
      # Get updated session
      cursor.execute('''
        SELECT s.*, g.name as group_name, a.name as activity_name,
        COUNT(wri.id) as review_items_count
        FROM study_sessions s
        JOIN groups g ON s.group_id = g.id
        JOIN study_activities a ON s.study_activity_id = a.id
        LEFT JOIN word_review_items wri ON wri.study_session_id = s.id
        WHERE s.id = ?
        GROUP BY s.id, s.group_id, g.name, a.name, s.created_at
      ''', (session_id,))
      session = cursor.fetchone()

      #updated_session = dict(cursor.fetchone())
      app.logger.info(f"Successfully updated study session: {session_id}")
            
            
      return jsonify({
        'session': {
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'study_activity_id': session['study_activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],
          'review_items_count': session['review_items_count']
        }
      }), 200

    except Exception as e:
      app.db.get().rollback()
      app.logger.error(f"Error updating session: {str(e)}")
      return jsonify({"error": str(e)}), 500 

  @app.route('/api/study-sessions/stats', methods=['GET'])
  @cross_origin()
  def get_study_sessions_stats():
    app.logger.info("Route hit: /api/study-sessions/stats GET")
    try:
        cursor = app.db.cursor()
        
        # Get time range from query parameters
        time_range = request.args.get('range', 'all')  # Options: all, today, week, month
        
        # Build date filter based on range
        date_filter = ''
        if time_range == 'today':
            date_filter = "WHERE DATE(ss.created_at) = DATE('now')"
        elif time_range == 'week':
            date_filter = "WHERE DATE(ss.created_at) >= DATE('now', '-7 days')"
        elif time_range == 'month':
            date_filter = "WHERE DATE(ss.created_at) >= DATE('now', '-30 days')"
        
        # Get overall statistics
        cursor.execute(f'''
            SELECT 
                COUNT(DISTINCT ss.id) as total_sessions,
                COUNT(DISTINCT ss.group_id) as unique_groups,
                COUNT(DISTINCT ss.study_activity_id) as unique_activities,
                COUNT(DISTINCT wri.word_id) as unique_words,
                COUNT(wri.id) as total_reviews,
                SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) as correct_reviews,
                AVG(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) * 100 as accuracy_rate,
                MAX(ss.created_at) as last_session_date
            FROM study_sessions ss
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            {date_filter}
        ''')
        overall_stats = cursor.fetchone()
        
        # Get stats by activity
        cursor.execute(f'''
            SELECT 
                sa.id as activity_id,
                sa.name as activity_name,
                COUNT(DISTINCT ss.id) as session_count,
                COUNT(DISTINCT wri.word_id) as words_reviewed,
                COUNT(wri.id) as total_reviews,
                SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) as correct_reviews,
                ROUND(AVG(CASE WHEN wri.correct = 1 THEN 1.0 ELSE 0 END) * 100, 2) as accuracy_rate
            FROM study_activities sa
            LEFT JOIN study_sessions ss ON ss.study_activity_id = sa.id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            {date_filter}
            GROUP BY sa.id, sa.name
            ORDER BY session_count DESC
        ''')
        activity_stats = cursor.fetchall()
        
        # Get stats by group
        cursor.execute(f'''
            SELECT 
                g.id as group_id,
                g.name as group_name,
                COUNT(DISTINCT ss.id) as session_count,
                COUNT(DISTINCT wri.word_id) as words_reviewed,
                COUNT(wri.id) as total_reviews,
                SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END) as correct_reviews,
                ROUND(AVG(CASE WHEN wri.correct = 1 THEN 1.0 ELSE 0 END) * 100, 2) as accuracy_rate
            FROM groups g
            LEFT JOIN study_sessions ss ON ss.group_id = g.id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            {date_filter}
            GROUP BY g.id, g.name
            ORDER BY session_count DESC
        ''')
        group_stats = cursor.fetchall()
        
        # Format response
        response_data = {
            'overall': {
                'total_sessions': overall_stats['total_sessions'],
                'unique_groups': overall_stats['unique_groups'],
                'unique_activities': overall_stats['unique_activities'],
                'unique_words': overall_stats['unique_words'],
                'total_reviews': overall_stats['total_reviews'],
                'correct_reviews': overall_stats['correct_reviews'],
                'accuracy_rate': round(overall_stats['accuracy_rate'] or 0, 2),
                'last_session_date': overall_stats['last_session_date']
            },
            'by_activity': [{
                'id': stat['activity_id'],
                'name': stat['activity_name'],
                'session_count': stat['session_count'],
                'words_reviewed': stat['words_reviewed'],
                'total_reviews': stat['total_reviews'],
                'correct_reviews': stat['correct_reviews'],
                'accuracy_rate': stat['accuracy_rate']
            } for stat in activity_stats],
            'by_group': [{
                'id': stat['group_id'],
                'name': stat['group_name'],
                'session_count': stat['session_count'],
                'words_reviewed': stat['words_reviewed'],
                'total_reviews': stat['total_reviews'],
                'correct_reviews': stat['correct_reviews'],
                'accuracy_rate': stat['accuracy_rate']
            } for stat in group_stats],
            'time_range': time_range
        }
        
        app.logger.info(f"Retrieved study session stats for time range: {time_range}")
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error retrieving study session stats: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/<int:session_id>/words', methods=['GET'])
  @cross_origin()
  def get_session_words(session_id):
    app.logger.info(f"Route hit: /api/study-sessions/{session_id}/words GET")
    try:
        cursor = app.db.cursor()
        
        # Check if session exists
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM study_sessions 
            WHERE id = ?
        ''', (session_id,))
        if cursor.fetchone()['count'] == 0:
            app.logger.warning(f"Study session not found: {session_id}")
            return jsonify({"error": "Study session not found"}), 404
            
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        
        # Get total count
        cursor.execute('''
            SELECT COUNT(DISTINCT w.id) as count
            FROM study_sessions ss
            JOIN groups g ON ss.group_id = g.id
            JOIN word_groups wg ON g.id = wg.group_id
            JOIN words w ON wg.word_id = w.id
            WHERE ss.id = ?
        ''', (session_id,))
        total_count = cursor.fetchone()['count']
        total_pages = (total_count + per_page - 1) // per_page
        
        # Get words with review status
        cursor.execute('''
            SELECT 
                w.id,
                w.kanji,
                w.romaji,
                w.english,
                w.parts,
                COUNT(DISTINCT CASE WHEN wri.correct = 1 THEN wri.id END) as correct_count,
                COUNT(DISTINCT CASE WHEN wri.correct = 0 THEN wri.id END) as wrong_count,
                MAX(wri.created_at) as last_reviewed_at
            FROM study_sessions ss
            JOIN groups g ON ss.group_id = g.id
            JOIN word_groups wg ON g.id = wg.group_id
            JOIN words w ON wg.word_id = w.id
            LEFT JOIN word_review_items wri ON wri.word_id = w.id AND wri.study_session_id = ss.id
            WHERE ss.id = ?
            GROUP BY w.id, w.kanji, w.romaji, w.english, w.parts
            ORDER BY last_reviewed_at DESC NULLS LAST, w.kanji
            LIMIT ? OFFSET ?
        ''', (session_id, per_page, offset))
        
        words = cursor.fetchall()
        words_data = []
        
        for word in words:
            word_data = {
                'id': word['id'],
                'kanji': word['kanji'],
                'romaji': word['romaji'],
                'english': word['english'],
                'parts': json.loads(word['parts']) if word['parts'] else None,
                'stats': {
                    'correct_count': word['correct_count'],
                    'wrong_count': word['wrong_count'],
                    'last_reviewed_at': word['last_reviewed_at']
                }
            }
            words_data.append(word_data)
            
        app.logger.info(f"Retrieved {len(words_data)} words for session {session_id}")
        
        return jsonify({
            'words': words_data,
            'pagination': {
                'total_items': total_count,
                'total_pages': total_pages,
                'current_page': page,
                'per_page': per_page
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error retrieving session words: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500
    
  # POST /study_sessions/:id/review
  @app.route('/api/study-sessions/<int:session_id>/review', methods=['POST'])    
  @cross_origin()
  def review_session(session_id):
    app.logger.info(f"Route hit: /api/study-sessions/{session_id}/review POST")
    try:
      data = request.get_json()
      app.logger.debug(f"Received review data: {data}")
      
      # Validate required fields
      required_fields = ['word_id', 'correct']
      if not all(field in data for field in required_fields):
        app.logger.warning("Missing required fields in review")
        return jsonify({"error": "Missing required fields. Need word_id and correct"}), 400
            
      # Validate data types
      if not isinstance(data['word_id'], int):
        app.logger.warning(f"Invalid word_id type: {data['word_id']}")
        return jsonify({"error": "word_id must be an integer"}), 400
            
      if not isinstance(data['correct'], bool):
        app.logger.warning(f"Invalid correct type: {data['correct']}")
        return jsonify({"error": "correct must be a boolean"}), 400
            
      cursor = app.db.cursor()
      
      try:
        # Start transaction
        cursor.execute('BEGIN')
            
        # Insert review record
        cursor.execute('''
          INSERT INTO word_review_items 
          (word_id, study_session_id, correct, created_at)
          VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ''', (data['word_id'], session_id, data['correct']))
            
        app.db.commit()
            
        return jsonify({
          "success": True,
          "message": "Review recorded successfully"
        })
            
      except Exception as e:
        app.db.get().rollback()
        raise e

    except Exception as e:
      app.logger.error(f"Error recording review: {str(e)}")
      return jsonify({"error": str(e)}), 500     