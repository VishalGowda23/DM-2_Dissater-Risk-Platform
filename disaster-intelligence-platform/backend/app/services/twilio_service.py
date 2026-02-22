"""
Twilio Messaging Service for PRAKALP
Sends real SMS and WhatsApp disaster alerts to citizens and authorities.
Supports media attachments (static evacuation-route maps via WhatsApp).
"""
import logging
from typing import Optional, List
from dataclasses import dataclass
from urllib.parse import quote

logger = logging.getLogger(__name__)


@dataclass
class MessageResult:
    success: bool
    sid: Optional[str] = None
    to: Optional[str] = None
    channel: Optional[str] = None
    error: Optional[str] = None
    status: Optional[str] = None


def build_static_map_url(
    ward_lat: float, ward_lon: float,
    shelter_lat: float, shelter_lon: float,
    ward_name: str = "Ward",
    shelter_name: str = "Shelter",
) -> str:
    """
    Build a Geoapify static-map URL showing the ward origin (red) and
    shelter destination (green) with a connecting line.
    Free tier: 3 000 req/day — more than enough for demo.
    Falls back to an OpenStreetMap static-map URL if needed.
    """
    # ---- Primary: Geoapify Static Maps (free, no key needed for low usage) ----
    # Use OSM-based static map service that doesn't need an API key
    cx = (ward_lon + shelter_lon) / 2
    cy = (ward_lat + shelter_lat) / 2

    # Use staticmap.openstreetmap.de (free, no key)
    markers = (
        f"{ward_lat},{ward_lon},red-pushpin|"
        f"{shelter_lat},{shelter_lon},ltblu-pushpin"
    )
    url = (
        f"https://staticmap.openstreetmap.de/staticmap.php"
        f"?center={cy},{cx}"
        f"&zoom=14&size=600x400&maptype=mapnik"
        f"&markers={markers}"
    )
    return url


def build_google_maps_link(
    ward_lat: float, ward_lon: float,
    shelter_lat: float, shelter_lon: float,
    route_coords: Optional[List[List[float]]] = None,
) -> str:
    """
    Google Maps walking-directions deep link that follows our computed
    safe evacuation path.

    If *route_coords* (the polyline from _generate_route) is supplied,
    the intermediate points are injected as waypoints so Google Maps
    traces the exact safe route instead of its own fastest path.
    """
    url = (
        f"https://www.google.com/maps/dir/?api=1"
        f"&origin={ward_lat},{ward_lon}"
        f"&destination={shelter_lat},{shelter_lon}"
        f"&travelmode=walking"
    )

    # Add intermediate waypoints (skip first=origin and last=destination)
    if route_coords and len(route_coords) > 2:
        waypoints = route_coords[1:-1]          # only the middle points
        wp_str = "|".join(f"{pt[0]},{pt[1]}" for pt in waypoints)
        url += f"&waypoints={wp_str}"

    return url


class TwilioService:
    """
    Wraps the Twilio SDK for sending SMS and WhatsApp messages.
    Gracefully degrades when credentials are not configured.
    """

    def __init__(self):
        self._client = None
        self._sms_from: Optional[str] = None
        self._whatsapp_from: Optional[str] = None
        self._ready = False
        self._init()

    def _init(self):
        try:
            try:
                from app.db.config import settings
            except ImportError:
                from core.config import settings
            from twilio.rest import Client

            sid = settings.TWILIO_ACCOUNT_SID
            token = settings.TWILIO_AUTH_TOKEN
            if not sid or not token or sid.startswith("AC" + "x"):
                logger.info("Twilio credentials not configured — messaging disabled")
                return

            self._client = Client(sid, token)
            self._sms_from = settings.TWILIO_SMS_FROM
            self._whatsapp_from = settings.TWILIO_WHATSAPP_FROM or "whatsapp:+14155238886"
            self._ready = True
            logger.info("Twilio service initialised ✓")

        except Exception as e:
            logger.warning(f"Twilio init failed: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready

    def send_sms(self, to: str, message: str, map_link: Optional[str] = None) -> MessageResult:
        """Send a plain SMS message.  Optionally appends a Google Maps link."""
        if not self._ready:
            return MessageResult(success=False, error="Twilio not configured")
        if not self._sms_from:
            return MessageResult(success=False, error="TWILIO_SMS_FROM not set")

        body = message
        if map_link:
            body += f"\n\n🗺️ Evacuation Map: {map_link}"

        to_number = self._normalise_phone(to)
        try:
            msg = self._client.messages.create(
                body=body[:1600],
                from_=self._sms_from,
                to=to_number,
            )
            logger.info(f"SMS sent → {to_number} | SID={msg.sid}")
            return MessageResult(success=True, sid=msg.sid, to=to_number,
                                 channel="sms", status=msg.status)
        except Exception as e:
            logger.error(f"SMS send failed → {to_number}: {e}")
            return MessageResult(success=False, to=to_number, channel="sms",
                                 error=str(e))

    def send_whatsapp(
        self, to: str, message: str,
        media_url: Optional[str] = None,
        map_link: Optional[str] = None,
    ) -> MessageResult:
        """Send a WhatsApp message via Twilio, optionally with a map image."""
        if not self._ready:
            return MessageResult(success=False, error="Twilio not configured")

        body = message
        if map_link:
            body += f"\n\n🗺️ View Evacuation Route on Map:\n{map_link}"

        to_wa = f"whatsapp:{self._normalise_phone(to)}"
        try:
            kwargs = dict(
                body=body[:4096],
                from_=self._whatsapp_from,
                to=to_wa,
            )
            if media_url:
                kwargs["media_url"] = [media_url]
                logger.info(f"WhatsApp media attached: {media_url}")

            msg = self._client.messages.create(**kwargs)
            logger.info(f"WhatsApp sent → {to_wa} | SID={msg.sid}")
            return MessageResult(success=True, sid=msg.sid, to=to_wa,
                                 channel="whatsapp", status=msg.status)
        except Exception as e:
            logger.error(f"WhatsApp send failed → {to_wa}: {e}")
            return MessageResult(success=False, to=to_wa, channel="whatsapp",
                                 error=str(e))

    def send_alert(
        self, to: str, message: str, channel: str = "sms",
        ward_lat: Optional[float] = None, ward_lon: Optional[float] = None,
        shelter_lat: Optional[float] = None, shelter_lon: Optional[float] = None,
        ward_name: str = "", shelter_name: str = "",
        route_coords: Optional[List[List[float]]] = None,
    ) -> MessageResult:
        """
        Route to SMS or WhatsApp based on channel.
        When ward/shelter coordinates are supplied, attaches a
        Google Maps walking-directions link that follows the safe
        evacuation route (using waypoints from route_coords).
        """
        map_link: Optional[str] = None

        has_coords = all(v is not None for v in (ward_lat, ward_lon, shelter_lat, shelter_lon))
        if has_coords:
            map_link = build_google_maps_link(
                ward_lat, ward_lon, shelter_lat, shelter_lon,
                route_coords=route_coords,
            )
            logger.info(f"Map link generated — {map_link}")

        if channel == "whatsapp":
            return self.send_whatsapp(to, message, map_link=map_link)
        return self.send_sms(to, message, map_link=map_link)

    def _normalise_phone(self, phone: str) -> str:
        """Ensure E.164 format. Add India +91 if bare 10-digit number."""
        p = phone.strip().replace(" ", "").replace("-", "")
        if not p.startswith("+"):
            # Bare 10-digit Indian number
            if len(p) == 10 and p.isdigit():
                p = "+91" + p
            else:
                p = "+" + p
        return p


# Global singleton
twilio_service = TwilioService()
