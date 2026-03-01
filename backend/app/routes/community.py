# backend/app/routes/community.py
from flask import Blueprint, jsonify, request

community_bp = Blueprint('community', __name__, url_prefix='/community')

# ----------------------
# MOCK DATA (заменить на реальные модели/ORM)
# ----------------------
ROOMS = [
    {
        "id": "neon-noir",
        "title": "Neon Noir",
        "subtitle": "Cyberpunk aesthetics, neon lights, and dystopian futures",
        "members_count": 12453,
        "posts_count": 3842,
        "image": "https://images.unsplash.com/photo-1550745165-9bc0b252726f",
        "header_image": "https://images.unsplash.com/photo-1550745165-9bc0b252726f",
        "is_trending": True,
        "tags": ["#NeonNoir", "#cyberpunk"],
        "moderators": [{"id":"sarah","display_name":"sarah_vaporwave","avatar":""}]
    },
    {
        "id": "dark-academia",
        "title": "Dark Academia",
        "subtitle": "Classical literature, vintage libraries, and intellectual pursuits",
        "members_count": 18926,
        "posts_count": 5621,
        "image": "https://images.unsplash.com/photo-1514894780063-588132192a9a",
        "header_image": "https://images.unsplash.com/photo-1514894780063-588132192a9a",
        "is_trending": True,
        "tags": ["#DarkAcademia"],
        "moderators": [{"id":"pixel","display_name":"pixel_dreams","avatar":""}]
    },
]

SHARES = {
    "neon-noir": [
        {"id":"p1","title":"","image":"https://images.unsplash.com/photo-1515879218367-8466d910aaa4","category":"travel","caption":"Tokyo street"},
        {"id":"p2","title":"","image":"https://images.unsplash.com/photo-1517336714731-489689fd1ca8","category":"music","caption":"Vinyl mix"}
    ],
    "dark-academia": [
        {"id":"d1","title":"","image":"https://images.unsplash.com/photo-1512820790803-83ca734da794","category":"books","caption":"Reading nook"}
    ]
}

# ----------------------
# Routes
# ----------------------

@community_bp.route('/rooms', methods=['GET'])
def list_rooms():
    """
    GET /community/rooms
    Возвращает список комнат. Поддерживает опциональные параметры:
      - q: search query
      - limit, offset
    """
    q = request.args.get('q', '').strip().lower()
    limit = int(request.args.get('limit') or 0) or None
    offset = int(request.args.get('offset') or 0) or 0

    results = ROOMS
    if q:
        results = [r for r in ROOMS if q in (r.get('title','') + r.get('subtitle','')).lower()]

    if limit:
        results = results[offset: offset + limit]
    else:
        results = results[offset:]

    return jsonify({"rooms": results}), 200


@community_bp.route('/rooms/<room_id>', methods=['GET'])
def room_details(room_id):
    """
    GET /community/rooms/<room_id>
    Возвращает детальную информацию по комнате.
    """
    r = next((x for x in ROOMS if x['id'] == room_id), None)
    if not r:
        return jsonify({"error": "Room not found"}), 404
    return jsonify({"room": r}), 200


@community_bp.route('/rooms/<room_id>/shares', methods=['GET'])
def room_shares(room_id):
    """
    GET /community/rooms/<room_id>/shares
    Возвращает shares (посты) для комнаты.
    Поддерживает пагинацию через limit и cursor (cursor простой: индекс).
    """
    arr = SHARES.get(room_id, [])
    limit = int(request.args.get('limit', 12))
    cursor = request.args.get('cursor')
    # Простой cursor: если передан — считаем его числом и сдвигаем начало
    start = 0
    if cursor:
        try:
            start = int(cursor)
        except Exception:
            start = 0

    slice_ = arr[start:start + limit]
    next_cursor = start + len(slice_) if (start + len(slice_)) < len(arr) else None

    return jsonify({"shares": slice_, "next_cursor": next_cursor}), 200
