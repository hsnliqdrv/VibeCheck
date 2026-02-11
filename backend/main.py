import os
from app import create_app
from app.database import close_db

app = create_app()

# Register teardown
app.teardown_appcontext(close_db)


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    ---
    tags:
      - Health
    responses:
      200:
        description: Service is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
            service:
              type: string
              example: VibeCheck API
    """
    return {'status': 'healthy', 'service': 'VibeCheck API'}, 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
