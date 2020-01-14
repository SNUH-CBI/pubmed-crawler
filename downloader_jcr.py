import json, requests, threading
import concurrent.futures
import argparse
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm
import constants as const


json_dir = const.JCR_DIR
journals_json_name = 'journals_'
category_json_name = 'categories.json'
category_info_json_name = 'category_info.json'
collection_json_name = 'issn_collection.json'
eissn_json_name = 'eissn_issn_map.json'
real_eissn_json_file = 'real_eissn_year_issn_map.json'
final_file = const.JCR_FINAL_JSON

output = set()
thread_lock = threading.Lock()

session = requests.Session()

year_first = 0
year_last = 0


# initialize before downloading
def initialize(email, pw):
    global session

    # login
    url_login = 'https://login.incites.clarivate.com/?IPStatus=IPValid&DestApp=IC2JCR&locale=en_US&Alias=IC2'
    param_login = {'username': email, 'password': pw, 'IPStatus': 'IPValid'}  # IPValid : inside network, IPError : outside network

    with requests.Session() as sess:
        print('Signing in...', end='', flush=True)
        login = sess.get(url_login, params=param_login)

        # Check if authentication was successful or not
        if 'The Email Address and Password do not match.'.encode() in login._content:
            print('Fail!')
            exit()

        session = sess
        print('Success')

    # create directory
    with Path(json_dir) as folder_json:
        if not folder_json.exists():
            folder_json.mkdir(exist_ok=True)
            print('json directory created.')
        else:
            print('json directory exists')


# download journals and category data from JCR. / categories.json, category_info.json, journals_year_first~2018.json
def jcr_jsonfy():
    """
    Retrieved data from JCR servers are byte types. To convert it to JSON format,
    You should convert value of the key '_content' with .decode('utf-8')
    """

    url_category = 'https://jcr.clarivate.com/AllCategoriesJson.action'  # Categories per year
    url_info = 'https://jcr.clarivate.com/CategoriesDataJson.action'  # Information of categories per year
    url_journal = 'https://jcr.clarivate.com/JournalHomeGridJson.action'  # list of journals per year (SCIE + SSCI)

    # Retreive Category list
    print('Category data retrieving...')
    with Path(json_dir + category_json_name) as file_category:
        if not file_category.exists():
            dict_category = {}

            for year in range(year_first, year_last):
                result_category = session.post(url_category, data={'jcrYear': year})
                dict_category[year] = json.loads(result_category._content.decode('utf-8'))

            file_category.write_text(json.dumps(dict_category, indent=4))
            print('CATEGORY json file is written')

    # Retrieve information of categories
    print('Category information data retrieving...')
    with Path(json_dir + category_info_json_name) as file_info:
        if not file_info.exists():
            dict_info = {}

            for year in range(year_first, year_last):
                result_info = session.get(url_info, params={'jcrYear': year, 'limit': 999})
                dict_info[year] = json.loads(result_info._content.decode('utf-8'))

            file_info.write_text(json.dumps(dict_info, indent=4))
            print('CATEGORY INFO json file is written')

    # Retrieve Journal information
    print('Journals information data retrieving...')
    with Path(json_dir + category_info_json_name) as file_info:
        # load category json data to utilize shorten category ID
        json_data = file_info.open().read()
        category_data = json.loads(json_data)

        # create journal info json per year
        for year in range(year_first, year_last):
            # create nested dictionary
            dict_journal = {}
            # JOURNALS[year] = {}

            # create json file
            with Path(json_dir + journals_json_name + str(year) + '.json') as file_journal:
                if not file_journal.exists():
                    print(year)
                    categories = category_data[str(year)]['data']

                    for category in categories:
                        category_id = category['categoryId']
                        # Should check category already exists in dictionary or it will overwrite data.
                        if not category_id in dict_journal:
                            result_journal = session.get(url_journal, params={'jcrYear': year, 'edition': 'Both', 'limit': 999, 'categoryIds': category_id})
                            dict_journal[category_id] = json.loads(result_journal._content.decode('utf-8'))
                            print(category_id, end=' ', flush=True)
                    print()

                    file_journal.write_text(json.dumps(dict_journal, indent=4, sort_keys=False))


# collect ISSN from journal information files and create a unique set from it. / issn_collection.json
def collect_issn():
    for year in range(year_first, year_last):
        with Path(json_dir + journals_json_name + str(year) + '.json') as file_journal:
            journal_data = json.load(file_journal.open())

            for category in tqdm(journal_data, desc=str(year) + 'category'):
                threads = []

                for data in journal_data[category]['data']:
                    thread = threading.Thread(target=collect_issn_thread, args=(data,))
                    threads.append(thread)

                # start threads and wait till they finish
                for thread in threads: thread.start()
                for thread in threads: thread.join()

    # print how many unique elements exist
    print('unique issn : ' + str(len(output)))

    # save to file
    with Path(json_dir + collection_json_name) as file_collection:
        file_collection.write_text(json.dumps({'data': list(output)}))


def collect_issn_thread(data):
    global output

    thread_lock.acquire()
    try:
        if 'issn' in data:
            output.add(data['issn'])
    finally:
        thread_lock.release()


# match EISSN with ISSNs (EISSN:ISSN = 1:N) / eissn_issn_map.json
def issn_eissn():
    output_dict = defaultdict(set)

    with Path(json_dir + collection_json_name) as file_collection:
        issn_list = json.load(file_collection.open())['data']

    # get eissn-issn mapping information from server
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        for future in list(tqdm(executor.map(get_eissn, issn_list), total=len(issn_list))):
            for result in future:
                if not result['eissn'] is '':
                    output_dict[result['eissn']].add(result['issn'])

    # convert Set to List
    list_output = dict()
    for key, set_value in tqdm(output_dict.items()):
        list_output[key] = list(set_value)

    # write out to json format
    with Path(json_dir + eissn_json_name) as file_eissn:
        file_eissn.write_text(json.dumps(list_output, indent=4, sort_keys=True))


# match year data with ESSIN / real_eissn_year_issn_map.json
def year_eissn_issn():
    output_result = dict()

    with Path(json_dir + eissn_json_name) as file_eissn:
        eissn_list = json.load(file_eissn.open())

    # get eissn-issn mapping information from server
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        for future in list(tqdm(executor.map(get_eissn, eissn_list), total=len(eissn_list))):
            output_result[future[0]['eissn']] = future

    # write out to json format
    with Path(json_dir + real_eissn_json_file) as file_real:
        file_real.write_text(json.dumps(output_result, indent=4, sort_keys=True))


def get_eissn(data):
    url_issn = 'https://jcr.clarivate.com/SearchJournalsJson.action'  # issn data per journal

    result = session.post(url_issn, data={'query': data}, timeout=5)
    res_data_collection = json.loads(result._content.decode('utf-8'))['data']

    return res_data_collection


# match IF and percentile with ISSN & EISSN / issn_eissn_IF_and_percentile_file.json
def year_issn_categories():
    final_result = dict()

    with Path(json_dir + category_json_name) as file_category:
        categories_info = json.load(file_category.open())

    year_category_id_name = dict()

    for year in range(year_first, year_last):
        category_id_name = dict()

        for cat_id_name in categories_info[str(year)]['data']:
            category_id_name[cat_id_name['categoryId']] = cat_id_name['categoryName']

        year_category_id_name[str(year)] = category_id_name

    # journals_year json  to  year-issn- if & categories id & categories name
    # // [year][issn] -> if ,  [ {categories id , categories name}  ]
    ##  [issn] - if
    ##  [issn] - [{categories id , categories name} , { }]
    for year in range(year_first, year_last):
        print(year)
        issn_if = dict()  ## [issn] -> if
        issn_if_percentile = dict()
        issn_category_ids = dict()  ## [issn] -> [{catid,name},{catid,name}]

        with Path(json_dir + journals_json_name + str(year) + '.json')  as file_journal:
            journals = json.load(file_journal.open())

            for category, journals_data in journals.items():
                for journal in journals_data['data']:
                    try:
                        issn_if[journal['issn']] = journal['journalImpactFactor']
                        issn_if_percentile[journal['issn']] = journal['jifPercentile']

                        # for journals that have multiple categories
                        if journal['issn'] in issn_category_ids:
                            cat_name = year_category_id_name[str(year)][category]
                            insert_dict = dict()
                            insert_dict['categoryId'] = category
                            insert_dict['categoryName'] = cat_name
                            insert_dict['edition'] = journal['edition']

                            issn_category_ids[journal['issn']].append(insert_dict)
                        else:
                            issn_category_ids[journal['issn']] = list()
                            cat_name = year_category_id_name[str(year)][category]
                            insert_dict = dict()
                            insert_dict['categoryId'] = category
                            insert_dict['categoryName'] = cat_name
                            insert_dict['edition'] = journal['edition']

                            issn_category_ids[journal['issn']].append(insert_dict)

                    except KeyError:
                        pass

        for issn, impact_factor in issn_if.items():
            insert_dict = dict()

            insert_dict['year'] = str(year)
            insert_dict['impactFactor'] = impact_factor
            insert_dict['percentile'] = issn_if_percentile[issn]

            if issn not in final_result:
                final_result[issn] = {'category':[], 'metric':[]}

            # merge all categories
            for category in issn_category_ids[issn]:
                if category not in final_result[issn]['category']:
                    final_result[issn]['category'].append(category)

            final_result[issn]['metric'].append(insert_dict)

    # add eissn
    with Path(json_dir + real_eissn_json_file) as file_real:
        eissn_info = json.load(file_real.open())

    for eissn, issn_info in eissn_info.items():
        for each_issn_info in issn_info:
            final_result[each_issn_info['eissn']] = final_result[each_issn_info['issn']]

    with Path(json_dir + final_file) as file_final:
        file_final.write_text(json.dumps(final_result, indent=4))

    print('Finished!')


if __name__ == '__main__':
    """    
    categories.json
    연도별 카테고리 목록 (id, 이름)

    category_info.json
    연도별 카테고리 상세 정보

    journals_year_first~2018.json
    카테고리별 논문 상세 정보

    issn_collection.json
    ISSN 목록

    eissn_issn_map.json
    EISSN 별 ISSN 대응 목록

    real_eissn_year_issn_map.json
    논문별 EISSN, ISSN, JCR 연도

    jcr_issn_eissn.json
    ISSN, EISSN 별 카테고리, 연도별 impact factor, percentile

    (이전)
    issn_eissn_IF_and_percentile_file.json
    연도별 ISSN, EISSN 별 impact factor, percentile, 카테고리
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--email", type=str, required=True)
    parser.add_argument("--pw", type=str, required=True)
    parser.add_argument("--fyear", type=int, default=1997)
    parser.add_argument("--lyear", type=int, default=2018)
    args = parser.parse_args()

    year_first = args.fyear
    year_last = args.lyear + 1

    print(f'Start collecting from {year_first} to {year_last - 1}')

    initialize(args.email, args.pw)
    jcr_jsonfy()
    collect_issn()
    issn_eissn()
    year_eissn_issn()
    year_issn_categories()
