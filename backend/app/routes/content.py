"""
Content routes - Movies, Albums, Games, Books, Locations

These endpoints are public (no JWT required).
They fetch data from external APIs and cache in PostgreSQL.
"""

import asyncio
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.content import Movie, Album, Game, Book, Location, MovieType, GameDifficulty
from app.services.external_apis import movies, albums, games, books, locations

content_bp = Blueprint('content', __name__)


# ────────────────────────────────────────────────────────────────
# Helper Functions
# ────────────────────────────────────────────────────────────────

def get_pagination_params():
    """Extract and validate limit/offset from query params"""
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        # Enforce reasonable limits
        limit = max(1, min(limit, 100))
        offset = max(0, offset)
        return limit, offset
    except (ValueError, TypeError):
        return 20, 0


def save_or_update_movie(db, movie_data):
    """Save or update a movie in the database"""
    existing = db.query(Movie).filter_by(id=movie_data['id']).first()
    if existing:
        # Update existing
        for key, value in movie_data.items():
            if key == 'type' and isinstance(value, str):
                value = MovieType(value)
            setattr(existing, key, value)
        return existing
    else:
        # Create new
        if isinstance(movie_data.get('type'), str):
            movie_data['type'] = MovieType(movie_data['type'])
        movie = Movie(**movie_data)
        db.add(movie)
        return movie


def save_or_update_album(db, album_data):
    """Save or update an album in the database"""
    existing = db.query(Album).filter_by(id=album_data['id']).first()
    if existing:
        for key, value in album_data.items():
            setattr(existing, key, value)
        return existing
    else:
        album = Album(**album_data)
        db.add(album)
        return album


def save_or_update_game(db, game_data):
    """Save or update a game in the database"""
    existing = db.query(Game).filter_by(id=game_data['id']).first()
    if existing:
        for key, value in game_data.items():
            if key == 'difficulty' and value and isinstance(value, str):
                value = GameDifficulty(value)
            setattr(existing, key, value)
        return existing
    else:
        if game_data.get('difficulty') and isinstance(game_data['difficulty'], str):
            game_data['difficulty'] = GameDifficulty(game_data['difficulty'])
        game = Game(**game_data)
        db.add(game)
        return game


def save_or_update_book(db, book_data):
    """Save or update a book in the database"""
    # Map totalPages to total_pages
    if 'totalPages' in book_data:
        book_data['total_pages'] = book_data.pop('totalPages')
    
    existing = db.query(Book).filter_by(id=book_data['id']).first()
    if existing:
        for key, value in book_data.items():
            setattr(existing, key, value)
        return existing
    else:
        book = Book(**book_data)
        db.add(book)
        return book


def save_or_update_location(db, location_data):
    """Save or update a location in the database"""
    existing = db.query(Location).filter_by(id=location_data['id']).first()
    if existing:
        for key, value in location_data.items():
            setattr(existing, key, value)
        return existing
    else:
        location = Location(**location_data)
        db.add(location)
        return location


# ────────────────────────────────────────────────────────────────
# Movie Endpoints
# ────────────────────────────────────────────────────────────────

@content_bp.route('/movies', methods=['GET'])
def get_movies():
    """
    Get all movies with optional filtering
    ---
    tags:
      - Content
    parameters:
      - name: search
        in: query
        type: string
        description: Search by title or director
      - name: year
        in: query
        type: integer
        description: Filter by year
      - name: type
        in: query
        type: string
        enum: [movie, tv]
        description: Filter by type
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of items to return
      - name: offset
        in: query
        type: integer
        default: 0
        description: Pagination offset
    responses:
      200:
        description: Movies list
      400:
        description: Bad request
    """
    try:
        db = get_db()
        limit, offset = get_pagination_params()
        
        search = request.args.get('search', '').strip()
        year = request.args.get('year', type=int)
        type_filter = request.args.get('type')
        
        # If search query provided, fetch from external API
        if search:
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    movies.search_movies(
                        search,
                        year=year,
                        type_filter=type_filter,
                        limit=limit,
                        offset=offset
                    )
                )
            finally:
                loop.close()
            
            # Save results to database
            for movie_data in result['data']:
                try:
                    save_or_update_movie(db, movie_data)
                except Exception as e:
                    print(f"Error saving movie: {e}")
            
            db.commit()
            
            return jsonify({
                'data': result['data'],
                'total': result['total'],
                'limit': limit,
                'offset': offset
            }), 200
        
        # Otherwise, query from database
        query = db.query(Movie)
        
        if year:
            query = query.filter(Movie.year == year)
        if type_filter:
            query = query.filter(Movie.type == MovieType(type_filter))
        
        total = query.count()
        movies_list = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'data': [m.to_dict() for m in movies_list],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@content_bp.route('/movies/<movie_id>', methods=['GET'])
def get_movie_by_id(movie_id):
    """
    Get movie details by ID
    ---
    tags:
      - Content
    parameters:
      - name: movie_id
        in: path
        type: string
        required: true
        description: Movie ID
    responses:
      200:
        description: Movie details
      404:
        description: Movie not found
    """
    try:
        db = get_db()
        
        # Check database first
        movie = db.query(Movie).filter_by(id=movie_id).first()
        
        if not movie:
            # Try fetching from external API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                movie_data = loop.run_until_complete(movies.get_movie_by_id(movie_id))
            finally:
                loop.close()
            
            if movie_data:
                movie = save_or_update_movie(db, movie_data)
                db.commit()
            else:
                return jsonify({'error': 'Movie not found'}), 404
        
        return jsonify(movie.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# ────────────────────────────────────────────────────────────────
# Album Endpoints
# ────────────────────────────────────────────────────────────────

@content_bp.route('/albums', methods=['GET'])
def get_albums():
    """
    Get all albums with optional filtering
    ---
    tags:
      - Content
    parameters:
      - name: search
        in: query
        type: string
        description: Search by title or artist
      - name: artist
        in: query
        type: string
        description: Filter by artist
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of items to return
      - name: offset
        in: query
        type: integer
        default: 0
        description: Pagination offset
    responses:
      200:
        description: Albums list
      400:
        description: Bad request
    """
    try:
        db = get_db()
        limit, offset = get_pagination_params()
        
        search = request.args.get('search', '').strip()
        artist_filter = request.args.get('artist', '').strip()
        
        # If search query provided, fetch from external API
        if search or artist_filter:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    albums.search_albums(
                        search or artist_filter,
                        artist=artist_filter if artist_filter else None,
                        limit=limit,
                        offset=offset
                    )
                )
            finally:
                loop.close()
            
            # Save results to database
            for album_data in result['data']:
                try:
                    save_or_update_album(db, album_data)
                except Exception as e:
                    print(f"Error saving album: {e}")
            
            db.commit()
            
            return jsonify({
                'data': result['data'],
                'total': result['total'],
                'limit': limit,
                'offset': offset
            }), 200
        
        # Otherwise, query from database
        query = db.query(Album)
        total = query.count()
        albums_list = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'data': [a.to_dict() for a in albums_list],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@content_bp.route('/albums/<album_id>', methods=['GET'])
def get_album_by_id(album_id):
    """
    Get album details by ID
    ---
    tags:
      - Content
    parameters:
      - name: album_id
        in: path
        type: string
        required: true
        description: Album ID
    responses:
      200:
        description: Album details
      404:
        description: Album not found
    """
    try:
        db = get_db()
        
        # Check database first
        album = db.query(Album).filter_by(id=album_id).first()
        
        if not album:
            # Try fetching from external API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                album_data = loop.run_until_complete(albums.get_album_by_id(album_id))
            finally:
                loop.close()
            
            if album_data:
                album = save_or_update_album(db, album_data)
                db.commit()
            else:
                return jsonify({'error': 'Album not found'}), 404
        
        return jsonify(album.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# ────────────────────────────────────────────────────────────────
# Game Endpoints
# ────────────────────────────────────────────────────────────────

@content_bp.route('/games', methods=['GET'])
def get_games():
    """
    Get all games with optional filtering
    ---
    tags:
      - Content
    parameters:
      - name: search
        in: query
        type: string
        description: Search by title
      - name: platform
        in: query
        type: string
        description: Filter by platform
      - name: difficulty
        in: query
        type: string
        enum: [Easy, Medium, Hard]
        description: Filter by difficulty
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of items to return
      - name: offset
        in: query
        type: integer
        default: 0
        description: Pagination offset
    responses:
      200:
        description: Games list
      400:
        description: Bad request
    """
    try:
        db = get_db()
        limit, offset = get_pagination_params()
        
        search = request.args.get('search', '').strip()
        platform = request.args.get('platform', '').strip()
        difficulty = request.args.get('difficulty', '').strip()
        
        # If search query provided, fetch from external API
        if search:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    games.search_games(
                        search,
                        platform=platform if platform else None,
                        difficulty=difficulty if difficulty else None,
                        limit=limit,
                        offset=offset
                    )
                )
            finally:
                loop.close()
            
            # Save results to database
            for game_data in result['data']:
                try:
                    save_or_update_game(db, game_data)
                except Exception as e:
                    print(f"Error saving game: {e}")
            
            db.commit()
            
            return jsonify({
                'data': result['data'],
                'total': result['total'],
                'limit': limit,
                'offset': offset
            }), 200
        
        # Otherwise, query from database
        query = db.query(Game)
        
        if platform:
            query = query.filter(Game.platform.ilike(f'%{platform}%'))
        if difficulty:
            query = query.filter(Game.difficulty == GameDifficulty(difficulty))
        
        total = query.count()
        games_list = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'data': [g.to_dict() for g in games_list],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@content_bp.route('/games/<game_id>', methods=['GET'])
def get_game_by_id(game_id):
    """
    Get game details by ID
    ---
    tags:
      - Content
    parameters:
      - name: game_id
        in: path
        type: string
        required: true
        description: Game ID
    responses:
      200:
        description: Game details
      404:
        description: Game not found
    """
    try:
        db = get_db()
        
        # Check database first
        game = db.query(Game).filter_by(id=game_id).first()
        
        if not game:
            # Try fetching from external API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                game_data = loop.run_until_complete(games.get_game_by_id(game_id))
            finally:
                loop.close()
            
            if game_data:
                game = save_or_update_game(db, game_data)
                db.commit()
            else:
                return jsonify({'error': 'Game not found'}), 404
        
        return jsonify(game.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# ────────────────────────────────────────────────────────────────
# Book Endpoints
# ────────────────────────────────────────────────────────────────

@content_bp.route('/books', methods=['GET'])
def get_books():
    """
    Get all books with optional filtering
    ---
    tags:
      - Content
    parameters:
      - name: search
        in: query
        type: string
        description: Search by title or author
      - name: author
        in: query
        type: string
        description: Filter by author
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of items to return
      - name: offset
        in: query
        type: integer
        default: 0
        description: Pagination offset
    responses:
      200:
        description: Books list
      400:
        description: Bad request
    """
    try:
        db = get_db()
        limit, offset = get_pagination_params()
        
        search = request.args.get('search', '').strip()
        author_filter = request.args.get('author', '').strip()
        
        # If search query provided, fetch from external API
        if search or author_filter:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    books.search_books(
                        search or author_filter,
                        author=author_filter if author_filter else None,
                        limit=limit,
                        offset=offset
                    )
                )
            finally:
                loop.close()
            
            # Save results to database
            for book_data in result['data']:
                try:
                    save_or_update_book(db, book_data)
                except Exception as e:
                    print(f"Error saving book: {e}")
            
            db.commit()
            
            return jsonify({
                'data': result['data'],
                'total': result['total'],
                'limit': limit,
                'offset': offset
            }), 200
        
        # Otherwise, query from database
        query = db.query(Book)
        total = query.count()
        books_list = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'data': [b.to_dict() for b in books_list],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@content_bp.route('/books/<book_id>', methods=['GET'])
def get_book_by_id(book_id):
    """
    Get book details by ID
    ---
    tags:
      - Content
    parameters:
      - name: book_id
        in: path
        type: string
        required: true
        description: Book ID
    responses:
      200:
        description: Book details
      404:
        description: Book not found
    """
    try:
        db = get_db()
        
        # Check database first
        book = db.query(Book).filter_by(id=book_id).first()
        
        if not book:
            # Try fetching from external API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                book_data = loop.run_until_complete(books.get_book_by_id(book_id))
            finally:
                loop.close()
            
            if book_data:
                book = save_or_update_book(db, book_data)
                db.commit()
            else:
                return jsonify({'error': 'Book not found'}), 404
        
        return jsonify(book.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


# ────────────────────────────────────────────────────────────────
# Location Endpoints
# ────────────────────────────────────────────────────────────────

@content_bp.route('/locations', methods=['GET'])
def get_locations():
    """
    Get all travel destinations with optional filtering
    ---
    tags:
      - Content
    parameters:
      - name: search
        in: query
        type: string
        description: Search by name or city
      - name: country
        in: query
        type: string
        description: Filter by country
      - name: limit
        in: query
        type: integer
        default: 20
        description: Maximum number of items to return
      - name: offset
        in: query
        type: integer
        default: 0
        description: Pagination offset
    responses:
      200:
        description: Locations list
      400:
        description: Bad request
    """
    try:
        db = get_db()
        limit, offset = get_pagination_params()
        
        search = request.args.get('search', '').strip()
        country = request.args.get('country', '').strip()
        
        # If search query provided, fetch from external API
        if search or country:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    locations.search_locations(
                        search or country,
                        country=country if country else None,
                        limit=limit,
                        offset=offset
                    )
                )
            finally:
                loop.close()
            
            # Save results to database
            for location_data in result['data']:
                try:
                    save_or_update_location(db, location_data)
                except Exception as e:
                    print(f"Error saving location: {e}")
            
            db.commit()
            
            return jsonify({
                'data': result['data'],
                'total': result['total'],
                'limit': limit,
                'offset': offset
            }), 200
        
        # Otherwise, query from database
        query = db.query(Location)
        total = query.count()
        locations_list = query.offset(offset).limit(limit).all()
        
        return jsonify({
            'data': [loc.to_dict() for loc in locations_list],
            'total': total,
            'limit': limit,
            'offset': offset
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@content_bp.route('/locations/<location_id>', methods=['GET'])
def get_location_by_id(location_id):
    """
    Get location details by ID
    ---
    tags:
      - Content
    parameters:
      - name: location_id
        in: path
        type: string
        required: true
        description: Location ID
    responses:
      200:
        description: Location details
      404:
        description: Location not found
    """
    try:
        db = get_db()
        
        # Check database first
        location = db.query(Location).filter_by(id=location_id).first()
        
        if not location:
            # Try fetching from external API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                location_data = loop.run_until_complete(locations.get_location_by_id(location_id))
            finally:
                loop.close()
            
            if location_data:
                location = save_or_update_location(db, location_data)
                db.commit()
            else:
                return jsonify({'error': 'Location not found'}), 404
        
        return jsonify(location.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
