try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import argparse
import os
import platform
import re
import sys
import threading
import time
from datetime import datetime

# Optional .env loader
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# GUI availability detection
GUI_AVAILABLE = False
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    if platform.system() == "Linux" and not os.environ.get("DISPLAY"):
        GUI_AVAILABLE = False
    else:
        GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False

import pandas as pd
import pyodbc

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ===================== CONFIG =====================
REQUEST_TIMEOUT = 90
WAIT_FOR_TABLE_S = 45
WAIT_FOR_LOGIN_S = 45
VALID_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")

# Footballguys login page candidates
FBG_LOGIN_URLS = [
    "https://www.footballguys.com/login",
    "https://www.footballguys.com/account/login",
    "https://www.footballguys.com/subscribers/login",
]

EMAIL_SELECTORS = [
    (By.CSS_SELECTOR, "input[type='email']"),
    (By.NAME, "email"),
    (By.ID, "email"),
    (By.CSS_SELECTOR, "input[name='username']"),
]
PASSWORD_SELECTORS = [
    (By.CSS_SELECTOR, "input[type='password']"),
    (By.NAME, "password"),
    (By.ID, "password"),
]
SUBMIT_SELECTORS = [
    (By.CSS_SELECTOR, "button[type='submit']"),
    (By.XPATH, "//button[contains(., 'Log in') or contains(., 'Sign in')]"),
    (By.XPATH, "//input[@type='submit']"),
]


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


class Logger:
    def __init__(self, tk_text_widget: "tk.Text | None" = None):
        self.tk_text_widget = tk_text_widget

    def log(self, msg: str):
        line = f"[{ts()}] {msg}\n"
        if self.tk_text_widget is not None:
            self.tk_text_widget.insert("end", line)
            self.tk_text_widget.see("end")
            try:
                self.tk_text_widget.update_idletasks()
            except Exception:
                pass
        else:
            print(line, end="")
            sys.stdout.flush()


class FbgScraperWithLogin:
    def __init__(self, table_name: str, log_fn, headless: bool, db_conn_str: str,
                 email: str, password: str, chrome_binary: str | None = None):
        self.table_name = table_name
        self.log = log_fn
        self.conn_str = db_conn_str

        if not email or not password:
            raise RuntimeError("Footballguys login requires email and password. Set FBG_EMAIL/FBG_PASSWORD or pass CLI flags.")

        self._ensure_table()

        chrome_options = Options()
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(REQUEST_TIMEOUT)
        try:
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
            )
        except Exception:
            pass

        self.wait = WebDriverWait(self.driver, WAIT_FOR_TABLE_S)

        self._login(email, password)

    # ---------- DB ----------
    def _ensure_table(self):
        with pyodbc.connect(self.conn_str) as conn:
            cur = conn.cursor()
            cur.execute(
                f"""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{self.table_name}' and xtype='U')
                CREATE TABLE {self.table_name} (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    player_name VARCHAR(120) NOT NULL,
                    position VARCHAR(10) NOT NULL,
                    team VARCHAR(50) NULL,
                    week_num INT NOT NULL,
                    year_num INT NOT NULL,
                    fantasy_points FLOAT NULL,
                    timestamp DATETIME NOT NULL DEFAULT GETDATE(),
                    CONSTRAINT UC_{self.table_name} UNIQUE (player_name, position, week_num, year_num)
                );
                """
            )
            conn.commit()

    # ---------- Login ----------
    def _find_first(self, selectors, timeout=WAIT_FOR_LOGIN_S):
        end = time.time() + timeout
        last_exc = None
        while time.time() < end:
            for by, sel in selectors:
                try:
                    el = self.driver.find_element(by, sel)
                    if el.is_displayed():
                        return el
                except Exception as e:
                    last_exc = e
            time.sleep(0.3)
        if last_exc:
            raise last_exc
        raise RuntimeError("Element not found")

    def _login(self, email: str, password: str):
        ok = False
        for url in FBG_LOGIN_URLS:
            try:
                self.log(f"Opening login page: {url}")
                self.driver.get(url)
                email_el = self._find_first(EMAIL_SELECTORS)
                pwd_el = self._find_first(PASSWORD_SELECTORS)
                email_el.clear()
                email_el.send_keys(email)
                pwd_el.clear()
                pwd_el.send_keys(password)
                btn = self._find_first(SUBMIT_SELECTORS)
                btn.click()
                time.sleep(1.0)
                try:
                    _ = self._find_first(EMAIL_SELECTORS, timeout=5)
                    self.log("Login form still present; trying next login URL…")
                    continue
                except Exception:
                    pass
                ok = True
                break
            except Exception as e:
                self.log(f"Login attempt on {url} failed: {e}")
                continue
        if not ok:
            raise RuntimeError("Could not log into Footballguys (check creds or site changes).")
        self.log("Logged into Footballguys.")

    # ---------- Helpers ----------
    @staticmethod
    def _norm_header(h: str) -> str:
        return re.sub(r"\s+", "", h).upper()

    @staticmethod
    def _to_float(s):
        if s is None:
            return None
        s = str(s).strip().replace(",", "")
        if s in {"", "-", "—", "–"}:
            return None
        try:
            return float(s)
        except ValueError:
            m = re.search(r"[-+]?\d+(\.\d+)?", s)
            return float(m.group(0)) if m else None

    def _urls_for(self, position: str, week: int, year: int):
        pos_variants = {
            "qb": ["qb"],
            "flex": ["flex"],
            "def": ["def", "td", "dst"],
        }[position]
        profile_variants = ["fd", None, "0"]
        urls = []
        base = "https://www.footballguys.com/playerhistoricalstats"
        for p in pos_variants:
            for prof in profile_variants:
                q = f"?pos={p}&yr={year}&startwk={week}&stopwk={week}"
                if prof is not None:
                    q += f"&profile={prof}"
                urls.append(base + q)
        return urls

    def _load_table_from_any_variant(self, position: str, week: int, year: int):
        last_err = None
        for url in self._urls_for(position, week, year):
            try:
                self.log(f"FBG try → {url}")
                self.driver.get(url)
                page = self.driver.page_source.lower()
                if "oops!" in page or "error has occurred" in page:
                    self.log("FBG returned its error page on this variant.")
                    continue
                table = WebDriverWait(self.driver, WAIT_FOR_TABLE_S).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                WebDriverWait(self.driver, WAIT_FOR_TABLE_S).until(
                    lambda d: len(table.find_elements(By.TAG_NAME, "tr")) > 1
                )
                return table
            except Exception as e:
                last_err = e
                self.log(f"Variant failed: {e}")
        raise RuntimeError(f"No working FBG variant for {position.upper()} Week {week} {year}: {last_err}")

    def _scrape_position(self, position: str, week: int, year: int) -> pd.DataFrame:
        table = self._load_table_from_any_variant(position, week, year)
        headers = [self._norm_header(th.text) for th in table.find_elements(By.TAG_NAME, "th")]
        rows = []
        for tr in table.find_elements(By.TAG_NAME, "tr")[1:]:
            tds = tr.find_elements(By.TAG_NAME, "td")
            if not tds:
                continue
            cells = [td.text.strip() for td in tds]
            if not cells:
                continue
            row = dict(zip(headers, cells))
            name = row.get("NAME") or row.get("PLAYER") or ""
            team = row.get("TEAM") or row.get("NFL") or ""
            pos_from_row = row.get("POS") or ""
            pts = row.get("FANTPT") or row.get("FPTS") or row.get("PTS") or ""
            if position == "def":
                final_pos = "DEF"
                if not team:
                    team_guess = name.replace("DST", "").replace("Defense", "").strip()
                    team = re.sub(r"\s{2,}", " ", team_guess)
            else:
                final_pos = pos_from_row.upper() if (position == "flex" and pos_from_row) else position.upper()
            rows.append(
                {
                    "player_name": name,
                    "team": team,
                    "position": final_pos,
                    "week_num": week,
                    "year_num": year,
                    "fantasy_points": self._to_float(pts),
                }
            )
        df = pd.DataFrame(rows)
        self.log(f"FBG rows: {len(df)} for {position.upper()}")
        return df

    def _merge_batch(self, df: pd.DataFrame):
        if df is None or df.empty:
            return
        cols = ["player_name", "position", "team", "week_num", "year_num", "fantasy_points"]
        df = df[cols].copy()
        with pyodbc.connect(self.conn_str) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                IF OBJECT_ID('tempdb..#stage_stats') IS NOT NULL DROP TABLE #stage_stats;
                CREATE TABLE #stage_stats (
                    player_name VARCHAR(120),
                    position    VARCHAR(10),
                    team        VARCHAR(50),
                    week_num    INT,
                    year_num    INT,
                    fantasy_points FLOAT
                );
                """
            )
            conn.commit()
            cur.fast_executemany = True
            cur.executemany(
                "INSERT INTO #stage_stats (player_name, position, team, week_num, year_num, fantasy_points) VALUES (?, ?, ?, ?, ?, ?);",
                df.itertuples(index=False, name=None),
            )
            conn.commit()
            cur.execute(
                f"""
                MERGE {self.table_name} AS target
                USING (SELECT player_name, position, team, week_num, year_num, fantasy_points FROM #stage_stats) AS src
                ON  target.player_name = src.player_name
                AND target.position    = src.position
                AND target.week_num    = src.week_num
                AND target.year_num    = src.year_num
                WHEN MATCHED THEN UPDATE SET
                    target.team = src.team,
                    target.fantasy_points = src.fantasy_points,
                    target.timestamp = GETDATE()
                WHEN NOT MATCHED THEN INSERT (player_name, position, team, week_num, year_num, fantasy_points)
                VALUES (src.player_name, src.position, src.team, src.week_num, src.year_num, src.fantasy_points);
                """
            )
            conn.commit()

    def scrape_week(self, week: int, year: int = 2025) -> pd.DataFrame:
        positions = ["qb", "flex", "def"]
        start = datetime.now()
        self.log(f"Starting scrape at {start}")
        frames = []
        try:
            for pos in positions:
                self.log(f"Scraping {pos.upper()} | Week {week} | Year {year}")
                df = self._scrape_position(pos, week, year)
                if not df.empty:
                    frames.append(df)
                time.sleep(0.6)
            if frames:
                all_df = pd.concat(frames, ignore_index=True)
                all_df.drop_duplicates(subset=["player_name", "position", "week_num", "year_num"], inplace=True)
                self._merge_batch(all_df)
                self.log(f"Saved {len(all_df)} rows.")
                return all_df
            else:
                self.log("No data scraped (FBG variants all failed).")
                return pd.DataFrame()
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.log(f"Scrape completed in {datetime.now() - start}")


def build_default_conn_str() -> str:
    env_conn = os.getenv("DB_CONN_STR")
    if env_conn:
        return env_conn
    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=TonyDB;"
        "Trusted_Connection=yes;"
        "Connection Timeout=5;"
    )


def run_cli():
    parser = argparse.ArgumentParser(description="Footballguys Stats Scraper")
    parser.add_argument("--week", type=int, default=int(os.getenv("WEEK", "1")))
    parser.add_argument("--year", type=int, default=int(os.getenv("YEAR", "2025")))
    parser.add_argument("--table", type=str, default=os.getenv("TABLE_NAME", "FootballStats"))
    parser.add_argument("--headless", action="store_true", default=os.getenv("HEADLESS", "false").lower() == "true")
    parser.add_argument("--email", type=str, default=os.getenv("FBG_EMAIL", ""))
    parser.add_argument("--password", type=str, default=os.getenv("FBG_PASSWORD", ""))
    parser.add_argument("--db-conn-str", type=str, default=os.getenv("DB_CONN_STR", ""))
    parser.add_argument("--chrome-binary", type=str, default=os.getenv("CHROME_BINARY", ""))
    parser.add_argument("--out-csv", type=str, default=os.getenv("OUT_CSV", ""), help="Optional: save results to CSV as well")
    args = parser.parse_args()

    if not (1 <= args.week <= 20):
        print("Week must be 1–20", file=sys.stderr)
        sys.exit(2)
    if not VALID_TABLE_RE.match(args.table):
        print("Invalid table name (letters/numbers/underscore; start with letter/_)", file=sys.stderr)
        sys.exit(2)

    logger = Logger()
    log = logger.log

    conn_str = args.db_conn_str if args.db_conn_str else build_default_conn_str()
    chrome_bin = args.chrome_binary if args.chrome_binary else None

    log(
        f"Starting scrape for Week {args.week}, Year {args.year}, Table '{args.table}' (headless={args.headless})"
    )
    scraper = FbgScraperWithLogin(
        table_name=args.table,
        log_fn=log,
        headless=args.headless,
        db_conn_str=conn_str,
        email=args.email,
        password=args.password,
        chrome_binary=chrome_bin,
    )
    df = scraper.scrape_week(args.week, args.year)
    if args.out_csv:
        out_path = os.path.abspath(args.out_csv)
        df.to_csv(out_path, index=False)
        log(f"Saved CSV: {out_path}")


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Footballguys Stats Scraper (With Login)")
        self.root.geometry("980x720")
        self.root.minsize(880, 640)
        self.root.update_idletasks()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        ww, wh = self.root.winfo_width(), self.root.winfo_height()
        x = (sw - ww) // 2
        y = (sh - wh) // 2
        self.root.geometry(f"{ww}x{wh}+{x}+{y}")

        style = ttk.Style()
        style.configure("TLabel", padding=5)
        style.configure("TButton", padding=5)

        main = ttk.Frame(self.root, padding="14")
        main.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        ttk.Label(main, text="Select Week (1-20):").grid(row=0, column=0, sticky="w")
        self.week_var = tk.StringVar(value="1")
        cb = ttk.Combobox(
            main,
            textvariable=self.week_var,
            values=[str(i) for i in range(1, 21)],
            width=6,
            state="readonly",
        )
        cb.grid(row=0, column=1, sticky="w")
        cb.bind("<<ComboboxSelected>>", self._note_playoffs)
        ttk.Label(main, text="Regular: 1–18  |  Playoffs: 19–20").grid(row=0, column=2, sticky="w")

        ttk.Label(main, text="Year (e.g., 2025):").grid(row=1, column=0, sticky="w")
        self.year_var = tk.StringVar(value="2025")
        ttk.Entry(main, textvariable=self.year_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(main, text="Table Name:").grid(row=2, column=0, sticky="w")
        self.table_name = tk.StringVar(value="FootballStats")
        ttk.Entry(main, textvariable=self.table_name, width=30).grid(
            row=2, column=1, columnspan=2, sticky="we"
        )

        self.headless_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main, text="Run headless (not recommended for FBG)", variable=self.headless_var
        ).grid(row=1, column=2, sticky="w")

        self.logbox = tk.Text(main, height=22, width=110)
        self.logbox.grid(row=3, column=0, columnspan=3, pady=10, sticky="nsew")
        main.rowconfigure(3, weight=1)
        for c in (0, 1, 2):
            main.columnconfigure(c, weight=1)
        sb = ttk.Scrollbar(main, orient="vertical", command=self.logbox.yview)
        sb.grid(row=3, column=3, sticky="ns")
        self.logbox["yscrollcommand"] = sb.set

        btm = ttk.Frame(main)
        btm.grid(row=4, column=0, columnspan=3, pady=8, sticky="e")
        self.start_btn = ttk.Button(btm, text="Start Scraping", command=self._start)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btm, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=5)

        self.logger = Logger(self.logbox)

    def log(self, msg):
        self.logger.log(msg)

    def _note_playoffs(self, *_):
        try:
            if int(self.week_var.get()) > 18:
                self.log("Note: Selected week is in playoff period.")
        except ValueError:
            pass

    def _start(self):
        tbl = self.table_name.get().strip()
        if not tbl:
            return messagebox.showerror("Error", "Please enter a table name")
        if not VALID_TABLE_RE.match(tbl):
            return messagebox.showerror(
                "Error", "Invalid table name (letters/numbers/underscore; start with letter/_)"
            )
        try:
            week = int(self.week_var.get())
            year = int(self.year_var.get())
        except ValueError:
            return messagebox.showerror("Error", "Week and Year must be numbers")
        if not (1 <= week <= 20):
            return messagebox.showerror("Error", "Week must be 1–20")
        if week > 18 and not messagebox.askyesno("Confirm", f"Week {week} is playoffs. Proceed?"):
            return

        self.logbox.delete(1.0, tk.END)
        self.log(
            f"Starting scrape for Week {week}, Year {year}, Table '{tbl}' (headless={self.headless_var.get()})"
        )
        self.start_btn.state(["disabled"])
        threading.Thread(
            target=self._run, args=(tbl, week, year, self.headless_var.get()), daemon=True
        ).start()

    def _run(self, tbl, week, year, headless):
        try:
            email = os.getenv("FBG_EMAIL", "")
            pwd = os.getenv("FBG_PASSWORD", "")
            conn_str = build_default_conn_str()
            chrome_bin = os.getenv("CHROME_BINARY") or None
            s = FbgScraperWithLogin(
                tbl, self.log, headless=headless, db_conn_str=conn_str, email=email, password=pwd, chrome_binary=chrome_bin
            )
            s.scrape_week(week, year)
            self.log("Scraping completed!")
        except Exception as e:
            self.log(f"Error: {e}")
            try:
                messagebox.showerror("Error", f"{e}")
            except Exception:
                pass
        finally:
            self.start_btn.state(["!disabled"])


def main():
    use_gui = GUI_AVAILABLE and os.getenv("USE_GUI", "true").lower() == "true"
    if use_gui:
        try:
            app = App()
            app.root.mainloop()
            return
        except Exception as e:
            print(f"GUI failed to start, falling back to CLI: {e}", file=sys.stderr)
    run_cli()


if __name__ == "__main__":
    main()

