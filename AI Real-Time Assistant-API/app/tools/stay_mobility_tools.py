from typing import List, Dict, Any, Optional
import math
import requests

from langchain_core.tools import tool
from langsmith import traceable

from app.core.config import get_settings


settings = get_settings()


# ============================================================
# Helper Functions
# ============================================================

def haversine_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculates approximate distance between two coordinates in kilometers.
    """

    radius = 6371

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(radius * c, 2)


def safe_place_coordinates(place: Dict[str, Any]) -> Optional[tuple[float, float]]:
    """
    Safely extracts latitude and longitude from a place dictionary.
    """

    lat = place.get("latitude")
    lon = place.get("longitude")

    if lat is None or lon is None:
        return None

    try:
        return float(lat), float(lon)
    except Exception:
        return None


def extract_area_name(place: Dict[str, Any]) -> str:
    """
    Extracts a readable area/locality name from address or tags.
    """

    address = place.get("address", "")
    tags = place.get("tags", {}) or {}

    if address:
        parts = [part.strip() for part in address.split(",") if part.strip()]

        if len(parts) >= 2:
            return parts[-2]

        if len(parts) == 1:
            return parts[0]

    for key in ["addr:suburb", "addr:city", "addr:street", "addr:district"]:
        if tags.get(key):
            return tags[key]

    category = place.get("category", "general")
    return f"{str(category).title()} Area"


def build_cluster_planning_tip(categories: Dict[str, int]) -> str:
    """
    Creates a planning tip based on the dominant categories inside a place cluster.
    """

    if categories.get("nightlife", 0) > 0:
        return "Good evening/night cluster. Avoid moving across distant areas late at night."

    if categories.get("cafe", 0) > 0 and categories.get("food", 0) > 0:
        return "Good food and cafe cluster. Suitable for relaxed afternoon or evening plan."

    if categories.get("heritage", 0) > 0:
        return "Good heritage cluster. Suitable for morning or afternoon sightseeing."

    if categories.get("shopping", 0) > 0:
        return "Good shopping cluster. Keep extra budget buffer."

    if categories.get("religious_place", 0) > 0:
        return "Good religious/cultural cluster. Suitable for morning or afternoon visit."

    if categories.get("beach", 0) > 0:
        return "Good beach cluster. Keep weather and return transport in mind."

    return "Use this cluster to group nearby activities and reduce travel time."


def estimate_cluster_spread(clusters: List[Dict[str, Any]]) -> float:
    """
    Estimates how spread out the activity clusters are.
    """

    if len(clusters) <= 1:
        return 3.0

    centers = []

    for cluster in clusters:
        center = cluster.get("center", {})
        lat = center.get("latitude")
        lon = center.get("longitude")

        if lat is not None and lon is not None:
            try:
                centers.append((float(lat), float(lon)))
            except Exception:
                continue

    if len(centers) <= 1:
        return 3.0

    max_distance = 0.0

    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            distance = haversine_distance_km(
                centers[i][0],
                centers[i][1],
                centers[j][0],
                centers[j][1],
            )
            max_distance = max(max_distance, distance)

    return round(max_distance, 2)


def build_daytime_transport_strategy(transport_pattern: str) -> str:
    """
    Builds daytime transport strategy based on cluster spread.
    """

    if transport_pattern == "compact":
        return (
            "Use short cabs, autos, walking where safe, or local transit. "
            "Most places appear close enough to group together."
        )

    if transport_pattern == "moderate":
        return (
            "Group places by area. Use public transport during the day where available "
            "and cabs for less connected routes."
        )

    return (
        "Avoid cross-city movement on the same day. Group places strictly by cluster "
        "and use cabs only where necessary."
    )


def build_late_night_plan(has_nightlife: bool, transport_pattern: str) -> str:
    """
    Builds late-night mobility plan.
    """

    if not has_nightlife:
        return "Avoid unnecessary late-night travel. Use cabs if returning after dark."

    if transport_pattern == "compact":
        return "Keep nightlife within one nearby cluster and return by app-based cab."

    if transport_pattern == "moderate":
        return (
            "Choose one nightlife area per night. Avoid switching between distant pubs "
            "or clubs late at night."
        )

    return (
        "Avoid late-night cross-city movement. Stay close to the nightlife cluster "
        "or reduce late-night activities."
    )


def build_stay_advice(
    interests_text: str,
    travel_style: str,
    score: int,
) -> str:
    """
    Builds stay recommendation text.
    """

    if any(keyword in interests_text for keyword in ["nightlife", "club", "pub", "bar"]):
        return (
            "Prefer staying close to this area to reduce late-night cab distance "
            "and improve return safety."
        )

    if "budget" in travel_style.lower():
        return "Prefer a stay with good daytime transport access to reduce cab dependency."

    if score >= 10:
        return "This appears to be a strong stay area based on discovered places and mobility access."

    return "This area can work if accommodation price and transport access are suitable."


def build_stay_budget_impact(
    interests_text: str,
    travel_style: str,
) -> str:
    """
    Builds stay-area budget impact note.
    """

    if any(keyword in interests_text for keyword in ["nightlife", "club", "pub", "bar"]):
        return (
            "Staying near nightlife may cost more for accommodation but can reduce "
            "late-night cab expenses."
        )

    if "budget" in travel_style.lower():
        return "Staying near transit can reduce daily transport cost."

    return "Staying near activity clusters usually reduces travel time and local transport cost."


def count_nearby_mobility_points(
    cluster_center: Dict[str, Any],
    mobility_points: List[Dict[str, Any]],
    radius_km: float = 3.5,
) -> int:
    """
    Counts mobility/essential service points near a cluster.
    """

    lat1 = cluster_center.get("latitude")
    lon1 = cluster_center.get("longitude")

    if lat1 is None or lon1 is None:
        return 0

    count = 0

    for point in mobility_points:
        coords = safe_place_coordinates(point)

        if not coords:
            continue

        distance = haversine_distance_km(
            float(lat1),
            float(lon1),
            coords[0],
            coords[1],
        )

        if distance <= radius_km:
            count += 1

    return count


# ============================================================
# OpenStreetMap Stay / Mobility Discovery Helpers
# ============================================================

def build_overpass_area_query(destination: str, limit: int = 30) -> str:
    """
    Builds Overpass query for stay and mobility points.
    """

    return f"""
    [out:json][timeout:25];
    area["name"="{destination}"]->.searchArea;
    (
      node(area.searchArea)["tourism"="hotel"];
      way(area.searchArea)["tourism"="hotel"];
      relation(area.searchArea)["tourism"="hotel"];

      node(area.searchArea)["tourism"="hostel"];
      way(area.searchArea)["tourism"="hostel"];
      relation(area.searchArea)["tourism"="hostel"];

      node(area.searchArea)["tourism"="guest_house"];
      way(area.searchArea)["tourism"="guest_house"];
      relation(area.searchArea)["tourism"="guest_house"];

      node(area.searchArea)["railway"="station"];
      way(area.searchArea)["railway"="station"];
      relation(area.searchArea)["railway"="station"];

      node(area.searchArea)["station"="subway"];
      way(area.searchArea)["station"="subway"];
      relation(area.searchArea)["station"="subway"];

      node(area.searchArea)["amenity"="bus_station"];
      way(area.searchArea)["amenity"="bus_station"];
      relation(area.searchArea)["amenity"="bus_station"];

      node(area.searchArea)["amenity"="taxi"];

      node(area.searchArea)["amenity"="hospital"];
      way(area.searchArea)["amenity"="hospital"];
      relation(area.searchArea)["amenity"="hospital"];

      node(area.searchArea)["amenity"="pharmacy"];
      way(area.searchArea)["amenity"="pharmacy"];
      relation(area.searchArea)["amenity"="pharmacy"];
    );
    out center {limit};
    """


def format_osm_mobility_element(
    element: Dict[str, Any],
    destination: str,
) -> Optional[Dict[str, Any]]:
    """
    Converts one OpenStreetMap element into a standard mobility point.
    """

    tags = element.get("tags", {}) or {}

    lat = element.get("lat")
    lon = element.get("lon")

    if lat is None or lon is None:
        center = element.get("center", {})
        lat = center.get("lat")
        lon = center.get("lon")

    if lat is None or lon is None:
        return None

    name = tags.get("name", "Unnamed mobility point")

    category = "mobility_point"

    if tags.get("tourism") in ["hotel", "hostel", "guest_house"]:
        category = "lodging"

    if tags.get("railway") == "station" or tags.get("station") == "subway":
        category = "transit_station"

    if tags.get("amenity") == "bus_station":
        category = "bus_station"

    if tags.get("amenity") == "taxi":
        category = "taxi_stand"

    if tags.get("amenity") in ["hospital", "pharmacy"]:
        category = "essential_service"

    address_parts = [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:suburb"),
        tags.get("addr:city"),
        tags.get("addr:postcode"),
    ]

    address = ", ".join([part for part in address_parts if part])

    return {
        "name": name,
        "destination": destination,
        "category": category,
        "source": "OpenStreetMap",
        "address": address,
        "latitude": lat,
        "longitude": lon,
        "tags": tags,
    }


# ============================================================
# Tools
# ============================================================

@tool
@traceable(name="stay_area_discovery_tool")
def stay_area_discovery_tool(
    destination: str,
    limit: int = 30,
) -> Dict[str, Any]:
    """
    Discovers real stay and mobility related points from OpenStreetMap.

    Finds:
    - hotels
    - hostels
    - guest houses
    - railway/metro stations
    - bus stations
    - taxi stands
    - hospitals
    - pharmacies
    """

    safe_limit = min(max(int(limit or 30), 10), 60)

    try:
        query = build_overpass_area_query(
            destination=destination,
            limit=safe_limit,
        )

        response = requests.post(
            settings.OVERPASS_API_URL,
            data={"data": query},
            timeout=20,
            headers={"User-Agent": "WayFinderStayMobilityAgent/1.0"},
        )

        response.raise_for_status()
        data = response.json()

        items = []

        for element in data.get("elements", []):
            formatted = format_osm_mobility_element(
                element=element,
                destination=destination,
            )

            if formatted:
                items.append(formatted)

        category_counts: Dict[str, int] = {}

        for item in items:
            category = item.get("category", "mobility_point")
            category_counts[category] = category_counts.get(category, 0) + 1

        return {
            "destination": destination,
            "provider": "OpenStreetMap Overpass API",
            "points_found": len(items),
            "category_counts": category_counts,
            "mobility_points": items[:safe_limit],
            "limitations": [
                "OpenStreetMap may not contain all hotels, transit points, or emergency services.",
                "Transit availability, hotel prices, and live cab fares should be verified separately.",
            ],
        }

    except Exception as e:
        return {
            "destination": destination,
            "provider": "OpenStreetMap Overpass API",
            "points_found": 0,
            "category_counts": {},
            "mobility_points": [],
            "limitations": [
                "Stay and mobility points could not be fetched from OpenStreetMap.",
            ],
            "error": str(e),
        }


@tool
@traceable(name="place_clustering_tool")
def place_clustering_tool(
    discovered_places: List[Dict[str, Any]],
    radius_km: float = 4.0,
) -> Dict[str, Any]:
    """
    Groups discovered places into approximate location clusters using coordinates.
    Places within radius_km are grouped together.
    """

    places = discovered_places or []
    valid_places = []

    for place in places:
        coords = safe_place_coordinates(place)

        if coords:
            valid_places.append(
                {
                    **place,
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "area_name": extract_area_name(place),
                }
            )

    clusters = []
    used_indexes = set()

    for index, place in enumerate(valid_places):
        if index in used_indexes:
            continue

        cluster_places = [place]
        used_indexes.add(index)

        lat1 = place["latitude"]
        lon1 = place["longitude"]

        for other_index, other_place in enumerate(valid_places):
            if other_index in used_indexes:
                continue

            lat2 = other_place["latitude"]
            lon2 = other_place["longitude"]

            distance = haversine_distance_km(
                lat1=lat1,
                lon1=lon1,
                lat2=lat2,
                lon2=lon2,
            )

            if distance <= float(radius_km or 4.0):
                cluster_places.append(other_place)
                used_indexes.add(other_index)

        categories: Dict[str, int] = {}

        for item in cluster_places:
            category = item.get("category", "place")
            categories[category] = categories.get(category, 0) + 1

        dominant_category = max(categories, key=categories.get) if categories else "general"

        cluster_lat = round(
            sum(item["latitude"] for item in cluster_places) / len(cluster_places),
            6,
        )
        cluster_lon = round(
            sum(item["longitude"] for item in cluster_places) / len(cluster_places),
            6,
        )

        area_names = [
            item.get("area_name")
            for item in cluster_places
            if item.get("area_name")
        ]

        area_name = (
            max(set(area_names), key=area_names.count)
            if area_names
            else "Nearby Area"
        )

        clusters.append(
            {
                "cluster_id": f"cluster_{len(clusters) + 1}",
                "area_name": area_name,
                "center": {
                    "latitude": cluster_lat,
                    "longitude": cluster_lon,
                },
                "dominant_category": dominant_category,
                "category_counts": categories,
                "places_count": len(cluster_places),
                "places": [
                    {
                        "name": item.get("name"),
                        "category": item.get("category"),
                        "latitude": item.get("latitude"),
                        "longitude": item.get("longitude"),
                        "address": item.get("address", ""),
                    }
                    for item in cluster_places
                ],
                "planning_tip": build_cluster_planning_tip(categories),
            }
        )

    clusters = sorted(
        clusters,
        key=lambda item: item.get("places_count", 0),
        reverse=True,
    )

    return {
        "clusters_found": len(clusters),
        "radius_km": float(radius_km or 4.0),
        "clusters": clusters,
        "limitations": [
            "Clusters are based on approximate coordinates from OpenStreetMap.",
            "Actual travel time may differ due to roads, traffic, and local conditions.",
        ],
    }


@tool
@traceable(name="transport_cost_tool")
def transport_cost_tool(
    place_clusters: List[Dict[str, Any]],
    days: int,
    travelers: int = 1,
    interests: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Estimates local transport strategy and budget impact based on place clusters.

    This does not use live cab pricing.
    It uses approximate cluster spread and interest-based assumptions.
    """

    clusters = place_clusters or []
    interests_text = " ".join(interests or []).lower()

    has_nightlife = any(
        keyword in interests_text
        for keyword in [
            "nightlife",
            "club",
            "clubs",
            "pub",
            "pubs",
            "bar",
            "bars",
            "party",
        ]
    )

    days = max(int(days or 1), 1)
    travelers = max(int(travelers or 1), 1)

    if not clusters:
        near_daily = 500 * travelers
        far_daily = 900 * travelers

        return {
            "transport_pattern": "unknown",
            "estimated_cluster_spread_km": None,
            "estimated_daily_transport_cost": {
                "near_stay": near_daily,
                "far_stay": far_daily,
            },
            "estimated_total_transport_cost": {
                "near_stay": near_daily * days,
                "far_stay": far_daily * days,
            },
            "far_vs_near_difference": (far_daily - near_daily) * days,
            "budget_impact": (
                "No place clusters were available, so transport impact is estimated "
                "using generic city travel assumptions."
            ),
            "daytime_strategy": (
                "Use a mix of cabs, autos, walking where safe, and public transport depending "
                "on local availability."
            ),
            "late_night_plan": "Use app-based cabs for late-night travel.",
            "limitations": [
                "Transport estimate is approximate because no place clusters were available.",
            ],
        }

    total_spread_km = estimate_cluster_spread(clusters)

    near_stay_daily = int(350 + total_spread_km * 35)
    far_stay_daily = int(700 + total_spread_km * 60)

    if has_nightlife:
        near_stay_daily += 350
        far_stay_daily += 700

    near_stay_total = near_stay_daily * days * travelers
    far_stay_total = far_stay_daily * days * travelers

    difference = far_stay_total - near_stay_total

    if total_spread_km <= 5:
        transport_pattern = "compact"
    elif total_spread_km <= 15:
        transport_pattern = "moderate"
    else:
        transport_pattern = "spread_out"

    return {
        "transport_pattern": transport_pattern,
        "estimated_cluster_spread_km": total_spread_km,
        "estimated_daily_transport_cost": {
            "near_stay": near_stay_daily * travelers,
            "far_stay": far_stay_daily * travelers,
        },
        "estimated_total_transport_cost": {
            "near_stay": near_stay_total,
            "far_stay": far_stay_total,
        },
        "far_vs_near_difference": difference,
        "budget_impact": (
            f"Staying far from the main activity clusters may increase local transport "
            f"cost by approximately ₹{difference} for this trip."
        ),
        "daytime_strategy": build_daytime_transport_strategy(transport_pattern),
        "late_night_plan": build_late_night_plan(
            has_nightlife=has_nightlife,
            transport_pattern=transport_pattern,
        ),
        "limitations": [
            "Transport estimate is approximate and based on place cluster spread, not live cab fares.",
            "Actual fares depend on traffic, surge pricing, route distance, and time of day.",
        ],
    }


@tool
@traceable(name="stay_area_scoring_tool")
def stay_area_scoring_tool(
    destination: str,
    interests: Optional[List[str]],
    place_clusters: List[Dict[str, Any]],
    mobility_points: List[Dict[str, Any]],
    travel_style: str,
    budget: int,
) -> Dict[str, Any]:
    """
    Scores stay areas dynamically using:
    - discovered place clusters
    - mobility points
    - user interests
    - travel style
    - budget context
    """

    interests_text = " ".join(interests or []).lower()
    clusters = place_clusters or []
    mobility_points = mobility_points or []

    stay_recommendations = []

    for cluster in clusters[:6]:
        category_counts = cluster.get("category_counts", {})
        center = cluster.get("center", {})

        score = 0
        reasons = []

        if any(keyword in interests_text for keyword in ["nightlife", "club", "pub", "bar"]):
            nightlife_count = category_counts.get("nightlife", 0)
            score += nightlife_count * 5

            if nightlife_count:
                reasons.append("Strong match for nightlife interests.")

        if any(keyword in interests_text for keyword in ["cafe", "cafes", "food", "restaurant"]):
            cafe_food_count = category_counts.get("cafe", 0) + category_counts.get("food", 0)
            score += cafe_food_count * 3

            if cafe_food_count:
                reasons.append("Good cafe and food availability.")

        if any(keyword in interests_text for keyword in ["shopping", "mall", "market"]):
            shopping_count = category_counts.get("shopping", 0)
            score += shopping_count * 4

            if shopping_count:
                reasons.append("Good match for shopping interests.")

        if any(keyword in interests_text for keyword in ["history", "heritage", "museum", "fort"]):
            heritage_count = category_counts.get("heritage", 0)
            score += heritage_count * 4

            if heritage_count:
                reasons.append("Good match for heritage sightseeing.")

        nearby_mobility_score = count_nearby_mobility_points(
            cluster_center=center,
            mobility_points=mobility_points,
            radius_km=3.5,
        )

        score += nearby_mobility_score * 2

        if nearby_mobility_score:
            reasons.append("Nearby transit, lodging, or essential services found.")

        if "budget" in travel_style.lower():
            score += nearby_mobility_score

        if not reasons:
            reasons.append("Useful area based on discovered nearby places.")

        stay_recommendations.append(
            {
                "area_name": cluster.get("area_name", "Recommended Area"),
                "score": score,
                "cluster_id": cluster.get("cluster_id"),
                "dominant_category": cluster.get("dominant_category"),
                "places_count": cluster.get("places_count"),
                "category_counts": category_counts,
                "reasons": reasons,
                "stay_advice": build_stay_advice(
                    interests_text=interests_text,
                    travel_style=travel_style,
                    score=score,
                ),
                "budget_impact": build_stay_budget_impact(
                    interests_text=interests_text,
                    travel_style=travel_style,
                ),
            }
        )

    stay_recommendations = sorted(
        stay_recommendations,
        key=lambda item: item.get("score", 0),
        reverse=True,
    )

    return {
        "destination": destination,
        "recommended_stay_areas": stay_recommendations[:3],
        "selection_logic": [
            "Areas are scored using discovered place density, user interests, nearby mobility points, and travel style.",
            "Higher scores indicate stronger match for stay location.",
        ],
        "limitations": [
            "This does not book or verify hotels.",
            "Accommodation prices and exact locality safety should be verified before booking.",
        ],
    }


@tool
@traceable(name="mobility_safety_tool")
def mobility_safety_tool(
    destination: str,
    interests: Optional[List[str]],
    weather_summary: Dict[str, Any],
    news_summary: str,
    transport_plan: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Creates area and mobility safety notes using interests, weather, news, and transport plan.
    """

    interests_text = " ".join(interests or []).lower()
    news_text = (news_summary or "").lower()
    weather_text = str(weather_summary or {}).lower()

    risk_score = 0
    reasons = []

    if any(keyword in interests_text for keyword in ["nightlife", "club", "pub", "bar", "party"]):
        risk_score += 2
        reasons.append("Trip includes nightlife or late-night movement.")

    if any(keyword in news_text for keyword in ["protest", "strike", "violence", "crime", "alert", "traffic"]):
        risk_score += 2
        reasons.append("Local news may include safety or disruption signals.")

    if any(keyword in weather_text for keyword in ["rain", "storm", "thunder", "heat", "extreme"]):
        risk_score += 1
        reasons.append("Weather may affect local movement.")

    if transport_plan.get("transport_pattern") == "spread_out":
        risk_score += 1
        reasons.append("Places appear spread out, increasing travel time and late movement risk.")

    if risk_score >= 4:
        safety_level = "Medium-High"
    elif risk_score >= 2:
        safety_level = "Medium"
    else:
        safety_level = "Low"

    safety_rules = [
        "Use app-based cabs for late-night travel.",
        "Avoid isolated streets and poorly lit areas after dark.",
        "Keep phone charged and share live location with a trusted contact.",
        "Verify place timings, entry rules, and availability before visiting.",
    ]

    if "rain" in weather_text or "storm" in weather_text:
        safety_rules.append(
            "Keep indoor alternatives and avoid long outdoor movement during bad weather."
        )

    if "traffic" in news_text:
        safety_rules.append(
            "Start earlier and avoid tightly packed schedules due to traffic risk."
        )

    return {
        "destination": destination,
        "mobility_safety_level": safety_level,
        "risk_score": risk_score,
        "reasons": reasons,
        "safety_rules": list(dict.fromkeys(safety_rules)),
    }