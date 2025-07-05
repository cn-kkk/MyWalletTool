import sys
import json
import os
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit, QPushButton, QLabel, QPlainTextEdit, QFormLayout, QLineEdit, QStackedWidget, QSizePolicy, QSpacerItem, QComboBox, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QThread, QMetaObject, Q_ARG
from PyQt5.QtGui import QFont, QColor, QPalette, QBrush
from util.walletUtil import WalletUtil

def resource_path(relative_path):
    """获取资源文件的绝对路径，兼容 PyInstaller 打包和源码运行"""
    try:
        # 如果是PyInstaller打包后的环境
        if hasattr(sys, '_MEIPASS'):
            # 从临时解压目录读取
            meipass_path = os.path.join(getattr(sys, '_MEIPASS'), relative_path)
            if os.path.exists(meipass_path):
                return meipass_path
        
        # 尝试从当前工作目录读取
        current_dir_path = os.path.join(os.getcwd(), relative_path)
        if os.path.exists(current_dir_path):
            return current_dir_path
        
        # 尝试从exe所在目录读取
        if hasattr(sys, 'executable'):
            exe_dir = os.path.dirname(sys.executable)
            exe_dir_path = os.path.join(exe_dir, relative_path)
            if os.path.exists(exe_dir_path):
                return exe_dir_path
        
        # 尝试从源码目录读取
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir_path = os.path.join(script_dir, relative_path)
        if os.path.exists(script_dir_path):
            return script_dir_path
        
        # 如果都找不到，返回当前工作目录的路径
        return current_dir_path
        
    except Exception as e:
        print(f"resource_path error for {relative_path}: {e}")
        return relative_path

class WorkerThread(QThread):
    """工作线程类"""
    result_ready = pyqtSignal(str, str)  # 信号：(结果类型, 结果内容)
    log_ready = pyqtSignal(str)  # 日志信号
    
    def __init__(self, task_type, *args, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.args = args
        self.kwargs = kwargs
        self.wallet_util = WalletUtil()
    
    def run(self):
        """执行任务"""
        try:
            if self.task_type == "generate_evm_address":
                address = self.wallet_util.generate_random_evm_address()
                result = json.dumps({"address": address}, indent=2, ensure_ascii=False)
                self.result_ready.emit("evm_address", result)
                self.log_ready.emit(f"EVM地址生成成功: {address}")
                
            elif self.task_type == "generate_sol_address":
                address = self.wallet_util.generate_random_sol_address()
                result = json.dumps({"address": address}, indent=2, ensure_ascii=False)
                self.result_ready.emit("sol_address", result)
                self.log_ready.emit(f"Solana地址生成成功: {address}")
                
            elif self.task_type == "generate_wallet":
                wallet = self.wallet_util.generate_wallet_info()
                result = json.dumps(wallet, indent=2, ensure_ascii=False)
                self.result_ready.emit("wallet", result)
                self.log_ready.emit(f"钱包生成成功: {wallet['evm_address']}")
                
            elif self.task_type == "evm_transfer":
                private_key, to_address, chain_name, coin_name, amount = self.args
                try:
                    result = self.wallet_util.transfer_token(private_key, to_address, chain_name, coin_name, amount)
                    result_json = json.dumps(result, indent=2, ensure_ascii=False)
                    self.result_ready.emit("evm_transfer", result_json)
                    
                    if result.get("success"):
                        self.log_ready.emit(f"EVM转账成功: {result.get('tx_hash', '')}")
                    else:
                        self.log_ready.emit(f"EVM转账失败: {result.get('error', '')}")
                except Exception as e:
                    error_result = {"success": False, "error": str(e)}
                    self.result_ready.emit("evm_transfer", json.dumps(error_result, indent=2, ensure_ascii=False))
                    self.log_ready.emit(f"EVM转账异常: {e}")
                    
            elif self.task_type == "sol_transfer":
                private_key, to_address, coin_name, amount = self.args
                try:
                    result = self.wallet_util.transfer_token(private_key, to_address, "Solana Mainnet", coin_name, amount)
                    result_json = json.dumps(result, indent=2, ensure_ascii=False)
                    self.result_ready.emit("sol_transfer", result_json)
                    
                    if result.get("success"):
                        self.log_ready.emit(f"Solana转账成功: {result.get('tx_hash', '')}")
                    else:
                        self.log_ready.emit(f"Solana转账失败: {result.get('error', '')}")
                except Exception as e:
                    error_result = {"success": False, "error": str(e)}
                    self.result_ready.emit("sol_transfer", json.dumps(error_result, indent=2, ensure_ascii=False))
                    self.log_ready.emit(f"Solana转账异常: {e}")
                    
        except Exception as e:
            error_msg = f"{self.task_type} 执行失败: {e}"
            self.result_ready.emit(self.task_type, error_msg)
            self.log_ready.emit(error_msg)

class LogWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont('Consolas', 10))
        # 设置浅色背景、深色字体
        pal = self.palette()
        pal.setColor(QPalette.Base, QColor(245, 245, 245))
        pal.setColor(QPalette.Text, QColor(30, 30, 30))
        self.setPalette(pal)
        self.setFixedHeight(300)  # 高度提升到300
        
        # 创建日志文件
        self.log_filename = self.create_log_file()
        self.log_buffer = []
        self.last_write_time = time.time()
        
        # 创建定时器，每10秒写入日志文件
        self.timer = QTimer()
        self.timer.timeout.connect(self.flush_log_buffer)
        self.timer.start(10000)  # 10秒
    
    def create_log_file(self):
        """创建日志文件"""
        if not os.path.exists("logs"):
            os.makedirs("logs")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/gui_{timestamp}.log"
        return filename
    
    def append_log(self, msg):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {msg}"
        
        self.append(log_msg)
        self.log_buffer.append(log_msg)
        
        # 滚动到底部
        sb = self.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())
    
    def flush_log_buffer(self):
        """将日志缓冲区写入文件"""
        if self.log_buffer:
            try:
                with open(self.log_filename, "a", encoding="utf-8") as f:
                    for msg in self.log_buffer:
                        f.write(msg + "\n")
                self.log_buffer.clear()
                self.last_write_time = time.time()
            except Exception as e:
                print(f"写入日志文件失败: {e}")
    
    def closeEvent(self, event):
        """关闭时写入日志"""
        self.flush_log_buffer()
        super().closeEvent(event)

class StyledSidebar(QListWidget):
    def __init__(self, items, width=360):
        super().__init__()
        self.setFixedWidth(width)
        self.setSpacing(16)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet('''
            QListView, QListWidget {
                outline: none;
            }
            QListWidget {
                border: none;
                background: transparent;
            }
            QListWidget::item {
                background: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 12px;
                margin: 8px 0;
                padding: 18px 24px;
                font-size: 18px;
                color: #333;
                outline: none;
            }
            QListWidget::item:selected {
                background: #d0eaff;
                border: 1.5px solid #3399ff;
                color: #005599;
                outline: none;
            }
            QListWidget::item:focus {
                outline: none;
            }
            QListWidget::item:active {
                outline: none;
            }
            QListWidget::item:hover {
                background: #e6f2ff;
            }
        ''')
        for item in items:
            self.addItem(item)
        self.setCurrentRow(0)

class CodeBlockTextEdit(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont('Consolas', 13))
        self.setStyleSheet('''
            QTextEdit {
                background: #23272e;
                color: #e6e6e6;
                border-radius: 10px;
                border: 1.5px solid #444;
                padding: 12px;
                font-family: Consolas, 'Courier New', monospace;
            }
        ''')
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)

class HomeTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("README 预览：")
        label.setFont(QFont('微软雅黑', 16, QFont.Bold))
        layout.addWidget(label)
        self.readme_view = QTextEdit()
        self.readme_view.setReadOnly(True)
        self.readme_view.setFont(QFont('Consolas', 12))
        try:
            readme_path = resource_path("README.md")
            print(f"尝试加载README文件: {readme_path}")
            if os.path.exists(readme_path):
                with open(readme_path, "r", encoding="utf-8") as f:
                    self.readme_view.setText(f.read())
            else:
                self.readme_view.setText(f"README.md 文件不存在: {readme_path}")
        except Exception as e:
            self.readme_view.setText(f"README.md 加载失败: {str(e)}")
        layout.addWidget(self.readme_view)
        self.setLayout(layout)

class ConfigTab(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout()
        self.sidebar = StyledSidebar(["链设置", "代币合约设置"])
        self.stack = QStackedWidget()
        
        # 链设置
        self.chain_edit = QPlainTextEdit()
        self.chain_edit.setFont(QFont('Consolas', 13))
        self.chain_edit.setReadOnly(True)  # 初始状态为只读
        self.load_chain_config()
        
        self.chain_edit_btn = QPushButton("编辑")
        self.chain_edit_btn.setFixedSize(120, 75)
        self.chain_save_btn = QPushButton("保存链设置")
        self.chain_save_btn.setFixedSize(300, 75)
        self.chain_save_btn.setEnabled(False)  # 初始状态禁用
        
        chain_widget = QWidget()
        chain_layout = QVBoxLayout()
        chain_layout.addWidget(self.chain_edit)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.chain_edit_btn)
        btn_layout.addWidget(self.chain_save_btn)
        chain_layout.addLayout(btn_layout)
        chain_widget.setLayout(chain_layout)
        
        # 代币合约设置
        self.token_edit = QPlainTextEdit()
        self.token_edit.setFont(QFont('Consolas', 13))
        self.token_edit.setReadOnly(True)  # 初始状态为只读
        self.load_contract_config()
        
        self.token_edit_btn = QPushButton("编辑")
        self.token_edit_btn.setFixedSize(120, 75)
        self.token_save_btn = QPushButton("保存代币合约设置")
        self.token_save_btn.setFixedSize(300, 75)
        self.token_save_btn.setEnabled(False)  # 初始状态禁用
        
        token_widget = QWidget()
        token_layout = QVBoxLayout()
        token_layout.addWidget(self.token_edit)
        btn_layout2 = QHBoxLayout()
        btn_layout2.addStretch(1)
        btn_layout2.addWidget(self.token_edit_btn)
        btn_layout2.addWidget(self.token_save_btn)
        token_layout.addLayout(btn_layout2)
        token_widget.setLayout(token_layout)
        
        self.stack.addWidget(chain_widget)
        self.stack.addWidget(token_widget)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)
        
        # 连接信号
        self.chain_edit_btn.clicked.connect(self.on_chain_edit_clicked)
        self.chain_save_btn.clicked.connect(self.on_chain_save_clicked)
        self.token_edit_btn.clicked.connect(self.on_token_edit_clicked)
        self.token_save_btn.clicked.connect(self.on_token_save_clicked)
    
    def load_chain_config(self):
        """加载链配置"""
        try:
            chain_path = resource_path("config/chain.json")
            print(f"尝试加载chain.json文件: {chain_path}")
            if os.path.exists(chain_path):
                with open(chain_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chain_edit.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                self.chain_edit.setPlainText(f"chain.json文件不存在: {chain_path}")
        except Exception as e:
            self.chain_edit.setPlainText(f"加载chain.json失败: {e}")
    
    def load_contract_config(self):
        """加载合约配置"""
        try:
            contract_path = resource_path("config/contract.json")
            print(f"尝试加载contract.json文件: {contract_path}")
            if os.path.exists(contract_path):
                with open(contract_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.token_edit.setPlainText(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                self.token_edit.setPlainText(f"contract.json文件不存在: {contract_path}")
        except Exception as e:
            self.token_edit.setPlainText(f"加载contract.json失败: {e}")
    
    def on_chain_edit_clicked(self):
        """链设置编辑按钮点击事件"""
        self.chain_edit.setReadOnly(False)
        self.chain_edit_btn.setEnabled(False)
        self.chain_save_btn.setEnabled(True)
    
    def on_chain_save_clicked(self):
        """链设置保存按钮点击事件"""
        try:
            content = self.chain_edit.toPlainText()
            data = json.loads(content)
            
            # 保存到文件
            with open(resource_path("config/chain.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 恢复只读状态
            self.chain_edit.setReadOnly(True)
            self.chain_edit_btn.setEnabled(True)
            self.chain_save_btn.setEnabled(False)
            
            QMessageBox.information(self, "成功", "链设置保存成功！")
            
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "错误", f"JSON格式错误: {e}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存失败: {e}")
    
    def on_token_edit_clicked(self):
        """代币合约设置编辑按钮点击事件"""
        self.token_edit.setReadOnly(False)
        self.token_edit_btn.setEnabled(False)
        self.token_save_btn.setEnabled(True)
    
    def on_token_save_clicked(self):
        """代币合约设置保存按钮点击事件"""
        try:
            content = self.token_edit.toPlainText()
            data = json.loads(content)
            
            # 保存到文件
            with open(resource_path("config/contract.json"), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 恢复只读状态
            self.token_edit.setReadOnly(True)
            self.token_edit_btn.setEnabled(True)
            self.token_save_btn.setEnabled(False)
            
            QMessageBox.information(self, "成功", "代币合约设置保存成功！")
            
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "错误", f"JSON格式错误: {e}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存失败: {e}")

class WalletTab(QWidget):
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget
        self.wallet_util = WalletUtil()
        
        main_layout = QHBoxLayout()
        self.sidebar = StyledSidebar(["生成随机EVM地址", "生成随机Sol地址", "生成EVM钱包"])
        self.stack = QStackedWidget()
        
        # 生成随机EVM地址
        evm_widget = QWidget()
        evm_layout = QVBoxLayout()
        self.evm_btn = QPushButton("开始生成")
        self.evm_btn.setFixedSize(360, 90)
        evm_btn_layout = QHBoxLayout()
        evm_btn_layout.addStretch(1)
        evm_btn_layout.addWidget(self.evm_btn)
        evm_btn_layout.addStretch(1)
        evm_layout.addLayout(evm_btn_layout)
        self.evm_result = CodeBlockTextEdit()
        evm_layout.addWidget(self.evm_result)
        evm_widget.setLayout(evm_layout)
        
        # 生成随机Sol地址
        sol_widget = QWidget()
        sol_layout = QVBoxLayout()
        self.sol_btn = QPushButton("开始生成")
        self.sol_btn.setFixedSize(360, 90)
        sol_btn_layout = QHBoxLayout()
        sol_btn_layout.addStretch(1)
        sol_btn_layout.addWidget(self.sol_btn)
        sol_btn_layout.addStretch(1)
        sol_layout.addLayout(sol_btn_layout)
        self.sol_result = CodeBlockTextEdit()
        sol_layout.addWidget(self.sol_result)
        sol_widget.setLayout(sol_layout)
        
        # 生成EVM钱包
        wallet_widget = QWidget()
        wallet_layout = QVBoxLayout()
        self.wallet_btn = QPushButton("开始生成")
        self.wallet_btn.setFixedSize(360, 90)
        wallet_btn_layout = QHBoxLayout()
        wallet_btn_layout.addStretch(1)
        wallet_btn_layout.addWidget(self.wallet_btn)
        wallet_btn_layout.addStretch(1)
        wallet_layout.addLayout(wallet_btn_layout)
        self.wallet_result = CodeBlockTextEdit()
        wallet_layout.addWidget(self.wallet_result)
        wallet_widget.setLayout(wallet_layout)
        
        self.stack.addWidget(evm_widget)
        self.stack.addWidget(sol_widget)
        self.stack.addWidget(wallet_widget)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)
        
        # 连接信号
        self.evm_btn.clicked.connect(self.generate_evm_address)
        self.sol_btn.clicked.connect(self.generate_sol_address)
        self.wallet_btn.clicked.connect(self.generate_wallet)
    
    def generate_evm_address(self):
        """生成EVM地址"""
        try:
            self.evm_btn.setEnabled(False)
            self.evm_btn.setText("生成中...")
            
            # 创建工作线程
            self.evm_worker = WorkerThread("generate_evm_address")
            self.evm_worker.result_ready.connect(self.on_evm_result)
            self.evm_worker.log_ready.connect(self.log_widget.append_log)
            self.evm_worker.finished.connect(self.on_evm_finished)
            self.evm_worker.start()
            
        except Exception as e:
            self.log_widget.append_log(f"生成EVM地址失败: {e}")
            self.evm_btn.setEnabled(True)
            self.evm_btn.setText("开始生成")
    
    def on_evm_result(self, result_type, result):
        """EVM地址生成结果处理"""
        self.evm_result.setPlainText(result)
    
    def on_evm_finished(self):
        """EVM地址生成完成"""
        self.evm_btn.setEnabled(True)
        self.evm_btn.setText("开始生成")
    
    def generate_sol_address(self):
        """生成Solana地址"""
        try:
            self.sol_btn.setEnabled(False)
            self.sol_btn.setText("生成中...")
            
            # 创建工作线程
            self.sol_worker = WorkerThread("generate_sol_address")
            self.sol_worker.result_ready.connect(self.on_sol_result)
            self.sol_worker.log_ready.connect(self.log_widget.append_log)
            self.sol_worker.finished.connect(self.on_sol_finished)
            self.sol_worker.start()
            
        except Exception as e:
            self.log_widget.append_log(f"生成Solana地址失败: {e}")
            self.sol_btn.setEnabled(True)
            self.sol_btn.setText("开始生成")
    
    def on_sol_result(self, result_type, result):
        """Solana地址生成结果处理"""
        self.sol_result.setPlainText(result)
    
    def on_sol_finished(self):
        """Solana地址生成完成"""
        self.sol_btn.setEnabled(True)
        self.sol_btn.setText("开始生成")
    
    def generate_wallet(self):
        """生成EVM钱包"""
        try:
            self.wallet_btn.setEnabled(False)
            self.wallet_btn.setText("生成中...")
            
            # 创建工作线程
            self.wallet_worker = WorkerThread("generate_wallet")
            self.wallet_worker.result_ready.connect(self.on_wallet_result)
            self.wallet_worker.log_ready.connect(self.log_widget.append_log)
            self.wallet_worker.finished.connect(self.on_wallet_finished)
            self.wallet_worker.start()
            
        except Exception as e:
            self.log_widget.append_log(f"生成钱包失败: {e}")
            self.wallet_btn.setEnabled(True)
            self.wallet_btn.setText("开始生成")
    
    def on_wallet_result(self, result_type, result):
        """钱包生成结果处理"""
        self.wallet_result.setPlainText(result)
    
    def on_wallet_finished(self):
        """钱包生成完成"""
        self.wallet_btn.setEnabled(True)
        self.wallet_btn.setText("开始生成")

class TransferTab(QWidget):
    def __init__(self, log_widget):
        super().__init__()
        self.log_widget = log_widget
        self.wallet_util = WalletUtil()
        
        # 加载配置文件
        self.refresh_configs()
        
        main_layout = QHBoxLayout()
        self.sidebar = StyledSidebar(["EVM地址一对一转账", "Sol地址一对一转账"])
        self.stack = QStackedWidget()
        
        # EVM转账
        evm_widget = QWidget()
        evm_layout = QVBoxLayout()
        evm_form = QFormLayout()
        evm_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        evm_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        evm_form.setHorizontalSpacing(24)
        evm_form.setVerticalSpacing(18)
        font = QFont('微软雅黑', 13)
        self.evm_priv = QLineEdit(); self.evm_priv.setFont(font); self.evm_priv.setMinimumHeight(32)
        self.evm_to = QLineEdit(); self.evm_to.setFont(font); self.evm_to.setMinimumHeight(32)
        self.evm_chain = QComboBox(); self.evm_chain.setFont(font); self.evm_chain.setMinimumHeight(32)
        self.evm_coin = QComboBox(); self.evm_coin.setFont(font); self.evm_coin.setMinimumHeight(32)
        self.evm_amount = QLineEdit(); self.evm_amount.setFont(font); self.evm_amount.setMinimumHeight(32)
        self.init_evm_chain_combo()
        evm_form.addRow("私钥:", self.evm_priv)
        evm_form.addRow("收款地址:", self.evm_to)
        evm_form.addRow("链名:", self.evm_chain)
        evm_form.addRow("币种:", self.evm_coin)
        evm_form.addRow("金额:", self.evm_amount)
        self.evm_transfer_btn = QPushButton("转账")
        self.evm_transfer_btn.setFixedSize(300, 75)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.evm_transfer_btn)
        self.evm_result = CodeBlockTextEdit()
        evm_layout.addLayout(evm_form)
        evm_layout.addLayout(btn_layout)
        evm_layout.addWidget(self.evm_result)
        evm_widget.setLayout(evm_layout)
        # Sol转账
        sol_widget = QWidget()
        sol_layout = QVBoxLayout()
        sol_form = QFormLayout()
        sol_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        sol_form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        sol_form.setHorizontalSpacing(24)
        sol_form.setVerticalSpacing(18)
        self.sol_priv = QLineEdit(); self.sol_priv.setFont(font); self.sol_priv.setMinimumHeight(32)
        self.sol_to = QLineEdit(); self.sol_to.setFont(font); self.sol_to.setMinimumHeight(32)
        self.sol_coin = QComboBox(); self.sol_coin.setFont(font); self.sol_coin.setMinimumHeight(32)
        self.sol_amount = QLineEdit(); self.sol_amount.setFont(font); self.sol_amount.setMinimumHeight(32)
        sol_form.addRow("私钥:", self.sol_priv)
        sol_form.addRow("收款地址:", self.sol_to)
        sol_form.addRow("币种:", self.sol_coin)
        sol_form.addRow("金额:", self.sol_amount)
        self.sol_transfer_btn = QPushButton("转账")
        self.sol_transfer_btn.setFixedSize(300, 75)
        btn_layout2 = QHBoxLayout()
        btn_layout2.addStretch(1)
        btn_layout2.addWidget(self.sol_transfer_btn)
        self.sol_result = CodeBlockTextEdit()
        sol_layout.addLayout(sol_form)
        sol_layout.addLayout(btn_layout2)
        sol_layout.addWidget(self.sol_result)
        sol_widget.setLayout(sol_layout)
        self.init_sol_coin_combo()  # 保证控件初始化后再调用
        self.stack.addWidget(evm_widget)
        self.stack.addWidget(sol_widget)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)
        self.evm_transfer_btn.clicked.connect(self.evm_transfer)
        self.sol_transfer_btn.clicked.connect(self.sol_transfer)
        self.evm_chain.currentTextChanged.connect(self.on_evm_chain_changed)
    
    def refresh_configs(self):
        """刷新配置文件"""
        self.chain_data = self.load_chain_config()
        self.contract_data = self.load_contract_config()
        # 不自动调用init_sol_coin_combo，由外部需要时调用
    
    def evm_transfer(self):
        """EVM转账"""
        try:
            private_key = self.evm_priv.text().strip()
            to_address = self.evm_to.text().strip()
            chain_name = self.evm_chain.currentText()
            coin_name = self.evm_coin.currentText()
            amount = self.evm_amount.text().strip()
            if not all([private_key, to_address, chain_name, coin_name, amount]):
                QMessageBox.warning(self, "错误", "请填写所有必填字段")
                return
            if chain_name in ["请选择链名", ""]:
                QMessageBox.warning(self, "错误", "请选择链名")
                return
            if coin_name in ["请选择币种", "请先选择链名", ""]:
                QMessageBox.warning(self, "错误", "请选择币种")
                return
            if not to_address.startswith("0x") or len(to_address) != 42:
                QMessageBox.warning(self, "错误", "收款地址格式不正确")
                return
            # 新增：弹窗确认
            confirm = QMessageBox.question(self, "转账确认", f"是否确认在【{chain_name}】链向【{to_address}】转账【{amount}】{coin_name}？", QMessageBox.Yes | QMessageBox.No)
            if confirm != QMessageBox.Yes:
                self.log_widget.append_log("[EVM转账] 用户取消了本次转账操作")
                return
            self.refresh_configs()
            self.log_widget.append_log(f"[EVM转账] 开始，收款地址: {to_address}，链: {chain_name}，币种: {coin_name}，金额: {amount}")
            self.evm_transfer_btn.setEnabled(False)
            self.evm_transfer_btn.setText("转账中...")
            self.evm_transfer_worker = WorkerThread("evm_transfer", private_key, to_address, chain_name, coin_name, amount)
            self.evm_transfer_worker.result_ready.connect(self.on_evm_transfer_result)
            self.evm_transfer_worker.log_ready.connect(self.log_widget.append_log)
            self.evm_transfer_worker.finished.connect(self.on_evm_transfer_finished)
            self.evm_transfer_worker.start()
        except Exception as e:
            self.log_widget.append_log(f"EVM转账失败: {e}")
            self.evm_transfer_btn.setEnabled(True)
            self.evm_transfer_btn.setText("转账")
    
    def on_evm_transfer_result(self, result_type, result):
        self.evm_result.setPlainText(result)
        # --- 新增：转账后日志 ---
        self.log_widget.append_log(f"[EVM转账] 结果: {result}")
    
    def on_evm_transfer_finished(self):
        """EVM转账完成"""
        self.evm_transfer_btn.setEnabled(True)
        self.evm_transfer_btn.setText("转账")
    
    def sol_transfer(self):
        """Solana转账"""
        try:
            private_key = self.sol_priv.text().strip()
            to_address = self.sol_to.text().strip()
            coin_name = self.sol_coin.currentText()
            amount = self.sol_amount.text().strip()
            if not all([private_key, to_address, coin_name, amount]):
                QMessageBox.warning(self, "错误", "请填写所有必填字段")
                return
            if coin_name in ["请选择币种", ""]:
                QMessageBox.warning(self, "错误", "请选择币种")
                return
            # 新增：弹窗确认
            confirm = QMessageBox.question(self, "转账确认", f"是否确认在【Solana Mainnet】链向【{to_address}】转账【{amount}】{coin_name}？", QMessageBox.Yes | QMessageBox.No)
            if confirm != QMessageBox.Yes:
                self.log_widget.append_log("[Solana转账] 用户取消了本次转账操作")
                return
            self.refresh_configs()
            self.log_widget.append_log(f"[Solana转账] 开始，收款地址: {to_address}，链: Solana Mainnet，币种: {coin_name}，金额: {amount}")
            self.sol_transfer_btn.setEnabled(False)
            self.sol_transfer_btn.setText("转账中...")
            self.sol_transfer_worker = WorkerThread("sol_transfer", private_key, to_address, coin_name, amount)
            self.sol_transfer_worker.result_ready.connect(self.on_sol_transfer_result)
            self.sol_transfer_worker.log_ready.connect(self.log_widget.append_log)
            self.sol_transfer_worker.finished.connect(self.on_sol_transfer_finished)
            self.sol_transfer_worker.start()
        except Exception as e:
            self.log_widget.append_log(f"Solana转账失败: {e}")
            self.sol_transfer_btn.setEnabled(True)
            self.sol_transfer_btn.setText("转账")
    
    def on_sol_transfer_result(self, result_type, result):
        """Solana转账结果处理"""
        self.sol_result.setPlainText(result)
    
    def on_sol_transfer_finished(self):
        """Solana转账完成"""
        self.sol_transfer_btn.setEnabled(True)
        self.sol_transfer_btn.setText("转账")
    
    def load_chain_config(self):
        """加载链配置文件"""
        try:
            with open(resource_path("config/chain.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载chain.json失败: {e}")
            return {"evm_chains": [], "solana_chains": [], "testnet_chains": []}
    
    def load_contract_config(self):
        """加载合约配置文件"""
        try:
            with open(resource_path("config/contract.json"), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载contract.json失败: {e}")
            return {"tokens": []}
    
    def init_evm_chain_combo(self):
        """初始化EVM链名下拉框"""
        self.evm_chain.clear()
        self.evm_chain.addItem("请选择链名")
        
        # 添加主网链
        for chain in self.chain_data.get("evm_chains", []):
            self.evm_chain.addItem(chain["chainName"])
        
        # 添加测试网链
        for chain in self.chain_data.get("testnet_chains", []):
            self.evm_chain.addItem(chain["chainName"])
    
    def on_evm_chain_changed(self, chain_name):
        """当EVM链名选择改变时更新币种列表"""
        if chain_name == "请选择链名":
            self.evm_coin.clear()
            self.evm_coin.addItem("请先选择链名")
            return
        
        self.evm_coin.clear()
        self.evm_coin.addItem("请选择币种")
        
        # 从合约配置中筛选对应链的币种
        for token in self.contract_data.get("tokens", []):
            if token["chainName"] == chain_name:
                self.evm_coin.addItem(token["coinName"])
    
    def init_sol_coin_combo(self):
        """初始化Solana币种下拉框"""
        self.sol_coin.clear()
        self.sol_coin.addItem("请选择币种")
        for token in self.contract_data.get("tokens", []):
            if token["chainName"] == "Solana Mainnet":
                self.sol_coin.addItem(token["coinName"])
    
    def _show_result(self, result_widget, log_widget, msg):
        result_widget.setPlainText(msg)
        log_widget.append_log(msg)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MyWalletTool 钱包工具")
        self.resize(1200, 800)
        
        main_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont('微软雅黑', 15, QFont.Bold))
        self.tabs.setStyleSheet('''
            QTabBar::tab {
                min-width: 200px;
                min-height: 60px;
                font-size: 18px;
                padding: 16px 32px;
                border: 2.5px solid #bbb;
                border-left: 2.5px solid #bbb;
                border-right: 2.5px solid #bbb;
                border-top: 2.5px solid #bbb;
                /* 不设置border-bottom */
                border-radius: 12px 12px 0 0;
                margin-right: 8px;
                margin-bottom: 12px;
            }
            QTabBar::tab:selected {
                background: #e6f2ff;
                color: #005599;
                border: 3px solid #3399ff;
                border-left: 3px solid #3399ff;
                border-right: 3px solid #3399ff;
                border-top: 3px solid #3399ff;
                /* 不设置border-bottom */
                border-radius: 12px 12px 0 0;
                margin-bottom: 12px;
            }
            QTabWidget::pane {
                border-top: 3px solid #3399ff;
                top: -3px;
            }
        ''')
        
        self.log_widget = LogWidget()
        
        # 创建各个标签页
        self.home_tab = HomeTab()
        self.config_tab = ConfigTab()
        self.wallet_tab = WalletTab(self.log_widget)
        self.transfer_tab = TransferTab(self.log_widget)
        
        self.tabs.addTab(self.home_tab, "首页")
        self.tabs.addTab(self.config_tab, "配置")
        self.tabs.addTab(self.wallet_tab, "钱包操作")
        self.tabs.addTab(self.transfer_tab, "转账")
        
        # 监听标签页切换事件，用于刷新配置
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        main_layout.addWidget(self.tabs)
        
        # 增加物理间隔
        spacer = QWidget()
        spacer.setFixedHeight(12)
        main_layout.addWidget(spacer)
        
        log_label = QLabel("日志：")
        log_label.setFont(QFont('微软雅黑', 12, QFont.Bold))
        main_layout.addWidget(log_label)
        main_layout.addWidget(self.log_widget)
        
        self.setLayout(main_layout)
        
        # 记录启动时间
        self.log_widget.append_log("GUI启动成功")
    
    def on_tab_changed(self, index):
        """标签页切换事件"""
        if index == 3:  # 转账标签页
            # 刷新转账页面的配置
            self.transfer_tab.refresh_configs()
            self.transfer_tab.init_evm_chain_combo()
    
    def closeEvent(self, event):
        """关闭事件"""
        self.log_widget.append_log("GUI正在关闭...")
        self.log_widget.flush_log_buffer()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 