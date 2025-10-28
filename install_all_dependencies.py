import subprocess
import sys
import platform

# Список всіх необхідних пакетів
packages = [
    "httpx",
    "playwright",
    "asyncio",
    "fake_useragent",
    "pyee",
    "greenlet",
    "typing-extensions"
]

is_windows = platform.system().lower() == "windows"

# Встановлюємо всі пакети через pip
for pkg in packages:
    print(f"Встановлюємо {pkg}...")
    if is_windows:
        subprocess.run([sys.executable, "-m", "pip", "install", pkg], shell=True)
    else:
        subprocess.run([sys.executable, "-m", "pip", "install", pkg, "--break-system-packages"])

# Додатково встановлюємо браузери для Playwright
try:
    import playwright
    print("Встановлюємо браузери Playwright...")
    if is_windows:
        subprocess.run([sys.executable, "-m", "playwright", "install"], shell=True)
    else:
        subprocess.run([sys.executable, "-m", "playwright", "install"])
except ImportError:
    print("Playwright не встановлено, пропускаємо установку браузерів.")

if is_windows:
    print("\nЯкщо виникнуть проблеми з правами, запустіть цей скрипт від імені адміністратора.")
    print("\nЯкщо pip не знайдено, додайте Python та pip у PATH.")

print("✅ Всі залежності встановлені!")
