import sys
import os
import json
from datetime import datetime, date
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QComboBox, QTableWidget, 
    QTableWidgetItem, QTabWidget, QMessageBox, QDateEdit, QDialog,
    QFormLayout, QScrollArea, QFrame, QGridLayout
)
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QDate
import matplotlib.backends.backend_qt5agg as backends

class StyledButton(QPushButton):
    def __init__(self, text, icon=None):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3e8e41;
            }
        """)
        if icon:
            self.setIcon(QIcon(icon))

class FinanceManager:
    def __init__(self, data_file='financas.json'):
        self.data_file = data_file
        self.data = self._load_data()

    def _load_data(self):
        """Carrega dados do arquivo JSON com tratamento de erro."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    
                # Validate required keys
                if 'transacoes' not in data:
                    return self._inicializar_dados_padrao()
                
                # Optional: Migrate data if needed
                for transaction in data.get('transacoes', []):
                    if 'tipo' not in transaction:
                        transaction['tipo'] = 'despesa' if transaction['valor'] < 0 else 'receita'
                
                return data
            except (json.JSONDecodeError, KeyError):
                return self._inicializar_dados_padrao()
        return self._inicializar_dados_padrao()

    def _inicializar_dados_padrao(self):
        """Inicializa dados padrão se o arquivo estiver corrompido ou não existir."""
        return {
            'transacoes': [], 
            'categorias': {
                'Alimentação': 0, 
                'Transporte': 0, 
                'Moradia': 0, 
                'Entretenimento': 0, 
                'Educação': 0, 
                'Saúde': 0, 
                'Outros': 0
            },
            'metas': {}
        }

    def _save_data(self):
        """Salva dados no arquivo JSON."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=4)
        except IOError:
            print(f"Erro ao salvar dados em {self.data_file}")

    def adicionar_transacao(self, valor, categoria, descricao, data, tipo='despesa'):
        """Adiciona uma nova transação com validações."""
        # Validar valor
        try:
            valor = float(valor)
            if valor <= 0:
                raise ValueError("Valor deve ser um número positivo")
        except ValueError:
            raise ValueError("Valor inválido")
        
        # Validar categoria
        if categoria not in self.data['categorias']:
            raise ValueError(f"Categoria {categoria} não existe")
        
        # Validar descrição
        if not descricao:
            raise ValueError("Descrição não pode estar vazia")

        transacao = {
            'data': data.toString("yyyy-MM-dd"),
            'valor': float(valor) * (-1 if tipo == 'despesa' else 1),
            'categoria': categoria,
            'descricao': descricao,
            'tipo': tipo
        }
        
        self.data['transacoes'].append(transacao)
        
        # Atualiza totais por categoria
        if tipo == 'despesa':
            self.data['categorias'][categoria] += float(valor)
        
        self._save_data()
        return True

    def adicionar_meta(self, categoria, valor_meta):
        """Adiciona uma meta de gastos para uma categoria."""
        try:
            valor_meta = float(valor_meta)
            if valor_meta <= 0:
                raise ValueError("Valor da meta deve ser positivo")
            
            self.data['metas'][categoria] = valor_meta
            self._save_data()
            return True
        except ValueError:
            return False

    def obter_transacoes(self, mes=None):
        """Obtém transações, opcionalmente filtradas por mês."""
        if mes:
            return [t for t in self.data['transacoes'] 
                    if datetime.strptime(t['data'], "%Y-%m-%d").strftime("%Y-%m") == mes]
        return self.data['transacoes']

    def gerar_relatorio_gastos(self, mes=None):
        try:
            df = pd.DataFrame(self.data['transacoes'])
            print("DataFrame completo:", df)  # Adicione esta linha
            
            if not df.empty:
                # Filtra apenas despesas
                df = df[df['tipo'] == 'despesa']
                print("DataFrame de despesas:", df)  # E esta linha
                
                if mes:
                    df['data'] = pd.to_datetime(df['data'])
                    df = df[df['data'].dt.strftime("%Y-%m") == mes]
                
                return df.groupby('categoria')['valor'].sum()
            return pd.Series()
        except Exception as e:
            print(f"Erro ao gerar relatório de gastos: {e}")
            return pd.Series()

    def verificar_metas(self):
        """Verifica o progresso das metas de gastos."""
        gastos = self.gerar_relatorio_gastos()
        metas = self.data['metas']
        
        resultado_metas = {}
        for categoria, meta in metas.items():
            gasto_atual = gastos.get(categoria, 0)
            percentual = (gasto_atual / meta) * 100 if meta > 0 else 0
            resultado_metas[categoria] = {
                'meta': meta,
                'gasto_atual': gasto_atual,
                'percentual': percentual
            }
        
        return resultado_metas

class AddTransactionDialog(QDialog):
    def __init__(self, finance_manager, parent=None):
        super().__init__(parent)
        self.finance_manager = finance_manager
        self.setWindowTitle("Adicionar Transação")
        self.setGeometry(300, 300, 450, 350)
        self.setStyleSheet("""
            QDialog {
                background-color: #f4f4f4;
            }
            QLabel {
                color: #333;
            }
            QLineEdit, QComboBox {
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)

        layout = QFormLayout()

        # Tipo de Transação
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(['Despesa', 'Receita'])
        layout.addRow("Tipo:", self.tipo_combo)

        # Valor
        self.valor_input = QLineEdit()
        self.valor_input.setPlaceholderText("Digite o valor")
        layout.addRow("Valor:", self.valor_input)

        # Categoria
        self.categoria_combo = QComboBox()
        self.categoria_combo.addItems(list(self.finance_manager.data['categorias'].keys()))
        layout.addRow("Categoria:", self.categoria_combo)

        # Descrição
        self.descricao_input = QLineEdit()
        self.descricao_input.setPlaceholderText("Descrição da transação")
        layout.addRow("Descrição:", self.descricao_input)

        # Data
        self.data_input = QDateEdit()
        self.data_input.setDate(QDate.currentDate())
        self.data_input.setCalendarPopup(True)
        layout.addRow("Data:", self.data_input)

        # Botão Adicionar
        self.adicionar_btn = StyledButton("Adicionar Transação")
        self.adicionar_btn.clicked.connect(self.adicionar_transacao)
        layout.addRow(self.adicionar_btn)

        self.setLayout(layout)

    def adicionar_transacao(self):
        try:
            valor = self.valor_input.text()
            categoria = self.categoria_combo.currentText()
            descricao = self.descricao_input.text()
            data = self.data_input.date()
            tipo = 'despesa' if self.tipo_combo.currentText() == 'Despesa' else 'receita'

            if self.finance_manager.adicionar_transacao(valor, categoria, descricao, data, tipo):
                QMessageBox.information(self, "Sucesso", "Transação adicionada com sucesso!")
                self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Erro", str(e))

class AddMetaDialog(QDialog):
    def __init__(self, finance_manager, parent=None):
        super().__init__(parent)
        self.finance_manager = finance_manager
        self.setWindowTitle("Adicionar Meta de Gastos")
        self.setGeometry(300, 300, 400, 250)

        layout = QFormLayout()

        # Categoria
        self.categoria_combo = QComboBox()
        self.categoria_combo.addItems(list(self.finance_manager.data['categorias'].keys()))
        layout.addRow("Categoria:", self.categoria_combo)

        # Valor da Meta
        self.valor_meta_input = QLineEdit()
        self.valor_meta_input.setPlaceholderText("Digite o valor da meta")
        layout.addRow("Valor da Meta:", self.valor_meta_input)

        # Botão Adicionar
        self.adicionar_btn = StyledButton("Adicionar Meta")
        self.adicionar_btn.clicked.connect(self.adicionar_meta)
        layout.addRow(self.adicionar_btn)

        self.setLayout(layout)

    def adicionar_meta(self):
        categoria = self.categoria_combo.currentText()
        valor_meta = self.valor_meta_input.text()

        if self.finance_manager.adicionar_meta(categoria, valor_meta):
            QMessageBox.information(self, "Sucesso", "Meta adicionada com sucesso!")
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", "Não foi possível adicionar a meta. Verifique o valor.")

class FinanceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.finance_manager = FinanceManager()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Gestor Financeiro')
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                background: white;
            }
            QTabBar::tab {
                background: #e0e0e0;
                padding: 8px 16px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: white;
            }
        """)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Abas
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Aba de Transações
        transacoes_tab = QWidget()
        transacoes_layout = QVBoxLayout()
        transacoes_tab.setLayout(transacoes_layout)

        # Tabela de Transações
        self.transacoes_table = QTableWidget()
        self.transacoes_table.setColumnCount(5)
        self.transacoes_table.setHorizontalHeaderLabels(['Data', 'Valor', 'Categoria', 'Descrição', 'Tipo'])
        self.transacoes_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f2f2f2;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 5px;
                border: 1px solid #ddd;
            }
        """)
        self.transacoes_table.setAlternatingRowColors(True)
        transacoes_layout.addWidget(self.transacoes_table)

        # Layout de botões
        botoes_layout = QHBoxLayout()
        
        # Botão Adicionar Transação
        adicionar_btn = StyledButton("Adicionar Transação")
        adicionar_btn.clicked.connect(self.abrir_adicionar_transacao)
        botoes_layout.addWidget(adicionar_btn)

        # Botão Adicionar Meta
        adicionar_meta_btn = StyledButton("Adicionar Meta")
        adicionar_meta_btn.clicked.connect(self.abrir_adicionar_meta)
        botoes_layout.addWidget(adicionar_meta_btn)

        transacoes_layout.addLayout(botoes_layout)

        # Aba de Relatórios
        relatorios_tab = QWidget()
        relatorios_layout = QVBoxLayout()
        relatorios_tab.setLayout(relatorios_layout)

        # Área para gráficos
        self.grafico_widget = QWidget()
        self.grafico_widget.setLayout(QVBoxLayout())
        relatorios_layout.addWidget(self.grafico_widget)

        # Layout para botões de relatório
        relatorio_botoes_layout = QHBoxLayout()

        # Botão Gerar Relatório de Gastos
        gerar_relatorio_btn = StyledButton("Relatório de Gastos")
        gerar_relatorio_btn.clicked.connect(self.gerar_relatorio_gastos)
        relatorio_botoes_layout.addWidget(gerar_relatorio_btn)

        # Botão Verificar Metas
        verificar_metas_btn = StyledButton("Verificar Metas")
        verificar_metas_btn.clicked.connect(self.mostrar_metas)
        relatorio_botoes_layout.addWidget(verificar_metas_btn)

        relatorios_layout.addLayout(relatorio_botoes_layout)

        # Área de Metas
        self.metas_widget = QWidget()
        self.metas_widget.setLayout(QVBoxLayout())
        relatorios_layout.addWidget(self.metas_widget)

        # Adicionar abas
        tab_widget.addTab(transacoes_tab, "Transações")
        tab_widget.addTab(relatorios_tab, "Relatórios")

        # Atualizar visualizações
        self.atualizar_transacoes()

    def abrir_adicionar_transacao(self):
        dialog = AddTransactionDialog(self.finance_manager, self)
        if dialog.exec_():
            self.atualizar_transacoes()

    def abrir_adicionar_meta(self):
            dialog = AddMetaDialog(self.finance_manager, self)
            if dialog.exec_():
                QMessageBox.information(self, "Sucesso", "Meta adicionada com sucesso!")

    def atualizar_transacoes(self):
        # Limpar tabela
        self.transacoes_table.setRowCount(0)

        # Obter transações
        transacoes = self.finance_manager.obter_transacoes()

        # Popular tabela
        self.transacoes_table.setRowCount(len(transacoes))
        for linha, transacao in enumerate(transacoes):
            self.transacoes_table.setItem(linha, 0, QTableWidgetItem(transacao['data']))
            
            # Formatar valor com cor
            valor_item = QTableWidgetItem(f"R$ {abs(transacao['valor']):.2f}")
            cor = QColor(255, 0, 0) if transacao['tipo'] == 'despesa' else QColor(0, 128, 0)
            valor_item.setForeground(cor)
            self.transacoes_table.setItem(linha, 1, valor_item)
            
            self.transacoes_table.setItem(linha, 2, QTableWidgetItem(transacao['categoria']))
            self.transacoes_table.setItem(linha, 3, QTableWidgetItem(transacao['descricao']))
            self.transacoes_table.setItem(linha, 4, QTableWidgetItem(transacao['tipo'].capitalize()))

    def migrate_transaction_data(self):
        """Ensure all transactions have a 'tipo' field."""
        for transaction in self.data['transacoes']:
            if 'tipo' not in transaction:
                # Default to 'despesa' if not specified
                transaction['tipo'] = 'despesa' if transaction['valor'] < 0 else 'receita'
        self._save_data()

    # Call this in _load_data method before returning
        self.migrate_transaction_data()

    def gerar_relatorio_gastos(self):
        try:
            # Limpar layout anterior
            layout = self.grafico_widget.layout()
            for i in reversed(range(layout.count())): 
                widget = layout.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            # Gerar relatório de gastos
            relatorio = self.finance_manager.gerar_relatorio_gastos()

            if not relatorio.empty:
                plt.close('all')  # Fechar figuras anteriores
                plt.style.use('seaborn')
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                
                # Gráfico de Pizza
                relatorio.plot(kind='pie', autopct='%1.1f%%', ax=ax1, 
                               colors=plt.cm.Pastel1.colors)
                ax1.set_title('Distribuição de Gastos por Categoria')
                ax1.set_ylabel('')

                # Gráfico de Barras
                relatorio.plot(kind='bar', ax=ax2)
                ax2.set_title('Gastos por Categoria')
                ax2.set_xlabel('Categorias')
                ax2.set_ylabel('Valor (R$)')
                plt.tight_layout()

                # Incorporar gráfico no PyQt
                canvas = backends.FigureCanvasQTAgg(fig)
                layout.addWidget(canvas)

                # Adicionar legenda com valores
                legenda = QLabel("\n".join([f"{cat}: R$ {valor:.2f}" for cat, valor in relatorio.items()]))
                layout.addWidget(legenda)
            else:
                QMessageBox.warning(self, "Aviso", "Não há dados para gerar relatório.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {str(e)}")

    def mostrar_metas(self):
        # Limpar layout anterior
        layout = self.metas_widget.layout()
        for i in reversed(range(layout.count())): 
            widget = layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Verificar metas
        resultado_metas = self.finance_manager.verificar_metas()

        if resultado_metas:
            # Criar layout de grade para metas
            grid = QGridLayout()
            
            # Cabeçalhos
            headers = ["Categoria", "Meta", "Gasto Atual", "Progresso"]
            for col, header in enumerate(headers):
                label = QLabel(f"<b>{header}</b>")
                label.setStyleSheet("color: #333; font-size: 14px;")
                grid.addWidget(label, 0, col)

            # Adicionar metas
            for linha, (categoria, meta_info) in enumerate(resultado_metas.items(), 1):
                # Categoria
                grid.addWidget(QLabel(categoria), linha, 0)
                
                # Meta
                grid.addWidget(QLabel(f"R$ {meta_info['meta']:.2f}"), linha, 1)
                
                # Gasto Atual
                gasto_label = QLabel(f"R$ {meta_info['gasto_atual']:.2f}")
                cor = QColor(255, 0, 0) if meta_info['gasto_atual'] > meta_info['meta'] else QColor(0, 128, 0)
                gasto_label.setStyleSheet(f"color: {cor.name()};")
                grid.addWidget(gasto_label, linha, 2)
                
                # Progresso
                progresso_label = QLabel(f"{meta_info['percentual']:.1f}%")
                progresso_label.setStyleSheet(f"color: {cor.name()};")
                grid.addWidget(progresso_label, linha, 3)

            # Criar widget de rolagem para metas
            scroll = QScrollArea()
            scroll_content = QWidget()
            scroll_content.setLayout(grid)
            scroll.setWidget(scroll_content)
            scroll.setWidgetResizable(True)

            # Adicionar ao layout de metas
            layout.addWidget(QLabel("<h2>Resumo de Metas de Gastos</h2>"))
            layout.addWidget(scroll)
        else:
            layout.addWidget(QLabel("Nenhuma meta definida."))

def main():
    try:
        app = QApplication(sys.argv)
        
        # Configurar fonte padrão do aplicativo
        font = QFont("Segoe UI", 10)
        app.setFont(font)
        
        finance_app = FinanceApp()
        finance_app.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()