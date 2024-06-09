from defusedxml.ElementTree import XML
from ratelimit import sleep_and_retry, limits
from sys import stderr
from typing import Final, Self
from xml.etree.ElementTree import Element
import re
import requests

UUID_PATTERN = re.compile(r"[0-9A-Fa-f]{8}-(?:[0-9A-Fa-f]{4}-){3}[0-9A-Fa-f]{12}")


# Thanks to Lucas Martin-King for providing the general idea for the following code
# https://github.com/lmartinking/melbourne-tramtracker/
class TramTrackerClient:
    """Interface class with the TramTracker PIDS Web Service."""

    _NAMESPACES: Final[dict[str, str]] = {"soap": "http://www.w3.org/2003/05/soap-envelope", "tramtracker": "http://www.yarratrams.com.au/pidsservice/"}
    CLIENT_TYPE: Final[str] = "WEBPID"
    CLIENT_VERSION: Final[str] = "0.1"
    CLIENT_WEB_SERVICE_VERSION: Final[str] = "6.4.0.0"

    def __init__(self, uuid: str | None = None) -> None:
        """
        Creates a TramTrackerInterface instance, requesting a new UUID from the service if one is not provided.

        :param uuid: The UUID for client authentication, or None to request one from the service
        :return: None
        """
        if type(uuid) not in (str, type(None)):
            raise TypeError("UUID must be str or None")
        if uuid is not None and UUID_PATTERN.fullmatch(uuid) is None:
            raise ValueError("Invalid UUID - UUIDs must take the form 00000000-0000-0000-0000-000000000000")
        self.uuid: Final[str] = self._get_new_uuid() if uuid is None else uuid
        return

    @classmethod
    @sleep_and_retry
    @limits(calls=1, period=30)
    def _post(cls: Self, data: str) -> str:
        """
        Send the specified data to the service, appending the necessary HTTP and XML headers.

        :param data: The data to send
        :return: The response from the service
        """
        print(data, file=stderr)
        r = requests.post(url="http://webpids.tramtracker.com.au/pidsservice/pids.asmx", data=f"<?xml version=\"1.0\" encoding=\"utf-8\"?><soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:soap=\"http://www.w3.org/2003/05/soap-envelope\">{data}</soap:Envelope>", headers={"Content-Type": "application/soap+xml; charset=utf-8"})
        r.raise_for_status()
        r.encoding = "utf-8"
        return r.text

    @classmethod
    def _get_new_uuid(cls: Self) -> str:
        """
        Request a new UUID for client identification from the service. Raises a ConnectionError if an unexpected response is received.

        :return: The new UUID
        """
        r = cls._post("<soap:Body><GetNewClientGuid xmlns=\"http://www.yarratrams.com.au/pidsservice/\" /><soap:Body />")
        tree: Element = XML(r)
        result = tree.find("./soap:Body/tramtracker:GetNewClientGuidResponse/tramtracker:GetNewClientGuidResult", cls._NAMESPACES)
        if result is None:
            raise ConnectionError("Service error: service responded successfully but did not return a UUID; check with developer")
        if UUID_PATTERN.fullmatch(result.text) is None:
            raise ConnectionError(f"Service error: service responded successfully but returned an unexpected value: \"{result.text}\"; check with developer")
        return result.text

    def _call(self: Self, request: str) -> str:
        """
        Make the request to the web service, appending the necessary headers to the request.

        :param request: XML request string
        :return: Result of request
        """
        return self._post(f"<soap:Header><PidsClientHeader xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><ClientGuid>{self.uuid}</ClientGuid><ClientType>{self.CLIENT_TYPE}</ClientType><ClientVersion>{self.CLIENT_VERSION}</ClientVersion><ClientWebServiceVersion>{self.CLIENT_WEB_SERVICE_VERSION}</ClientWebServiceVersion></PidsClientHeader></soap:Header><soap:Body>{request}</soap:Body>")

    def list_destinations(self: Self):
        self._call("<GetDestinationsForAllRoutes xmlns=\"http://www.yarratrams.com.au/pidsservice/\" />")

    def get_destinations(self: Self, route: str | int):
        self._call(f"<GetDestinationsForRoute xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><routeNo>{route}</routeNo></GetDestinationsForRoute>")

    def list_routes(self: Self):
        self._call("<GetMainRoutes xmlns=\"http://www.yarratrams.com.au/pidsservice/\" />")

    def list_stops(self: Self, route: str | int) -> list[dict[str, str | int]]:
        response = self._call(f"<GetRouteStopsByRoute xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><routeNo>{route}</routeNo></GetRouteStopsByRoute>")
        result: Element = XML(response).find("./soap:Body/tt:GetRouteStopsByRouteResponse/tt:GetRouteStopsByRouteResult/diffgr:diffgram/DocumentElement", namespaces={"soap": "http://www.w3.org/2003/05/soap-envelope", "tt": "http://www.yarratrams.com.au/pidsservice/", "diffgr": "urn:schemas-microsoft-com:xml-diffgram-v1"})

        return [{"tt_id": int(element.find("./TID").text),
                 "stop_name": element.find("./Description").text,
                 "full_stop_name": element.find("./StopName").text,
                 "locality": element.find("./SuburbName").text,
                 "latitude": element.find("./Latitude").text,
                 "longitude": element.find("./Longitude").text
                 } for element in result]

    def get_stop(self: Self, stop_id: int):
        self._call(f"<GetStopInformation xmlns=\"http://www.yarratrams.com.au/pidsservice/\"><stopNo>{stop_id}</stopNo></GetStopInformation>")
