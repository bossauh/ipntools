import os

from .bruteforcer import BruteForcer
from fluxhelper import Database
from .lookup import mcLookup
from termcolor import colored


if __name__ == '__main__':

    invalid = 0
    valid = 0

    def pinger(ip: str) -> dict:
        global invalid
        global valid

        query = mcLookup(ip)
        if query:
            valid += 1

            print(f"""
{colored(f'[+] {ip}', 'green')} - [{colored(f'{query["players"]["online"]}/{query["players"]["max"]}', 'yellow')}] - {colored(f'{query["ping"]}', 'cyan')}
---------
{colored(f'MOTD:', 'cyan', attrs=['bold'])} {query['motd']}
{colored(f'Version:', 'cyan', attrs=['bold'])} {query['software']['version']}
""")

            return query

        invalid += 1
        print(colored(
            f"Invalid IP: {ip} | Validated: {valid}/{invalid + valid}", "red") + " " * 20, end="\r")

        return None

    br = BruteForcer(
        Database(
            "iptools", connectionString=os.environ["IP_TOOLS_CONNECTION_STRING"]),
        maxIps=7000, workers=270, preventLogs=["invalid", "valid"], pinger=pinger, maxCache=1
    )
    br.start(block=True)
