import tkinter as tk
from tkinter import messagebox, ttk
from collections import deque
import json
import os
from datetime import datetime

# Tenta importar o tema Sun Valley (opcional)
try:
    import sv_ttk
except Exception as e:
    sv_ttk = None


# | BACKEND |

class Processo:
    def __init__(self, pid, prioridade, tempo_execucao, nome="Processo Genérico"):
        self.pid = pid
        self.prioridade = prioridade
        self.tempo_execucao = tempo_execucao
        self.nome = nome
        self.estado = "Pronto"

    def __repr__(self):
        return f"PID={self.pid} ({self.nome})"

# | CORES DA INTERFACE|
COR_FUNDO = "#f5f7fa"
CARTAO = "#ffffff"
ACENTO = "#212cca"      # azul suave para destaques
VERDE = "#05C71F"       # executado
AMARELO = "#f10f0f"     # interrompido (kill)
AZUL = "#257bfd"        # executando
TEXTO_ESCURO = "#141516"
SOMBRA = "#e6eef8"
CINZA_CLARO = "#dfe7ef"

# CORES DA ÁRVORE RUBRO-NEGRA
VERMELHO = "#e74c3c"
PRETO = "#000000"

class No:
    def __init__(self, processo=None, cor=VERMELHO, nil=None):
        self.proc = processo
        self.cor = cor
        self.esq = nil
        self.dir = nil
        self.pai = nil

class ArvoreRubroNegra:
    def __init__(self):
        self.NIL = No(None, PRETO)
        self.NIL.esq = self.NIL
        self.NIL.dir = self.NIL
        self.NIL.pai = self.NIL
        self.raiz = self.NIL

    def buscar_por_pid(self, no, pid):
        if no == self.NIL: return None
        if no.proc.pid == pid: return no
        res = self.buscar_por_pid(no.esq, pid)
        if res: return res
        return self.buscar_por_pid(no.dir, pid)

    def minimo(self, no):
        while no.esq != self.NIL:
            no = no.esq
        return no

    def comparar(self, p1, p2):
        # Lógica de prioridade: Menor número = Maior prioridade
        if p1.prioridade < p2.prioridade: return -1
        if p1.prioridade > p2.prioridade: return 1
        # Desempate por PID
        if p1.pid < p2.pid: return -1
        if p1.pid > p2.pid: return 1
        return 0

    def rotacao_esq(self, x):
        y = x.dir
        x.dir = y.esq
        if y.esq != self.NIL:
            y.esq.pai = x
        y.pai = x.pai
        if x.pai == self.NIL:
            self.raiz = y
        elif x == x.pai.esq:
            x.pai.esq = y
        else:
            x.pai.dir = y
        y.esq = x
        x.pai = y

    def rotacao_dir(self, y):
        x = y.esq
        y.esq = x.dir
        if x.dir != self.NIL:
            x.dir.pai = y
        x.pai = y.pai
        if y.pai == self.NIL:
            self.raiz = x
        elif y == y.pai.dir:
            y.pai.dir = x
        else:
            y.pai.esq = x
        x.dir = y
        y.pai = x

    def inserir(self, processo):
        z = No(processo, VERMELHO, self.NIL)
        y = self.NIL
        x = self.raiz
        while x != self.NIL:
            y = x
            if self.comparar(z.proc, x.proc) < 0:
                x = x.esq
            else:
                x = x.dir
        z.pai = y
        if y == self.NIL:
            self.raiz = z
        elif self.comparar(z.proc, y.proc) < 0:
            y.esq = z
        else:
            y.dir = z
        z.esq = self.NIL
        z.dir = self.NIL
        z.cor = VERMELHO
        self._inserir_fixup(z)

    def _inserir_fixup(self, z):
        while z.pai.cor == VERMELHO:
            if z.pai == z.pai.pai.esq:
                y = z.pai.pai.dir
                if y.cor == VERMELHO:
                    z.pai.cor = PRETO
                    y.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    z = z.pai.pai
                else:
                    if z == z.pai.dir:
                        z = z.pai
                        self.rotacao_esq(z)
                    z.pai.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    self.rotacao_dir(z.pai.pai)
            else:
                y = z.pai.pai.esq
                if y.cor == VERMELHO:
                    z.pai.cor = PRETO
                    y.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    z = z.pai.pai
                else:
                    if z == z.pai.esq:
                        z = z.pai
                        self.rotacao_dir(z)
                    z.pai.cor = PRETO
                    z.pai.pai.cor = VERMELHO
                    self.rotacao_esq(z.pai.pai)
        self.raiz.cor = PRETO

    def transplant(self, u, v):
        if u.pai == self.NIL:
            self.raiz = v
        elif u == u.pai.esq:
            u.pai.esq = v
        else:
            u.pai.dir = v
        v.pai = u.pai

    def remover_no(self, z):
        if z == self.NIL: return None
        processo_removido = z.proc
        y = z
        y_cor_original = y.cor

        if z.esq == self.NIL:
            x = z.dir
            self.transplant(z, z.dir)
        elif z.dir == self.NIL:
            x = z.esq
            self.transplant(z, z.esq)
        else:
            y = self.minimo(z.dir)
            y_cor_original = y.cor
            x = y.dir
            if y.pai == z:
                x.pai = y
            else:
                self.transplant(y, y.dir)
                y.dir = z.dir
                y.dir.pai = y
            self.transplant(z, y)
            y.esq = z.esq
            y.esq.pai = y
            y.cor = z.cor

        if y_cor_original == PRETO:
            self._remover_fixup(x)
        return processo_removido

    def _remover_fixup(self, x):
        while x != self.raiz and x.cor == PRETO:
            if x == x.pai.esq:
                w = x.pai.dir
                if w.cor == VERMELHO:
                    w.cor = PRETO
                    x.pai.cor = VERMELHO
                    self.rotacao_esq(x.pai)
                    w = x.pai.dir
                if w.esq.cor == PRETO and w.dir.cor == PRETO:
                    w.cor = VERMELHO
                    x = x.pai
                else:
                    if w.dir.cor == PRETO:
                        w.esq.cor = PRETO
                        w.cor = VERMELHO
                        self.rotacao_dir(w)
                        w = x.pai.dir
                    w.cor = x.pai.cor
                    x.pai.cor = PRETO
                    w.dir.cor = PRETO
                    self.rotacao_esq(x.pai)
                    x = self.raiz
            else:
                w = x.pai.esq
                if w.cor == VERMELHO:
                    w.cor = PRETO
                    x.pai.cor = VERMELHO
                    self.rotacao_dir(x.pai)
                    w = x.pai.esq
                if w.dir.cor == PRETO and w.esq.cor == PRETO:
                    w.cor = VERMELHO
                    x = x.pai
                else:
                    if w.esq.cor == PRETO:
                        w.dir.cor = PRETO
                        w.cor = VERMELHO
                        self.rotacao_esq(w)
                        w = x.pai.esq
                    w.cor = x.pai.cor
                    x.pai.cor = PRETO
                    w.esq.cor = PRETO
                    self.rotacao_dir(x.pai)
                    x = self.raiz
        x.cor = PRETO

    def contar_nos(self, no):
        if no == self.NIL: return 0
        return 1 + self.contar_nos(no.esq) + self.contar_nos(no.dir)


# | FRONTEND (MODELAGEM INTERFACE)|

class EscalonadorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Escalonador Rubro-Negro - Melhorado")
        self.root.geometry("1400x850")
        self.root.configure(bg=COR_FUNDO)
        
        self.arvore = ArvoreRubroNegra()
        self.fila = deque()
        self.politica = 1  # 1=Prioridade, 2=FIFO
        self.processo_em_execucao = None
        self.simulacao_ativa = False
        self.eventos_log = []  # (nome, pid, estado, timestamp)

        self._config_style()
        self._criar_layout()
        
        self.gerar_dados_padrao_se_necessario()
        self.carregar_dados()

        self.root.bind("<Configure>", self._ao_redimensionar)

        self.atualizar_visualizacao()
        self.atualizar_tabela()
        self._atualizar_historico_visual()  # caso haja histórico

    def _config_style(self):
        style = ttk.Style()
        
        try:
            style.theme_use("clam")
        except:
            pass
        
        default_font = ("Segoe UI", 11)
        style.configure(".", font=default_font, background=COR_FUNDO, foreground=TEXTO_ESCURO)

        style.configure("Card.TFrame", background=CARTAO, relief="flat")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), background=CARTAO, foreground=TEXTO_ESCURO)
        style.configure("Section.TLabelframe", background=CARTAO, foreground=TEXTO_ESCURO, font=("Segoe UI", 12, "bold"))
        style.configure("Small.TLabel", font=("Segoe UI", 11), background=CARTAO, foreground="#444")
        
        style.configure("Accent.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.map("Accent.TButton",
                  background=[('active', ACENTO), ('!disabled', ACENTO)],
                  foreground=[('!disabled', 'white')])

        style.configure("Treeview", font=("Segoe UI", 11), background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 12, "bold"))

    def _criar_layout(self):
        
        left = ttk.Frame(self.root, style="Card.TFrame", padding=12)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=12, pady=12)

        ttk.Label(left, text="Painel de Controle", style="Title.TLabel").pack(anchor="w", pady=(0, 12))

        add_frame = ttk.Labelframe(left, text="Novo Processo", style="Section.TLabelframe", padding=8)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        self.entry_nome = self._campo(add_frame, "Nome:")
        self.entry_pid = self._campo(add_frame, "PID:")
        self.entry_prio = self._campo(add_frame, "Prioridade:")
        self.entry_tempo = self._campo(add_frame, "Tempo (s):")
        ttk.Button(add_frame, text="Adicionar", style="Accent.TButton", command=self.criar_processo).pack(fill=tk.X, pady=6)

        cpu_frame = ttk.Labelframe(left, text="CPU e Simulação", style="Section.TLabelframe", padding=8)
        cpu_frame.pack(fill=tk.X, pady=6)

        self.lbl_politica = ttk.Label(cpu_frame, text="Política: Prioridade (RB)", style="Small.TLabel")
        self.lbl_politica.pack(anchor="w", pady=(0,4))

        self.frame_cpu_display = tk.Frame(cpu_frame, bg="#111827", bd=0, relief="flat", padx=6, pady=6)
        self.frame_cpu_display.pack(fill=tk.X, pady=4)
        self.lbl_cpu_info = tk.Label(self.frame_cpu_display, text="OCIOSO", fg=VERDE, bg="#111827", font=("Consolas", 12, "bold"))
        self.lbl_cpu_info.pack(pady=4)

        row_btns = ttk.Frame(cpu_frame)
        row_btns.pack(fill=tk.X, pady=6)
        ttk.Button(row_btns, text="Trocar Política", style="Accent.TButton", command=self.trocar_politica).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        self.btn_sim = ttk.Button(row_btns, text="INICIAR", style="Accent.TButton", command=self.toggle_simulacao)
        self.btn_sim.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)

        kill_frame = ttk.Labelframe(left, text="Matar Processo", style="Section.TLabelframe", padding=8)
        kill_frame.pack(fill=tk.X, pady=8)
        self.entry_kill = self._campo(kill_frame, "PID:")
        ttk.Button(kill_frame, text="Kill", style="Accent.TButton", command=self.kill_processo).pack(fill=tk.X, pady=6)

        right = ttk.Frame(self.root, padding=8)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_arvore = ttk.Frame(self.notebook, padding=6)
        self.notebook.add(self.tab_arvore, text="  Visualização (Árvore)  ")
        
        self.canvas = tk.Canvas(self.tab_arvore, bg="#ffffff", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=(6, 10))

        hist_frame = ttk.Labelframe(self.tab_arvore, text="Histórico de Processos", style="Section.TLabelframe", padding=8)
        hist_frame.pack(fill=tk.X, padx=6, pady=(0,6))

        self.hist_tree = ttk.Treeview(hist_frame, columns=("nome", "pid", "estado"), show="headings", height=6)
        self.hist_tree.heading("nome", text="Nome do processo")
        self.hist_tree.heading("pid", text="PID")
        self.hist_tree.heading("estado", text="Estado")

        self.hist_tree.column("nome", anchor="w", width=400)
        self.hist_tree.column("pid", anchor="center", width=120)
        self.hist_tree.column("estado", anchor="center", width=200)

        self.hist_tree.tag_configure("executado", foreground=VERDE)
        self.hist_tree.tag_configure("interrompido", foreground=AMARELO)
        self.hist_tree.tag_configure("executando", foreground=AZUL)

        self.hist_tree.pack(fill=tk.X, expand=True)

        self.tab_lista = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_lista, text="  Lista de Processos  ")

        colunas = ("PID", "Nome", "Prioridade", "Tempo", "Status")
        self.tree_lista = ttk.Treeview(self.tab_lista, columns=colunas, show="headings", height=20)
        self.tree_lista.heading("PID", text="PID")
        self.tree_lista.heading("Nome", text="Nome")
        self.tree_lista.heading("Prioridade", text="Prioridade")
        self.tree_lista.heading("Tempo", text="Tempo Restante")
        self.tree_lista.heading("Status", text="Status")
        
        for col in colunas:
            self.tree_lista.column(col, anchor="center")

        self.tree_lista.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        footer = ttk.Frame(right)
        footer.pack(fill=tk.X, pady=5)
        self.lbl_status = ttk.Label(footer, text="Pronto.", font=("Segoe UI", 10))
        self.lbl_status.pack(side=tk.RIGHT)

    def _campo(self, parent, texto):
        f = ttk.Frame(parent)
        f.pack(fill=tk.X, pady=6)
        ttk.Label(f, text=texto, width=12).pack(side=tk.LEFT)
        e = ttk.Entry(f)
        e.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        return e
    
    def _ao_redimensionar(self, event):
        # Apenas redesenha se a aba ativa for a árvore e o evento for do canvas/root
        if self.notebook.index("current") == 0:
            self.atualizar_visualizacao()

    # | LÓGICA |

    def gerar_dados_padrao_se_necessario(self):
        if not os.path.exists("dados_escalonador.json"):
            dados_iniciais = [
                {"pid": 101, "prio": 5, "tempo": 10, "nome": "Video Render"},
                {"pid": 102, "prio": 2, "tempo": 5, "nome": "Servidor Web"},
                {"pid": 103, "prio": 8, "tempo": 15, "nome": "Calculo Vetorial"},
                {"pid": 104, "prio": 1, "tempo": 8, "nome": "Kernel Ops"},
                {"pid": 105, "prio": 5, "tempo": 12, "nome": "Banco Dados"},
                {"pid": 106, "prio": 3, "tempo": 6, "nome": "Spotify"},
                {"pid": 107, "prio": 7, "tempo": 9, "nome": "Backup"}
            ]
            with open("dados_escalonador.json", "w") as f:
                json.dump(dados_iniciais, f)

    def carregar_dados(self):
        if not os.path.exists("dados_escalonador.json"):
            return
        try:
            with open("dados_escalonador.json", "r") as f:
                dados = json.load(f)
            self.fila.clear()
            self.arvore = ArvoreRubroNegra()
            
            for item in dados:
                p = Processo(item["pid"], item["prio"], item["tempo"], item.get("nome", "Proc"))
                self.arvore.inserir(p)
                self.fila.append(p)
            self.atualizar_visualizacao()
            self.atualizar_tabela()
        except Exception as e:
            print(f"Erro ao carregar: {e}")

    def salvar_dados(self):
        lista = []
        for p in self.fila:
            lista.append({"pid": p.pid, "prio": p.prioridade, "tempo": p.tempo_execucao, "nome": p.nome})
        try:
            with open("dados_escalonador.json", "w") as f:
                json.dump(lista, f)
        except:
            pass

    def criar_processo(self):
        try:
            nome = self.entry_nome.get() or "Novo Proc"
            pid = int(self.entry_pid.get())
            prio = int(self.entry_prio.get())
            tempo = int(self.entry_tempo.get())
            
            if self.arvore.buscar_por_pid(self.arvore.raiz, pid):
                messagebox.showerror("Erro", "PID já existe!")
                return

            p = Processo(pid, prio, tempo, nome)
            self.arvore.inserir(p)
            self.fila.append(p)
            
            self.entry_pid.delete(0, tk.END)
            self.entry_tempo.delete(0, tk.END)
            self.entry_nome.delete(0, tk.END)
            self.entry_prio.delete(0, tk.END)
            
            self.atualizar_visualizacao()
            self.atualizar_tabela()
            self.salvar_dados()
        except ValueError:
            messagebox.showerror("Erro", "Preencha os campos numéricos corretamente.")

    def kill_processo(self):
        try:
            pid = int(self.entry_kill.get())
            # tenta encontrar processo tanto na árvore quanto na fila
            no = self.arvore.buscar_por_pid(self.arvore.raiz, pid)
            nome = None
            # pega nome antes de remover, se possível
            if no and no.proc:
                nome = no.proc.nome
            else:
                # busca na fila
                for p in list(self.fila):
                    if p.pid == pid:
                        nome = p.nome
                        break

            if no:
                self.arvore.remover_no(no)
                # Remove da fila linear também
                for p in list(self.fila):
                    if p.pid == pid:
                        self.fila.remove(p)
                        break
                
                if self.processo_em_execucao and self.processo_em_execucao.pid == pid:
                    # foi morto enquanto executava
                    self.processo_em_execucao = None
                    self.lbl_cpu_info.config(text="OCIOSO", fg=VERDE)
                
                # adicionar ao histórico como Interrompido (KILL)
                if nome is None:
                    nome = f"PID {pid}"
                self._adicionar_ao_historico(nome, pid, "Interrompido (KILL)", tag="interrompido")
                
                self.atualizar_visualizacao()
                self.atualizar_tabela()
                self.salvar_dados()
                messagebox.showinfo("Sucesso", f"Processo {pid} eliminado.")
            else:
                messagebox.showerror("Erro", "PID não encontrado.")
        except ValueError:
            pass

    def trocar_politica(self):
        self.politica = 2 if self.politica == 1 else 1
        txt = "Prioridade (RB)" if self.politica == 1 else "FIFO (Fila)"
        self.lbl_politica.config(text=f"Política: {txt}")

    def toggle_simulacao(self):
        self.simulacao_ativa = not self.simulacao_ativa
        if self.simulacao_ativa:
            self.btn_sim.config(text="PAUSAR")
            self.tick()
        else:
            self.btn_sim.config(text="CONTINUAR")

    def tick(self):
        if not self.simulacao_ativa: return

        if not self.processo_em_execucao:
            self._escalonar()

        if self.processo_em_execucao:
            # marca como em execução no histórico (se ainda não estiver)
            self._marcar_executando(self.processo_em_execucao)

            self.processo_em_execucao.tempo_execucao -= 1
            nome = self.processo_em_execucao.nome
            pid = self.processo_em_execucao.pid
            t = self.processo_em_execucao.tempo_execucao
            
            self.lbl_cpu_info.config(text=f"{pid}: {nome} ({t}s)", fg=AZUL)
            
            if t <= 0:
                self._finalizar_processo()
            
            self.atualizar_visualizacao() 
            self.atualizar_tabela()       

        self.root.after(1000, self.tick)

    def _escalonar(self):
        if self.politica == 1: # Prioridade (RB)
            if self.arvore.raiz != self.arvore.NIL:
                no = self.arvore.minimo(self.arvore.raiz)
                self.processo_em_execucao = no.proc
        else: # FIFO
            if self.fila:
                self.processo_em_execucao = self.fila[0]

        if self.processo_em_execucao:
            self._marcar_executando(self.processo_em_execucao)

    def _finalizar_processo(self):
        if not self.processo_em_execucao: return
        
        pid = self.processo_em_execucao.pid
        nome = self.processo_em_execucao.nome

        # Remove da árvore
        no = self.arvore.buscar_por_pid(self.arvore.raiz, pid)
        if no:
            self.arvore.remover_no(no)
        # Remove da fila
        if self.processo_em_execucao in self.fila:
            self.fila.remove(self.processo_em_execucao)
            
        # Registra no histórico como executado
        self._adicionar_ao_historico(nome, pid, "Executado", tag="executado")

        self.processo_em_execucao = None
        self.lbl_cpu_info.config(text="OCIOSO", fg=VERDE)
        self.salvar_dados()

    # | HISTÓRICO | 
    
    def _adicionar_ao_historico(self, nome, pid, estado_texto, tag=None):
        
        # procura entrada existente por PID
        existing = None
        for iid in self.hist_tree.get_children():
            vals = self.hist_tree.item(iid, "values")
            if vals and str(vals[1]) == str(pid):
                existing = iid
                break

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        display_estado = estado_texto  

        if existing:
            # atualiza
            self.hist_tree.item(existing, values=(nome, pid, display_estado), tags=(tag,))
        else:
            self.hist_tree.insert("", "end", values=(nome, pid, display_estado), tags=(tag,))

        self.eventos_log.append((nome, pid, estado_texto, timestamp))
        
        children = self.hist_tree.get_children()
        if children:
            self.hist_tree.see(children[-1])

    def _marcar_executando(self, processo):
        
        if not processo: return
        self._adicionar_ao_historico(processo.nome, processo.pid, "Em execução", tag="executando")
        
        self.atualizar_tabela()
        self._atualizar_historico_visual()

    def _atualizar_historico_visual(self):
        
        for iid in self.hist_tree.get_children():
            tags = self.hist_tree.item(iid, "tags")
            if "executado" in tags:
                self.hist_tree.item(iid, tags=("executado",))
            elif "interrompido" in tags:
                self.hist_tree.item(iid, tags=("interrompido",))
            elif "executando" in tags:
                self.hist_tree.item(iid, tags=("executando",))

    # | VISUALIZAÇÃO |

    def atualizar_tabela(self):
        
        for i in self.tree_lista.get_children():
            self.tree_lista.delete(i)
        
        
        for p in self.fila:
            status = "Executando" if (self.processo_em_execucao and p.pid == self.processo_em_execucao.pid) else "Pronto"
            if self.processo_em_execucao and p.pid == self.processo_em_execucao.pid:
                status = "Em execução"
            self.tree_lista.insert("", "end", values=(p.pid, p.nome, p.prioridade, p.tempo_execucao, status))

    def atualizar_visualizacao(self):
        
        self.canvas.delete("all")
        if self.arvore.raiz != self.arvore.NIL:
            w = max(200, self.canvas.winfo_width())
            self._desenhar_no(self.arvore.raiz, w // 2, 50, w // 4)
        else:
            # mensagem quando vazia
            self.canvas.create_text(self.canvas.winfo_width()//2, 80, text="Árvore vazia", fill="#666", font=("Segoe UI", 12))

    def _desenhar_no(self, no, x, y, offset):
        if no == self.arvore.NIL: return

        # Linhas
        if no.esq != self.arvore.NIL:
            self.canvas.create_line(x, y+20, x-offset, y+80, fill="#c5cdd9", width=2)
            self._desenhar_no(no.esq, x-offset, y+80, offset/2)
        if no.dir != self.arvore.NIL:
            self.canvas.create_line(x, y+20, x+offset, y+80, fill="#c5cdd9", width=2)
            self._desenhar_no(no.dir, x+offset, y+80, offset/2)

        cor = no.cor
        is_running = (self.processo_em_execucao and self.processo_em_execucao.pid == no.proc.pid)
        outline = "#257bfd" if is_running else "#5b6b7a"
        width = 3 if is_running else 1
        r = 28
        
        self.canvas.create_oval(x-r+3, y-r+3, x+r+3, y+r+3, fill="#eef3fb", outline="", width=0)
        self.canvas.create_oval(x-r, y-r, x+r, y+r, fill=cor, outline=outline, width=width)
        
        self.canvas.create_text(x, y, text=str(no.proc.pid), fill="white", font=("Segoe UI", 11, "bold"))
        
        lbl_nome = f"{no.proc.nome}\n({no.proc.tempo_execucao}s)"
        self.canvas.create_text(x, y+r+18, text=lbl_nome, fill="#234", font=("Segoe UI", 10), justify="center")

if __name__ == "__main__":
    if sv_ttk:
        try:
            sv_ttk.set_theme("light")  
        except:
            pass
    root = tk.Tk()
    app = EscalonadorGUI(root)
    root.mainloop()
