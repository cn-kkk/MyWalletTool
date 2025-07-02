# MyWalletTool - Web3钱包工具

这是一个自用的Web3钱包工具项目，提供生成EVM和Solana钱包地址的功能。

## 功能特性

- 生成随机EVM地址
- 生成随机Solana地址
- 批量创建新钱包（包含助记词、EVM地址、Solana地址）
- 自动保存钱包信息到文件
- 链上转账功能（支持EVM链和Solana链）
- 配置验证和地址格式验证

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 基本使用

```python
from util.walletUtil import WalletUtil

# 创建钱包工具实例
wallet_util = WalletUtil()

# 生成随机EVM地址
evm_address = wallet_util.generate_random_evm_address()
print(f"EVM地址: {evm_address}")

# 生成随机Solana地址
sol_address = wallet_util.generate_random_sol_address()
print(f"Solana地址: {sol_address}")

# 创建5个新钱包并保存到文件
wallets = wallet_util.create_new_wallets(5)

# 转账示例（需要有效私钥和余额）
# result = wallet_util.transfer_token(
#     private_key="0x...",  # 发送方私钥
#     to_address="0x...",   # 接收方地址
#     chain_name="Ethereum", # 链名称
#     coin_name="ETH",      # 代币名称
#     amount="0.001"        # 转账数量
# )
# print(f"转账结果: {result}")

### 2. 运行转账测试

```bash
python example_transfer.py
```

### 3. 直接运行工具类

```bash
python util/walletUtil.py
```

## 文件说明

- `util/walletUtil.py` - 主要的钱包工具类
- `requirements.txt` - 项目依赖包
- `test_wallet.py` - 测试脚本
- `wallets.txt` - 生成的钱包信息文件（运行后自动创建）

## 安全提醒

⚠️ **重要安全提醒**：

1. 生成的助记词和私钥请妥善保管，不要泄露给他人
2. 建议在离线环境中使用此工具
3. 生成的钱包文件请加密存储
4. 不要在生产环境中使用此工具生成的钱包

## 依赖包说明

- `eth-account`: 用于生成和管理以太坊账户
- `solana`: 用于生成Solana地址
- `mnemonic`: 用于生成助记词
- `hdwallet`: 用于HD钱包功能
- `web3`: 用于EVM链交互和转账
- `requests`: 用于HTTP请求

## 注意事项

- 工具类使用了`Account.enable_unaudited_hdwallet_features()`，这在生产环境中不推荐使用
- 生成的助记词强度为128位（12个单词）
- 钱包信息会保存在项目根目录的`wallets.txt`文件中
- 转账功能需要有效的私钥和足够的余额
- 建议先在测试网络上测试转账功能
- Solana转账功能暂未完全实现 