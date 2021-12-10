import random
import datetime
import threading
import time

from urllib.request import Request, urlopen
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
        self.proxies = []

        threading.Thread(target=self.refresher, daemon=True).start()

    def refresher(self) -> None:
        """
        Refreshes the proxy list every self.refreshRate.
        """

        while True:
            self.refreshProxies()
            time.sleep(self.refreshRate)

    def retrieveProxies(self) -> List[str]:
        proxies_db = Request("https://www.sslproxies.org/")
        proxies_db.add_header("User-Agent", self.ua.random)
        proxies_doc = urlopen(proxies_db).read().decode("utf8")

        soup = BeautifulSoup(proxies_doc, "html.parser")
        proxies_table = soup.find(
            "div", {"class": "table-responsive fpl-list"})

        l = []
        for row in proxies_table.tbody.find_all("tr"):
            l.append({
                "ip": row.find_all("td")[0].string,
                "port": row.find_all("td")[1].string
            })

        return l

    def verifyProxy(self, host: str, port: str, timeout: int = 1) -> bool:
        req = Request("http://icanhazip.com")
        req.set_proxy(f"{host}:{port}", "http")

        try:
            urlopen(req, timeout=timeout).read().decode("utf-8")
            return True
        except Exception:
            return False

    def verifyProxies(self, unverified: List[str]) -> None:
        for u in unverified:
            proxy = Proxy(u["ip"], u["port"], datetime.datetime.now())
            inList = [x for x in self.proxies if x.ip == proxy.ip]

            if self.verifyProxy(u["ip"], u["port"]):
                if not inList:
                    self.proxies.append(proxy)
            else:
                if inList:
                    self.proxies.remove(inList[0])

    def refreshProxies(self) -> None:
        """
        Initialize the first proxies.
        """

        unverified = self.retrieveProxies()
        self.verifyProxies(unverified)

    def get(self, used: bool = True) -> Proxy:
        """
        Get a random proxy, if the proxy that is supposed to be return invalid, it will be removed and a new one will be returned. If there are no more proxies, it will return None.
        """

        if not self.proxies:
            return None

        proxy = random.choice(self.proxies)
        if self.verifyProxy(proxy.ip, proxy.port, timeout=1):

            if used:
                proxy.uses += 1
            return proxy

        else:
            try:
                self.proxies.remove(proxy)
            except ValueError:
                pass

            return self.get()

