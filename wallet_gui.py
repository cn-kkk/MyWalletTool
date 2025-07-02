import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit, QPushButton, QLabel, QPlainTextEdit, QFormLayout, QLineEdit, QStackedWidget, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QColor, QPalette, QBrush

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
        self.setFixedHeight(150)
    def append_log(self, msg):
        self.append(msg)
        sb = self.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())

class StyledSidebar(QListWidget):
    def __init__(self, items, width=360):
        super().__init__()
        self.setFixedWidth(width)
        self.setSpacing(16)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet('''
            QListView, QListWidget {
                outline: none;
                box-shadow: none;
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
                box-shadow: none;
            }
            QListWidget::item:selected {
                background: #d0eaff;
                border: 1.5px solid #3399ff;
                color: #005599;
                outline: none;
                box-shadow: none;
            }
            QListWidget::item:focus {
                outline: none;
                box-shadow: none;
            }
            QListWidget::item:active {
                outline: none;
                box-shadow: none;
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
            with open("README.md", "r", encoding="utf-8") as f:
                self.readme_view.setText(f.read())
        except Exception:
            self.readme_view.setText("README.md 加载失败")
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
        self.chain_edit.setPlainText("这里显示 chain.json 内容")
        self.chain_save_btn = QPushButton("保存链设置")
        self.chain_save_btn.setFixedWidth(120)
        chain_widget = QWidget()
        chain_layout = QVBoxLayout()
        chain_layout.addWidget(self.chain_edit)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.chain_save_btn)
        chain_layout.addLayout(btn_layout)
        chain_widget.setLayout(chain_layout)
        # 代币合约设置
        self.token_edit = QPlainTextEdit()
        self.token_edit.setFont(QFont('Consolas', 13))
        self.token_edit.setPlainText("这里显示 contract.json 内容")
        self.token_save_btn = QPushButton("保存代币合约设置")
        self.token_save_btn.setFixedWidth(140)
        token_widget = QWidget()
        token_layout = QVBoxLayout()
        token_layout.addWidget(self.token_edit)
        btn_layout2 = QHBoxLayout()
        btn_layout2.addStretch(1)
        btn_layout2.addWidget(self.token_save_btn)
        token_layout.addLayout(btn_layout2)
        token_widget.setLayout(token_layout)
        self.stack.addWidget(chain_widget)
        self.stack.addWidget(token_widget)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)

class WalletTab(QWidget):
    def __init__(self, log_widget):
        super().__init__()
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
        self.evm_btn.clicked.connect(lambda: self._show_result(self.evm_result, log_widget, "EVM地址: 0x123...abc"))
        self.sol_btn.clicked.connect(lambda: self._show_result(self.sol_result, log_widget, "Sol地址: 4f3...xyz"))
        self.wallet_btn.clicked.connect(lambda: self._show_result(self.wallet_result, log_widget, "EVM钱包已生成\n助记词: ..."))
    def _show_result(self, result_widget, log_widget, msg):
        result_widget.setPlainText(msg)
        log_widget.append_log(msg)

class TransferTab(QWidget):
    def __init__(self, log_widget):
        super().__init__()
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
        self.evm_chain = QLineEdit(); self.evm_chain.setFont(font); self.evm_chain.setMinimumHeight(32)
        self.evm_coin = QLineEdit(); self.evm_coin.setFont(font); self.evm_coin.setMinimumHeight(32)
        self.evm_amount = QLineEdit(); self.evm_amount.setFont(font); self.evm_amount.setMinimumHeight(32)
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
        self.sol_coin = QLineEdit(); self.sol_coin.setFont(font); self.sol_coin.setMinimumHeight(32)
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
        self.stack.addWidget(evm_widget)
        self.stack.addWidget(sol_widget)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)
        self.evm_transfer_btn.clicked.connect(lambda: self._show_result(self.evm_result, log_widget, "EVM转账成功，tx_hash: 0xabc..."))
        self.sol_transfer_btn.clicked.connect(lambda: self._show_result(self.sol_result, log_widget, "Sol转账成功，tx_hash: 4f3..."))
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
        self.tabs.addTab(HomeTab(), "首页")
        self.tabs.addTab(ConfigTab(), "配置")
        self.tabs.addTab(WalletTab(self.log_widget), "钱包操作")
        self.tabs.addTab(TransferTab(self.log_widget), "转账")
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 