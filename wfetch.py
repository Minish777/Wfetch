#!/usr/bin/env python3
"""
Wfetch - Минималистичный системный fetch
Исправленная версия с рабочим конфигом
"""

import sys
import platform
import os
import json
import random
import time
import hashlib
import socket
import subprocess
from pathlib import Path
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# ============= ЛОГОТИПЫ =============
W_LOGO = [
    "██╗    ██╗",
    "██║    ██║", 
    "██║ █╗ ██║",
    "██║███╗██║",
    "╚███╔███╔╝",
    " ╚══╝╚══╝ ",
]

ALT_LOGO = [
    " __        _________  __",
    " \\ \\      / / ____\\ \\/ /",
    "  \\ \\ /\\ / /|  _|  \\  /", 
    "   \\ V  V / | |___ /  \\",
    "    \\_/\\_/  |_____/_/\\_\\",
    "                         ",
]

def get_logo(alt_chance=15):
    """Получить логотип"""
    return ALT_LOGO if random.random() < (alt_chance / 100) else W_LOGO

# ============= ЦВЕТА =============
class Colors:
    RESET = "\033[0m"
    
    @staticmethod
    def ansi(code):
        return f"\033[38;5;{code}m"
    
    @staticmethod
    def get_color_scheme(random_colors=True):
        """Получить цветовую схему"""
        if random_colors:
            schemes = [
                {"primary": 213, "secondary": 117, "accent": 141, "text": 250, "highlight": 84},
                {"primary": 208, "secondary": 45, "accent": 220, "text": 248, "highlight": 82},
                {"primary": 129, "secondary": 212, "accent": 225, "text": 252, "highlight": 48},
                {"primary": 42, "secondary": 39, "accent": 51, "text": 247, "highlight": 46},
            ]
            return random.choice(schemes)
        else:
            return {"primary": 213, "secondary": 117, "accent": 141, "text": 250, "highlight": 84}

# ============= КОНФИГ =============
def get_config_path():
    """Получить путь к конфиг файлу"""
    if platform.system() == "Windows":
        base = os.environ.get('APPDATA', '')
        config_dir = Path(base) / 'wfetch'
    else:
        config_dir = Path.home() / '.config' / 'wfetch'
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'config.json'

def load_config():
    """Загрузить конфиг - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    config_path = get_config_path()
    
    # Дефолтный конфиг с ВСЕМИ полями
    default_config = {
        "display": {
            "spacing": 2,
            "padding": 0,
            "border": False,
            "compact": False
        },
        "colors": {
            "scheme": "random",
            "primary": 213,
            "secondary": 117,
            "accent": 141,
            "text": 250,
            "highlight": 84
        },
        "info": {
            "os": True,
            "host": True,
            "kernel": True,
            "uptime": True,
            "packages": True,
            "memory": True,
            "shell": True,
            "wm_de": True,
            "cpu": False,
            "terminal": False
        },
        "behavior": {
            "random_colors": True,
            "show_color_bar": True,
            "alt_logo_chance": 15,
            "live_memory": True,
            "windows_packages": False  # На Windows медленно, поэтому false по умолчанию
        }
    }
    
    # Если файла нет - создаем дефолтный
    if not config_path.exists():
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    # Загружаем пользовательский конфиг
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        
        # Глубокое слияние конфигов
        def deep_merge(default, user):
            merged = default.copy()
            for key, value in user.items():
                if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key] = deep_merge(merged[key], value)
                else:
                    merged[key] = value
            return merged
        
        merged_config = deep_merge(default_config, user_config)
        
        # Сохраняем объединенный конфиг обратно
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(merged_config, f, indent=2)
        
        return merged_config
        
    except Exception as e:
        print(f"⚠  Ошибка загрузки конфига: {e}")
        print("⚠  Используется конфиг по умолчанию")
        return default_config

# ============= СБОР ИНФОРМАЦИИ - ИСПРАВЛЕНО =============
def get_os_info():
    """Получить информацию об ОС - ИСПРАВЛЕНО"""
    system = platform.system()
    
    if system == "Linux":
        try:
            with open('/etc/os-release', 'r', encoding='utf-8') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('PRETTY_NAME='):
                        name = line.split('=', 1)[1].strip().strip('"')
                        return name if len(name) <= 30 else name[:27] + "..."
                for line in content.split('\n'):
                    if line.startswith('NAME='):
                        name = line.split('=', 1)[1].strip().strip('"')
                        return f"{name} {platform.release()}"
        except:
            pass
        return f"Linux {platform.release()}"
    
    elif system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            product = winreg.QueryValueEx(key, "ProductName")[0]
            display = winreg.QueryValueEx(key, "DisplayVersion")[0] if platform.release() == "10" else platform.release()
            
            # Чистим название
            product = product.replace("Microsoft ", "").replace("®", "").replace("™", "")
            return f"{product} {display}"
        except:
            # Если не получилось через реестр, используем platform
            win_ver = platform.win32_ver()
            if win_ver[0]:
                return f"Windows {win_ver[0]}"
            return f"Windows {platform.release()}"
    
    elif system == "Darwin":
        try:
            result = subprocess.run(['sw_vers', '-productVersion'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return f"macOS {result.stdout.strip()}"
        except:
            pass
        return f"macOS {platform.mac_ver()[0]}"
    
    return system

def get_kernel():
    """Получить версию ядра - ИСПРАВЛЕНО для Windows"""
    system = platform.system()
    
    if system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            build = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
            ubr = winreg.QueryValueEx(key, "UBR")[0] if platform.release() == "10" else 0
            return f"10.0.{build}.{ubr}" if ubr else f"10.0.{build}"
        except:
            return platform.release()
    
    return platform.release()

def get_packages(config):
    """Получить количество пакетов - ИСПРАВЛЕНО"""
    system = platform.system()
    
    if system == "Linux":
        # Попробуем разные менеджеры пакетов
        managers = [
            ("pacman", "-Qq", "Arch"),
            ("dpkg-query", "-f '.\n' -W", "Debian"),
            ("rpm", "-qa", "RHEL"),
            ("xbps-query", "-l", "Void"),
            ("apk", "info", "Alpine"),
        ]
        
        for cmd, arg, _ in managers:
            try:
                result = subprocess.run([cmd, arg] if arg else [cmd],
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    lines = [l for l in result.stdout.split('\n') if l.strip()]
                    return str(len(lines))
            except:
                continue
        return "?"
    
    elif system == "Windows":
        # На Windows подсчет пакетов медленный, можно отключить
        if not config.get("behavior", {}).get("windows_packages", False):
            return "N/A"
        
        try:
            import winreg
            count = 0
            # Проверяем оба раздела реестра
            for base in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    key = winreg.OpenKey(base, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                    i = 0
                    while True:
                        try:
                            winreg.EnumKey(key, i)
                            count += 1
                            i += 1
                        except OSError:
                            break
                except:
                    continue
            return str(count) if count > 0 else "0"
        except:
            return "?"
    
    elif system == "Darwin":
        try:
            # Проверяем Homebrew
            result = subprocess.run(['brew', 'list'],
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                lines = [l for l in result.stdout.split('\n') if l.strip()]
                return str(len(lines))
        except:
            pass
        return "?"
    
    return "?"

def get_memory(live=False):
    """Получить использование памяти"""
    if not PSUTIL_AVAILABLE:
        return "N/A"
    
    try:
        mem = psutil.virtual_memory()
        used = mem.used / (1024**3)
        total = mem.total / (1024**3)
        percent = mem.percent
        
        if live:
            bar_length = 10
            filled = int(bar_length * percent / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            return f"{used:.1f}/{total:.1f} GB [{bar}]"
        else:
            return f"{used:.1f}/{total:.1f} GB"
    except:
        return "N/A"

def get_shell():
    """Получить текущую shell"""
    if platform.system() == "Windows":
        # Проверяем PowerShell
        if 'PSModulePath' in os.environ:
            return 'PowerShell'
        return 'CMD'
    
    shell = os.environ.get('SHELL', '')
    if shell:
        return Path(shell).name
    
    return 'bash'  # Дефолт для Linux/macOS

def get_wm_de():
    """Получить WM/DE для Linux"""
    if platform.system() != "Linux":
        return ""
    
    de = os.environ.get('XDG_CURRENT_DESKTOP', '') or os.environ.get('DESKTOP_SESSION', '')
    if de:
        de_lower = de.lower()
        if 'kde' in de_lower:
            return "KDE"
        elif 'gnome' in de_lower:
            return "GNOME"
        elif 'xfce' in de_lower:
            return "XFCE"
        return de.split(':')[-1]
    
    return ""

# ============= ОТОБРАЖЕНИЕ =============
def print_wfetch(config):
    """Основная функция отображения"""
    # Получаем цвета
    color_scheme = Colors.get_color_scheme(config["behavior"]["random_colors"])
    colors = {k: Colors.ansi(v) for k, v in color_scheme.items()}
    
    # Получаем логотип
    logo = get_logo(config["behavior"]["alt_logo_chance"])
    
    # Собираем информацию ИЗ КОНФИГА
    info_items = []
    if config["info"]["os"]:
        info_items.append(("OS", get_os_info()))
    if config["info"]["host"]:
        info_items.append(("Host", socket.gethostname().split('.')[0]))
    if config["info"]["kernel"]:
        info_items.append(("Kernel", get_kernel()))
    if config["info"]["uptime"]:
        uptime = get_uptime() if PSUTIL_AVAILABLE else "N/A"
        info_items.append(("Uptime", uptime))
    if config["info"]["packages"]:
        info_items.append(("Packages", get_packages(config)))
    if config["info"]["memory"]:
        info_items.append(("Memory", get_memory(config["behavior"]["live_memory"])))
    if config["info"]["shell"]:
        info_items.append(("Shell", get_shell()))
    if config["info"]["wm_de"]:
        wm_de = get_wm_de()
        if wm_de:
            info_items.append(("WM/DE", wm_de))
    
    # Выравниваем
    max_key_len = max(len(key) for key, _ in info_items) if info_items else 0
    
    # Выводим
    logo_height = len(logo)
    info_height = len(info_items)
    
    for i in range(max(logo_height, info_height)):
        parts = []
        
        # Логотип
        if i < logo_height:
            parts.append(colors["primary"] + logo[i] + Colors.RESET)
        else:
            parts.append(" " * len(logo[0]) if logo else "")
        
        # Разделитель
        if i > 0 and i < logo_height:
            parts.append(colors["text"] + "│" + Colors.RESET)
        else:
            parts.append(" ")
        
        # Информация
        if i < info_height:
            key, value = info_items[i]
            value_color = colors["highlight"] if key == "Memory" else colors["secondary"]
            parts.append(f"{colors['text']}{key:<{max_key_len}}{Colors.RESET} {value_color}{value}{Colors.RESET}")
        
        spacing = config["display"]["spacing"]
        padding = config["display"]["padding"]
        print(" " * padding + (" " * spacing).join(parts))
    
    # Цветовая палитра
    if config["behavior"]["show_color_bar"]:
        print()
        color_bar = "".join(f"{colors[c]}██{Colors.RESET}" for c in ["primary", "secondary", "accent", "highlight"])
        print(f"{colors['text']}Colors:{Colors.RESET}  {color_bar}")

def get_uptime():
    """Получить uptime"""
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "N/A"

# ============= КОМАНДЫ =============
def main():
    """Главная функция"""
    args = sys.argv[1:]
    
    if not args:
        # Обычный запуск
        config = load_config()
        print_wfetch(config)
        return
    
    if args[0] in ["-h", "--help"]:
        print("""
Wfetch v3.5 - System Fetch Tool

Usage:
  wfetch                    # Run with current config
  wfetch --gen-config      # Generate new config file
  wfetch --config          # Show current config
  wfetch --compact         # Compact mode
  wfetch --no-colors       # Disable colors
  wfetch --help            # Show this help

Config location:
  Windows: %APPDATA%\\wfetch\\config.json
  Linux/macOS: ~/.config/wfetch/config.json

Tips:
  - Edit config.json to customize
  - Set "windows_packages": true to count Windows apps (slow)
  - Set "alt_logo_chance": 0 to disable alternative logo
        """)
    
    elif args[0] in ["--gen-config", "-g"]:
        config_path = get_config_path()
        if config_path.exists():
            print(f"Config already exists: {config_path}")
            response = input("Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                return
        
        config = load_config()  # Создаст новый
        print(f"✅ Config created: {config_path}")
        print("Edit it to customize wfetch")
    
    elif args[0] in ["--config", "-c"]:
        config = load_config()
        print(json.dumps(config, indent=2, ensure_ascii=False))
    
    elif args[0] in ["--compact"]:
        config = load_config()
        config["display"]["compact"] = True
        config["display"]["spacing"] = 1
        print_wfetch(config)
    
    elif args[0] in ["--no-colors", "-n"]:
        config = load_config()
        config["behavior"]["random_colors"] = False
        config["behavior"]["show_color_bar"] = False
        print_wfetch(config)
    
    elif args[0] in ["-v", "--version"]:
        print("Wfetch v3.5")
    
    else:
        print(f"Unknown command: {args[0]}")
        print("Use: wfetch --help")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Try: wfetch --gen-config")
        sys.exit(1)