import os

# 1. Определяем, где мы находимся
current_dir = os.path.dirname(os.path.abspath(__file__)) # Папка src
root_dir = os.path.dirname(current_dir)                # Главная папка
env_path = os.path.join(root_dir, '.env')              # Путь к файлу .env

print(f"🔍 Ищу ключи здесь: {env_path}")

GEMINI_API_KEY = None
TELEGRAM_TOKEN = None

# 2. Читаем файл вручную (самый надежный способ)
if os.path.exists(env_path):
    try:
        # Пытаемся открыть как UTF-8 (стандарт)
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Если файл прочитался, ищем ключи
        for line in lines:
            line = line.strip() # Убираем пробелы
            if line.startswith('GEMINI_API_KEY='):
                GEMINI_API_KEY = line.split('=', 1)[1]
                print("✅ Ключ Gemini найден!")
            if line.startswith('TELEGRAM_BOT_TOKEN='):
                TELEGRAM_TOKEN = line.split('=', 1)[1]
                print("✅ Токен Telegram найден!")
                
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
else:
    print("❌ Файл .env вообще не найден!")

# 3. Финальная проверка
if not GEMINI_API_KEY or not TELEGRAM_TOKEN:
    print("\n💀 ОШИБКА: Ключи пустые. Проверь файл .env!")
    # Если ключи не найдены, программа остановится здесь
    raise ValueError("Нет ключей — нет работы.")