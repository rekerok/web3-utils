from mnemonic import Mnemonic
import openpyxl
from web3 import Web3
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("count", type=int, help="number of created accounts")

args = parser.parse_args()

wb = openpyxl.Workbook()
sheet = wb.active
sheet["A1"], sheet["B1"], sheet["C1"] = "address", "private key", "mnemonic"
sheet.column_dimensions["A"].width = 30
sheet.column_dimensions["B"].width = 30
sheet.column_dimensions["C"].width = 30

w3 = Web3(Web3.HTTPProvider("https://rpc.payload.de"))
w3.eth.account.enable_unaudited_hdwallet_features()

for i in range(args.count):
    mnemo = Mnemonic("english")
    words = mnemo.generate(strength=128)
    acc = w3.eth.account.from_mnemonic(words)
    sheet.append((acc.address, w3.to_hex(acc._private_key)[2:], words))

wb.save("wallet.xlsx")
