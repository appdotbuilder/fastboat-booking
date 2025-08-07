from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum


# Enums for status fields
class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ScheduleStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


# Language and Translation Models
class Language(SQLModel, table=True):
    __tablename__ = "languages"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, max_length=5, description="Language code (e.g., 'en', 'id')")
    name: str = Field(max_length=100, description="Language name in English")
    native_name: str = Field(max_length=100, description="Language name in native script")
    is_active: bool = Field(default=True)
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    translations: List["Translation"] = Relationship(back_populates="language")


class Translation(SQLModel, table=True):
    __tablename__ = "translations"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(max_length=200, description="Translation key")
    value: str = Field(description="Translated text")
    language_id: int = Field(foreign_key="languages.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    language: Language = Relationship(back_populates="translations")


# User Management
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, max_length=255)
    password_hash: str = Field(max_length=255)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    role: UserRole = Field(default=UserRole.CUSTOMER)
    preferred_language: str = Field(default="en", max_length=5)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    bookings: List["Booking"] = Relationship(back_populates="user")


# Location and Route Management
class Location(SQLModel, table=True):
    __tablename__ = "locations"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, max_length=10, description="Airport/port code")
    name: str = Field(max_length=200)
    city: str = Field(max_length=100)
    country: str = Field(max_length=100)
    timezone: str = Field(max_length=50, default="UTC")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    departure_routes: List["Route"] = Relationship(
        back_populates="departure_location", sa_relationship_kwargs={"foreign_keys": "Route.departure_location_id"}
    )
    arrival_routes: List["Route"] = Relationship(
        back_populates="arrival_location", sa_relationship_kwargs={"foreign_keys": "Route.arrival_location_id"}
    )


class Route(SQLModel, table=True):
    __tablename__ = "routes"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    departure_location_id: int = Field(foreign_key="locations.id")
    arrival_location_id: int = Field(foreign_key="locations.id")
    distance_km: Optional[Decimal] = Field(default=None, max_digits=8, decimal_places=2)
    estimated_duration_minutes: int = Field(description="Estimated travel time in minutes")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    departure_location: Location = Relationship(
        back_populates="departure_routes", sa_relationship_kwargs={"foreign_keys": "Route.departure_location_id"}
    )
    arrival_location: Location = Relationship(
        back_populates="arrival_routes", sa_relationship_kwargs={"foreign_keys": "Route.arrival_location_id"}
    )
    schedules: List["Schedule"] = Relationship(back_populates="route")
    seasonal_prices: List["SeasonalPrice"] = Relationship(back_populates="route")


# Fastboat and Schedule Management
class Fastboat(SQLModel, table=True):
    __tablename__ = "fastboats"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200)
    operator: str = Field(max_length=200)
    capacity: int = Field(description="Maximum number of passengers")
    boat_type: str = Field(max_length=100, default="fastboat")
    facilities: Dict[str, Any] = Field(default={}, sa_column=Column(JSON), description="Available facilities")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    schedules: List["Schedule"] = Relationship(back_populates="fastboat")


class Schedule(SQLModel, table=True):
    __tablename__ = "schedules"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    route_id: int = Field(foreign_key="routes.id")
    fastboat_id: int = Field(foreign_key="fastboats.id")
    departure_time: time = Field(description="Daily departure time")
    arrival_time: time = Field(description="Daily arrival time")
    base_price: Decimal = Field(max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    days_of_week: List[int] = Field(default=[], sa_column=Column(JSON), description="Operating days (0=Monday)")
    effective_from: date = Field(description="Schedule start date")
    effective_until: Optional[date] = Field(default=None, description="Schedule end date")
    status: ScheduleStatus = Field(default=ScheduleStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    route: Route = Relationship(back_populates="schedules")
    fastboat: Fastboat = Relationship(back_populates="schedules")
    daily_schedules: List["DailySchedule"] = Relationship(back_populates="schedule")


class DailySchedule(SQLModel, table=True):
    __tablename__ = "daily_schedules"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    schedule_id: int = Field(foreign_key="schedules.id")
    travel_date: date = Field(description="Specific travel date")
    available_seats: int = Field(description="Available seats for this date")
    price_override: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    is_available: bool = Field(default=True)
    booking_deadline: Optional[datetime] = Field(default=None)
    notes: str = Field(default="", max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    schedule: Schedule = Relationship(back_populates="daily_schedules")
    bookings: List["Booking"] = Relationship(back_populates="daily_schedule")


# Seasonal Pricing
class SeasonalPrice(SQLModel, table=True):
    __tablename__ = "seasonal_prices"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    route_id: int = Field(foreign_key="routes.id")
    season_name: str = Field(max_length=100, description="Season name (e.g., 'High Season')")
    start_date: date = Field(description="Season start date (year-agnostic)")
    end_date: date = Field(description="Season end date (year-agnostic)")
    price_multiplier: Decimal = Field(max_digits=5, decimal_places=3, description="Multiply base price by this")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    route: Route = Relationship(back_populates="seasonal_prices")


# Booking Management
class Booking(SQLModel, table=True):
    __tablename__ = "bookings"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_reference: str = Field(unique=True, max_length=20, description="Unique booking reference")
    user_id: int = Field(foreign_key="users.id")
    daily_schedule_id: int = Field(foreign_key="daily_schedules.id")
    passenger_count: int = Field(description="Number of passengers")
    total_amount: Decimal = Field(max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    status: BookingStatus = Field(default=BookingStatus.PENDING)
    contact_email: str = Field(max_length=255)
    contact_phone: str = Field(max_length=20)
    special_requests: str = Field(default="", max_length=1000)
    booking_deadline: datetime = Field(description="Deadline for completing payment")
    booked_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: Optional[datetime] = Field(default=None)
    cancelled_at: Optional[datetime] = Field(default=None)
    cancellation_reason: str = Field(default="", max_length=500)

    user: User = Relationship(back_populates="bookings")
    daily_schedule: DailySchedule = Relationship(back_populates="bookings")
    passengers: List["Passenger"] = Relationship(back_populates="booking")
    payments: List["Payment"] = Relationship(back_populates="booking")


class Passenger(SQLModel, table=True):
    __tablename__ = "passengers"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="bookings.id")
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    date_of_birth: Optional[date] = Field(default=None)
    nationality: Optional[str] = Field(default=None, max_length=100)
    passport_number: Optional[str] = Field(default=None, max_length=50)
    id_number: Optional[str] = Field(default=None, max_length=50)
    special_needs: str = Field(default="", max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    booking: Booking = Relationship(back_populates="passengers")


# Payment Management
class Payment(SQLModel, table=True):
    __tablename__ = "payments"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="bookings.id")
    payment_reference: str = Field(unique=True, max_length=100, description="Gateway reference")
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    payment_method: str = Field(max_length=50, description="credit_card, bank_transfer, etc.")
    gateway_provider: str = Field(max_length=50, description="Stripe, PayPal, etc.")
    gateway_transaction_id: Optional[str] = Field(default=None, max_length=255)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    gateway_response: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    processed_at: Optional[datetime] = Field(default=None)
    failed_at: Optional[datetime] = Field(default=None)
    failure_reason: str = Field(default="", max_length=500)
    refunded_at: Optional[datetime] = Field(default=None)
    refund_amount: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    booking: Booking = Relationship(back_populates="payments")


# Admin Dashboard and Reports
class AdminAction(SQLModel, table=True):
    __tablename__ = "admin_actions"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    admin_user_id: int = Field(foreign_key="users.id")
    action_type: str = Field(max_length=100, description="Type of action performed")
    resource_type: str = Field(max_length=100, description="Type of resource affected")
    resource_id: Optional[int] = Field(default=None, description="ID of affected resource")
    description: str = Field(max_length=500)
    action_metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemSettings(SQLModel, table=True):
    __tablename__ = "system_settings"  # type: ignore[assignment]

    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(unique=True, max_length=100)
    value: str = Field(description="Setting value as string")
    data_type: str = Field(max_length=20, description="string, number, boolean, json")
    description: str = Field(default="", max_length=500)
    is_public: bool = Field(default=False, description="Can be accessed by frontend")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Non-persistent schemas for API and forms
class UserCreate(SQLModel, table=False):
    email: str = Field(max_length=255)
    password: str = Field(min_length=6)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    phone: Optional[str] = Field(default=None, max_length=20)
    preferred_language: str = Field(default="en", max_length=5)


class UserLogin(SQLModel, table=False):
    email: str = Field(max_length=255)
    password: str


class RouteSearch(SQLModel, table=False):
    departure_location_id: int
    arrival_location_id: int
    travel_date: date
    passenger_count: int = Field(default=1, ge=1)


class BookingCreate(SQLModel, table=False):
    daily_schedule_id: int
    passenger_count: int = Field(ge=1)
    contact_email: str = Field(max_length=255)
    contact_phone: str = Field(max_length=20)
    special_requests: str = Field(default="", max_length=1000)
    passengers: List[Dict[str, Any]] = Field(description="Passenger details")


class PaymentCreate(SQLModel, table=False):
    booking_id: int
    payment_method: str = Field(max_length=50)
    gateway_provider: str = Field(max_length=50)
    return_url: str = Field(description="URL to redirect after payment")


class ScheduleCreate(SQLModel, table=False):
    route_id: int
    fastboat_id: int
    departure_time: time
    arrival_time: time
    base_price: Decimal = Field(max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    days_of_week: List[int] = Field(description="Operating days (0=Monday)")
    effective_from: date
    effective_until: Optional[date] = None


class DailyScheduleUpdate(SQLModel, table=False):
    available_seats: Optional[int] = None
    price_override: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    is_available: Optional[bool] = None
    booking_deadline: Optional[datetime] = None
    notes: Optional[str] = Field(default=None, max_length=500)


class SalesReportFilters(SQLModel, table=False):
    start_date: date
    end_date: date
    route_id: Optional[int] = None
    fastboat_id: Optional[int] = None
    status: Optional[BookingStatus] = None
