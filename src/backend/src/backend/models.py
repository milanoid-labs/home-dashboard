from typing import Literal

from pydantic import BaseModel, Field

ControlState = Literal[
    "on", "off", "toggle", "open", "close", "stop", "stepOpen", "stepClose"
]


class Device(BaseModel):
    """A single device (actuator or sensor) as exposed by the SHC."""

    id: str
    name: str
    type: str
    value: str | None = None
    unit: str | None = None
    operations: list[str] = Field(default_factory=list)
    controllable: bool = False


class Zone(BaseModel):
    """A room/zone and the devices in it."""

    zone_id: str
    zone_name: str
    devices: list[Device]


class ControlRequest(BaseModel):
    state: ControlState


class ControlResult(BaseModel):
    ok: bool
