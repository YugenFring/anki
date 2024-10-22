import json
from anki import op

if __name__ == '__main__':
    with open('./db_config.json', encoding='utf-8') as file:
        db_config = json.load(file)
    directory = './corpus'
    op.load(db_config, directory)
    op.start(db_config)
