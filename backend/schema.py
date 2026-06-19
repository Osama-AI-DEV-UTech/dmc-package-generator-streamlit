"""Pydantic models mirroring the platform's package.json EXACTLY.

Dump with .model_dump(by_alias=True) to reproduce the original key names
(notably the reserved word 'from' inside Transportation)."""
from __future__ import annotations

from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class IdValue(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    value: str


class IdValueDesc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    value: str
    desc: Optional[str] = None


class Destination(BaseModel):
    regions: IdValue
    country: IdValue
    city: List[IdValue] = Field(default_factory=list)
    landmarks: List[Any] = Field(default_factory=list)


class Image(BaseModel):
    imageName: str
    imageSize: int
    s3url: str = ""
    key: str = ""


class Accommodation(BaseModel):
    city: IdValue
    country: IdValue
    serviceId: str = ""
    roomId: List[str] = Field(default_factory=list)
    noOfNights: int = 0


class TourPlan(BaseModel):
    arrival: str = ""
    accommodation: List[Accommodation] = Field(default_factory=list)
    departure: str = ""


class MealItem(BaseModel):
    numberOfMeals: int = 0
    desc: str = ""


class MealSummary(BaseModel):
    availableMealPref: List[IdValue] = Field(default_factory=list)
    breakfast: MealItem = Field(default_factory=MealItem)
    lunch: MealItem = Field(default_factory=MealItem)
    dinner: MealItem = Field(default_factory=MealItem)


class TransferPoint(BaseModel):
    location: str = ""
    transferPoint: str = ""
    time: str = ""


class Transportation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    day: int
    from_: TransferPoint = Field(alias="from", default_factory=TransferPoint)
    to: TransferPoint = Field(default_factory=TransferPoint)
    availableType: List[IdValue] = Field(default_factory=list)


class TransportationUpgrade(BaseModel):
    isTransportationUpgrade: bool = False
    upgradeName: str = ""
    upgradePrice: float = 0


class ItineraryDetail(BaseModel):
    day: int
    detail: str


class Policy(BaseModel):
    pkg: str = ""
    ubidtours: bool = False


class TravelService(BaseModel):
    included: List[str] = Field(default_factory=list)
    notIncluded: List[str] = Field(default_factory=list)


class PackageAvailability(BaseModel):
    pkgDays: List[IdValue] = Field(default_factory=list)
    pkgMonths: List[IdValue] = Field(default_factory=list)
    pkgYears: List[IdValue] = Field(default_factory=list)
    overRideBasePrice: float = 0
    overRideSingleSuplimentPrc: float = 0
    overRideSeatsPerTour: int = 0
    overRideChildDiscountPrice: float = 0
    overRideInfantDiscountPrice: float = 0
    overRideGroupDiscountPrice: float = 0
    overRideMisc1: Optional[Any] = None
    overRideMisc2: Optional[Any] = None
    overRideMisc3: Optional[Any] = None
    adminOverRideBasePrice: float = 0
    adminOverRideChildDiscountPrice: float = 0
    adminOverRideInfantDiscountPrice: float = 0
    adminOverRideGroupDiscountPrice: float = 0


class Package(BaseModel):
    """The complete package object — identical shape to package.json."""
    model_config = ConfigDict(populate_by_name=True)

    skuId: str
    dmcId: str
    packageId: str
    dmcApproved: bool = False
    adminApproved: str = "PENDING"
    name: str
    packageMood: List[IdValue] = Field(default_factory=list)
    subMood: List[IdValueDesc] = Field(default_factory=list)
    createdAt: str
    updatedAt: str
    destinations: List[Destination] = Field(default_factory=list)
    image: List[Image] = Field(default_factory=list)
    numberOfDays: int
    tourDetail: str = ""
    ageRange: IdValue
    isChildFriendly: bool = True
    isHandicapAccessible: bool = False
    isInsuranceRequired: bool = False
    promotionPercentage: float = 0
    seatsPerTour: int = 0
    groupSize: int = 0
    pkgType: List[IdValue] = Field(default_factory=list)
    tourPlan: TourPlan = Field(default_factory=TourPlan)
    numberTravelerPrice: List[Any] = Field(default_factory=list)
    mealSummary: MealSummary = Field(default_factory=MealSummary)
    transportation: List[Transportation] = Field(default_factory=list)
    transportationUpgrade: TransportationUpgrade = Field(default_factory=TransportationUpgrade)
    itineraryDetail: List[ItineraryDetail] = Field(default_factory=list)
    policy: Policy = Field(default_factory=Policy)
    travelService: TravelService = Field(default_factory=TravelService)
    packageAvailability: List[PackageAvailability] = Field(default_factory=list)
    basePrice: float = 0
    singleSuplimentPrc: float = 0
    childDiscountPrice: float = 0
    childAgeRange: IdValue
    infantDiscountPrice: float = 0
    misc1: float = 0
    misc2: float = 0
    misc3: float = 0
    adminBasePrice: float = 0
    adminChildDiscountPrice: float = 0
    adminInfantDiscountPrice: float = 0
    isActive: bool = True
    isDeleted: bool = False
    isConverted: bool = False
    isTopRated: bool = False

    def as_json(self) -> dict:
        return self.model_dump(by_alias=True)


# Fields that carry pricing — blanked for the DMC (without-prices) version.
PRICE_FIELDS = [
    "promotionPercentage", "basePrice", "singleSuplimentPrc",
    "childDiscountPrice", "infantDiscountPrice", "misc1", "misc2", "misc3",
    "adminBasePrice", "adminChildDiscountPrice", "adminInfantDiscountPrice",
]


class PriceReference(BaseModel):
    item: str
    estimate: Optional[float] = None
    currency: str = "USD"
    basis: Optional[str] = None         # e.g. "per room / night", "per person"
    source_url: Optional[str] = None
    note: Optional[str] = None


class DMCInfo(BaseModel):
    """Full details of the Destination Management Company offering the package."""
    name: str
    legal_name: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    specialisation: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    why_recommended: Optional[str] = None
    source_url: Optional[str] = None
    verified: bool = False              # True only if drawn from a live source
