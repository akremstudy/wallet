
import os
import bit
import json
import subprocess
from web3 import Web3
from constants import *
from dotenv import load_dotenv
from eth_account import Account
from web3.middleware import geth_poa_middleware

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
load_dotenv()

def derive_wallets(coin):
    mnemonic = os.getenv('MNEMONIC')
    command = f'./derive -g --mnemonic="{mnemonic}" --cols=address,index,path,privkey,pubkey,xprv,xpub --coin={coin} --numderive=2 --format=json'

    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()

    keys = json.loads(output)
    return(keys)

coins = {BTCTEST: derive_wallets(BTCTEST), ETH:derive_wallets(ETH)}

def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    if coin == BTCTEST:
        return bit.PrivateKeyTestnet(priv_key)

def create_tx(coin, account, recipient, amount):
    if coin == ETH:
        gasEstimate = w3.eth.estimateGas(
        {"from": account.address, "to": recipient, "value": amount})
        return {
            "to": recipient,
            "from": account.address,
            "value": amount,
            "gas": gasEstimate,
            "gasPrice": w3.eth.gasPrice,
            "nonce": w3.eth.getTransactionCount(account.address),
            "chainID": w3.eth.chainId(account.address)}
    if coin == BTCTEST:
        return bit.PrivateKeyTestnet.prepare_transaction(account.address, [(recipient, amount, BTC)])

def send_tx(coin, account, recipient, amount):
    if coin == ETH:
        total = w3.toWei(amount, 'ether')
        raw_tx = create_tx(coin, account, recipient, total)
        signed_tx = account.sign_transaction(raw_tx)
        result = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return result.hex()
    if coin == BTCTEST:
        raw_tx = create_tx(coin, account, recipient, amount)
        signed_tx = account.sign_transaction(raw_tx)
        return bit.network.NetworkAPI.broadcast_tx_testnet(signed_tx)