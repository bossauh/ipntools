import threading
import time
import datetime
from fluxhelper import Database, Logger
from pymongo.database import Database as MongoDatabase
from queue import Queue
from .lookup import regularLookup
from .basics import generateIp


class Threads:
    """
    Loops that runs in the background that is responsible for the bruteforce
    """

    def _generator(self) -> None:
        while not self.stopped:
            ip = generateIp()
            data = {"ip": ip, "data": {}}
            self.ips.put(data)

    def _storage(self) -> None:
        while not self.stopped:
            if self.toStore.full():
                compiled = []
                for _ in range(self.toStore.qsize()):
                    compiled.append(self.toStore.get())

                self.db.ips.insert_many(compiled)

    def _worker(self) -> None:
        """
        Responsible for continuously running the pinging function for the ip addresses.
        """
        while not self.stopped:
            ip = self.ips.get()
            if ip:
                pingData = self.pinger(ip["ip"])

                if pingData:

                    if not "valid" in self.preventLogs:
                        self.logging.success(f"Valid IP: {ip['ip']}")

                    ip["data"] = pingData
                    ip["__datetime__"] = datetime.datetime.utcnow()

                    self.toStore.put(ip)
                else:

                    if not "invalid" in self.preventLogs:
                        self.logging.error("Invalid IP: {}".format(ip["ip"]))


class BruteForcer(Threads):
    def __init__(self, db: MongoDatabase, debug: bool = True, **kwargs) -> None:
        self.logging = Logger(debug=debug)
        self.dbClient = db
        self.db = self.dbClient.db

        # Kwargs
        self.workers = kwargs.get('workers', 200)
        self.pinger = kwargs.get("pinger", self.ping)
        self.preventLogs = kwargs.get("preventLogs", [])

        # Queues
        self.ips = Queue(maxsize=kwargs.get("maxIps", 5000000))
        self.toStore = Queue(maxsize=kwargs.get("maxCache", 100))

        # Status
        self.stopped = False

    def start(self, block=True) -> None:
        threading.Thread(target=self._generator, daemon=True).start()
        threading.Thread(target=self._storage, daemon=True).start()

        workers = [self._worker] * self.workers
        for worker in workers:
            threading.Thread(target=worker, daemon=True).start()

        if block:
            while True:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    self.logging.info("Stopping...")
                    self.stop()
                    break

    def stop(self) -> None:
        self.stopped = True

    def ping(self, ip: str) -> None:
        data = regularLookup(ip)
        if data:
            self.logging.success(
                f"Valid IP: {ip} ({data['ping']}ms) | Domain: {data['domain']}")
            return data

        return None


if __name__ == "__main__":

    bruteforcer = BruteForcer(
        Database("deep-ip"), debug=True, maxIps=5000, workers=250, preventLogs=["valid"])
    bruteforcer.start(block=True)
