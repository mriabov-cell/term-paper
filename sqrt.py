from datetime import datetime, timedelta
import io
import os
import random
import sys
import tkinter as tk
from tkinter import messagebox, ttk, filedialog

try:
    from PIL import Image, ImageTk, ImageFile, ImageDraw

    ImageFile.LOAD_TRUNCATED_IMAGES = True
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# --- АКТУАЛЬНИЙ КУРС ВАЛЮТ (НБУ) ---
USD_RATE = 45.59  # 1 USD = 45.59 UAH

# --- СХОВИЩЕ АВАТАРОК ТА ОБКЛАДИНОК ---
CLIENT_AVATAR_FILES = [
    "b5df7b1a1055b68b27c4933630199bd5.jpg",
    "images.jpg",
    "images1.jpg"
]
AVATAR_CACHE = {}

GENRE_COLORS = {
    "Роман": "#1B365D",
    "Пригоди": "#2E5A44",
    "Повість": "#5C3A21",
    "Драма": "#6B1D2F",
    "Поезія": "#4A2E5D",
    "Фантастика": "#0F4C81",
    "Детектив": "#2C3E50"
}


def load_avatar_image(filename: str, size=(60, 60)):
    if not HAS_PIL:
        return None
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    full_path = os.path.join(script_dir, filename)

    if not os.path.exists(full_path):
        return None

    cache_key = f"{filename}_{size[0]}x{size[1]}"
    if cache_key in AVATAR_CACHE:
        return AVATAR_CACHE[cache_key]

    try:
        with open(full_path, 'rb') as f:
            img_bytes = f.read()
        stream = io.BytesIO(img_bytes)
        img = Image.open(stream).convert("RGB")
        img = img.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        AVATAR_CACHE[cache_key] = photo
        return photo
    except Exception:
        return None


def generate_auto_cover(genre: str, width=220, height=440):
    if not HAS_PIL:
        return None

    color = GENRE_COLORS.get(genre, "#154332")
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)

    draw.rectangle([10, 10, width - 10, height - 10], outline="#E2E8F0", width=3)
    draw.rectangle([15, 15, width - 15, height - 15], outline="#E2E8F0", width=1)

    draw.text((width // 2, height // 2 - 20), "КНИЖКОВА ОБКЛАДИНКА", fill="#FFFFFF", anchor="mm")
    draw.text((width // 2, height // 2 + 10), f"Жанр: {genre}", fill="#CBD5E0", anchor="mm")

    photo = ImageTk.PhotoImage(img)
    return photo


# --- МОДЕЛІ ДАНИХ ---
class Book:
    def __init__(self, book_id: int, title: str, author: str, year: int, genre: str = "Роман", annotation: str = "",
                 is_available: bool = True, price: int = 0):
        self.book_id = int(book_id)
        self.title = title
        self.author = author
        self.year = year
        self.genre = genre
        self.annotation = annotation or f"Видання '{title}' автора {author}."
        self.is_available = is_available
        self.price = price


class Reader:
    def __init__(self, reader_id: int, name: str, phone: str, email: str = "", is_blocked: bool = False,
                 avatar_file: str = None):
        self.reader_id = int(reader_id)
        self.name = name
        self.phone = phone
        self.email = email or f"{name.lower().replace(' ', '.')}@example.com"
        self.is_blocked = is_blocked
        self.avatar_file = avatar_file or random.choice(CLIENT_AVATAR_FILES)


class BorrowRecord:
    def __init__(self, record_id: int, book: Book, reader: Reader, days_allowed: int = 14):
        self.record_id = int(record_id)
        self.book = book
        self.reader = reader
        self.issue_date = datetime.now() - timedelta(days=days_allowed)
        self.due_date = self.issue_date + timedelta(days=14)
        self.is_returned = False
        self.fine_paid = False

    def get_overdue_days(self) -> int:
        now = datetime.now()
        if now > self.due_date:
            return (now - self.due_date).days
        return 0

    def calculate_fine(self) -> int:
        if self.fine_paid:
            return 0
        return self.get_overdue_days() * 100


class Library:
    def __init__(self, name: str):
        self.name = name
        self._books = []
        self._readers = []
        self._records = []
        self._record_counter = 1
        self.wallet_balance = 1000.0  # Початковий баланс
        self.currency = "UAH"
        self.payment_history = []

        self.shop_catalog = [
            Book(901, "Дюна", "Френк Герберт", 1965, "Фантастика",
                 "Культовий науково-фантастичний роман про планету Арракіс.", price=300),
            Book(902, "1984", "Джордж Орвелл", 1949, "Роман", "Класична антиутопія про тоталітарне суспільство.",
                 price=250),
            Book(903, "Шерлок Холмс", "Артур Конан Дойл", 1892, "Детектив",
                 "Захопливі детективні розслідування видатного нишпорки.", price=200),
            Book(904, "Володар Перснів", "Дж. Р. Р. Толкін", 1954, "Пригоди",
                 "Епічне фентезі про боротьбу із Сауроном.", price=400),
            Book(905, "Маленький принц", "Антуан де Сент-Екзюпері", 1943, "Повість",
                 "Алегорична казка-повість про дружбу та любов.", price=150),
            Book(906, "Алхімік", "Пауло Коельйо", 1988, "Роман", "Філософський роман про слідування за власною мрією.",
                 price=220),
            Book(907, "Гра престолів", "Джордж Р. Р. Мартін", 1996, "Пригоди",
                 "Перша книга масштабного циклу 'Пісня льоду й полум'я'.", price=350),
            Book(908, "Убити пересмішника", "Харпер Лі", 1960, "Роман",
                 "Видатний роман про справедливість та зростання.", price=280),
            Book(909, "Гаррі Поттер і філософський камінь", "Дж. К. Роулінг", 1997, "Пригоди",
                 "Початок історії про юного чарівника.", price=320),
            Book(910, "Три товариші", "Еріх Марія Ремарк", 1936, "Роман", "Роман про справжню дружбу та кохання.",
                 price=270)
        ]

    def add_book(self, book: Book):
        self._books.append(book)

    def register_reader(self, reader: Reader):
        self._readers.append(reader)

    def calculate_statistics(self) -> dict:
        total = len(self._books)
        avail = sum(1 for b in self._books if b.is_available)
        overdue = sum(1 for r in self._records if r.calculate_fine() > 0 and not r.is_returned)
        return {"total_books": total, "available_books": avail, "issued_books": total - avail, "overdue_books": overdue}

    def issue_book(self, book_id: int, reader_id: int, simulate_days_ago: int = 0) -> tuple[bool, str]:
        b = next((x for x in self._books if x.book_id == int(book_id)), None)
        r = next((x for x in self._readers if x.reader_id == int(reader_id)), None)
        if not b: return False, "Книгу з таким ID не знайдено."
        if not b.is_available: return False, "Книга вже видана."
        if not r: return False, "Читача з таким ID не знайдено."
        if r.is_blocked: return False, f"Читач {r.name} заблокований! Видача заборонена."

        record = BorrowRecord(self._record_counter, b, r, days_allowed=14)
        if simulate_days_ago > 0:
            record.issue_date = datetime.now() - timedelta(days=simulate_days_ago)
            record.due_date = record.issue_date + timedelta(days=14)

        self._records.append(record)
        self._record_counter += 1
        b.is_available = False
        return True, f"Книгу '{b.title}' видано читачу {r.name}!"

    def convert_wallet_currency(self):
        if self.currency == "UAH":
            self.wallet_balance = round(self.wallet_balance / USD_RATE, 2)
            self.currency = "USD"
            return True, f"Баланс конвертовано в USD за курсом {USD_RATE} грн/$"
        else:
            self.wallet_balance = round(self.wallet_balance * USD_RATE, 2)
            self.currency = "UAH"
            return True, f"Баланс конвертовано назад у UAH за курсом {USD_RATE} грн/$"

    def return_book(self, book_id: int) -> tuple[bool, str, int]:
        target_id = int(book_id)
        for rec in self._records:
            if rec.book.book_id == target_id and not rec.is_returned:
                fine = rec.calculate_fine()
                rec.is_returned = True
                rec.book.is_available = True

                if fine > 0 and not rec.fine_paid:
                    rec.fine_paid = True
                    add_amount = fine if self.currency == "UAH" else round(fine / USD_RATE, 2)
                    self.wallet_balance += add_amount
                    self.payment_history.append({
                        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        "reader": rec.reader.name,
                        "book": rec.book.title,
                        "amount": f"{add_amount} {self.currency}",
                        "type": "Штраф"
                    })
                    return True, f"Книгу '{rec.book.title}' повернуто. Штраф {fine} грн ({add_amount} {self.currency}) зараховано у гаманець!", fine
                return True, f"Книгу '{rec.book.title}' повернуто до фонду вчасно.", 0
        return False, "Активного запису видачі не знайдено.", 0

    def buy_new_book_for_library(self, shop_book_id: int) -> tuple[bool, str]:
        book_to_buy = next((b for b in self.shop_catalog if b.book_id == int(shop_book_id)), None)
        if not book_to_buy:
            return False, "Книгу не знайдено в магазині."

        price_in_curr = book_to_buy.price if self.currency == "UAH" else round(book_to_buy.price / USD_RATE, 2)

        if self.wallet_balance < price_in_curr:
            return False, f"Недостатньо коштів! Потрібно {price_in_curr} {self.currency}, а є лише {self.wallet_balance} {self.currency}."

        self.wallet_balance -= price_in_curr
        self.shop_catalog.remove(book_to_buy)

        new_id = max([b.book_id for b in self._books] or [100]) + 1
        book_to_buy.book_id = new_id
        self._books.append(book_to_buy)

        self.payment_history.append({
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "reader": "Адміністратор",
            "book": f"Закупка: {book_to_buy.title}",
            "amount": f"-{price_in_curr} {self.currency}",
            "type": "Купівля"
        })

        return True, f"Книгу '{book_to_buy.title}' успішно куплено та додано до каталогу!"

    def pay_reader_fine_online(self, record_id: int) -> tuple[bool, str]:
        rec = next((r for r in self._records if r.record_id == int(record_id)), None)
        if not rec:
            return False, "Запис не знайдено."
        fine = rec.calculate_fine()
        if fine <= 0:
            return False, "Штраф відсутній або вже сплачений."

        rec.fine_paid = True
        add_amount = fine if self.currency == "UAH" else round(fine / USD_RATE, 2)
        self.wallet_balance += add_amount
        self.payment_history.append({
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "reader": rec.reader.name,
            "book": rec.book.title,
            "amount": f"{add_amount} {self.currency}",
            "type": "Онлайн штраф"
        })
        return True, f"Штраф у розмірі {fine} грн успішно сплачено онлайн!"

    def toggle_reader_block(self, reader_id: int) -> tuple[bool, str]:
        r = next((x for x in self._readers if x.reader_id == int(reader_id)), None)
        if not r: return False, "Читача не знайдено."
        r.is_blocked = not r.is_blocked
        status = "заблоковано ❌" if r.is_blocked else "розблоковано ✅"
        return True, f"Читача {r.name} успішно {status}."

    def get_active_borrows(self) -> list:
        return [r for r in self._records if not r.is_returned]

    def get_user_borrows(self, reader_id: int) -> list:
        return [r for r in self._records if r.reader.reader_id == int(reader_id) and not r.is_returned]

    def __iter__(self):
        return iter(self._books)


# --- ГОЛОВНИЙ ІНТЕРФЕЙС ТА ОПТИМІЗОВАНІ ТЕМИ ---
class LibraryApp:
    def __init__(self, root, library: Library):
        self.root = root
        self.lib = library
        self.root.title("Читай / LIBRARY MANAGEMENT SYSTEM")
        self.root.geometry("1200x780")

        self.current_theme = tk.StringVar(value="Світла")
        self.current_role = tk.StringVar(value="Адміністратор")
        self.active_reader_id = tk.IntVar(value=1)

        # Оптимізована кольорова палітра без кислотних відтінків
        self.themes = {
            "Світла": {
                "bg": "#F9F8F6",
                "sidebar_bg": "#F2EFF0",
                "card_bg": "#FFFFFF",
                "fg": "#1A202C",
                "text_secondary": "#718096",
                "accent": "#154332",
                "accent_active": "#1E5E46",
                "tree_bg": "#FFFFFF",
                "tree_fg": "#2D3748",
                "tree_head_bg": "#F2EFF0",
                "tree_select_bg": "#E2E8F0",
                "tree_select_fg": "#1A202C",
                "entry_bg": "#FFFFFF",
                "entry_fg": "#1A202C",
                "border": "#CBD5E0"
            },
            "Темна": {
                "bg": "#121212",  # М'який темний фон замість чорного
                "sidebar_bg": "#1E1E1E",  # Комфортний колір бічної панелі
                "card_bg": "#252526",  # Картки та блоки
                "fg": "#E0E0E0",  # М'який білий для основного тексту (не ріже очі)
                "text_secondary": "#A0A0A0",  # Приглушений сірий для підписів
                "accent": "#2D6A4F",  # Приємний зелений акцент
                "accent_active": "#40916C",
                "tree_bg": "#1E1E1E",
                "tree_fg": "#E0E0E0",
                "tree_head_bg": "#2D2D2D",
                "tree_select_bg": "#3A3A3C",  # Виділений рядок у таблиці
                "tree_select_fg": "#FFFFFF",
                "entry_bg": "#2D2D2D",
                "entry_fg": "#E0E0E0",
                "border": "#3A3A3C"
            }
        }

        self.top_bar = tk.Frame(root, padx=25, pady=12)
        self.top_bar.pack(fill="x")

        self.lbl_logo = tk.Label(self.top_bar, text="📗 Читай", font=("Segoe UI", 15, "bold"))
        self.lbl_logo.pack(side="left")
        self.lbl_sublogo = tk.Label(self.top_bar, text="SYSTEM", font=("Segoe UI", 8, "bold"))
        self.lbl_sublogo.pack(side="left", padx=(5, 0))

        self.btn_open_wallet_window = ttk.Button(self.top_bar, text="💰 Гаманець та закупка книг",
                                                 style="Accent.TButton", command=self._open_wallet_modal)
        self.btn_open_wallet_window.pack(side="left", padx=20)

        self.role_frame = tk.Frame(self.top_bar)
        self.role_frame.pack(side="right")

        self.lbl_role_txt = tk.Label(self.role_frame, text="Роль:", font=("Segoe UI", 9, "bold"))
        self.lbl_role_txt.pack(side="left", padx=(0, 5))
        role_cb = ttk.Combobox(self.role_frame, textvariable=self.current_role, values=["Адміністратор", "Читач"],
                               state="readonly", width=14)
        role_cb.pack(side="left", padx=5)
        role_cb.bind("<<ComboboxSelected>>", self._on_role_change)

        self.lbl_reader_select = tk.Label(self.role_frame, text="Читач:", font=("Segoe UI", 9, "bold"))
        self.cb_reader_select = ttk.Combobox(self.role_frame, state="readonly", width=18)
        self.cb_reader_select.bind("<<ComboboxSelected>>", self._on_active_reader_changed)

        self.container = tk.Frame(root)
        self.container.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(self.container, width=230, padx=15, pady=20)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_content = tk.Frame(self.container, padx=25, pady=15)
        self.main_content.pack(side="right", fill="both", expand=True)

        self.pages = {}
        for k in ["catalog", "readers", "borrows", "my_books", "settings"]:
            self.pages[k] = tk.Frame(self.main_content)

        self._setup_sidebar()
        self._setup_catalog_page()
        self._setup_readers_page()
        self._setup_borrows_page()
        self._setup_my_books_page()
        self._setup_settings_page()

        self._apply_theme()
        self._update_reader_combobox()
        self.show_page("catalog")
        self.refresh_all()

    def _apply_theme(self):
        t = self.themes[self.current_theme.get()]

        self.root.configure(bg=t["bg"])
        self.top_bar.configure(bg=t["bg"])
        self.role_frame.configure(bg=t["bg"])
        self.lbl_logo.configure(bg=t["bg"], fg=t["accent"])
        self.lbl_sublogo.configure(bg=t["bg"], fg=t["text_secondary"])
        self.lbl_role_txt.configure(bg=t["bg"], fg=t["fg"])
        self.lbl_reader_select.configure(bg=t["bg"], fg=t["fg"])
        self.container.configure(bg=t["bg"])
        self.sidebar.configure(bg=t["sidebar_bg"])
        self.main_content.configure(bg=t["bg"])

        for p in self.pages.values():
            p.configure(bg=t["bg"])

        # Оновлення графічних стилів TTK
        s = ttk.Style()
        s.theme_use("clam")
        s.configure(".", font=("Segoe UI", 10), background=t["bg"], foreground=t["fg"])
        s.configure("Treeview", background=t["tree_bg"], fieldbackground=t["tree_bg"], foreground=t["tree_fg"],
                    rowheight=36, borderwidth=0)
        s.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background=t["tree_head_bg"], foreground=t["fg"],
                    relief="flat")
        s.map("Treeview", background=[("selected", t["tree_select_bg"])],
              foreground=[("selected", t["tree_select_fg"])])

        s.configure("TCombobox", fieldbackground=t["entry_bg"], background=t["card_bg"], foreground=t["fg"])
        s.map("TCombobox", fieldbackground=[("readonly", t["entry_bg"])], foreground=[("readonly", t["fg"])])

        s.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), foreground="#FFFFFF", background=t["accent"],
                    borderwidth=0)
        s.map("Accent.TButton", background=[("active", t["accent_active"])])

        s.configure("TNotebook", background=t["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", background=t["sidebar_bg"], foreground=t["fg"], padding=[10, 5])
        s.map("TNotebook.Tab", background=[("selected", t["card_bg"])], foreground=[("selected", t["fg"])])

        self._apply_theme_to_widgets(self.main_content, t)
        self._setup_sidebar()

    def _apply_theme_to_widgets(self, parent, t):
        """Рекурсивно оновлює кольори для всіх вкладених стандартних віджетів tkinter."""
        for child in parent.winfo_children():
            w_type = child.winfo_class()
            if w_type in ["Frame", "Labelframe"]:
                child.configure(bg=t["bg"])
                if w_type == "Labelframe":
                    child.configure(fg=t["fg"])
                self._apply_theme_to_widgets(child, t)
            elif w_type == "Label":
                # Не змінюємо спеціально виділені статусний борг та інформацію
                if child not in [getattr(self, "lbl_my_debt", None), getattr(self, "lbl_stats", None)]:
                    child.configure(bg=t["bg"], fg=t["fg"])
            elif w_type == "Button":
                child.configure(bg=t["sidebar_bg"], fg=t["fg"], activebackground=t["bg"], activeforeground=t["fg"])

    def _update_reader_combobox(self):
        readers_list = [f"{r.reader_id}: {r.name}" for r in self.lib._readers]
        self.cb_reader_select["values"] = readers_list
        if readers_list:
            self.cb_reader_select.set(readers_list[0])

    def _on_active_reader_changed(self, event=None):
        val = self.cb_reader_select.get()
        if val:
            r_id = int(val.split(":")[0])
            self.active_reader_id.set(r_id)
            self.refresh_my_books()

    def _setup_sidebar(self):
        for widget in self.sidebar.winfo_children():
            widget.destroy()

        t = self.themes[self.current_theme.get()]
        tk.Label(self.sidebar, text="МЕНЮ СИСТЕМИ", font=("Segoe UI", 8, "bold"), bg=t["sidebar_bg"],
                 fg=t["text_secondary"], anchor="w").pack(fill="x", pady=(0, 12))

        if self.current_role.get() == "Адміністратор":
            self.btn_open_wallet_window.pack(side="left", padx=20)
            self.lbl_reader_select.pack_forget()
            self.cb_reader_select.pack_forget()
            nav = [("Каталог книг", "catalog"), ("Керування читачами", "readers"), ("Видачі та штрафи", "borrows"),
                   ("Налаштування", "settings")]
        else:
            self.btn_open_wallet_window.pack_forget()
            self.lbl_reader_select.pack(side="left", padx=(10, 5))
            self.cb_reader_select.pack(side="left", padx=2)
            nav = [("Каталог", "catalog"), ("Мій кабінет (Мої книги)", "my_books")]

        for text, key in nav:
            btn = tk.Button(self.sidebar, text=f"  {text}", font=("Segoe UI", 10), bg=t["sidebar_bg"], fg=t["fg"],
                            activebackground=t["bg"], activeforeground=t["fg"], bd=0, anchor="w", relief="flat",
                            cursor="hand2", command=lambda k=key: self.show_page(k))
            btn.pack(fill="x", pady=3, ipady=6)

    def _on_role_change(self, event=None):
        self._setup_sidebar()
        self.show_page("catalog" if self.current_role.get() == "Адміністратор" else "my_books")
        self.refresh_all()

    def show_page(self, key):
        for p in self.pages.values():
            p.pack_forget()
        self.pages[key].pack(fill="both", expand=True)

    def refresh_all(self):
        self.refresh_catalog()
        self.refresh_readers()
        self.refresh_borrows()
        self.refresh_my_books()

    # --- МОДАЛЬНЕ ВІКНО ГАМАНЦЯ ---
    def _open_wallet_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("💰 Гаманець та закупівля книг")
        modal.geometry("700x560")
        modal.configure(padx=20, pady=20)
        modal.transient(self.root)
        modal.grab_set()

        t = self.themes[self.current_theme.get()]
        modal.configure(bg=t["bg"])

        top_f = tk.Frame(modal, bg=t["bg"])
        top_f.pack(fill="x", pady=(0, 15))

        lbl_balance = tk.Label(top_f, text="", font=("Segoe UI", 15, "bold"),
                               fg="#4E9F3D" if self.current_theme.get() == "Темна" else "#2E7D32", bg=t["bg"])
        lbl_balance.pack(side="left")

        def update_bal_label():
            usd_equiv = round(self.lib.wallet_balance / USD_RATE,
                              2) if self.lib.currency == "UAH" else self.lib.wallet_balance
            lbl_balance.config(text=f"Баланс: {self.lib.wallet_balance} {self.lib.currency} (≈ ${usd_equiv} USD)")

        update_bal_label()

        def toggle_currency():
            ok, msg = self.lib.convert_wallet_currency()
            update_bal_label()
            refresh_shop()
            messagebox.showinfo("Валюта", msg, parent=modal)

        ttk.Button(top_f, text="💱 Перевести UAH <-> USD", command=toggle_currency).pack(side="right")

        notebook = ttk.Notebook(modal)
        notebook.pack(fill="both", expand=True)

        tab_shop = tk.Frame(notebook, bg=t["bg"], padx=10, pady=10)
        notebook.add(tab_shop, text="🛒 Магазин нових книг")

        cols_shop = ("id", "title", "author", "genre", "price")
        tree_shop = ttk.Treeview(tab_shop, columns=cols_shop, show="headings", height=8)
        for c, h, w in [("id", "ID", 40), ("title", "Назва", 180), ("author", "Автор", 140), ("genre", "Жанр", 90),
                        ("price", "Ціна", 100)]:
            tree_shop.heading(c, text=h)
            tree_shop.column(c, width=w, anchor="center" if c in ["id", "price", "genre"] else "w")
        tree_shop.pack(fill="both", expand=True, pady=(0, 10))

        def refresh_shop():
            tree_shop.delete(*tree_shop.get_children())
            for b in self.lib.shop_catalog:
                p_val = b.price if self.lib.currency == "UAH" else round(b.price / USD_RATE, 2)
                tree_shop.insert("", "end",
                                 values=(b.book_id, b.title, b.author, b.genre, f"{p_val} {self.lib.currency}"))

        refresh_shop()

        def buy_selected():
            sel = tree_shop.selection()
            if not sel:
                return messagebox.showwarning("Увага", "Оберіть книгу з магазину!", parent=modal)
            shop_id = int(tree_shop.item(sel[0])["values"][0])
            ok, msg = self.lib.buy_new_book_for_library(shop_id)
            if ok:
                messagebox.showinfo("Успіх", msg, parent=modal)
                update_bal_label()
                refresh_shop()
                self.refresh_all()
            else:
                messagebox.showerror("Помилка", msg, parent=modal)

        ttk.Button(tab_shop, text="🛒 Купити обрану книгу у фонд", style="Accent.TButton", command=buy_selected).pack(
            anchor="e")

        tab_history = tk.Frame(notebook, bg=t["bg"], padx=10, pady=10)
        notebook.add(tab_history, text="📜 Історія транзакцій")

        cols_hist = ("date", "type", "reader", "book", "amount")
        tree_hist = ttk.Treeview(tab_history, columns=cols_hist, show="headings", height=8)
        for c, h, w in [("date", "Дата", 120), ("type", "Тип", 90), ("reader", "Читач/Адм", 130),
                        ("book", "Деталі", 160), ("amount", "Сума", 90)]:
            tree_hist.heading(c, text=h)
            tree_hist.column(c, width=w, anchor="center" if c in ["date", "type", "amount"] else "w")
        tree_hist.pack(fill="both", expand=True, pady=(0, 10))

        for pay in reversed(self.lib.payment_history):
            tree_hist.insert("", "end",
                             values=(pay["date"], pay.get("type", "Штраф"), pay["reader"], pay["book"], pay["amount"]))

    # --- КАТАЛОГ ---
    def _setup_catalog_page(self):
        p = self.pages["catalog"]

        hdr = tk.Frame(p)
        hdr.pack(fill="x", pady=(0, 10))
        self.lbl_cat_sub = tk.Label(hdr, text="БІБЛІОТЕЧНИЙ ФОНД", font=("Segoe UI", 8, "bold"))
        self.lbl_cat_sub.pack(anchor="w")

        title_f = tk.Frame(hdr)
        title_f.pack(fill="x")
        self.lbl_cat_title = tk.Label(title_f, text="Каталог книг", font=("Segoe UI", 18, "bold"))
        self.lbl_cat_title.pack(side="left")

        self.btn_add_book = ttk.Button(title_f, text="+ Додати книгу", style="Accent.TButton",
                                       command=self._open_add_book_dialog)
        self.btn_add_book.pack(side="right")

        self.lbl_stats = tk.Label(p, text="", font=("Segoe UI", 9), bd=1, relief="solid")
        self.lbl_stats.pack(fill="x", pady=(0, 10), ipadx=10, ipady=6)

        cols = ("id", "title", "author", "year", "genre", "status")
        self.tree_catalog = ttk.Treeview(p, columns=cols, show="headings")
        for c, h, w in [("id", "ID", 50), ("title", "Назва книги (Двічі клікніть для перегляду)", 280),
                        ("author", "Автор", 180), ("year", "Рік", 60), ("genre", "Жанр", 100),
                        ("status", "Статус", 90)]:
            self.tree_catalog.heading(c, text=h)
            self.tree_catalog.column(c, width=w, anchor="center" if c in ["id", "year", "status", "genre"] else "w")

        self.tree_catalog.pack(fill="both", expand=True)
        self.tree_catalog.bind("<Double-1>", self._on_book_double_click)

    def refresh_catalog(self):
        t = self.themes[self.current_theme.get()]
        self.lbl_stats.configure(bg=t["card_bg"], fg=t["fg"])

        if self.current_role.get() == "Адміністратор":
            self.btn_add_book.pack(side="right")
        else:
            self.btn_add_book.pack_forget()

        self.tree_catalog.delete(*self.tree_catalog.get_children())
        for b in self.lib:
            status = "Доступна" if b.is_available else "На руках"
            self.tree_catalog.insert("", "end", values=(b.book_id, b.title, b.author, b.year, b.genre, status))

        s = self.lib.calculate_statistics()
        self.lbl_stats.config(
            text=f"Усього видань: {s['total_books']}  |  В наявності: {s['available_books']}  |  На руках: {s['issued_books']}  |  Боржників: {s['overdue_books']}")

    def _on_book_double_click(self, event):
        sel = self.tree_catalog.selection()
        if not sel: return
        b_id = int(self.tree_catalog.item(sel[0])["values"][0])
        book = next((x for x in self.lib if x.book_id == b_id), None)
        if book:
            self._open_book_details_dialog(book)

    # --- ДЕТАЛЬНЕ ВІКНО КНИГИ ---
    def _open_book_details_dialog(self, book: Book):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{book.title} — Деталі")
        dialog.geometry("640x440")
        dialog.transient(self.root)
        dialog.grab_set()

        t = self.themes[self.current_theme.get()]
        dialog.configure(bg=t["bg"])

        left_p = tk.Frame(dialog, bg=t["sidebar_bg"], width=220)
        left_p.pack(side="left", fill="y")
        left_p.pack_propagate(False)

        img_label = tk.Label(left_p, bg=t["sidebar_bg"])
        img_label.pack(fill="both", expand=True)

        cover_img = generate_auto_cover(book.genre)
        if cover_img:
            img_label.config(image=cover_img)
            img_label.image = cover_img

        right_p = tk.Frame(dialog, bg=t["bg"], padx=20, pady=20)
        right_p.pack(side="right", fill="both", expand=True)

        tk.Label(right_p, text=f"ID {book.book_id:04d} • {book.genre.upper()}", font=("Segoe UI", 8, "bold"),
                 fg=t["accent"], bg=t["bg"]).pack(anchor="w")
        tk.Label(right_p, text=book.title, font=("Segoe UI", 18, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w")
        tk.Label(right_p, text=book.author, font=("Segoe UI", 11), bg=t["bg"], fg=t["text_secondary"]).pack(anchor="w",
                                                                                                            pady=(0,
                                                                                                                  10))

        status_txt = "Доступна у бібліотеці" if book.is_available else "На руках"
        status_bg = "#1E3A2B" if (self.current_theme.get() == "Темна" and book.is_available) else (
            "#E6F4EA" if book.is_available else "#3A1E1E")
        status_fg = "#66BB6A" if (self.current_theme.get() == "Темна" and book.is_available) else (
            "#137333" if book.is_available else "#EF5350")

        tags_f = tk.Frame(right_p, bg=t["bg"])
        tags_f.pack(anchor="w", pady=(0, 15))
        tk.Label(tags_f, text=f"{book.year} рік", font=("Segoe UI", 9), bg=t["sidebar_bg"], fg=t["fg"], padx=8,
                 pady=3).pack(side="left", padx=(0, 5))
        tk.Label(tags_f, text=book.genre, font=("Segoe UI", 9), bg=t["sidebar_bg"], fg=t["fg"], padx=8, pady=3).pack(
            side="left", padx=(0, 5))
        tk.Label(tags_f, text=status_txt, font=("Segoe UI", 9, "bold"), bg=status_bg, fg=status_fg, padx=8,
                 pady=3).pack(side="left")

        tk.Label(right_p, text="АНОТАЦІЯ", font=("Segoe UI", 8, "bold"), fg=t["text_secondary"], bg=t["bg"]).pack(
            anchor="w")
        txt_annot = tk.Text(right_p, font=("Segoe UI", 9), bg=t["bg"], fg=t["fg"], bd=0, wrap="word", height=6)
        txt_annot.insert("1.0", book.annotation)
        txt_annot.config(state="disabled")
        txt_annot.pack(fill="x", pady=(0, 15))

        if book.is_available and self.current_role.get() == "Адміністратор":
            ttk.Button(right_p, text="Оформити видачу", style="Accent.TButton",
                       command=lambda: [dialog.destroy(), self._open_issue_dialog(book.book_id)]).pack(anchor="e")

    def _open_add_book_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Додати нову книгу")
        dialog.geometry("450x520")
        dialog.transient(self.root)
        dialog.grab_set()

        t = self.themes[self.current_theme.get()]
        dialog.configure(bg=t["bg"], padx=25, pady=20)

        tk.Label(dialog, text="Нова книга", font=("Segoe UI", 18, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w",
                                                                                                        pady=(0, 15))

        fields = {}
        for label, key in [("Назва книги", "title"), ("Автор", "author"), ("Рік видання", "year")]:
            tk.Label(dialog, text=label, font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w")
            e = tk.Entry(dialog, bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"], relief="solid", bd=1)
            e.pack(fill="x", pady=(0, 10))
            fields[key] = e

        tk.Label(dialog, text="Жанр", font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w")
        cb_genre = ttk.Combobox(dialog,
                                values=["Повість", "Драма", "Роман", "Пригоди", "Поезія", "Фантастика", "Детектив"],
                                state="readonly")
        cb_genre.set("Роман")
        cb_genre.pack(fill="x", pady=(0, 10))

        tk.Label(dialog, text="Анотація", font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w")
        txt_annot = tk.Text(dialog, font=("Segoe UI", 9), height=4, bd=1, relief="solid", bg=t["entry_bg"],
                            fg=t["entry_fg"], insertbackground=t["fg"])
        txt_annot.pack(fill="x", pady=(0, 15))

        def save():
            try:
                title, author = fields["title"].get(), fields["author"].get()
                year = int(fields["year"].get())
                genre = cb_genre.get()
                annot = txt_annot.get("1.0", "end").strip()
                if not title or not author: raise ValueError

                new_id = max([b.book_id for b in self.lib] or [100]) + 1
                self.lib.add_book(Book(new_id, title, author, year, genre, annot))
                messagebox.showinfo("Успіх", f"Книгу '{title}' додано до каталогу!", parent=dialog)
                self.refresh_catalog()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Помилка", "Перевірте коректність заповнення полів!", parent=dialog)

        btn_f = tk.Frame(dialog, bg=t["bg"])
        btn_f.pack(fill="x")
        ttk.Button(btn_f, text="Скасувати", command=dialog.destroy).pack(side="left")
        ttk.Button(btn_f, text="+ Додати до каталогу", style="Accent.TButton", command=save).pack(side="right")

    # --- ЧИТАЧІ ---
    def _setup_readers_page(self):
        p = self.pages["readers"]

        hdr = tk.Frame(p)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text="ЧИТАЦЬКІ ПРОФІЛІ", font=("Segoe UI", 8, "bold")).pack(anchor="w")

        title_f = tk.Frame(hdr)
        title_f.pack(fill="x")
        tk.Label(title_f, text="Керування читачами", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Button(title_f, text="+ Зареєструвати читача", style="Accent.TButton",
                   command=self._open_add_reader_dialog).pack(side="right")

        cols = ("id", "name", "phone", "email", "status")
        self.tree_readers = ttk.Treeview(p, columns=cols, show="headings")
        for c, h, w in [("id", "ID", 50), ("name", "ПІБ Читача", 200), ("phone", "Телефон", 130),
                        ("email", "Email", 180), ("status", "Статус", 120)]:
            self.tree_readers.heading(c, text=h)
            self.tree_readers.column(c, width=w, anchor="center" if c in ["id", "phone", "status"] else "w")
        self.tree_readers.pack(fill="both", expand=True, pady=(0, 10))

        btn_bar = tk.Frame(p)
        btn_bar.pack(fill="x")
        ttk.Button(btn_bar, text="👁️ Переглянути фото читача", command=self._show_reader_photo).pack(side="left")
        ttk.Button(btn_bar, text="🚫 Заблокувати / Розблокувати", command=self._action_toggle_block).pack(side="right")

    def refresh_readers(self):
        self.tree_readers.delete(*self.tree_readers.get_children())
        for r in self.lib._readers:
            status = "Заблоковано ❌" if r.is_blocked else "Активний ✅"
            self.tree_readers.insert("", "end", values=(r.reader_id, r.name, r.phone, r.email, status))
        self._update_reader_combobox()

    def _show_reader_photo(self):
        sel = self.tree_readers.selection()
        if not sel: return messagebox.showwarning("Увага", "Оберіть читача зі списку!")
        r_id = int(self.tree_readers.item(sel[0])["values"][0])
        r = next((x for x in self.lib._readers if x.reader_id == r_id), None)
        if r:
            dlg = tk.Toplevel(self.root)
            dlg.title(f"Профіль — {r.name}")
            dlg.geometry("300x320")
            dlg.transient(self.root)

            t = self.themes[self.current_theme.get()]
            dlg.configure(bg=t["bg"], padx=15, pady=15)

            img = load_avatar_image(r.avatar_file, size=(160, 160))
            if img:
                lbl_img = tk.Label(dlg, image=img, bg=t["bg"])
                lbl_img.image = img
                lbl_img.pack(pady=10)

            tk.Label(dlg, text=r.name, font=("Segoe UI", 12, "bold"), bg=t["bg"], fg=t["fg"]).pack()
            tk.Label(dlg, text=f"Аватарка: {r.avatar_file}", font=("Segoe UI", 8), fg=t["text_secondary"],
                     bg=t["bg"]).pack()

    def _action_toggle_block(self):
        sel = self.tree_readers.selection()
        if not sel: return messagebox.showwarning("Увага", "Оберіть читача зі списку!")
        r_id = int(self.tree_readers.item(sel[0])["values"][0])
        ok, msg = self.lib.toggle_reader_block(r_id)
        if ok:
            messagebox.showinfo("Результат", msg)
            self.refresh_readers()

    def _open_add_reader_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Зареєструвати читача")
        dialog.geometry("400x320")
        dialog.transient(self.root)
        dialog.grab_set()

        t = self.themes[self.current_theme.get()]
        dialog.configure(bg=t["bg"], padx=20, pady=20)

        tk.Label(dialog, text="Новий читач", font=("Segoe UI", 16, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w",
                                                                                                         pady=(0, 15))

        entries = {}
        for lbl, key in [("ПІБ Читача", "name"), ("Телефон", "phone"), ("Email", "email")]:
            tk.Label(dialog, text=lbl, font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w")
            e = tk.Entry(dialog, bg=t["entry_bg"], fg=t["entry_fg"], insertbackground=t["fg"], relief="solid", bd=1)
            e.pack(fill="x", pady=(0, 10))
            entries[key] = e

        def save():
            name, phone, email = entries["name"].get(), entries["phone"].get(), entries["email"].get()
            if not name or not phone: return messagebox.showwarning("Помилка", "Заповніть обов'язкові поля!",
                                                                    parent=dialog)
            new_id = max([r.reader_id for r in self.lib._readers] or [0]) + 1
            self.lib.register_reader(Reader(new_id, name, phone, email))
            messagebox.showinfo("Успіх", f"Читача {name} зареєстровано!", parent=dialog)
            self.refresh_readers()
            dialog.destroy()

        ttk.Button(dialog, text="Зареєструвати", style="Accent.TButton", command=save).pack(fill="x", pady=10)

    # --- ВИДАЧІ ---
    def _setup_borrows_page(self):
        p = self.pages["borrows"]

        hdr = tk.Frame(p)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text="ОБЛІК ФОНДУ ТА ШТРАФІВ (100 грн / день)", font=("Segoe UI", 8, "bold")).pack(anchor="w")

        title_f = tk.Frame(hdr)
        title_f.pack(fill="x")
        tk.Label(title_f, text="Видача та повернення", font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Button(title_f, text="+ Оформити видачу", style="Accent.TButton",
                   command=lambda: self._open_issue_dialog()).pack(side="right")

        cols = ("book_id", "book_title", "reader_name", "due_date", "overdue_days", "fine")
        self.tree_borrows = ttk.Treeview(p, columns=cols, show="headings")
        for c, h, w in [
            ("book_id", "ID Книги", 70), ("book_title", "Книга", 230), ("reader_name", "Читач", 180),
            ("due_date", "Термін (14 дн)", 110), ("overdue_days", "Прострочено", 90), ("fine", "Штраф (грн)", 100)
        ]:
            self.tree_borrows.heading(c, text=h)
            self.tree_borrows.column(c, width=w,
                                     anchor="center" if c in ["book_id", "due_date", "overdue_days", "fine"] else "w")
        self.tree_borrows.pack(fill="both", expand=True, pady=(0, 10))

        btn_bar = tk.Frame(p)
        btn_bar.pack(fill="x")
        ttk.Button(btn_bar, text="↩ Прийняти книгу та прийняти штраф", style="Accent.TButton",
                   command=self._action_return_book).pack(side="left")

    def refresh_borrows(self):
        self.tree_borrows.delete(*self.tree_borrows.get_children())
        for rec in self.lib.get_active_borrows():
            overdue_days = rec.get_overdue_days()
            fine = rec.calculate_fine()
            fine_str = f"{fine} грн ⚠️" if fine > 0 else "0 грн ✅"
            days_str = f"{overdue_days} дн" if overdue_days > 0 else "Вчасно"

            self.tree_borrows.insert("", "end", values=(
                rec.book.book_id, rec.book.title, rec.reader.name, rec.due_date.strftime("%d.%m.%Y"), days_str, fine_str
            ))

    def _action_return_book(self):
        sel = self.tree_borrows.selection()
        if not sel: return messagebox.showwarning("Увага", "Оберіть видачу у таблиці!")

        b_id = int(self.tree_borrows.item(sel[0])["values"][0])
        ok, msg, fine = self.lib.return_book(b_id)
        if ok:
            messagebox.showinfo("Результат повернення", msg)
            self.refresh_all()

    def _open_issue_dialog(self, preselect_book_id=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Оформити видачу")
        dialog.geometry("440x420")
        dialog.transient(self.root)
        dialog.grab_set()

        t = self.themes[self.current_theme.get()]
        dialog.configure(bg=t["bg"], padx=20, pady=20)

        tk.Label(dialog, text="Оформити видачу", font=("Segoe UI", 16, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w",
                                                                                                             pady=(0,
                                                                                                                   15))

        tk.Label(dialog, text="Оберіть книгу", font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w")
        avail_books = [f"{b.book_id}: {b.title}" for b in self.lib if b.is_available]
        cb_books = ttk.Combobox(dialog, values=avail_books, state="readonly")
        cb_books.pack(fill="x", pady=(0, 10))
        if preselect_book_id:
            pb = next((f"{b.book_id}: {b.title}" for b in self.lib if b.book_id == preselect_book_id), None)
            if pb: cb_books.set(pb)

        tk.Label(dialog, text="Оберіть читача", font=("Segoe UI", 9, "bold"), bg=t["bg"], fg=t["fg"]).pack(anchor="w")
        active_readers = [f"{r.reader_id}: {r.name}" for r in self.lib._readers if not r.is_blocked]
        cb_readers = ttk.Combobox(dialog, values=active_readers, state="readonly")
        cb_readers.pack(fill="x", pady=(0, 10))

        tk.Label(dialog, text="Симуляція протермінування (днів тому):", font=("Segoe UI", 9), bg=t["bg"],
                 fg=t["text_secondary"]).pack(anchor="w")
        spin_sim = ttk.Spinbox(dialog, from_=0, to=60, width=10)
        spin_sim.set(0)
        spin_sim.pack(anchor="w", pady=(0, 10))

        info_bg = "#1E3A2B" if self.current_theme.get() == "Темна" else "#E8F5E9"
        info_fg = "#66BB6A" if self.current_theme.get() == "Темна" else "#1B5E20"

        info_f = tk.Frame(dialog, bg=info_bg, padx=10, pady=10)
        info_f.pack(fill="x", pady=(0, 15))
        tk.Label(info_f, text="Безкоштовно: 14 днів.\nПонад 14 днів = 100 грн штрафу за кожен день.",
                 font=("Segoe UI", 8, "bold"), bg=info_bg, fg=info_fg).pack(anchor="w")

        def submit():
            if not cb_books.get() or not cb_readers.get():
                return messagebox.showwarning("Помилка", "Заповніть усі поля!", parent=dialog)
            b_id = int(cb_books.get().split(":")[0])
            r_id = int(cb_readers.get().split(":")[0])
            sim_days = int(spin_sim.get() or 0)

            ok, msg = self.lib.issue_book(b_id, r_id, simulate_days_ago=sim_days)
            if ok:
                messagebox.showinfo("Успіх", msg, parent=dialog)
                self.refresh_all()
                dialog.destroy()

        btn_f = tk.Frame(dialog, bg=t["bg"])
        btn_f.pack(fill="x")
        ttk.Button(btn_f, text="Скасувати", command=dialog.destroy).pack(side="left")
        ttk.Button(btn_f, text="Видати книгу", style="Accent.TButton", command=submit).pack(side="right")

    # --- МОЇ КНИГИ ---
    def _setup_my_books_page(self):
        p = self.pages["my_books"]

        self.hdr_my = tk.Frame(p, padx=15, pady=15, bd=1, relief="solid")
        self.hdr_my.pack(fill="x", pady=(0, 15))

        self.lbl_reader_avatar = tk.Label(self.hdr_my)
        self.lbl_reader_avatar.pack(side="left", padx=(0, 15))

        self.info_f_my = tk.Frame(self.hdr_my)
        self.info_f_my.pack(side="left", fill="both", expand=True)

        self.lbl_my_name = tk.Label(self.info_f_my, text="", font=("Segoe UI", 14, "bold"))
        self.lbl_my_name.pack(anchor="w")

        self.lbl_my_details = tk.Label(self.info_f_my, text="", font=("Segoe UI", 9))
        self.lbl_my_details.pack(anchor="w")

        self.lbl_my_debt = tk.Label(self.hdr_my, text="", font=("Segoe UI", 12, "bold"), padx=10, pady=5)
        self.lbl_my_debt.pack(side="right")

        cols = ("rec_id", "title", "author", "due_date", "fine")
        self.tree_my_books = ttk.Treeview(p, columns=cols, show="headings")
        for c, h, w in [("rec_id", "ID Запису", 70), ("title", "Назва книги", 240), ("author", "Автор", 160),
                        ("due_date", "Термін повернення", 120), ("fine", "Поточний штраф", 110)]:
            self.tree_my_books.heading(c, text=h)
            self.tree_my_books.column(c, width=w, anchor="center" if c in ["rec_id", "due_date", "fine"] else "w")
        self.tree_my_books.pack(fill="both", expand=True, pady=(0, 10))

        btn_bar = tk.Frame(p)
        btn_bar.pack(fill="x")
        ttk.Button(btn_bar, text="💳 Сплатити штраф онлайн", style="Accent.TButton",
                   command=self._pay_fine_online_action).pack(side="right")

    def refresh_my_books(self):
        self.tree_my_books.delete(*self.tree_my_books.get_children())
        reader = next((r for r in self.lib._readers if r.reader_id == self.active_reader_id.get()), None)

        if not reader:
            return

        t = self.themes[self.current_theme.get()]
        self.hdr_my.configure(bg=t["card_bg"])
        self.info_f_my.configure(bg=t["card_bg"])
        self.lbl_my_name.config(text=f"Профіль: {reader.name}", bg=t["card_bg"], fg=t["fg"])
        self.lbl_my_details.config(text=f"Тел: {reader.phone}  |  Email: {reader.email}", bg=t["card_bg"],
                                   fg=t["text_secondary"])

        img = load_avatar_image(reader.avatar_file, size=(60, 60))
        if img:
            self.lbl_reader_avatar.config(image=img, bg=t["card_bg"])
            self.lbl_reader_avatar.image = img

        total_debt = 0
        user_borrows = self.lib.get_user_borrows(reader.reader_id)

        for rec in user_borrows:
            fine = rec.calculate_fine()
            total_debt += fine
            fine_str = f"{fine} грн ⚠️" if fine > 0 else "0 грн ✅"
            self.tree_my_books.insert("", "end", values=(rec.record_id, rec.book.title, rec.book.author,
                                                         rec.due_date.strftime("%d.%m.%Y"), fine_str))

        debt_bg = "#3A1E1E" if self.current_theme.get() == "Темна" else "#FFF5F5"
        debt_fg = "#EF5350" if self.current_theme.get() == "Темна" else "#C5221F"
        self.lbl_my_debt.config(text=f"Борг: {total_debt} грн", bg=debt_bg, fg=debt_fg)

    def _pay_fine_online_action(self):
        sel = self.tree_my_books.selection()
        if not sel: return messagebox.showwarning("Увага", "Оберіть запис із заборгованістю!")
        rec_id = int(self.tree_my_books.item(sel[0])["values"][0])

        ok, msg = self.lib.pay_reader_fine_online(rec_id)
        if ok:
            messagebox.showinfo("Оплата успішна", msg)
            self.refresh_all()
        else:
            messagebox.showwarning("Помилка оплати", msg)

    # --- НАЛАШТУВАННЯ ТА ЗМІНА ТЕМИ ---
    def _setup_settings_page(self):
        p = self.pages["settings"]

        tk.Label(p, text="СИСТЕМА", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(p, text="Налаштування бібліотеки", font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 15))

        f_theme = tk.LabelFrame(p, text=" Тема інтерфейсу ", font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        f_theme.pack(fill="x", pady=(0, 15))

        tk.Label(f_theme, text="Оберіть тему оформлення:").pack(side="left", padx=(0, 10))
        cb_theme = ttk.Combobox(f_theme, textvariable=self.current_theme, values=["Світла", "Темна"], state="readonly",
                                width=12)
        cb_theme.pack(side="left")
        cb_theme.bind("<<ComboboxSelected>>", lambda e: self._apply_theme())

        f_set = tk.LabelFrame(p, text=" Параметри системних штрафів ", font=("Segoe UI", 10, "bold"), padx=15, pady=15)
        f_set.pack(fill="x", pady=(0, 15))

        tk.Label(f_set, text="Безкоштовний термін видачі:").grid(row=0, column=0, sticky="e", pady=5)
        tk.Label(f_set, text="14 днів", font=("Segoe UI", 9, "bold")).grid(row=0, column=1, sticky="w", padx=10, pady=5)

        tk.Label(f_set, text="Розмір штрафу за 1 день:").grid(row=1, column=0, sticky="e", pady=5)
        tk.Label(f_set, text="100 грн / день", font=("Segoe UI", 9, "bold"),
                 fg="#EF5350" if self.current_theme.get() == "Темна" else "#C5221F").grid(row=1, column=1, sticky="w",
                                                                                          padx=10, pady=5)

        tk.Label(f_set, text="Поточний курс долара (НБУ):").grid(row=2, column=0, sticky="e", pady=5)
        tk.Label(f_set, text=f"1 USD = {USD_RATE} UAH", font=("Segoe UI", 9, "bold"),
                 fg="#66BB6A" if self.current_theme.get() == "Темна" else "#2E7D32").grid(row=2, column=1, sticky="w",
                                                                                          padx=10, pady=5)


# --- ТОЧКА ВХОДУ ---
if __name__ == "__main__":
    library = Library("Central Library")

    books_data = [
        (101, "Місто", "Валер'ян Підмогильний", 1928, "Роман", "Історія молодого селянина Степана Радченка."),
        (102, "Тигролови", "Іван Багряний", 1944, "Пригоди",
         "Роман про втечу политичного в'язня Григорія Многогрішного."),
        (103, "Кайдашева сім'я", "Іван Нечуй-Левицький", 1879, "Повість", "Повість про родинні конфлікти та побут."),
        (104, "Лісова пісня", "Леся Українка", 1911, "Драма", "Драма-феєрія про кохання Мавки та Лукаша."),
        (105, "Кобзар", "Тарас Шевченко", 1840, "Поезія", "Збірка поетичних творів Кобзаря."),
        (106, "Тіні забутих предків", "Михайло Коцюбинський", 1911, "Повість",
         "Історія гуцульського кохання Івана та Марічки."),
        (107, "Залишенець. Чорний Ворон", "Василь Шкляр", 2009, "Роман",
         "Роман про боротьбу повстанців Холодного Яру."),
        (108, "Фелікс Австрія", "Софія Андрухович", 2014, "Роман",
         "Таємнича історія взаємин двох жінок у Станіславові."),
        (109, "Інтернат", "Сергій Жадан", 2017, "Роман", "Історія вчителя Паші на тлі фронтових подій."),
        (110, "Сузір’я дів", "Мирослав Лаюк", 2018, "Роман", "Захоплива родинна сага кілька поколінь."),
        (111, "Захар Беркут", "Іван Франко", 1883, "Повість", "Історична повість про тухольську громаду."),
        (112, "Волинь", "Улас Самчук", 1934, "Роман", "Трилогія про життя українського села."),
        (113, "Я (Романтика)", "Микола Хвильовий", 1924, "Повість", "Новела про роздвоєння особистості."),
        (114, "Собор", "Олесь Гончар", 1968, "Роман", "Роман про збереження духовної спадщини."),
        (115, "Маруся Чурай", "Ліна Костенко", 1979, "Поезія", "Історичний роман у віршах."),
        (116, "Чорна рада", "Пантелеймон Куліш", 1857, "Роман", "Перший український історичний роман."),
        (117, "Земля", "Ольга Кобилянська", 1902, "Роман", "Соціально-психологічний роман про владу землі."),
        (118, "Перехресні стежки", "Іван Франко", 1900, "Роман", "Роман про чесного адвоката Рафаловича."),
        (119, "Марія", "Улас Самчук", 1933, "Роман", "Перший роман про Голодомор."),
        (120, "Хіба ревуть воли, як ясла повні?", "Панас Мирний", 1880, "Роман", "Історія Чіпки Варениченка."),
        (121, "Українські джури", "Володимир Рутківський", 2007, "Пригоди",
         "Пригодницька трилогія про молодих козаків."),
        (122, "Енеїда", "Іван Котляревський", 1798, "Поезія", "Перший твір нової української літератури."),
        (123, "Мойсей", "Іван Франко", 1905, "Поезія", "Філософська poema про провідника народу."),
        (124, "Intermezzo", "Михайло Коцюбинський", 1908, "Повість", "Психологічна новела про втому і відновлення."),
        (125, "Палач", "Микола Хвильовий", 1926, "Повість", "Психологічний розріз епохи."),
        (126, "Холодний Яр", "Юрій Горліс-Горський", 1937, "Пригоди", "Спогади про визвольну боротьбу."),
        (127, "Жовтий князь", "Василь Барка", 1962, "Роман", "Роман про Голодомор 1932-1933 років."),
        (128, "Сад Гетсиманський", "Іван Багряний", 1950, "Роман", "Роман про стійкість людини в жорновах репресій."),
        (129, "Диво", "Павло Загребельний", 1968, "Роман", "Історичний роман про Київську Русь."),
        (130, "Роксоляна", "Павло Загребельний", 1980, "Роман", "Історія української дівчини на османському престолі."),
        (131, "Перверзія", "Юрій Андрухович", 1996, "Роман", "Постмодерністський роман про Венецію."),
        (132, "Ворошиловград", "Сергій Жадан", 2010, "Роман", "Роман про повернення до рідного Донбасу."),
        (133, "Солодка Даруся", "Марія Матіос", 2004, "Роман", "Драма буковинського села."),
        (134, "Музеї покинутих секретів", "Оксана Забужко", 2009, "Роман", "Масштабне дослідження трьох поколінь."),
        (135, "Танго смерті", "Юрій Винничук", 2012, "Роман", "Роман про передвоєнний та воєнний Львів."),
        (136, "Класика на ніч", "Максим Рильський", 1940, "Поезія", "Лірична збірка поезій."),
        (137, "Століття Якова", "Володимир Лис", 2010, "Роман", "Історія поліщука Якова, що прожив 100 років."),
        (138, "Амадока", "Софія Андрухович", 2020, "Роман", "Роман про пам'ять, любов та втрату."),
        (139, "Класики жанру", "Лесь Подерв'янський", 2001, "Драма", "Сатиричні п'єси."),
        (140, "Баборня", "Мирослав Лаюк", 2016, "Роман", "Історія вчительки біології та її таємниць."),
        (141, "Спитайте Мієчку", "Євгенія Кузнєцова", 2021, "Роман", "Затишна історія про літо в селі."),
        (142, "Драбина", "Євгенія Кузнєцова", 2023, "Роман", "Сучасний роман про життя біженців."),
        (143, "Записки українського самашедшого", "Ліна Костенко", 2010, "Роман", "Прозаїчний дебют великої поетеси."),
        (144, "Казковий світ", "Володимир Нестайко", 1979, "Пригоди", "Дитячі та юнацькі пригоди."),
        (145, "Тореадори з Васюківки", "Володимир Нестайко", 1963, "Пригоди",
         "Весела та захоплива трилогія для підлітків."),
        (146, "Ніч перед Різдвом", "Микола Гоголь", 1832, "Повість", "Класична казкова повість."),
        (147, "Тарас Бульба", "Микола Гоголь", 1835, "Повість", "Епічна повість про козацтво."),
        (148, "Війна та мир", "Лев Толстой", 1869, "Роман", "Масштабне історичне полотно."),
        (149, "Анна Кареніна", "Лев Толстой", 1877, "Роман", "Психологічна драма кохання."),
        (150, "Злочин і кара", "Федір Достоєвський", 1866, "Роман", "Філософський психологічний роман.")
    ]

    for b in books_data:
        library.add_book(Book(b[0], b[1], b[2], b[3], b[4], b[5]))

    readers_data = [
        Reader(1, "Іван Петренко", "+380671112233"),
        Reader(2, "Марія Коваленко", "+380509998877"),
        Reader(3, "Олександр Бойко", "+380633334455"),
        Reader(4, "Олена Шевченко", "+380975556677"),
        Reader(5, "Дмитро Ткаченко", "+380931234567"),
        Reader(6, "Наталія Бондаренко", "+380501112244"),
        Reader(7, "Андрій Кравченко", "+380672223355"),
        Reader(8, "Вікторія Клименко", "+380634445566"),
        Reader(9, "Сергій Мороз", "+380958889900"),
        Reader(10, "Тетяна Лисенко", "+380987776655")
    ]
    for r in readers_data:
        library.register_reader(r)

    # Стартові прострочені видачі
    library.issue_book(101, 2, simulate_days_ago=5)
    library.issue_book(102, 1, simulate_days_ago=20)  # Штраф 600 грн
    library.issue_book(105, 3, simulate_days_ago=17)  # Штраф 300 грн

    root = tk.Tk()
    app = LibraryApp(root, library)
    root.mainloop()