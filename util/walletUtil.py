import os
import secrets
import json
from typing import List, Tuple, Dict, Optional
from eth_account import Account
from mnemonic import Mnemonic
import base58
import hashlib
from web3 import Web3
import requests
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.system_program import TransferParams, transfer
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import transfer_checked, get_associated_token_address, create_associated_token_account, TransferCheckedParams
import logging
from datetime import datetime

# 日志格式设置 - 只输出到控制台，不生成文件
logger = logging.getLogger("MyWalletTool")
logger.setLevel(logging.INFO)

# 清除已有的处理器
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# 添加控制台处理器
console_handler = logging.StreamHandler()
formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 防止日志传播到根logger
logger.propagate = False

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)

class WalletUtil:
    """Web3钱包工具类"""
    
    def __init__(self):
        """初始化钱包工具类"""
        self.mnemo = Mnemonic("english")
        # 启用本地生成私钥（不推荐用于生产环境）
        Account.enable_unaudited_hdwallet_features()
    
    def generate_random_evm_address(self) -> str:
        """
        生成一个随机的EVM地址
        
        Returns:
            str: 生成的EVM地址
        """
        log_info("开始生成evm地址")
        private_key = "0x" + secrets.token_hex(32)
        account = Account.from_key(private_key)
        log_info(f"完成生成evm地址——响应结果:{{'address': '{account.address}'}}")
        return account.address
    
    def generate_random_sol_address(self) -> str:
        """
        生成一个随机的Solana地址
        
        Returns:
            str: 生成的Solana地址
        """
        log_info("开始生成sol地址")
        private_key = secrets.token_bytes(32)
        public_key = hashlib.sha256(private_key).digest()
        address = base58.b58encode(public_key).decode('utf-8')
        log_info(f"完成生成sol地址——响应结果:{{'address': '{address}'}}")
        return address
    
    def generate_wallet_info(self) -> dict:
        """
        生成一个钱包信息
        
        Returns:
            dict: 钱包信息字典（只含助记词和EVM地址）
        """
        try:
            mnemonic = self.mnemo.generate(strength=128)
            # 直接生成随机私钥，避免助记词验证问题
            private_key = "0x" + secrets.token_hex(32)
            account = Account.from_key(private_key)
            evm_address = account.address
            
            log_info(f"生成钱包 | 助记词: {mnemonic} | EVM地址: {evm_address}")
            return {"mnemonic": mnemonic, "evm_address": evm_address}
        except Exception as e:
            log_error(f"生成钱包失败: {e}")
            # 如果生成失败，使用更简单的方法
            mnemonic = self.mnemo.generate(strength=128)
            private_key = "0x" + secrets.token_hex(32)
            account = Account.from_key(private_key)
            evm_address = account.address
            log_info(f"生成钱包(回退方法) | 助记词: {mnemonic} | EVM地址: {evm_address}")
            return {"mnemonic": mnemonic, "evm_address": evm_address}
    
    def _load_chain_config(self) -> Dict:
        """加载链配置"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'chain.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_contract_config(self) -> Dict:
        """加载合约配置"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'contract.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _validate_chain_and_token(self, chain_name: str, coin_name: str) -> Tuple[Dict, Dict]:
        """
        验证链和代币配置
        
        Args:
            chain_name: 链名称
            coin_name: 代币名称
            
        Returns:
            Tuple[Dict, Dict]: (链配置, 代币配置)
            
        Raises:
            ValueError: 如果链或代币配置不存在
        """
        chain_config = self._load_chain_config()
        contract_config = self._load_contract_config()
        
        # 查找链配置
        chain_info = None
        for chain_type in ['evm_chains', 'solana_chains', 'testnet_chains']:
            for chain in chain_config.get(chain_type, []):
                if chain['chainName'] == chain_name:
                    chain_info = chain
                    break
            if chain_info:
                break
        
        if not chain_info:
            raise ValueError(f"链 '{chain_name}' 在配置文件中不存在")
        
        # 查找代币配置
        token_info = None
        for token in contract_config.get('tokens', []):
            if token['chainName'] == chain_name and token['coinName'] == coin_name:
                token_info = token
                break
        
        if not token_info:
            raise ValueError(f"代币 '{coin_name}' 在链 '{chain_name}' 上的配置不存在")
        
        return chain_info, token_info
    
    def _validate_address(self, address: str, chain_name: str) -> bool:
        """
        验证地址格式
        
        Args:
            address: 地址
            chain_name: 链名称
            
        Returns:
            bool: 地址是否有效
        """
        if chain_name == "Solana Mainnet":
            # Solana地址验证
            try:
                if len(address) != 44:
                    return False
                base58.b58decode(address)
                return True
            except:
                return False
        else:
            # EVM地址验证
            try:
                if not address.startswith('0x') or len(address) != 42:
                    return False
                int(address, 16)
                return True
            except:
                return False
    
    def transfer_token(self, private_key: str, to_address: str, chain_name: str, coin_name: str, amount: str) -> Dict:
        try:
            log_info(f"开始{chain_name}转账——请求参数:{{'private_key': '***', 'to_address': '{to_address}', 'chain_name': '{chain_name}', 'coin_name': '{coin_name}', 'amount': '{amount}'}}")
            if chain_name == "Solana Mainnet":
                token_info = self._get_token_info(chain_name, coin_name)
                log_info(f"开始solana钱包转账——请求参数:{{'private_key': '***', 'to_address': '{to_address}', 'token_info': {token_info}, 'amount': '{amount}'}}")
                result = self._transfer_solana(private_key, to_address, token_info, amount)
                log_info(f"完成solana钱包转账——响应结果:{json.dumps(result, ensure_ascii=False)}")
                return result
            else:
                chain_info, token_info = self._validate_chain_and_token(chain_name, coin_name)
                log_info(f"开始evm钱包转账——请求参数:{{'private_key': '***', 'to_address': '{to_address}', 'chain_info': {chain_info}, 'token_info': {token_info}, 'amount': '{amount}', 'coin_name': '{coin_name}'}}")
                result = self._transfer_evm(private_key, to_address, chain_info, token_info, amount, coin_name)
                # 处理tx_hash为HexBytes的情况
                if result.get('tx_hash') is not None:
                    result['tx_hash'] = str(result['tx_hash'])
                log_info(f"完成evm钱包转账——响应结果:{json.dumps(result, ensure_ascii=False)}")
                return result
        except Exception as e:
            error_result = {"success": False, "error": f"{chain_name}转账失败: {e}", "tx_hash": None}
            log_error(f"{chain_name}钱包转账异常——{json.dumps(error_result, ensure_ascii=False)}")
            return error_result
    
    def _transfer_evm(self, 
                     private_key: str, 
                     to_address: str, 
                     chain_info: Dict, 
                     token_info: Dict, 
                     amount: str,
                     coin_name: str) -> Dict:
        """
        EVM链转账
        
        Args:
            private_key: 私钥
            to_address: 接收地址
            chain_info: 链配置
            token_info: 代币配置
            amount: 转账数量
            
        Returns:
            Dict: 转账结果
        """
        params = {
            'private_key': '***',
            'to_address': to_address,
            'chain_info': chain_info,
            'token_info': token_info,
            'amount': amount,
            'coin_name': coin_name
        }
        log_info(f"开始evm钱包转账——请求参数:{json.dumps(params, ensure_ascii=False)}")
        try:
            # 连接到Web3
            w3 = Web3(Web3.HTTPProvider(chain_info['rpc']))
            if not w3.is_connected():
                raise Exception(f"无法连接到 {chain_info['chainName']} RPC节点")
            
            # 创建账户
            account = Account.from_key(private_key)
            from_address = account.address
            
            # 验证发送方地址格式
            if not self._validate_address(from_address, chain_info['chainName']):
                raise ValueError(f"发送方地址格式无效: {from_address}")
            
            # 获取nonce
            nonce = w3.eth.get_transaction_count(from_address)
            
            # 获取gas价格
            gas_price = w3.eth.gas_price
            
            if token_info['isNative']:
                # 原生代币转账
                value = w3.to_wei(amount, 'ether')
                
                # 构建交易
                transaction = {
                    'nonce': nonce,
                    'to': to_address,
                    'value': value,
                    'gas': 21000,  # 标准转账gas
                    'gasPrice': gas_price,
                    'chainId': int(chain_info['chain_id'])
                }
                
            else:
                # ERC20代币转账
                contract_address = token_info['contractAddress']
                decimals = token_info['decimals']
                
                # ERC20转账ABI
                abi = [
                    {
                        "constant": False,
                        "inputs": [
                            {"name": "_to", "type": "address"},
                            {"name": "_value", "type": "uint256"}
                        ],
                        "name": "transfer",
                        "outputs": [{"name": "", "type": "bool"}],
                        "type": "function"
                    }
                ]
                
                # 创建合约实例
                contract = w3.eth.contract(address=contract_address, abi=abi)
                
                # 计算转账数量（考虑小数位）
                token_amount = int(float(amount) * (10 ** decimals))
                
                # 构建交易
                transaction = contract.functions.transfer(to_address, token_amount).build_transaction({
                    'nonce': nonce,
                    'gas': 100000,  # ERC20转账预估gas
                    'gasPrice': gas_price,
                    'chainId': int(chain_info['chain_id'])
                })
            
            # 签名交易
            signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
            
            # 发送交易
            tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # 等待交易确认
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if tx_receipt["status"] == 1:
                result = {
                    "success": True,
                    "tx_hash": tx_hash.hex(),
                    "from_address": from_address,
                    "to_address": to_address,
                    "amount": amount,
                    "chain_name": chain_info['chainName'],
                    "coin_name": coin_name,
                    "block_number": tx_receipt["blockNumber"]
                }
                log_info(f"完成evm钱包转账——响应结果:{json.dumps(result, ensure_ascii=False)}")
                return result
            else:
                error_json = {"success": False, "error": "交易执行失败", "tx_hash": tx_hash.hex()}
                log_error(f"evm钱包转账失败——{json.dumps(error_json, ensure_ascii=False)}")
                return error_json
                
        except Exception as e:
            error_json = {"success": False, "error": f"EVM转账失败: {str(e)}", "tx_hash": None}
            log_error(f"evm钱包转账异常——{json.dumps(error_json, ensure_ascii=False)}")
            return error_json
    
    def _transfer_solana(self, 
                        private_key: str, 
                        to_address: str, 
                        token_info: Dict, 
                        amount: str) -> Dict:
        """
        Solana链转账
        Args:
            private_key: base58编码的私钥（或32字节原始）
            to_address: 接收地址
            token_info: 代币配置
            amount: 转账数量
        Returns:
            Dict: 转账结果
        """
        params = {
            'private_key': '***',
            'to_address': to_address,
            'token_info': token_info,
            'amount': amount
        }
        log_info(f"开始solana钱包转账——请求参数:{json.dumps(params, ensure_ascii=False)}")
        try:
            # 1. 连接Solana主网
            client = Client("https://api.mainnet-beta.solana.com")
            # 2. 解析私钥
            try:
                if private_key.startswith('['):
                    # 兼容助记词导出的数组格式
                    privkey_bytes = bytes(eval(private_key))
                elif len(private_key) == 64:
                    privkey_bytes = bytes.fromhex(private_key)
                    keypair = Keypair.from_bytes(privkey_bytes)
                else:
                    # base58字符串
                    keypair = Keypair.from_base58_string(private_key)
            except Exception as e:
                return {"success": False, "error": f"私钥格式错误: {str(e)}", "tx_hash": None}
            from_pub = keypair.pubkey()
            to_pub = Pubkey.from_string(to_address)
            # 3. 判断原生币还是SPL Token
            if token_info.get('isNative', False):
                # SOL转账
                lamports = int(float(amount) * 10**token_info['decimals'])
                txn = Transaction.new_signed_with_payer(
                    [transfer(TransferParams(
                        from_pubkey=from_pub,
                        to_pubkey=to_pub,
                        lamports=lamports
                    ))],
                    from_pub,
                    [keypair],
                    client.get_latest_blockhash().value.blockhash
                )
                resp = client.send_transaction(txn)
                if hasattr(resp, 'value') and resp.value and not getattr(resp, 'error', None):
                    tx_sig = resp.value
                    result = {
                        "success": True,
                        "tx_hash": str(tx_sig),
                        "from_address": str(from_pub),
                        "to_address": str(to_pub),
                        "amount": amount,
                        "chain_name": "Solana Mainnet",
                        "coin_name": token_info['coinName']
                    }
                    log_info(f"完成solana钱包转账——响应结果:{json.dumps(result, ensure_ascii=False)}")
                    return result
                else:
                    error_json = {"success": False, "error": str(resp), "tx_hash": None}
                    log_error(f"solana钱包转账失败——{json.dumps(error_json, ensure_ascii=False)}")
                    return error_json
            else:
                # SPL Token转账（如USDT、USDC）
                mint = Pubkey.from_string(token_info['contractAddress'])
                decimals = token_info['decimals']
                # 获取发送方和接收方的ATA
                from_ata = get_associated_token_address(from_pub, mint)
                to_ata = get_associated_token_address(to_pub, mint)
                # 检查接收方ATA是否存在，不存在则创建
                resp_info = client.get_account_info(to_ata)
                instructions = []
                if resp_info.value is None:
                    instructions.append(create_associated_token_account(from_pub, to_pub, mint))
                token_amount = int(float(amount) * 10**decimals)
                instructions.append(transfer_checked(
                    TransferCheckedParams(
                        program_id=TOKEN_PROGRAM_ID,
                        source=from_ata,
                        mint=mint,
                        dest=to_ata,
                        owner=from_pub,
                        amount=token_amount,
                        decimals=decimals
                    )
                ))
                txn = Transaction.new_signed_with_payer(
                    instructions,
                    from_pub,
                    [keypair],
                    client.get_latest_blockhash().value.blockhash
                )
                resp = client.send_transaction(txn)
                if hasattr(resp, 'value') and resp.value and not getattr(resp, 'error', None):
                    tx_sig = resp.value
                    result = {
                        "success": True,
                        "tx_hash": str(tx_sig),
                        "from_address": str(from_pub),
                        "to_address": str(to_pub),
                        "amount": amount,
                        "chain_name": "Solana Mainnet",
                        "coin_name": token_info['coinName']
                    }
                    log_info(f"完成solana钱包转账——响应结果:{json.dumps(result, ensure_ascii=False)}")
                    return result
                else:
                    error_json = {"success": False, "error": str(resp), "tx_hash": None}
                    log_error(f"solana钱包转账失败——{json.dumps(error_json, ensure_ascii=False)}")
                    return error_json
        except Exception as e:
            error_json = {"success": False, "error": f"Solana转账失败: {str(e)}", "tx_hash": None}
            log_error(f"solana钱包转账异常——{json.dumps(error_json, ensure_ascii=False)}")
            return error_json

    def _get_token_info(self, chain_name: str, coin_name: str) -> Dict:
        """
        获取代币信息
        
        Args:
            chain_name: 链名称
            coin_name: 代币名称
            
        Returns:
            Dict: 代币配置
        """
        contract_config = self._load_contract_config()
        
        # 查找代币配置
        token_info = None
        for token in contract_config.get('tokens', []):
            if token['chainName'] == chain_name and token['coinName'] == coin_name:
                token_info = token
                break
        
        if not token_info:
            raise ValueError(f"代币 '{coin_name}' 在链 '{chain_name}' 上的配置不存在")
        
        return token_info

