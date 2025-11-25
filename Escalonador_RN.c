import tkinter as tk
from tkinter import messagebox, ttk
from collections import deque
import json
import os

# Aplicação do Sun Valley Theme
try:
    import sv_ttk
except Exception as e:
    sv_ttk = None
    print("Aviso: sv_ttk não encontrado. Rode 'pip install sv_ttk' para tema Sun Valley.")

# Modelo dos dados (Backend)

class Processo:
    def __init__(self, pid, prioridade, tempo_execucao):
        self.pid = pid
        self.prioridade = prioridade
        self.tempo_execucao = tempo_execucao
        self.estado = "Pronto"

    def __repr__(self):
        return f"PID={self.pid}(P:{self.prioridade})"


# Personalização da Árvore Rubro-Negra
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

    # --- Métodos da árvore (mantidos) ---
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
        if p1.prioridade < p2.prioridade: return -1
        if p1.prioridade > p2.prioridade: return 1
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

# Interface Gráfica (Frontend)

class EscalonadorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Escalonador Rubro-Negro")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)

        # Aplicação do tema dark
        if sv_ttk:
            sv_ttk.set_theme("dark")

        # Dados e estado
        self.arvore = ArvoreRubroNegra()
        self.fila = deque()
        self.politica = 1  # 1 = Prioridade (RB), 2 = FIFO

        self.processo_em_execucao = None
        self.simulacao_ativa = False

        # Criar UI
        self._config_style()
        self._criar_layout()
        self.carregar_dados()

        # Eventos para reajustar desenho
        self.canvas.bind("<Configure>", lambda e: self.atualizar_visualizacao())

    # Estilo extra (para complementar sv_ttk)

    def _config_style(self):
        style = ttk.Style(self.root)
        style.configure("Card.TFrame", padding=12, relief="flat", background="#1f1f1f")
        style.configure("Title.TLabel", font=("Segoe UI", 13, "bold"), background="#1f1f1f", foreground="white")
        style.configure("Small.TLabel", font=("Segoe UI", 10), background="#1f1f1f", foreground="#DDDDDD")
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=8)
        # Entradas (ttk.Entry usa diretamente o tema sv_ttk)
        # Listbox custom
        # Frame background geral
        self.root.configure(bg="#181818")

    # Layout
    def _criar_layout(self):
        # Left panel (controls)
        left = ttk.Frame(self.root, style="Card.TFrame")
        left.pack(side=tk.LEFT, fill=tk.Y, ipadx=8, ipady=8, padx=(12,8), pady=12)

        # Header
        ttk.Label(left, text="Escalonador", style="Title.TLabel").pack(anchor="w", pady=(0,8))

        # Add process block
        add_frame = ttk.LabelFrame(left, text="Adicionar Processo", padding=8)
        add_frame.pack(fill=tk.X, pady=(0,10))

        self.entry_pid = self._label_entry(add_frame, "PID:")
        self.entry_prio = self._label_entry(add_frame, "Prioridade (menor = maior):")
        self.entry_tempo = self._label_entry(add_frame, "Tempo (s):")

        ttk.Button(add_frame, text="Criar Processo", style="Accent.TButton", command=self.criar_processo).pack(fill=tk.X, pady=(8,0))

        # CPU controls
        cpu_frame = ttk.LabelFrame(left, text="CPU", padding=8)
        cpu_frame.pack(fill=tk.X, pady=6)

        self.lbl_politica = ttk.Label(cpu_frame, text="Política: PRIORIDADE (RB)", style="Small.TLabel")
        self.lbl_politica.pack(anchor="w", pady=(0,6))

        btns_row = ttk.Frame(cpu_frame)
        btns_row.pack(fill=tk.X)
        ttk.Button(btns_row, text="Trocar Política", command=self.trocar_politica).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,6))
        self.btn_sim = ttk.Button(btns_row, text="INICIAR SIMULAÇÃO", style="Accent.TButton", command=self.toggle_simulacao)
        self.btn_sim.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # CPU display
        self.frame_cpu = tk.Frame(cpu_frame, bg="#0f0f0f", bd=1, relief=tk.SOLID)
        self.frame_cpu.pack(fill=tk.X, pady=8)
        tk.Label(self.frame_cpu, text="NA CPU:", fg="#00D46A", bg="#0f0f0f", font=("Consolas", 10, "bold")).pack(anchor="w", padx=8, pady=(6,0))
        self.lbl_cpu_info = tk.Label(self.frame_cpu, text="Ocioso", fg="white", bg="#0f0f0f", font=("Consolas", 14))
        self.lbl_cpu_info.pack(anchor="w", padx=8, pady=(4,8))

        # Kill
        kill_frame = ttk.LabelFrame(left, text="Kill", padding=8)
        kill_frame.pack(fill=tk.X, pady=6)
        self.entry_kill = self._label_entry(kill_frame, "Kill PID:")
        ttk.Button(kill_frame, text="Kill", style="Accent.TButton", command=self.kill_processo).pack(fill=tk.X, pady=(6,0))

        # Espaço livre (antes ocupava o log)
        spacer = ttk.Frame(left)
        spacer.pack(fill=tk.BOTH, expand=True, pady=(8,0))

        # Right panel (visual)
        right = ttk.Frame(self.root)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8,12), pady=12)

        # Top area: canvas (árvore)
        canvas_card = ttk.Frame(right)
        canvas_card.pack(fill=tk.BOTH, expand=True, pady=(0,8))
        self.canvas = tk.Canvas(canvas_card, bg="#121212", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bottom area: fila
        fila_card = ttk.Frame(right, padding=6)
        fila_card.pack(fill=tk.X)
        ttk.Label(fila_card, text="Fila de Chegada", style="Small.TLabel").pack(anchor="w", pady=(0,6))
        self.frame_fila = tk.Frame(fila_card, bg="#111111")
        self.frame_fila.pack(fill=tk.X, pady=(0,6))

    def _label_entry(self, parent, label_text):
        ttk.Label(parent, text=label_text, style="Small.TLabel").pack(anchor="w")
        ent = ttk.Entry(parent)
        ent.pack(fill=tk.X, pady=(2,6))
        return ent

    # Lógica do relógio / escalonador
    
    def toggle_simulacao(self):
        self.simulacao_ativa = not self.simulacao_ativa
        if self.simulacao_ativa:
            self.btn_sim.config(text="PAUSAR SIMULAÇÃO")
            self.tick()
        else:
            self.btn_sim.config(text="INICIAR SIMULAÇÃO")

    def tick(self):
        if not self.simulacao_ativa:
            return

        if self.processo_em_execucao is None:
            self.escalonar_proximo()

        if self.processo_em_execucao:
            proc = self.processo_em_execucao
            proc.tempo_execucao -= 1
            self.lbl_cpu_info.config(text=f"PID {proc.pid} — {proc.tempo_execucao}s")
            self.atualizar_visualizacao()
            self.salvar_dados()
            if proc.tempo_execucao <= 0:
                self.finalizar_processo_atual()
        else:
            self.lbl_cpu_info.config(text="Ocioso")

        self.root.after(1000, self.tick)

    def escalonar_proximo(self):
        proc = None
        if self.politica == 1:
            if self.arvore.raiz != self.arvore.NIL:
                no = self.arvore.minimo(self.arvore.raiz)
                proc = no.proc
        else:
            if self.fila:
                proc = self.fila[0]
        if proc:
            self.processo_em_execucao = proc
            # processo carregado na CPU

    def finalizar_processo_atual(self):
        if not self.processo_em_execucao:
            return
        pid = self.processo_em_execucao.pid
        no = self.arvore.buscar_por_pid(self.arvore.raiz, pid)
        if no:
            self.arvore.remover_no(no)
        try:
            self.fila.remove(self.processo_em_execucao)
        except ValueError:
            pass
        self.processo_em_execucao = None
        self.lbl_cpu_info.config(text="Ocioso")
        self.atualizar_visualizacao()
        self.salvar_dados()


    # Operações básicas (criar / kill / política)
    
    def criar_processo(self):
        try:
            pid = int(self.entry_pid.get())
            prio = int(self.entry_prio.get())
            tempo = int(self.entry_tempo.get())
        except Exception:
            messagebox.showerror("Erro", "Preencha PID, Prioridade e Tempo com números inteiros.")
            return

        if self.arvore.buscar_por_pid(self.arvore.raiz, pid):
            messagebox.showerror("Erro", "PID já existe.")
            return

        p = Processo(pid, prio, tempo)
        self.arvore.inserir(p)
        self.fila.append(p)
        self.entry_pid.delete(0, tk.END)
        self.entry_prio.delete(0, tk.END)
        self.entry_tempo.delete(0, tk.END)
        self.atualizar_visualizacao()
        self.salvar_dados()

    def kill_processo(self):
        try:
            pid = int(self.entry_kill.get())
        except Exception:
            return

        if self.processo_em_execucao and self.processo_em_execucao.pid == pid:
            self.processo_em_execucao = None
            self.lbl_cpu_info.config(text="Kill na CPU")

        no = self.arvore.buscar_por_pid(self.arvore.raiz, pid)
        if no:
            p_ref = no.proc
            self.arvore.remover_no(no)
            try:
                self.fila.remove(p_ref)
            except ValueError:
                pass
            # chamada ao log removida
            self.atualizar_visualizacao()
            self.salvar_dados()
        self.entry_kill.delete(0, tk.END)

    def trocar_politica(self):
        self.politica = 2 if self.politica == 1 else 1
        texto = "PRIORIDADE (RB)" if self.politica == 1 else "FIFO"
        self.lbl_politica.config(text=f"Política: {texto}")
        # política alterada

    
    # Visualização (canvas + fila)
    
    def atualizar_visualizacao(self):
        # redesenha árvore e fila
        self.canvas.delete("all")
        largura = self.canvas.winfo_width()
        altura = self.canvas.winfo_height()
        if largura < 100:
            largura = 800
        self._desenhar_no(self.arvore.raiz, largura/2, 60, largura/4)

        # desenha fila
        for w in self.frame_fila.winfo_children():
            w.destroy()
        if not self.fila:
            tk.Label(self.frame_fila, text="[Fila Vazia]", bg="#111111", fg="#BBBBBB", padx=8, pady=6).pack()
        else:
            for p in self.fila:
                bg = "#00A86B" if self.processo_em_execucao == p else "#222222"
                lbl = tk.Label(self.frame_fila, text=f"[{p.pid}] {p.tempo_execucao}s", bg=bg, fg="white", padx=8, pady=6, bd=0)
                lbl.pack(side=tk.LEFT, padx=6)

    def _desenhar_no(self, no, x, y, offset):
        if no == self.arvore.NIL:
            return

        # linhas para filhos
        child_y = y + 90
        if no.esq != self.arvore.NIL:
            x_left = x - offset
            self.canvas.create_line(x, y+30, x_left, child_y-30, fill="#555555", width=2)
            self._desenhar_no(no.esq, x_left, child_y, offset/2)
        if no.dir != self.arvore.NIL:
            x_right = x + offset
            self.canvas.create_line(x, y+30, x_right, child_y-30, fill="#555555", width=2)
            self._desenhar_no(no.dir, x_right, child_y, offset/2)

        # nó
        fill_color = no.cor if hasattr(no, "cor") else VERMELHO
        outline = "#00FF99" if self.processo_em_execucao == no.proc else "#BBBBBB"
        width_outline = 4 if self.processo_em_execucao == no.proc else 2

        r = 36  # raio do nó
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill_color, outline=outline, width=width_outline)
        # texto com pid e tempo
        texto = f"{no.proc.pid}\n{no.proc.tempo_execucao}s"
        self.canvas.create_text(x, y, text=texto, fill="white", font=("Segoe UI", 11, "bold"))

    
    # Persistência
    
    def salvar_dados(self):
        lista = []
        for p in self.fila:
            lista.append({"pid": p.pid, "prio": p.prioridade, "tempo": p.tempo_execucao})
        try:
            with open("dados_escalonador.json", "w") as f:
                json.dump(lista, f)
        except Exception:
            pass

    def carregar_dados(self):
        if not os.path.exists("dados_escalonador.json"):
            return
        try:
            with open("dados_escalonador.json", "r") as f:
                dados = json.load(f)
            for item in dados:
                p = Processo(item["pid"], item["prio"], item["tempo"])
                self.arvore.inserir(p)
                self.fila.append(p)
        except Exception:
            pass
        self.atualizar_visualizacao()




# Execução da aplicação

if __name__ == "__main__":
    root = tk.Tk()
    if sv_ttk:
        sv_ttk.set_theme("dark")  # "dark" ou "light"
    app = EscalonadorGUI(root)
    root.mainloop()
