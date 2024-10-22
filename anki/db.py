import pymysql
import random
from datetime import datetime
from dataclasses import dataclass, fields, field
from typing import List
from snowflake import SnowflakeGenerator

gen = SnowflakeGenerator(520)


@dataclass
class Corpus:
    """用于存储 card 的数据表"""
    id: int = field(default_factory=lambda: next(gen))
    language_type: str = 'JP'
    material_type: str = ''
    original_content: str = ''
    phonetic_alphabet: str = ''
    translated_content: str = ''
    explanation: str = ''
    test_times: int = 0
    success_times: int = 0
    last_review_date: datetime = field(default_factory=datetime.now)
    memory_strength: float = 1.0
    ease_factor: float = 1.3
    next_review_date: datetime = field(default_factory=datetime.now)
    inserted_date: datetime = field(default_factory=datetime.now)


def cls_to_create_sql(cls: dataclass) -> str:
    """将 dataclass 转换为 create 语句"""
    tb_fields = []
    for field in fields(cls):
        if field.type == int:
            field_type = "BIGINT"
        elif field.type == str:
            field_type = "TEXT"
        elif field.type == float:
            field_type = "FLOAT"
        elif field.type == datetime:
            field_type = "DATETIME"
        else:
            field_type = "VARCHAR(255)"
        tb_fields.append(f'{field.name} {field_type}')

    tb_name = cls.__name__.lower()
    create_tb_sql = f"""
        CREATE TABLE IF NOT EXISTS {tb_name} (
            {','.join(tb_fields)},
            PRIMARY KEY (id)
        );
    """

    return create_tb_sql


def cls_to_upsert_sql(cls: dataclass) -> str:
    """将 class 转换为 upsert 语句"""
    field_names = [field.name for field in fields(cls)]
    placeholders = ','.join(['%s'] * len(field_names))

    tb_name = cls.__name__.lower()
    insert_sql = f"""
        INSERT INTO {tb_name} ({','.join(field_names)})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE
    """

    update_stmt = ','.join(
        [f'{name} = VALUES({name})' for name in field_names if name != 'id'])
    upsert_sql = insert_sql + update_stmt

    return upsert_sql


class Cards:
    def __init__(self, db_info: dict, cls: dataclass = Corpus) -> None:
        self.conn = pymysql.connect(**db_info)
        self.cls = cls
        self._create_database()

    def _create_database(self) -> None:
        """创建 corpus 表如果不存在"""
        with self.conn.cursor() as cursor:
            sql = cls_to_create_sql(self.cls)
            cursor.execute(sql)
        self.conn.commit()
        # print(f'table created.')

    def upsert(self, cards: List[Corpus]) -> None:
        """执行 upsert 操作"""
        with self.conn.cursor() as cursor:
            sql = cls_to_upsert_sql(self.cls)
            values = [tuple(getattr(c, f.name) for f in fields(c))
                      for c in cards]
            cursor.executemany(sql, values)
        self.conn.commit()
        # print('upserted.')

    def get_random_card(self) -> None:
        """随机获取一个 card"""
        with self.conn.cursor(pymysql.cursors.DictCursor) as cursor:
            tb_name = self.cls.__name__.lower()
            sql = f"""
                SELECT *
                FROM {tb_name}
                ORDER BY DATEDIFF(next_review_date, CURDATE())
                LIMIT 10
            """
            cursor.execute(sql)
            results = cursor.fetchall()
        cards = [Corpus(**row) for row in results]
        if cards:
            return random.choice(cards)
        return None

    def __del__(self):
        self.conn.close()
