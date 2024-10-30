import time
import os
import json
from datetime import datetime, timedelta
from dataclasses import asdict
from .db import Cards, Corpus, CorpusBase
from . import algo


def json_loader(file_path: str, encoding='utf-8') -> list[dict]:
    """加载 json 文件"""
    with open(file_path, encoding=encoding) as file:
        json_data = json.load(file)
    return json_data


def json_writer(file_path: str, data: list[dict], encoding='utf-8') -> None:
    """写入 json 文件"""
    with open(file_path, 'w', encoding=encoding) as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load(db_info: dict, directory: str) -> None:
    """将 json 文件写入到数据库, 并将 id 反写到源文件中"""
    cards_db = Cards(db_info)
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if not file_path.endswith('.json'):
            continue
        json_list = json_loader(file_path)
        card_list = [CorpusBase(**c) for c in json_list]

        cards_need_insert = []
        cards_need_update = []

        for j, c in zip(json_list, card_list):
            if not j.get('id', None):
                j['id'] = c.id
                cards_need_insert.append(Corpus(**asdict(c)))
            else:
                cards_need_update.append(c)
        cards_db.upsert(cards_need_insert)
        cards_db.upsert(cards_need_update)

        json_writer(file_path, json_list)


def unload(directory: str) -> None:
    """去除源文件中的 id"""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        json_list = json_loader(file_path)

        for j in json_list:
            del j['id']

        json_writer(file_path, json_list)


def start(db_info: dict) -> None:
    """开始 review"""
    cards_db = Cards(db_info)
    while True:
        card = cards_db.get_random_card()
        print(f"Q: {card.translated_content}")
        print(f"E: {card.explanation}")

        start_time = time.time()
        answer = input('A: ')
        end_time = time.time()
        answer_duration = end_time - start_time
        card.ease_factor = algo.update_ease_factor(
            card.ease_factor, answer_duration)

        similarity = algo.compare_sentences(answer, card.original_content)
        success = 1 if similarity > 0.85 else 0
        card.test_times += 1
        card.success_times += success
        print(f'R: {card.original_content}({card.phonetic_alphabet})')
        print(f'S: {similarity * 100:.2f}')
        print()

        review_date = datetime.now()
        new_memory_strangth = algo.calculate_memory_strength(
            review_date, card.last_review_date, card.memory_strength)
        card.memory_strength = new_memory_strangth

        expected_interval = card.next_review_date - card.last_review_date
        real_interval = review_date - card.last_review_date
        interval_ratio = expected_interval / real_interval
        interval_ratio = 2 * interval_ratio / (interval_ratio + 1)
        current_interval = real_interval * interval_ratio
        current_interval = current_interval.total_seconds() / (24 * 3600)
        success_rate = card.success_times / (card.test_times + 0.000001)
        new_interval = algo.calculate_review_interval(
            current_interval, card.ease_factor,
            card.memory_strength, success_rate
        )
        card.next_review_date = review_date + timedelta(days=new_interval)
        card.last_review_date = review_date

        cards_db.upsert([card])
