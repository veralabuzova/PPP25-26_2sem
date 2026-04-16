import hashlib
import requests
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Item(Base):
    __tablename__ = 'clothes'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    price = Column(Float)
    source = Column(String)
    category = Column(String)
    size = Column(String)
    brand = Column(String)
    hash = Column(String, unique=True)

class ClothesExtractor:
    def extract(self):
        results = []
        try:
            r = requests.get('https://fakestoreapi.com/products/category/men\'s%20clothing', timeout=10)
            men = r.json()[:2]
            r = requests.get('https://fakestoreapi.com/products/category/women\'s%20clothing', timeout=10)
            women = r.json()[:3]
            clothes = men + women

            for item in clothes:
                transformed = {
                    'source': 'fakestoreapi',
                    'title': item['title'],
                    'price': item['price'] * 90,
                    'category': 'Мужская' if 'men' in item['category'] else 'Женская',
                    'size': 'M/L/XL',
                    'brand': item['title'].split()[0],
                    'hash': hashlib.md5(f"{item['title']}_{item['price']}".encode()).hexdigest()
                }
                results.append(transformed)
        except:
            pass
        return results

class DatabaseLoader:
    def __init__(self, db_url='sqlite:///clothes.db'):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def load(self, items):
        for item in items:
            try:
                self.session.add(Item(**item))
                self.session.commit()
            except:
                self.session.rollback()

    def show(self):
        for item in self.session.query(Item).all():
            print(f"{item.id}. {item.title}")
            print(f"   {item.price:,.0f} руб | {item.category} | {item.brand}\n")

    def close(self):
        self.session.close()

if __name__ == "__main__":
    data = ClothesExtractor().extract()
    db = DatabaseLoader()
    db.load(data)
    db.show()
    db.close()
