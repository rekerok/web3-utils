import pprint
import requests
from web3 import Web3
from config_networks import coins
from tqdm import tqdm
from tabulate import tabulate
import colorama

colorama.init(autoreset=True)

### CONFIG ###
view_more_than = 0  # показать балансы монет где больше чем это число (usdt)
round_numbers = 4  # сколько чисел после запятой выводить
# sort_by_total = True  # вывод будет начинаться с кошелька с наибольшй суммой
check_native_token = True  # показывать нативный токены сети True - да / False - нет
output_zero_balance = False  # выводить пустые баланы (True - да, False - нет)
# output_in_file = "" # "" - вывод будет в терминал | "name.txt" вывов в файл name.txt
##############


def collect_coin(symbol, ampunt, amount_usdt):
    return {symbol: {"amount": ampunt, "usdt": amount_usdt}}


def collect_all_coins(balances):
    coin_totals = dict()
    for i in balances.values():
        for network, coins in i[0].items():
            if network != "GOERLI":
                for coin, details in coins.items():
                    if coin not in coin_totals:
                        coin_totals[coin] = {
                            "amount": details["amount"],
                            "usdt": details["usdt"],
                        }
                    else:
                        coin_totals[coin]["amount"] += details["amount"]
                        coin_totals[coin]["usdt"] += details["usdt"]
    return coin_totals


def collect_balance_one_address():
    balance = list()
    balance.append(dict())
    total_on_wallet = 0
    for network in coins:
        for key, value in network.items():
            w3 = Web3(Web3.HTTPProvider(value["rpc"]))
            balance[0][key] = dict()
            if check_native_token:
                amount = w3.eth.get_balance(i) / 10**18
                price_usdt = float(get_price_token(value["symbol"])) * amount
                total_on_wallet += price_usdt
                balance[0][key].update(
                    collect_coin(value["symbol"], amount, price_usdt)
                )
            for coin in value["coins"]:
                token = w3.eth.contract(
                    address=w3.to_checksum_address(coin["address"]), abi=coin["abi"]
                )
                amount = (
                    token.functions.balanceOf(w3.to_checksum_address(i)).call()
                    / 10 ** coin["decimal"]
                )
                price_usdt = float(get_price_token(coin["symbol"])) * amount
                total_on_wallet += price_usdt
                balance[0][key].update(collect_coin(coin["symbol"], amount, price_usdt))
        if "GOERLI" in balance[0]:
            total_on_wallet = total_on_wallet - balance[0]["GOERLI"]["ETH"]["usdt"]
        else:
            total_on_wallet = total_on_wallet
        balance.append({"total": total_on_wallet})
        return balance


def get_price_token(symbol):
    for i in prices_all_tokens:
        if i["currency_pair"] == f"{symbol}_USD":
            return i["last"]
    return 0


def output_balances(balances, filename=""):
    count = 1
    if not filename:
        print("=" * 15)
        for wallet, networks in balances.items():
            if round(networks[1]["total"], round_numbers) == 0:
                continue
            print(f"{count}) {wallet}")
            for network, coins in networks[0].items():
                print(network)
                for key, value in coins.items():
                    if not output_zero_balance and value["amount"] == 0.0:
                        continue
                    if value["usdt"] >= view_more_than:
                        print(
                            f"\t{key.ljust(6)}{str(round(value['amount'],round_numbers))} | {round(value['usdt'],round_numbers)}$"
                        )
            print(f"На кошельке {round(networks[1]['total'],round_numbers)}$")
            count += 1
            print("=" * 15)
    else:
        with open(filename, "w") as file:
            file.write("=" * 15 + "\n")
            count = 1
            for wallet, networks in balances.items():
                file.write(f"{count}) {wallet}\n")
                for network, coins in networks[0].items():
                    file.write(network + "\n")
                    for key, value in coins.items():
                        if not output_zero_balance and value["amount"] == 0.0:
                            continue
                        if value["usdt"] >= view_more_than:
                            file.write(
                                f"\t{key.ljust(6)}{str(round(value['amount'], round_numbers))} | {round(value['usdt'], round_numbers)}$\n"
                            )
                file.write(
                    f"На кошельке {round(networks[1]['total'], round_numbers)}$\n"
                )
                count += 1
                file.write("=" * 15 + "\n")


def output_total_coins(coin_totals):
    for key, value in coin_totals.items():
        print(
            f"{key.ljust(6)}{round(value['amount'],round_numbers)} {round(value['usdt'],round_numbers)}$"
        )


def round_values(data):
    rounded_data = [
        [item[0], item[1], item[2], round(item[3], 1), round(item[4], 1)]
        for item in data
    ]
    return rounded_data


def remove_duplicates(data):
    cleaned_data = []
    unique_addresses = set()
    for item in data:
        address = item[0]
        network = item[1]
        if (address, network) not in unique_addresses:
            unique_addresses.add((address, network))
            cleaned_data.append(item)
        else:
            item[1] = ""  # Замена сети на пустую строку
            cleaned_data.append(item)
    return remove_duplicates_adress(cleaned_data)


def remove_duplicates_adress(data):
    unique_addresses = set()
    cleaned_data = []
    for item in data:
        address = item[0]
        if address not in unique_addresses:
            unique_addresses.add(address)
            cleaned_data.append(item)
        else:
            item[0] = ""  # Замена адреса на пустую строку
            cleaned_data.append(item)
    return cleaned_data


# def get_tabulate(balances):
#     data = list()
#     for wallet, networks in balances.items():
#         tokens = list()
#         for network, coins in networks[0].items():
#             for symbol, value in coins.items():
#                 data.append([wallet, network, symbol, value["amount"], value["usdt"]])
#     # print(data)
#     headers = ["Wallet", "Network", "Token", "Amount", "USDT"]
#     print(data)
#     print(
#         tabulate(
#             remove_duplicates(round_values(data)), headers=headers, tablefmt="grid"
#         )
#     )


if __name__ == "__main__":
    prices_all_tokens = requests.get("https://api.gateio.ws/api/v4/spot/tickers").json()
    with open("./public.txt", "r") as wallets_txt:
        public_keys = wallets_txt.read().splitlines(keepends=False)
        public_keys = list(filter(None, public_keys))
    total_on_wallets = 0
    balances = dict()
    for i in tqdm(public_keys, desc="Fetching balances", unit="wallet"):
        balance_of_wallet = collect_balance_one_address()
        total_on_wallets += balance_of_wallet[1]["total"]
        balances[i] = balance_of_wallet
    output_balances(balances)
    print(f"Всего на кошельках {round(total_on_wallets,round_numbers)}$")
    output_total_coins(collect_all_coins(balances))
