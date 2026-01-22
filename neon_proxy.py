# Replace your neon_proxy.py with this DEBUGGING version
import os
import sys
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

print("🚀 Starting Neon Proxy...", file=sys.stderr)

app = Flask(__name__)
CORS(app)

# Test basic route first
@app.route('/')
def index():
    return jsonify({
        'service': 'Neon Proxy',
        'status': 'running',
        'endpoints': ['/health', '/query', '/batch']
    })

@app.route('/health')
def health():
    try:
        # Try to import and test database connection
        import psycopg2
        NEON_URL = os.environ.get('NEON_URL', 
            'postgresql://neondb_owner:npg_3l6oBALVutJx@ep-still-lab-afqaguni-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require')
        
        conn = psycopg2.connect(NEON_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 as health, version() as version")
        result = cursor.fetchone()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'version': result[1] if result else 'unknown'
        })
    except Exception as e:
        print(f"❌ Health check failed: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'neon_url': os.environ.get('NEON_URL', 'not set')[:50] + '...' if os.environ.get('NEON_URL') else 'not set'
        }), 500

@app.route('/query', methods=['POST'])
def execute_query():
    try:
        data = request.json
        if not data or 'sql' not in data:
            return jsonify({'error': 'Missing SQL query'}), 400
        
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        NEON_URL = os.environ.get('NEON_URL')
        sql = data['sql']
        params = data.get('params', [])
        
        print(f"📝 Executing query: {sql[:100]}...", file=sys.stderr)
        
        conn = psycopg2.connect(NEON_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql, params)
        
        if sql.strip().upper().startswith('SELECT'):
            results = cursor.fetchall()
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
        print(f"❌ Query error: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    print("✅ Flask app loaded successfully", file=sys.stderr)
    print(f"🌍 Environment variables: {dict(os.environ)}", file=sys.stderr)
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🔄 Starting server on port {port}...", file=sys.stderr)
    
    # Use gunicorn in production, but for debugging use Flask dev server
    if os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
        from gunicorn.app.base import BaseApplication
        
        class StandaloneApplication(BaseApplication):
            def __init__(self, app, options=None):
                self.application = app
                self.options = options or {}
                super().__init__()
            
            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key, value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'0.0.0.0:{port}',
            'workers': 2,
            'timeout': 120,
            'accesslog': '-',
            'errorlog': '-',
            'loglevel': 'debug'
        }
        
        print("🚀 Starting with gunicorn...", file=sys.stderr)
        StandaloneApplication(app, options).run()
    else:
        print("🔧 Starting with Flask dev server...", file=sys.stderr)
        app.run(host='0.0.0.0', port=port, debug=True)