import random
import datetime
import asyncio
import aiohttp

from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from typing import List
from dataclasses import dataclass


@dataclass
class Proxy:
    ip: str
    port: str
    created: datetime.datetime
    uses: int = 0

    @property
    def lifetime(self) -> int:
        return datetime.datetime.now().timestamp - self.created.timestamp

    @property
    def raw(self) -> dict:
        return {
            "http": f"http://{self.ip}:{self.port}",
            "https": f"https://{self.ip}:{self.port}"
        }


class RotatingProxy:
    """
    A class that handles rotating proxies. This uses the proxy list from https://www.sslproxies.org/.
    """

    def __init__(self, refreshRate: int = 600) -> None:
        self.ua = UserAgent()
        self.refreshRate = refreshRate
        self.loop = asyncio.get_event_loop()
        self.proxies = []

        self.refresherTask = self.loop.create_task(self.refresher())

    async def refresher(self) -> None:
        """
        Refreshes the proxy list every self.refreshRate.
        """

        while True:
            await self.refreshProxies()
            await asyncio.sleep(self.refreshRate)

    async def retrieveProxies(self) -> List[str]:
        async with aiohttp.ClientSession(headers={"User-Agent": self.ua.random}) as session:

            try:
                async with session.get("https://www.sslproxies.org/") as resp:
                    soup = BeautifulSoup(await resp.text(), "html.parser")
                    proxies_table = soup.find(
                        "div", {"class": "table-responsive fpl-list"})
                    proxies = proxies_table.tbody.find_all("tr")
                    proxies = [{
                        "ip": x.find_all("td")[0].string,
                        "port": x.find_all("td")[1].string
                    } for x in proxies]
                    return proxies
            except Exception:
                return []

    async def verifyProxy(self, host: str, port: str, timeout: int = 1) -> bool:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("http://icanhazip.com/", proxy=f"http://{host}:{port}", timeout=timeout) as resp:
                    return True
            except Exception:
                return False

    async def verifyProxies(self, unverified: List[str]) -> None:

        for u in unverified:
            proxy = Proxy(u["ip"], u["port"], datetime.datetime.now())
            inList = [x for x in self.proxies if x.ip == proxy.ip]

            if await self.verifyProxy(u["ip"], u["port"]):

                if not inList:
                    self.proxies.append(proxy)
            else:
                if inList:
                    self.proxies.remove(inList[0])

    async def refreshProxies(self) -> None:
        """
        Initialize the first proxies.
        """

        unverified = await self.retrieveProxies()
        await self.verifyProxies(unverified)

    async def get(self, used: bool = True) -> Proxy:
        """
        Get a random proxy, if the proxy that is supposed to be return invalid, it will be removed and a new one will be returned. If there are no more proxies, it will return None.
        """

        if not self.proxies:
            return None

        proxy = random.choice(self.proxies)
        if await self.verifyProxy(proxy.ip, proxy.port, timeout=1):

            if used:
                proxy.uses += 1
            return proxy

        else:
            try:
                self.proxies.remove(proxy)
            except ValueError:
                pass

            return await self.get()
