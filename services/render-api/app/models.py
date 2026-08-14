from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class RenderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    axis_inclination_degrees: float = Field(ge=0, le=85)
    background: Literal["procedural-stars", "deep-space"]
    blue_spectrum: bool
    disk_thickness: float = Field(ge=0.02, le=0.5)
    disk_temperature: float = Field(ge=1_000_000, le=100_000_000)
    emissivity_slope: float = Field(ge=1, le=5)
    flow_direction: Literal["prograde", "retrograde"]
    inner_disk_radius: float = Field(ge=1, le=20)
    jet_strength: float = Field(ge=0, le=1)
    magnetic_state: Literal["sane", "mad"]
    observing_band: Literal["230-ghz", "optical"]
    orbit_degrees: float = Field(ge=0, le=360)
    seed: int = Field(ge=0, le=4_294_967_295)
    spin: float = Field(ge=0, le=0.998)
    zoom: float = Field(ge=0.5, le=3)
    mass: float = Field(default=1.0, gt=0)

    @computed_field(return_type=float)
    @property
    def field_of_view(self) -> float:
        """Derive the server-render FOV from the UI zoom; clients cannot override it."""
        return 48.0 / self.zoom
