"""
Global Search Route

Provides search across all content types (movies, albums, games, books, locations)
"""

from flask import Blueprint, request, jsonify
from app.database import get_db
from app.models.content import Movie, Album, Game, Book, Location

search_bp = Blueprint('search', __name__)


@search_bp.route('', methods=['GET'])
def global_search():
    """
    Global search across all content types
    ---
    tags:
      - Search
    parameters:
      - name: query
        in: query
        type: string
        required: true
        description: Search query
      - name: categories
        in: query
        type: string
        description: 'Comma-separated list of categories: cinema,music,games,books,travel'
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of results per category
    responses:
      200:
        description: Search results across categories
      400:
        description: Bad request - missing query parameter
    """
    try:
        query_string = request.args.get('query', '').strip()
        if not query_string:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        try:
            limit = int(request.args.get('limit', 20))
            limit = max(1, min(limit, 100))  # Enforce reasonable limits
        except (ValueError, TypeError):
            limit = 20
        
        categories_param = request.args.get('categories', '')
        
        # Parse categories
        if categories_param:
            categories = [c.strip() for c in categories_param.split(',')]
        else:
            categories = ['cinema', 'music', 'games', 'books', 'travel']
        
        db = get_db()
        results = {
            'query': query_string,
            'results': [],
            'total': 0
        }
        
        # Search movies/TV (cinema)
        if 'cinema' in categories:
            movies = db.query(Movie).filter(
                (Movie.title.ilike(f'%{query_string}%')) | 
                (Movie.director.ilike(f'%{query_string}%'))
            ).limit(limit).all()
            results['results'].extend([{
                'category': 'cinema',
                'type': 'movie',
                **m.to_dict()
            } for m in movies])
        
        # Search albums (music)
        if 'music' in categories:
            albums = db.query(Album).filter(
                (Album.title.ilike(f'%{query_string}%')) |
                (Album.artist.ilike(f'%{query_string}%'))
            ).limit(limit).all()
            results['results'].extend([{
                'category': 'music',
                'type': 'album',
                **a.to_dict()
            } for a in albums])
        
        # Search games
        if 'games' in categories:
            games_list = db.query(Game).filter(
                Game.title.ilike(f'%{query_string}%')
            ).limit(limit).all()
            results['results'].extend([{
                'category': 'games',
                'type': 'game',
                **g.to_dict()
            } for g in games_list])
        
        # Search books
        if 'books' in categories:
            books_list = db.query(Book).filter(
                (Book.title.ilike(f'%{query_string}%')) |
                (Book.author.ilike(f'%{query_string}%'))
            ).limit(limit).all()
            results['results'].extend([{
                'category': 'books',
                'type': 'book',
                **b.to_dict()
            } for b in books_list])
        
        # Search locations (travel)
        if 'travel' in categories:
            locations_list = db.query(Location).filter(
                (Location.name.ilike(f'%{query_string}%')) |
                (Location.city.ilike(f'%{query_string}%')) |
                (Location.country.ilike(f'%{query_string}%'))
            ).limit(limit).all()
            results['results'].extend([{
                'category': 'travel',
                'type': 'location',
                **loc.to_dict()
            } for loc in locations_list])
        
        results['total'] = len(results['results'])
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
