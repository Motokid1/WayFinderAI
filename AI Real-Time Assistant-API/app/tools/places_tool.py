from typing import List, Dict, Any, Optional
import requests

from langchain_core.tools import tool
from langsmith import traceable

from app.core.config import get_settings

settings = get_settings()


INTEREST_TO_OSM_TAGS = {
    "clubs": [
        {"key": "amenity", "value": "nightclub"},
        {"key": "amenity", "value": "bar"},
        {"key": "amenity", "value": "pub"},
    ],
    "pubs": [
        {"key": "amenity", "value": "pub"},
        {"key": "amenity", "value": "bar"},
    ],
    "nightlife": [
        {"key": "amenity", "value": "nightclub"},
        {"key": "amenity", "value": "bar"},
        {"key": "amenity", "value": "pub"},
    ],
    "bars": [
        {"key": "amenity", "value": "bar"},
        {"key": "amenity", "value": "pub"},
    ],
    "cafes": [
        {"key": "amenity", "value": "cafe"},
    ],
    "restaurants": [
        {"key": "amenity", "value": "restaurant"},
    ],
    "food": [
        {"key": "amenity", "value": "restaurant"},
        {"key": "amenity", "value": "cafe"},
        {"key": "amenity", "value": "fast_food"},
    ],
    "shopping": [
        {"key": "shop", "value": "mall"},
        {"key": "shop", "value": "clothes"},
        {"key": "shop", "value": "jewelry"},
    ],
    "malls": [
        {"key": "shop", "value": "mall"},
    ],
    "history": [
        {"key": "tourism", "value": "museum"},
        {"key": "historic", "value": "monument"},
        {"key": "historic", "value": "castle"},
        {"key": "historic", "value": "fort"},
    ],
    "historical places": [
        {"key": "tourism", "value": "museum"},
        {"key": "historic", "value": "monument"},
        {"key": "historic", "value": "castle"},
        {"key": "historic", "value": "fort"},
    ],
    "museums": [
        {"key": "tourism", "value": "museum"},
    ],
    "hospitals": [
        {"key": "amenity", "value": "hospital"},
    ],
    "pharmacy": [
        {"key": "amenity", "value": "pharmacy"},
    ],
}


def normalize_interest(interest: str) -> str:
    return interest.strip().lower()


def get_osm_tags_for_interests(interests: Optional[List[str]]) -> List[Dict[str, str]]:
    interests = interests or []

    tags = []

    for interest in interests:
        normalized = normalize_interest(interest)

        for key, mapped_tags in INTEREST_TO_OSM_TAGS.items():
            if key in normalized:
                tags.extend(mapped_tags)

    if not tags:
        tags = [
            {"key": "tourism", "value": "attraction"},
            {"key": "amenity", "value": "restaurant"},
            {"key": "amenity", "value": "cafe"},
        ]

    unique = []
    seen = set()

    for tag in tags:
        identifier = f'{tag["key"]}:{tag["value"]}'
        if identifier not in seen:
            seen.add(identifier)
            unique.append(tag)

    return unique


def build_overpass_query(destination: str, tags: List[Dict[str, str]], limit: int) -> str:
    """
    Uses geocodeArea by city name and searches nodes/ways/relations inside that area.
    """

    blocks = []

    for tag in tags:
        key = tag["key"]
        value = tag["value"]

        blocks.append(f'node(area.searchArea)["{key}"="{value}"];')
        blocks.append(f'way(area.searchArea)["{key}"="{value}"];')
        blocks.append(f'relation(area.searchArea)["{key}"="{value}"];')

    blocks_text = "\n      ".join(blocks)

    return f"""
    [out:json][timeout:25];
    area["name"="{destination}"]->.searchArea;
    (
      {blocks_text}
    );
    out center {limit};
    """


def format_osm_element(element: Dict[str, Any], destination: str, category: str) -> Dict[str, Any]:
    tags = element.get("tags", {})

    lat = element.get("lat")
    lon = element.get("lon")

    if not lat or not lon:
        center = element.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")

    return {
        "name": tags.get("name", "Unnamed place"),
        "category": category,
        "source": "OpenStreetMap",
        "destination": destination,
        "address": build_address(tags),
        "latitude": lat,
        "longitude": lon,
        "osm_type": element.get("type"),
        "osm_id": element.get("id"),
        "tags": {
            "amenity": tags.get("amenity"),
            "tourism": tags.get("tourism"),
            "historic": tags.get("historic"),
            "shop": tags.get("shop"),
            "cuisine": tags.get("cuisine"),
            "opening_hours": tags.get("opening_hours"),
            "website": tags.get("website"),
            "phone": tags.get("phone"),
        },
        "verification_note": (
            "Verify current opening hours, ratings, entry rules, and availability before visiting."
        ),
    }


def build_address(tags: Dict[str, Any]) -> str:
    parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
        tags.get("addr:postcode"),
    ]

    return ", ".join([part for part in parts if part])


def infer_category_from_tags(tags: Dict[str, Any]) -> str:
    if tags.get("amenity") in ["bar", "pub", "nightclub"]:
        return "nightlife"

    if tags.get("amenity") == "cafe":
        return "cafe"

    if tags.get("amenity") in ["restaurant", "fast_food"]:
        return "food"

    if tags.get("shop"):
        return "shopping"

    if tags.get("tourism") == "museum" or tags.get("historic"):
        return "heritage"

    if tags.get("amenity") in ["hospital", "pharmacy"]:
        return "essential_service"

    return "place"


def dedupe_places(places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    unique = []

    for place in places:
        name = place.get("name", "").strip().lower()
        lat = place.get("latitude")
        lon = place.get("longitude")

        if not name or name == "unnamed place":
            continue

        identifier = f"{name}:{lat}:{lon}"

        if identifier not in seen:
            seen.add(identifier)
            unique.append(place)

    return unique


@tool
@traceable(name="places_discovery_tool")
def places_discovery_tool(
    destination: str,
    interests: Optional[List[str]] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Discover real places for a destination using OpenStreetMap Overpass API.

    Args:
        destination: City or destination name.
        interests: User interests such as clubs, pubs, cafes, shopping, history, food, hospitals.
        limit: Maximum number of places to return.

    Returns:
        Real place results from OpenStreetMap with names, categories, coordinates, and verification notes.
    """

    interests = interests or []
    tags = get_osm_tags_for_interests(interests)

    query = build_overpass_query(
        destination=destination,
        tags=tags,
        limit=min(max(limit, 5), 30),
    )

    try:
        response = requests.post(
            settings.OVERPASS_API_URL,
            data={"data": query},
            timeout=30,
            headers={
                "User-Agent": "WayFinderTravelPlanner/1.0"
            },
        )

        response.raise_for_status()
        data = response.json()

        elements = data.get("elements", [])

        places = []

        for element in elements:
            tags_data = element.get("tags", {})
            category = infer_category_from_tags(tags_data)

            places.append(
                format_osm_element(
                    element=element,
                    destination=destination,
                    category=category,
                )
            )

        unique_places = dedupe_places(places)

        return {
            "destination": destination,
            "provider": "OpenStreetMap Overpass API",
            "interests": interests,
            "tags_used": tags,
            "places_found": len(unique_places),
            "places": unique_places[:limit],
            "limitations": [
                "OpenStreetMap may not include ratings, reviews, photos, or complete opening hours.",
                "Place availability, entry rules, and timings should be verified before visiting.",
            ],
        }

    except Exception as e:
        return {
            "destination": destination,
            "provider": "OpenStreetMap Overpass API",
            "interests": interests,
            "tags_used": tags,
            "places_found": 0,
            "places": [],
            "limitations": [
                "Places could not be fetched from OpenStreetMap at this time.",
                "Use weather, budget, news, and general planning guidance as fallback.",
            ],
            "error": str(e),
        }