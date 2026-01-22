# neon_proxy.py - Save this in your project
import os
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Neon URL from environment
NEON_URL = os.environ.get('NEON_URL', 'postgresql://neondb_owner:npg_3l6oBALVutJx@ep-still-lab-afqaguni-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        with psycopg2.connect(NEON_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 as health")
                result = cursor.fetchone()
                return jsonify({
                    'status': 'healthy',
                    'database': 'connected',
                    'result': result[0] if result else None
                })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/query', methods=['POST'])
def execute_query():
    """Execute SQL query on Neon"""
    try:
        data = request.json
        if not data or 'sql' not in data:
            return jsonify({'error': 'Missing SQL query'}), 400
        
        sql = data['sql']
        params = data.get('params', [])
        
        logger.info(f"Executing query: {sql[:100]}...")
        
        with psycopg2.connect(NEON_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql, params)
                
                if sql.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    # Convert to list of dicts
                    return jsonify({
                        'success': True,
                        'results': results,
                        'rowcount': len(results)
                    })
                else:
                    conn.commit()
                    return jsonify({
                        'success': True,
                        'rowcount': cursor.rowcount
                    })
                    
    except Exception as e:
        logger.error(f"Query error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/batch', methods=['POST'])
def execute_batch():
    """Execute batch operations"""
    try:
        data = request.json
        if not data or 'queries' not in data:
            return jsonify({'error': 'Missing queries'}), 400
        
        queries = data['queries']
        results = []
        
        with psycopg2.connect(NEON_URL) as conn:
            for query_data in queries:
                sql = query_data['sql']
                params = query_data.get('params', [])
                
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql, params)
                    
                    if sql.strip().upper().startswith('SELECT'):
                        results.append({
                            'success': True,
                            'results': cursor.fetchall()
                        })
                    else:
                        results.append({
                            'success': True,
                            'rowcount': cursor.rowcount
                        })
            
            conn.commit()
            return jsonify({
                'success': True,
                'results': results
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)