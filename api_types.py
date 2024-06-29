from typing import List, Optional, Callable, Any
from dataclasses import dataclass


@dataclass
class ExtendParams:
    image_url: str
    image_end_url: str
    expand_prompt: bool
    user_prompt: str


@dataclass
class Subscription:
    active: bool
    plan: str
    type: Any


@dataclass
class Plan:
    name: str
    key: str
    capacity_per_month: int
    monthly_cost_in_cents: int
    yearly_cost_in_cents: int


@dataclass
class UsageResponse:
    consumed: int
    capacity: int
    available: int
    subscription: Subscription
    plans: List[Plan]


@dataclass
class Video:
    url: str
    width: int
    height: int
    thumbnail: Any


@dataclass
class GenerationItem:
    id: str
    prompt: str
    state: str
    created_at: str
    video: Video
    liked: Any
    estimate_wait_seconds: Any


@dataclass
class GenerateResponse:
    pass  # Add appropriate fields if needed


@dataclass
class ConstructorParams:
    cookies: Optional[List[Any]]  # Adjust type if specific cookie class is available
    profileRoot: str
    username: str
    password: str


@dataclass
class SendPostParams:
    url: str
    headers: Optional[Any] = None
    body: Optional[Any] = None
    doLogin: Optional[bool] = None
    useProxy: Optional[bool] = None
    method: Optional[str] = None  # 'POST' or 'PUT'
    duplex: Optional[Any] = None

