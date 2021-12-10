import time
import socket
import aiohttp
from typing import Union
from mcstatus import MinecraftServer

from .proxies import Proxy
from fake_useragent import UserAgent


async def mcLookup(ip: str) -> dict:
    """
    Checks if an ip address is a minecraft ip address, if it is, return the details as a dictionary, if it isn't, return None.
    This will only check the query ports.
    """

    if not ":" in ip:
        ip = ip + ":25561"

    data = {"ip": ip}
    server = MinecraftServer.lookup(ip)
    try:
        start = time.time()
        query = server.query(tries=1)
        ping = round((time.time() - start)*1000, 2)

        data["ping"] = ping
        data["motd"] = query.motd
        data["map"] = query.map
        data["players"] = {
            "online": query.players.online,
            "max": query.players.max,
            "names": query.players.names
        }
        data["software"] = {
            "version": query.software.version,
            "brand": query.software.brand,
            "plugins": query.software.plugins
        }

    except (socket.timeout, OSError):
        data = None

    return data


async def apiLookup(ip: str, proxy: Union[Proxy, None], returnResponse: bool = False) -> dict:
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    proxies = proxy.raw if proxy else None

    if proxies:
        kwargs = {
            "proxy": proxies["http"],
        }
    else:
        kwargs = {}
    
    tries = 0
    while True:
        tries += 1

        if tries > 1:
            return "Critical error"

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(f"http://ip-api.com/json/{ip}?fields=66846719", **kwargs) as resp:
                    if returnResponse:
                        return resp

                    resp.raise_for_status()
                    data = await resp.json()
                    return data
        except aiohttp.ClientProxyConnectionError:
            kwargs = {}


async def regularLookup(ip: str, proxy: Union[Proxy, None] = None, performGeo: bool = False) -> dict:
    # # Option for the number of packets as a function of
    # param = '-n' if platform.system().lower() == 'windows' else '-c'

    # # Building the command. Ex: "ping -c 1 google.com"
    # command = ['ping', param, '1', ip]

    # start = time.time()
    # status = subprocess.call(
    #     command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0
    # ping = round((time.time() - start)*1000, 2)

    try:
        start = time.time()
        domain = socket.gethostbyaddr(ip)[0]
        ping = round((time.time() - start)*1000, 2)
    except socket.herror:
        domain = "Unknown"
        ping = None
    
    if ping:

        if performGeo:
            try:
                geolocation = await apiLookup(ip, proxy)
            except aiohttp.ClientResponseError as e:
                if e.status == 429:
                    geolocation = "Rate limit exceeded"
        else:
            geolocation = "Unperformed"

        data = {"ping": ping, "domain": domain, "geolocation": geolocation}
        return data
    return None

async def autoLookUp(ip: str, proxy: Union[Proxy, None] = None) -> dict:
    """
    Combines all the functions above into one.
    """

    data = {"type": "unknown"}

    # Minecraft server
    mcLookupData = await mcLookup(ip)
    if mcLookupData:
        data["data"] = data
        data["type"] = "minecraft"
        return data
    
    # Regular ip address, attempt to get the details
    regularLookupData = await regularLookup(ip, proxy, True)
    if regularLookupData:
        data["data"] = regularLookupData
        data["type"] = "regular"
        data["rateLimited"] = False

        if regularLookupData["geolocation"] == "Rate limit exceeded":
            data["rateLimited"] = True
        return data
    
    return None
