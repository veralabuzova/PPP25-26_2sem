import sqlite3
import json
import hashlib
import urllib.request
from datetime import datetime
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


class Site1Extractor:
    def extract(self) -> List[Dict]:
        logging.info("Извлечение с сайта 1 (парсинг)")
        return [
            {'source': 'site1', 'title': 'iPhone 13', 'price': '69990 руб', 'date': '15.03.2024', 'category': 'phones'},
            {'source': 'site1', 'title': 'Samsung TV', 'price': '45990', 'date': '20.03.2024', 'category': 'tv'},
            {'source': 'site1', 'title': 'iPhone 13', 'price': '69990 руб', 'date': '15.03.2024', 'category': 'phones'},
        ]


class Site2Extractor:
    def extract(self) -> List[Dict]:
        logging.info("Извлечение с сайта 2 (API)")
        return [
            {'source': 'site2', 'name': 'iPhone 13', 'amount': 72000.0, 'created': '2024-03-16', 'type': 'electronics'},
            {'source': 'site2', 'name': 'Xiaomi Band', 'amount': 2990.0, 'created': '2024-03-18', 'type': 'gadgets'},
        ]


def save_raw_data(data: List[Dict], filename: str):
    with open(f"raw_{filename}.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Transformer:
    def transform(self, data1: List[Dict], data2: List[Dict]) -> List[Dict]:
        unified = []

        for item in data1:
            price_str = item['price'].replace(' руб', '') if isinstance(item['price'], str) else str(item['price'])
            unified.append({
                'title': item['title'],
                'price': float(price_str),
                'date': datetime.strptime(item['date'], '%d.%m.%Y').isoformat(),
                'source': item['source'],
                'category': 'Смартфоны' if item['category'] == 'phones' else 'Телевизоры',
                'hash': hashlib.md5(f"{item['title']}_{item['price']}".encode()).hexdigest()
            })

        for item in data2:
            unified.append({
                'title': item['name'],
                'price': float(item['amount']),
                'date': datetime.strptime(item['created'], '%Y-%m-%d').isoformat(),
                'source': item['source'],
                'category': 'Смартфоны' if 'iPhone' in item['name'] else 'Гаджеты',
                'hash': hashlib.md5(f"{item['name']}_{item['amount']}".encode()).hexdigest()
            })

        seen = set()
        unique = []
        for item in unified:
            if item['hash'] not in seen:
                seen.add(item['hash'])
                unique.append(item)

        return unique


class DatabaseLoader:
    def __init__(self, db_name='etl.db'):
        self.conn = sqlite3.connect(db_name)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS items 
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             title TEXT, price REAL, date TEXT, 
                             source TEXT, category TEXT, hash TEXT UNIQUE)''')

    def load(self, items: List[Dict]):
        cursor = self.conn.cursor()
        count = 0
        for item in items:
            try:
                cursor.execute('''INSERT INTO items 
                                  (title, price, date, source, category, hash) 
                                  VALUES (?, ?, ?, ?, ?, ?)''',
                               (item['title'], item['price'], item['date'],
                                item['source'], item['category'], item['hash']))
                count += 1
            except sqlite3.IntegrityError:
                pass
        self.conn.commit()
        logging.info(f"Загружено {count} новых записей")

    def show(self):
        print("\n=== СОДЕРЖИМОЕ БАЗЫ ДАННЫХ ===")
        for row in self.conn.execute("SELECT id, title, price, source, category FROM items"):
            print(f"{row[0]}. {row[1]} - {row[2]} руб ({row[3]}, {row[4]})")

    def close(self):
        self.conn.close()


def run_etl():
    s1 = Site1Extractor().extract()
    s2 = Site2Extractor().extract()
    save_raw_data(s1, "site1")
    save_raw_data(s2, "site2")

    transformed = Transformer().transform(s1, s2)

    loader = DatabaseLoader()
    loader.load(transformed)
    loader.show()
    loader.close()

    logging.info(f"✅ ETL завершен. Уникальных записей: {len(transformed)}")

if __name__ == "__main__":
    run_etl()
