#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WalletUtil使用示例
"""

import sys
import os

# 添加util目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'util'))

try:
    from util.walletUtil import WalletUtil
    
    def main():
        """主函数"""
        print("=== MyWalletTool 使用示例 ===\n")
        
        # 创建钱包工具实例
        wallet_util = WalletUtil()

        # 示例: Solana主网SOL转账测试
        print("\n5. Solana主网SOL转账测试:")
        from_private_key = ""
        from_address = ""
        # 0xSun地址
        to_address = "HUpPyLU8KWisCAr3mzWy2FKT6uuxQ2qGgJQxyTpDoes5"
        print(f"   转账目标地址: {to_address}")
        result = wallet_util.transfer_token(
            private_key=from_private_key,
            to_address=to_address,
            chain_name="Solana Mainnet",
            coin_name="SOL",
            amount="0.0001"
        )
        print(f"   转账结果: {result}")
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"导入错误: {e}")
    print("请先安装依赖包:")
    print("pip install -r requirements.txt")
except Exception as e:
    print(f"运行过程中出现错误: {e}")

print(sys.executable) 