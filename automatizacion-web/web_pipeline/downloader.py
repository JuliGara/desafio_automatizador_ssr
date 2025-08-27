import os, time, json, re
from typing import List, Tuple, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Descarga de archivos XLSX/CSV desde web con Selenium
def make_driver(download_dir:str, headless:bool=True):
    os.makedirs(download_dir,exist_ok=True)
    o=Options()
    if headless: o.add_argument("--headless=new")
    o.add_argument("--no-sandbox"); o.add_argument("--disable-dev-shm-usage"); o.add_argument("--disable-gpu")
    o.add_argument("--log-level=3"); o.add_argument("--disable-extensions")
    o.add_experimental_option("excludeSwitches", ["enable-logging","enable-automation"])
    o.add_experimental_option("useAutomationExtension", False)
    o.add_experimental_option("prefs",{
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    try:
        svc=Service(ChromeDriverManager().install(), log_output=os.devnull)
    except TypeError:
        svc=Service(ChromeDriverManager().install())
    d=webdriver.Chrome(service=svc, options=o)
    d.set_window_size(1400,900)
    return d

def _snapshot(dirpath):
    return {f for f in os.listdir(dirpath) if os.path.isfile(os.path.join(dirpath, f))}

# Espera archivo nuevo en dirpath modificado después de 'before' (timestamp)
def wait_for_new_file(dirpath,before,exts=None,timeout=35):
    exts=[e.lower() for e in (exts or [])] if exts else []
    end=time.time()+timeout
    while time.time()<end:
        c=[]
        for f in os.listdir(dirpath):
            p=os.path.join(dirpath,f)
            if os.path.isfile(p) and os.path.getmtime(p)>before and (not exts or any(f.lower().endswith(x) for x in exts)):
                if not f.endswith(".crdownload"): c.append(p)
        if c:
            c.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return c[0]
        time.sleep(0.2)
    return None

# Espera archivo nuevo en dirpath que no esté en before_names
def wait_for_new_file_by_name(dirpath, before_names, timeout=25):
    end = time.time() + timeout
    while time.time() < end:
        after = _snapshot(dirpath)
        new_names = [f for f in after if f not in before_names and not f.endswith(".crdownload")]
        if new_names:
            paths = [os.path.join(dirpath, f) for f in new_names]
            paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return paths[0]
        time.sleep(0.2)
    return None

# Detecta si hay formulario de login en la página actual
def is_login_present(d):
    try:
        if d.find_elements(By.CSS_SELECTOR,"#password, input[type='password']"): return True
    except: pass
    u=(d.current_url or "").lower()
    return any(k in u for k in ["/login","signin","ingresar","acceder"])

# Intenta login con usuario y contraseña
def try_login(d,u,p):
    def _find(css_list):
        for sel in css_list:
            els=d.find_elements(By.CSS_SELECTOR,sel)
            if els: return els[0]
        return None
    user=_find(["#username","[name='username']","[name='email']","input[type='email']","input[type='text']"])
    pwd=_find(["#password","[name='password']","input[type='password']"])
    if user and pwd:
        user.clear(); user.send_keys(u); pwd.clear(); pwd.send_keys(p)
        btn = _find(["#login-form button[type='submit']","button[type='submit']"])
        if btn:
            btn.click()
            WebDriverWait(d,30).until(lambda x: "/login" not in (x.current_url or "").lower())

# Fuerza click en elemento (scroll + JS fallback)
def force_click(d, el):
    try:
        WebDriverWait(d,10).until(EC.element_to_be_clickable(el))
        try: d.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        except: pass
        el.click()
        return True
    except:
        try: d.execute_script("arguments[0].click();", el); return True
        except: return False

# Descubre botones de descarga en la página principal
def discover_landing_buttons(d):
    btns = WebDriverWait(d,20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,"section button[id^='download-button-']")))
    cards=[]
    for b in btns:
        bid=b.get_attribute("id")
        try:
            h=b.find_element(By.XPATH,"./ancestor::*[self::div or self::article][1]//*[self::h3 or self::h2][1]").text.strip()
        except:
            h=bid
        cards.append((h, f"#{bid}"))
    return cards

def click_landing_button(d, css_sel):
    el=WebDriverWait(d,15).until(EC.presence_of_element_located((By.CSS_SELECTOR,css_sel)))
    return force_click(d, el)

# Intenta descargar desde página de proveedor (checkboxes + botón)
def try_provider_page_download(d,download_dir,exts):
    boxes=d.find_elements(By.CSS_SELECTOR,"#brands-checkboxes input[type='checkbox']")
    if boxes:
        for cb in boxes:
            try:
                if cb.is_displayed() and cb.is_enabled() and not cb.is_selected():
                    d.execute_script("arguments[0].scrollIntoView({block:'center'});",cb); cb.click()
            except: pass
        try:
            btn=d.find_element(By.CSS_SELECTOR,"form button[type='submit'], #price-list-form button[type='submit'], #price-list-form button")
            if force_click(d, btn):
                return wait_for_new_file(download_dir,time.time(),exts,20)
        except: pass
    try:
        btn2=d.find_element(By.CSS_SELECTOR,"button.download-button")
        if force_click(d, btn2):
            return wait_for_new_file(download_dir,time.time(),exts,20)
    except: pass
    try:
        btn3=d.find_element(By.XPATH,"//*[@id='root']/div/div/main/div/div/div[1]/section[1]/div/div/div/div[2]/button")
        if force_click(d, btn3):
            return wait_for_new_file(download_dir,time.time(),exts,20)
    except: pass
    try:
        btn4=WebDriverWait(d,5).until(EC.element_to_be_clickable((By.XPATH,"//button[contains(normalize-space(),'Descargar lista de precios')]")))
        if force_click(d, btn4):
            return wait_for_new_file(download_dir,time.time(),exts,20)
    except: pass
    return None

# Descarga todos los archivos según credenciales y devuelve lista (nombre, path)
def download_all(credentials_path:str, download_dir:str, headless:bool=True) -> List[Tuple[str,str]]:
    with open(credentials_path,"r",encoding="utf-8") as f:
        c=json.load(f)
    base=c.get("base_url","https://desafiodataentryait.vercel.app/")
    u=(c.get("username") or "").strip(); p=(c.get("password") or "").strip()

    d=make_driver(download_dir,headless=headless)
    results=[]
    try:
        d.get(base); time.sleep(0.7)
        cards=discover_landing_buttons(d)
        if not cards: raise RuntimeError("No se encontraron tarjetas de descarga.")
        for name, css_sel in cards:
            name = re.sub(r'(?i)^#?download[-_]?button[-_]?', '', str(name).strip())
            print(f"[{name}] -> Downloading soon...")
            d.get(base); time.sleep(0.7)
            t0=time.time()
            before_names = _snapshot(download_dir)
            try:
                click_landing_button(d, css_sel)
            except:
                d.get(base); time.sleep(0.7); click_landing_button(d, css_sel)
            path=wait_for_new_file(download_dir,t0,[".xlsx",".xls",".csv"],35)
            if not path and is_login_present(d) and u and p:
                try_login(d,u,p); time.sleep(0.8)
                path=wait_for_new_file(download_dir,time.time(),[".xlsx",".xls",".csv"],20)
                if not path: path=try_provider_page_download(d,download_dir,[".xlsx",".xls"])
            if not path: path=try_provider_page_download(d,download_dir,[".xlsx",".xls"])
            if not path:
                path = wait_for_new_file_by_name(download_dir, before_names, timeout=25)
            if not path:
                print("[ERROR] No se pudo descargar el archivo."); continue
            print(f"[DESCARGA] {path}")
            results.append((name, path))
    finally:
        try: d.quit()
        except: pass
    return results

if __name__=="__main__":
    import argparse, os
    a=argparse.ArgumentParser()
    a.add_argument("--credentials",default="credentials.json")
    a.add_argument("--download_dir",default="./data/raw")
    a.add_argument("--headless",type=lambda x:x.lower()=="true",default=True)
    args=a.parse_args()
    os.makedirs(args.download_dir,exist_ok=True)
    files=download_all(args.credentials,args.download_dir,headless=args.headless)
    for name, path in files:
        print(name, "->", path)
