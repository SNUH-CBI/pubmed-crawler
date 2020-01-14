import os
import json
from pathlib import Path
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import constants as const


def run():
    es_host = [{'host': const.ES_HOST, 'port': const.ES_PORT}]
    es = Elasticsearch(es_host)

    if es.ping():
        print('Connected.')
        print(es.info())
    else:
        print('Connection Failed.')
        exit(1)

    with Path(const.ES_MAPPING) as file:
        mapping_json = json.load(file.open('r'))

    if not es.indices.exists(index=const.ES_INDEX):
        result = es.indices.create(index=const.ES_INDEX, body=mapping_json)
        print(result)

    insert_json_list = []

    for file in os.listdir(const.COMBINED_JSON):
        if file.endswith('.json'):
            with open(const.COMBINED_JSON + file) as json_file:
                insert_json_list.append(json.load(json_file))

    bulk(es, insert_json_list)

    print('Finished!')


if __name__ == '__main__':
    run()
