"""User input model — only the important fields the user fills."""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class UserInput(BaseModel):
    # --- Basic --------------------------------------------------------
    name: Optional[str] = None
    brief: Optional[str] = Field(default=None, description="Short notes; AI expands.")
    number_of_days: int = Field(4, ge=1, le=60)
    seats_per_tour: int = Field(20, ge=1)
    group_size: int = Field(20, ge=1)

    # --- Destination --------------------------------------------------
    region: str = "Asia"
    country: str
    cities: List[str] = Field(default_factory=list)
    landmarks: List[str] = Field(default_factory=list)

    # --- Theme / audience --------------------------------------------
    package_moods: List[str] = Field(default_factory=list)
    package_types: List[str] = Field(default_factory=list)
    age_range: str = "0-99"
    child_age_range: str = "2-8"

    # --- Hotels / transfers / meals ----------------------------------
    min_hotel_stars: int = Field(3, ge=1, le=5)
    hotel_rating: Optional[str] = None          # "3-Star" / "4-Star" / "5-Star"
    accommodation_type: List[str] = Field(default_factory=list)  # Hotels / Resorts ...
    room_category: Optional[str] = None         # Standard Rooms / Suites ...
    guide_languages: List[str] = Field(default_factory=list)     # English / Spanish ...
    transfer_types: List[str] = Field(default_factory=lambda: ["Coach / Bus"])
    meal_preferences: List[str] = Field(default_factory=list)

    # --- Availability -------------------------------------------------
    travel_days: List[str] = Field(default_factory=list)
    travel_months: List[str] = Field(default_factory=list)
    travel_years: List[str] = Field(default_factory=list)

    # --- Commercials --------------------------------------------------
    currency: str = "USD"

    # --- Service preferences -----------------------------------------
    must_include: List[str] = Field(default_factory=list)
    must_exclude: List[str] = Field(default_factory=list)
    special_requirements: Optional[str] = None

    # --- Flags --------------------------------------------------------
    is_child_friendly: bool = True
    is_handicap_accessible: bool = False
    is_insurance_required: bool = False
    is_active: bool = True
    is_top_rated: bool = False
    ubidtours_policy: bool = False

    # --- How many distinct packages to generate ----------------------
    package_count: int = Field(3, ge=1, le=10)

    def nights(self) -> int:
        return max(self.number_of_days - 1, 0)
