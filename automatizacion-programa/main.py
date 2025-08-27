import argparse
import time
import pyautogui as pag
import pyperclip

def open_calculator_via_run():
    print("[1/3] Abriendo Calculadora con Win+R...")
    pag.hotkey("win", "r")
    time.sleep(0.6)
    pag.typewrite("calc")
    time.sleep(0.2)
    pag.press("enter")

def type_and_eval(expr: str):
    print(f"[2/3] Ejecutando expresión: {expr}")
    pyperclip.copy(expr)
    pag.hotkey("ctrl", "v")
    time.sleep(0.2)
    pag.press("enter")

def close_calculator():
    print("[3/3] Cerrando Calculadora (Alt+F4)...")
    time.sleep(0.6)  # deja ver el resultado un instante
    pag.hotkey("alt", "f4")

def main():
    ap = argparse.ArgumentParser(description="Automatización Calculadora (Windows)")
    ap.add_argument("--expr", default="123+45", help="Expresión a evaluar (ej: 256*4)")
    ap.add_argument("--delay", type=float, default=0.6, help="Pausa global entre acciones (seg)")
    args = ap.parse_args()

    # Config de PyAutoGUI
    pag.FAILSAFE = True          # mover el mouse a la esquina sup-izq para abortar
    pag.PAUSE = args.delay

    open_calculator_via_run()
    time.sleep(1.2)              # tiempo para que se abra
    type_and_eval(args.expr)
    close_calculator()
    print("[OK] Proceso completado.")

if __name__ == "__main__":
    main()
