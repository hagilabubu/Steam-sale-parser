# Steam-Sale Parser 🎮

Headless парсер акционных страниц Steam (app/bundle/sub/DLC)  
- ✅ Ленивая прокрутка + WebDriverWait для React  
- ✅ MySQL с дедубликацией  
- ✅ Cron-запуск на Ubuntu Server  

## Быстрый старт
```bash
git clone https://github.com/hagilabubu/steam-sale-parser.git
cd steam-sale-parser
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # заполните MySQL данные
python3 main.py
