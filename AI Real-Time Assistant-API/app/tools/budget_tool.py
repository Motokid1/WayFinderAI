from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from langsmith import traceable


CITY_COST_PROFILES = {
    "hyderabad": {
        "cost_tier": "mid",
        "budget": {
            "accommodation": 1200,
            "food": 500,
            "local_transport": 400,
            "activities": 500,
        },
        "comfort": {
            "accommodation": 2200,
            "food": 800,
            "local_transport": 700,
            "activities": 800,
        },
        "premium": {
            "accommodation": 3800,
            "food": 1400,
            "local_transport": 1200,
            "activities": 1400,
        },
        "luxury": {
            "accommodation": 7000,
            "food": 2500,
            "local_transport": 2200,
            "activities": 2500,
        },
    },
    "bengaluru": {
        "cost_tier": "high",
        "budget": {
            "accommodation": 1400,
            "food": 600,
            "local_transport": 500,
            "activities": 600,
        },
        "comfort": {
            "accommodation": 2600,
            "food": 1000,
            "local_transport": 900,
            "activities": 1000,
        },
        "premium": {
            "accommodation": 4500,
            "food": 1600,
            "local_transport": 1400,
            "activities": 1600,
        },
        "luxury": {
            "accommodation": 8500,
            "food": 3000,
            "local_transport": 2600,
            "activities": 3000,
        },
    },
    "chennai": {
        "cost_tier": "mid",
        "budget": {
            "accommodation": 1200,
            "food": 500,
            "local_transport": 400,
            "activities": 450,
        },
        "comfort": {
            "accommodation": 2300,
            "food": 800,
            "local_transport": 700,
            "activities": 800,
        },
        "premium": {
            "accommodation": 4000,
            "food": 1400,
            "local_transport": 1200,
            "activities": 1300,
        },
        "luxury": {
            "accommodation": 7500,
            "food": 2600,
            "local_transport": 2200,
            "activities": 2400,
        },
    },
    "goa": {
        "cost_tier": "tourist_high",
        "budget": {
            "accommodation": 1800,
            "food": 800,
            "local_transport": 800,
            "activities": 900,
        },
        "comfort": {
            "accommodation": 3500,
            "food": 1300,
            "local_transport": 1300,
            "activities": 1500,
        },
        "premium": {
            "accommodation": 6500,
            "food": 2200,
            "local_transport": 2200,
            "activities": 2500,
        },
        "luxury": {
            "accommodation": 12000,
            "food": 4000,
            "local_transport": 3500,
            "activities": 4500,
        },
    },
    "mumbai": {
        "cost_tier": "very_high",
        "budget": {
            "accommodation": 1800,
            "food": 700,
            "local_transport": 600,
            "activities": 700,
        },
        "comfort": {
            "accommodation": 3500,
            "food": 1200,
            "local_transport": 1100,
            "activities": 1200,
        },
        "premium": {
            "accommodation": 6500,
            "food": 2200,
            "local_transport": 1800,
            "activities": 2200,
        },
        "luxury": {
            "accommodation": 12000,
            "food": 4000,
            "local_transport": 3200,
            "activities": 4200,
        },
    },
}


DEFAULT_CITY_PROFILE = {
    "cost_tier": "unknown",
    "budget": {
        "accommodation": 1300,
        "food": 600,
        "local_transport": 500,
        "activities": 600,
    },
    "comfort": {
        "accommodation": 2500,
        "food": 900,
        "local_transport": 800,
        "activities": 900,
    },
    "premium": {
        "accommodation": 4500,
        "food": 1600,
        "local_transport": 1400,
        "activities": 1600,
    },
    "luxury": {
        "accommodation": 8000,
        "food": 3000,
        "local_transport": 2500,
        "activities": 3000,
    },
}


CATEGORY_COST_ADJUSTMENTS = {
    "nightlife": {
        "food": 600,
        "local_transport": 700,
        "activities": 1600,
        "note": "Nightlife places were discovered, so the estimate includes venue, food, cover charge, and late-night cab buffer.",
    },
    "cafe": {
        "food": 350,
        "activities": 200,
        "note": "Cafe places were discovered, so the estimate includes cafe-hopping and casual dining buffer.",
    },
    "food": {
        "food": 450,
        "activities": 150,
        "note": "Restaurant/food places were discovered, so the estimate includes extra dining flexibility.",
    },
    "shopping": {
        "activities": 1400,
        "local_transport": 300,
        "note": "Shopping places were discovered, so the estimate includes discretionary shopping and local transport buffer.",
    },
    "heritage": {
        "activities": 350,
        "local_transport": 250,
        "note": "Heritage places were discovered, so the estimate includes tickets and local transport.",
    },
    "beach": {
        "food": 350,
        "local_transport": 500,
        "activities": 700,
        "note": "Beach places were discovered, so the estimate includes beach transport, snacks, and activity buffer.",
    },
    "essential_service": {
        "local_transport": 150,
        "note": "Essential services were found nearby; only a small emergency transport buffer is added.",
    },
}


INTEREST_KEYWORDS = {
    "nightlife": [
        "nightlife",
        "club",
        "clubs",
        "pub",
        "pubs",
        "bar",
        "bars",
        "party",
        "parties",
        "lounge",
        "lounges",
    ],
    "cafe": ["cafe", "cafes", "coffee", "brunch"],
    "food": ["food", "restaurant", "restaurants", "dining"],
    "shopping": ["shopping", "market", "markets", "mall", "malls"],
    "heritage": [
        "history",
        "historical",
        "heritage",
        "museum",
        "museums",
        "fort",
        "forts",
        "monument",
        "monuments",
    ],
    "beach": ["beach", "beaches", "shack", "shacks", "sunset"],
}


FOOD_PREFERENCE_RULES = {
    "veg": {
        "multiplier": 0.95,
        "note": "Vegetarian food is estimated slightly lower in most city plans.",
    },
    "vegan": {
        "multiplier": 1.10,
        "note": "Vegan food can cost slightly more due to limited specialized options.",
    },
    "non-veg": {
        "multiplier": 1.10,
        "note": "Non-vegetarian food is estimated slightly higher for restaurants and local specialties.",
    },
    "mixed": {
        "multiplier": 1.05,
        "note": "Mixed food preference keeps a moderate food cost buffer.",
    },
}


def normalize_style(travel_style: str) -> str:
    style = (travel_style or "budget").lower()

    if "luxury" in style:
        return "luxury"

    if "premium" in style:
        return "premium"

    if "comfort" in style or "standard" in style:
        return "comfort"

    return "budget"


def normalize_city(destination: str) -> str:
    return (destination or "").strip().lower()


def detect_interest_categories(interests: Optional[List[str]]) -> List[str]:
    interest_text = " ".join(interests or []).lower()
    categories = []

    for category, keywords in INTEREST_KEYWORDS.items():
        if any(keyword in interest_text for keyword in keywords):
            categories.append(category)

    return categories


def analyze_discovered_places(
    discovered_places: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    places = discovered_places or []

    category_counts = {}
    named_places = []

    for place in places:
        category = place.get("category", "place")
        category_counts[category] = category_counts.get(category, 0) + 1

        name = place.get("name")
        if name:
            named_places.append(
                {
                    "name": name,
                    "category": category,
                    "source": place.get("source", "OpenStreetMap"),
                }
            )

    dominant_categories = sorted(
        category_counts.keys(),
        key=lambda item: category_counts[item],
        reverse=True,
    )

    return {
        "places_found": len(places),
        "category_counts": category_counts,
        "dominant_categories": dominant_categories,
        "sample_places": named_places[:8],
    }


def infer_location_multiplier(
    city_profile: Dict[str, Any],
    place_analysis: Dict[str, Any],
    interest_categories: List[str],
) -> float:
    cost_tier = city_profile.get("cost_tier", "unknown")

    multiplier = 1.0

    if cost_tier == "mid":
        multiplier += 0.00
    elif cost_tier == "high":
        multiplier += 0.08
    elif cost_tier == "very_high":
        multiplier += 0.18
    elif cost_tier == "tourist_high":
        multiplier += 0.20
    elif cost_tier == "unknown":
        multiplier += 0.05

    category_counts = place_analysis.get("category_counts", {})

    nightlife_count = category_counts.get("nightlife", 0)
    cafe_count = category_counts.get("cafe", 0)
    food_count = category_counts.get("food", 0)
    shopping_count = category_counts.get("shopping", 0)

    if nightlife_count >= 5:
        multiplier += 0.12
    elif nightlife_count >= 2:
        multiplier += 0.07

    if cafe_count >= 5:
        multiplier += 0.05

    if food_count >= 5:
        multiplier += 0.04

    if shopping_count >= 3:
        multiplier += 0.08

    if "nightlife" in interest_categories and nightlife_count == 0:
        multiplier += 0.05

    return round(multiplier, 2)


def apply_place_category_adjustments(
    daily_costs: Dict[str, int],
    place_analysis: Dict[str, Any],
    interest_categories: List[str],
) -> tuple[Dict[str, int], List[str]]:
    adjusted = daily_costs.copy()
    notes = []

    category_counts = place_analysis.get("category_counts", {})

    categories_to_apply = set(interest_categories)

    for category in category_counts.keys():
        if category in CATEGORY_COST_ADJUSTMENTS:
            categories_to_apply.add(category)

    for category in categories_to_apply:
        rule = CATEGORY_COST_ADJUSTMENTS.get(category)

        if not rule:
            continue

        weight = 1

        count = category_counts.get(category, 0)

        if count >= 5:
            weight = 1.25
        elif count >= 2:
            weight = 1.0
        elif count == 1:
            weight = 0.75

        for key in ["food", "local_transport", "activities"]:
            if key in rule:
                adjusted[key] = int(adjusted.get(key, 0) + rule[key] * weight)

        notes.append(rule["note"])

    return adjusted, notes


def apply_location_multiplier(
    daily_costs: Dict[str, int],
    multiplier: float,
) -> Dict[str, int]:
    return {
        key: int(value * multiplier)
        for key, value in daily_costs.items()
    }


def build_range(value: int) -> Dict[str, int]:
    return {
        "low": int(value * 0.85),
        "expected": int(value),
        "high": int(value * 1.25),
    }


def get_confidence(
    city_known: bool,
    places_found: int,
    city_guide_context: str,
) -> str:
    has_city_guide = "No stored RAG city guide was found" not in (city_guide_context or "")

    if city_known and places_found > 0 and has_city_guide:
        return "high"

    if city_known and (places_found > 0 or has_city_guide):
        return "medium-high"

    if places_found > 0:
        return "medium"

    return "low"


def build_daily_budget_plan(
    days: int,
    expected_total: int,
    dominant_categories: List[str],
    budget_status: str,
) -> Dict[str, Dict[str, Any]]:
    daily_plan = {}
    base_daily_amount = int(expected_total / days)

    if not dominant_categories:
        dominant_categories = ["general"]

    category_focus_map = {
        "nightlife": "Nightlife, pubs, lounges, and safe late-night transport",
        "cafe": "Cafe hopping and relaxed dining",
        "food": "Restaurants, local food, and dining",
        "shopping": "Shopping, markets, malls, and discretionary spend",
        "heritage": "Museums, forts, monuments, and local transport",
        "beach": "Beach areas, shacks, sunsets, and local transport",
        "general": "Balanced sightseeing, food, transport, and activities",
    }

    for day in range(1, days + 1):
        category = dominant_categories[(day - 1) % len(dominant_categories)]
        focus = category_focus_map.get(category, "Balanced local exploration")

        if budget_status == "over_budget":
            guidance = "Keep this day controlled. Avoid premium add-ons and reduce paid activities."
        elif budget_status == "tight_budget":
            guidance = "Spend carefully and keep a small emergency buffer."
        else:
            guidance = "Budget is comfortable if spending stays near the estimate."

        daily_plan[f"day_{day}"] = {
            "suggested_spend": base_daily_amount,
            "focus": focus,
            "guidance": guidance,
        }

    return daily_plan


def build_budget_recommendations(
    budget_status: str,
    dominant_categories: List[str],
    style: str,
) -> List[str]:
    recommendations = []

    if budget_status == "within_budget":
        recommendations.append(
            "Your budget is reasonable for the selected destination, style, and interests."
        )

    if budget_status == "tight_budget":
        recommendations.append(
            "Your budget may work, but keep paid activities limited and monitor transport costs."
        )

    if budget_status == "over_budget":
        recommendations.append(
            "This plan may exceed your budget. Reduce premium venues, paid activities, or long-distance cab usage."
        )

    if "nightlife" in dominant_categories:
        recommendations.append(
            "Stay close to the nightlife area to reduce late-night cab costs."
        )
        recommendations.append(
            "Choose one main nightlife venue per night instead of multiple paid venues."
        )

    if "cafe" in dominant_categories:
        recommendations.append(
            "Limit cafe hopping to one or two places per day to control food expenses."
        )

    if "shopping" in dominant_categories:
        recommendations.append(
            "Set a separate shopping limit because shopping can quickly exceed the trip budget."
        )

    if "heritage" in dominant_categories:
        recommendations.append(
            "Group nearby heritage places together to reduce local transport costs."
        )

    if "beach" in dominant_categories:
        recommendations.append(
            "Keep extra transport buffer for beach areas, especially if staying far from the coast."
        )

    if style in ["premium", "luxury"]:
        recommendations.append(
            "For premium or luxury travel, the high estimate may be more realistic than the expected estimate."
        )

    return recommendations


def build_saving_plan(
    budget_status: str,
    dominant_categories: List[str],
) -> List[str]:
    if budget_status == "within_budget":
        return [
            "Keep 10–15% of the total budget unused for unexpected transport, weather changes, or entry charges."
        ]

    saving_plan = [
        "Choose accommodation close to the main activity zone.",
        "Use public transport or shared rides during daytime where safe and practical.",
        "Avoid adding too many paid activities on the same day.",
    ]

    if "nightlife" in dominant_categories:
        saving_plan.extend(
            [
                "Prefer cafes or casual lounges over high-cover-charge clubs if budget is tight.",
                "Avoid long late-night cab rides by staying near the nightlife zone.",
            ]
        )

    if "shopping" in dominant_categories:
        saving_plan.append(
            "Separate shopping money from travel money and set a fixed purchase limit."
        )

    return saving_plan


def build_budget_note(
    destination: str,
    budget_status: str,
    expected_total: int,
    user_budget: int,
    confidence: str,
) -> str:
    if budget_status == "within_budget":
        return (
            f"The expected estimate for {destination} is around ₹{expected_total}, "
            f"which fits within your planned budget of ₹{user_budget}. "
            f"Budget confidence: {confidence}."
        )

    if budget_status == "tight_budget":
        return (
            f"The expected estimate for {destination} is around ₹{expected_total}. "
            f"Your budget of ₹{user_budget} may work, but flexibility is limited. "
            f"Budget confidence: {confidence}."
        )

    return (
        f"The expected estimate for {destination} is around ₹{expected_total}, "
        f"which is above your planned budget of ₹{user_budget}. "
        f"Budget confidence: {confidence}."
    )


@tool
@traceable(name="budget_estimator_tool")
def budget_estimator_tool(
    destination: str,
    days: int,
    budget: int,
    travel_style: str,
    interests: Optional[List[str]] = None,
    food_preference: str = "mixed",
    travelers: int = 1,
    discovered_places: Optional[List[Dict[str, Any]]] = None,
    city_guide_context: str = "",
) -> Dict[str, Any]:
    """
    Dynamic location-specific budget estimator.

    Uses:
    - destination city profile
    - travel style
    - user interests
    - food preference
    - number of travelers
    - discovered real places from Places API/OpenStreetMap
    - city guide availability

    Returns:
    - range-based budget
    - category totals
    - location-specific cost drivers
    - daily budget allocation
    - confidence level
    """

    city = normalize_city(destination)
    style = normalize_style(travel_style)

    days = max(int(days or 1), 1)
    travelers = max(int(travelers or 1), 1)
    user_budget = int(budget or 0)

    city_known = city in CITY_COST_PROFILES
    city_profile = CITY_COST_PROFILES.get(city, DEFAULT_CITY_PROFILE)

    base_daily_costs = city_profile.get(style, city_profile["budget"]).copy()

    interest_categories = detect_interest_categories(interests)
    place_analysis = analyze_discovered_places(discovered_places)

    place_adjusted_costs, place_notes = apply_place_category_adjustments(
        daily_costs=base_daily_costs,
        place_analysis=place_analysis,
        interest_categories=interest_categories,
    )

    location_multiplier = infer_location_multiplier(
        city_profile=city_profile,
        place_analysis=place_analysis,
        interest_categories=interest_categories,
    )

    location_adjusted_costs = apply_location_multiplier(
        daily_costs=place_adjusted_costs,
        multiplier=location_multiplier,
    )

    food_rule = FOOD_PREFERENCE_RULES.get(
        (food_preference or "mixed").lower(),
        FOOD_PREFERENCE_RULES["mixed"],
    )

    location_adjusted_costs["food"] = int(
        location_adjusted_costs["food"] * food_rule["multiplier"]
    )

    accommodation_total = location_adjusted_costs["accommodation"] * days
    food_total = location_adjusted_costs["food"] * days * travelers
    transport_total = location_adjusted_costs["local_transport"] * days * travelers
    activities_total = location_adjusted_costs["activities"] * days * travelers

    base_total_without_adjustment = (
        base_daily_costs["accommodation"] * days
        + base_daily_costs["food"] * days * travelers
        + base_daily_costs["local_transport"] * days * travelers
        + base_daily_costs["activities"] * days * travelers
    )

    adjusted_subtotal = (
        accommodation_total
        + food_total
        + transport_total
        + activities_total
    )

    location_specific_extra = max(0, adjusted_subtotal - base_total_without_adjustment)

    buffer_percentage = 0.12

    high_variability_categories = ["nightlife", "shopping", "beach"]

    dominant_categories = place_analysis.get("dominant_categories", [])

    if any(category in dominant_categories for category in high_variability_categories):
        buffer_percentage = 0.18

    if any(category in interest_categories for category in ["nightlife", "shopping"]):
        buffer_percentage = max(buffer_percentage, 0.18)

    buffer = int(adjusted_subtotal * buffer_percentage)
    expected_total = adjusted_subtotal + buffer
    total_range = build_range(expected_total)

    budget_gap = user_budget - total_range["expected"]

    if user_budget >= total_range["expected"]:
        budget_status = "within_budget"
    elif user_budget >= total_range["low"]:
        budget_status = "tight_budget"
    else:
        budget_status = "over_budget"

    confidence = get_confidence(
        city_known=city_known,
        places_found=place_analysis.get("places_found", 0),
        city_guide_context=city_guide_context,
    )

    cost_drivers = []

    if city_known:
        cost_drivers.append(
            f"Used {destination} city cost profile with {city_profile.get('cost_tier')} cost tier."
        )
    else:
        cost_drivers.append(
            "Destination is not in the static city cost profile database, so default metro estimates were used."
        )

    if place_analysis.get("places_found", 0) > 0:
        cost_drivers.append(
            f"Used {place_analysis.get('places_found')} discovered real places to adjust budget by category."
        )
    else:
        cost_drivers.append(
            "No discovered places were available, so budget relies more on destination profile and interests."
        )

    cost_drivers.extend(place_notes)
    cost_drivers.append(food_rule["note"])

    if travelers > 1:
        cost_drivers.append(
            f"Food, transport, and activity costs were calculated for {travelers} travelers."
        )

    daily_budget_plan = build_daily_budget_plan(
        days=days,
        expected_total=total_range["expected"],
        dominant_categories=dominant_categories or interest_categories,
        budget_status=budget_status,
    )

    recommendations = build_budget_recommendations(
        budget_status=budget_status,
        dominant_categories=dominant_categories or interest_categories,
        style=style,
    )

    saving_plan = build_saving_plan(
        budget_status=budget_status,
        dominant_categories=dominant_categories or interest_categories,
    )

    return {
        "currency": "INR",
        "destination": destination,
        "city_profile_used": city if city_known else "default",
        "location_specific": True,
        "days": days,
        "travelers": travelers,
        "travel_style": style,
        "food_preference": food_preference,
        "interests": interests or [],
        "place_analysis": place_analysis,
        "location_multiplier": location_multiplier,
        "daily_cost_per_person_estimate": {
            "accommodation": location_adjusted_costs["accommodation"],
            "food": location_adjusted_costs["food"],
            "local_transport": location_adjusted_costs["local_transport"],
            "activities": location_adjusted_costs["activities"],
            "total": sum(location_adjusted_costs.values()),
        },
        "category_totals": {
            "accommodation": accommodation_total,
            "food": food_total,
            "local_transport": transport_total,
            "activities": activities_total,
            "location_specific_extra": location_specific_extra,
            "buffer": buffer,
        },
        "total_estimate": total_range,
        "total_estimated_cost": total_range["expected"],
        "user_budget": user_budget,
        "within_budget": budget_status == "within_budget",
        "budget_status": budget_status,
        "budget_gap": budget_gap,
        "buffer_percentage": buffer_percentage,
        "daily_budget_plan": daily_budget_plan,
        "confidence": confidence,
        "cost_drivers": cost_drivers,
        "recommendations": recommendations,
        "saving_plan": saving_plan,
        "budget_note": build_budget_note(
            destination=destination,
            budget_status=budget_status,
            expected_total=total_range["expected"],
            user_budget=user_budget,
            confidence=confidence,
        ),
    }