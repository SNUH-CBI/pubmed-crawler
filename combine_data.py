# -*- coding: utf-8 -*-
import os
import json
import glob
import re
from bs4 import BeautifulSoup
import constants as const


# Processing XML DATA
def processing_value(get_key, get_value):
    if get_key.__eq__('PubDate'):
        regex_numbers = re.compile(r'[\d]+')
        result = regex_numbers.findall(get_value.get_text())
        if result.__ne__(None):
            for get_PubDate in result:
                if int(get_PubDate) > 1900:
                    return get_PubDate
        else:
            return '-1'

    elif get_key.__eq__('Keyword'):
        flag_keyword = True
        get_Keyword_list = []
        for get_keyword in get_value:
            flag_keyword = False
            insert_dict = {'Keyword': get_keyword.get_text()}
            get_Keyword_list.append(insert_dict)
        if flag_keyword:
            insert_dict = {'Keyword': '-1'}
            return insert_dict
        return get_Keyword_list

    elif get_key.__eq__('PublicationType'):
        flag_PublicationType = True
        get_PublicationType_list = []
        for get_PublicationType in get_value:
            flag_PublicationType = False
            insert_dict = {'PublicationType': get_PublicationType.get_text()}
            get_PublicationType_list.append(insert_dict)
        if flag_PublicationType:
            insert_dict = {'PublicationType': '-1'}
            return insert_dict
        return get_PublicationType_list

    elif get_key.__eq__('Author'):
        author_info_dict_list = []
        for each_author in get_value:
            author_info_dict = {}
            for want_param in ['LastName', 'ForeName', 'Affiliation', 'CollectiveName']:
                get_elememt_list = each_author.find_all(want_param)
                if get_elememt_list.__ne__(None):
                    input_string = ''
                    flag_input = False
                    for list_element in get_elememt_list:
                        if flag_input:
                            input_string += ' / '
                        flag_input = True
                        input_string += list_element.get_text()
                if input_string.__eq__(''):
                    input_string = '-1'
                author_info_dict[want_param] = input_string

            input_ForeName = author_info_dict['ForeName']
            input_LastName = author_info_dict['LastName']
            if input_ForeName.__eq__('-1') and input_LastName.__eq__('-1'):
                FullName = '-1'
            elif input_ForeName.__eq__('-1') or input_LastName.__eq__('-1'):
                FullName = input_LastName if input_ForeName.__eq__('-1') else input_ForeName
            else:
                FullName = input_ForeName + ' ' + input_LastName
            author_info_dict['FullName'] = FullName

            input_ForeName = author_info_dict['ForeName']
            input_LastName = author_info_dict['LastName']
            if input_ForeName.__eq__('-1') and input_LastName.__eq__('-1'):
                regexFullName = '-1'
            elif input_ForeName.__eq__('-1') or input_LastName.__eq__('-1'):
                regexFullName = input_LastName if input_ForeName.__eq__('-1') else input_ForeName
            else:
                regexFullName = input_ForeName + ' ' + input_LastName
                regexFullName = re.sub(r'\W', ' ', regexFullName)
            author_info_dict['regexFullName'] = regexFullName
            author_info_dict_list.append(author_info_dict)

        return author_info_dict_list

    elif get_key.__eq__('AbstractText'):
        flag_keyword = True
        get_AbstractText_Sum = ''
        for get_AbstractText in get_value:
            flag_keyword = False
            get_AbstractText_Sum += get_AbstractText.get_text()
        if flag_keyword:
            return '-1'
        return get_AbstractText_Sum

    elif get_key.__eq__('MeshHeading'):
        flag_keyword = True
        MeshHeading_dict_list = []
        for get_AbstractText in get_value:
            regex_numbers = re.compile(r'[^\n]*')
            result = regex_numbers.findall(get_AbstractText.get_text())
            for result_element in result:
                if result_element.__ne__(''):
                    flag_keyword = False
                    insert_dict = {'MeshHeading': result_element}
                    MeshHeading_dict_list.append(insert_dict)
        if flag_keyword:
            insert_dict = {'MeshHeading': '-1'}
            return insert_dict
        return MeshHeading_dict_list

    else:
        print('Exception from processing_value!')


def Affiliation_Element(get_value):
    affiliation_regex = r'[\w\ \'\-\_]+[\w]'
    email_regex = r'[\w]+[\w\.\-\_]+@[\w\.]+[\w]'

    processed_value = get_value
    processing_value_Email = get_value

    email_matches = re.finditer(email_regex, processing_value_Email)
    param_email_matches = email_matches

    sub_len = 0

    for _, match in enumerate(param_email_matches, start=1):
        processed_value = processed_value[0: match.start() - sub_len:] + processed_value[match.end() - sub_len::]
        sub_len += len(match.group())

    affiliation_matches = re.finditer(affiliation_regex, processed_value)

    return affiliation_matches, email_matches


def combine():
    pubmed_files = []
    file_name_list = []

    with open(const.JCR_DIR + const.JCR_FINAL_JSON) as file:
        jcr_data = json.load(file)

    for file_name in glob.glob(const.PUBMED_DIR_UNZIP + '*.xml'):
        pubmed_files.append(file_name)

    print('File List : ', end='', flush=True)
    for file_name in pubmed_files:
        print(f'{file_name} ', end='', flush=True)
        file_name_list.append(file_name.replace('\\', '/'))
    print()

    count_total_insert = 0

    for read_xml_file in file_name_list:
        count_id = 1
        p = re.compile(r'[\w]+.xml')
        get_prefix = p.findall(read_xml_file)
        id_prefix = get_prefix[0]

        xml_opened = open(read_xml_file, 'r')
        contents = xml_opened.read().encode('utf-8')

        print(f'Started parsing {read_xml_file}')

        soup = BeautifulSoup(contents, 'xml')
        articles = soup.find_all('PubmedArticle')

        print(f'Number of articles : {len(articles)}')

        print(f'Started insert {read_xml_file}')

        for article in articles:
            count_total_insert += 1
            count_id += 1

            medline_citation = article.find('MedlineCitation')
            article_detail = medline_citation.find('Article')
            medline_journal_info_detail = medline_citation.find('MedlineJournalInfo')
            journal_detail = article_detail.find('Journal')

            journal_data_dict = {
                'Country': medline_journal_info_detail.find('Country'),
                'PMID': medline_citation.find('PMID'),
                'ArticleTitle': article_detail.find('ArticleTitle'),
                'Language': article_detail.find('Language'),
                'ISSN': journal_detail.find('ISSN'),
                'Title': journal_detail.find('Title'),
                'PubDate': journal_detail.find('PubDate'),
                'AbstractText': article_detail.find_all('AbstractText'),
                'Keyword': medline_citation.find_all('Keyword'),
                'PublicationType': article_detail.find_all('PublicationType'),
                'MeshHeading': medline_citation.find_all('MeshHeading'),
                'Author': article_detail.find_all('Author')
            }

            # get data
            processing_key = ['PubDate', 'Keyword', 'PublicationType', 'Author', 'AbstractText', 'MeshHeading']
            for key, value in journal_data_dict.items():
                if str(key) in processing_key:
                    get_value = processing_value(key, value)
                    journal_data_dict[key] = get_value
                    continue
                elif value.__ne__(None):
                    journal_data_dict[key] = value.text
                    continue
                journal_data_dict[key] = '-1'

            # AffiliationSet , EmailAffiliationSet
            autor_dict_list = journal_data_dict['Author']
            set_aff = set()
            set_email = set()
            for autor_dict in autor_dict_list:
                aff_result, email_result = Affiliation_Element(autor_dict['Affiliation'])
                for _, match in enumerate(aff_result, start=1):
                    set_aff.add(match.group().strip().lower())
                for _, match in enumerate(email_result, start=1):
                    set_email.add(match.group().strip().lower())

            if len(set_aff) >= 2:
                is_check = True if '-1' in set_aff else False
                if is_check:
                    set_aff.remove('-1')
            elif len(set_aff) == 0:
                set_aff.add('-1')

            if len(set_email) >= 2:
                is_check = True if '-1' in set_email else False
                if is_check:
                    set_email.remove('-1')
            elif len(set_email) == 0:
                set_email.add('-1')

            list_aff = []
            for data_aff in set_aff:
                dict_aff = {'AffiliationSet': data_aff}
                list_aff.append(dict_aff)
            journal_data_dict['AffiliationSet'] = list_aff

            list_email = []
            for data_email in set_email:
                dict_email = {'EmailAffiliationSet': data_email}
                list_email.append(dict_email)
            journal_data_dict['EmailAffiliationSet'] = list_email

            # data from JCR
            try:
                jcr_journal_data = jcr_data[journal_data_dict['ISSN']]

                list_metric = []
                for data_metric in jcr_journal_data['metric']:
                    dict_metric = {
                        'JCRYear': data_metric['year'],
                        'JCRImpactFactor': data_metric['impactFactor'],
                        'JCRPercentile': data_metric['percentile']
                    }
                    list_metric.append(dict_metric)
                journal_data_dict['JCRMetrics'] = list_metric

                list_category = []
                for data_category in jcr_journal_data['category']:
                    dict_category = {
                        'JCRCategoryID': data_category['categoryId'],
                        'JCRCategoryName': data_category['categoryName'],
                        'JCRCategoryEdition': data_category['edition']
                    }
                    list_category.append(dict_category)
                journal_data_dict['JCRCategoryList'] = list_category

            except KeyError:
                journal_data_dict['JCRImpactFactor'] = '-1'
                journal_data_dict['JCRAvgImpactFactorPercentile'] = '-1'
                journal_data_dict['JCRMetrics'] = [{'year':'-1', "impactFactor":'-1', "percentile":'-1'}]
                journal_data_dict['JCRCategoryList'] = [{'JCRCategoryID': '-1', 'JCRCategoryName': '-1', 'JCRCategoryEdition': '-1'}]

            # save to json
            result_json = {
                '_index': const.ES_INDEX,
                '_type': '_doc',
                '_op_type': 'create',
                '_id': id_prefix + '#' + str(count_id),
                '_source': {
                    'PMID': journal_data_dict['PMID'],
                    'ArticleTitle': journal_data_dict['ArticleTitle'],
                    'AbstractText': journal_data_dict['AbstractText'],
                    'Language': journal_data_dict['Language'],
                    'PublicationTypeList': journal_data_dict['PublicationType'],
                    'PubDate': journal_data_dict['PubDate'],
                    'ISSN': journal_data_dict['ISSN'],
                    'Title': journal_data_dict['Title'],
                    'Author': journal_data_dict['Author'],
                    'KeywordList': journal_data_dict['Keyword'],
                    'MeshHeadingList': journal_data_dict['MeshHeading'],
                    'Country': journal_data_dict['Country'],
                    'AffiliationSetList': journal_data_dict['AffiliationSet'],
                    'EmailAffiliationSetList': journal_data_dict['EmailAffiliationSet'],
                    'JCRMetrics': journal_data_dict['JCRMetrics'],
                    'JCRCategoryList': journal_data_dict['JCRCategoryList']
                }
            }

            pmid = journal_data_dict['PMID']

            with open(f'{const.COMBINED_JSON}{pmid}.json', 'w', encoding='utf-8') as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2)

            print(pmid)

        xml_opened.close()

        print('Insert done : ', read_xml_file)
        print(read_xml_file, 'Id Last Number : ', count_id)
        print(read_xml_file, 'Insert number until now: ', count_total_insert)

    print('Total insert number : ', count_total_insert)


def run():
    if not os.path.isdir(const.COMBINED_JSON):
        os.mkdir(const.COMBINED_JSON)

    combine()


if __name__ == '__main__':
    run()


'''
@@ : 파싱 구현 완료

      XML Syntax           	  		                                Real world Semantic
@MedlineCitation - PMID   				                              ## PMID
@MedlineCitation - Article - ArticleTitle 	    	                  ##Article title
@MedlineCitation - Article - Abstract - AbstractText 	              ##ArticleAbstract
@MedlineCitation - Article - Language                                 ## Article Language
@MedlineCitation - Article - PublicationTypeList                      ## PublicationType [List]
                                         - PublicationType

@MedlineCitation - Article - Journal  - JournalIssue 	               ## Article Year
                                      - PubDate -Year/MedlineDate   
@MedlineCitation - Article - Journal  - ISSN  		                   ##Published journal  ISSN	
@MedlineCitation - Article - Journal  - Title  		                   ##Published journal  Title



@@MedlineCitation - Article - AuthorList - Author              	       ##Author names  [List]	
                                        -> LastName	                   ## Authors’ affiliations [String append 로 진행]
				                        -> ForeName
				                        -   AffiliationInfo - Affiliation    

Author List                                                             ## Author List 분석 Set 자료구조
   = {'CollectiveName', 'Suffix', None, 'LastName', 'AffiliationInfo', 'Initials', 'Identifier', 'ForeName'}

@MedlineCitation - KeywordList                                          ## Article KeywordList [List]
@MedlineCitation - MedlineJournalInfo - Country                         ## Country

@MedlineCitation - MeshHeadingList - MeshHeading                        ## MeSH
                                   -> DescriptorName
                                   -> QualifierName

##
Year - ISSN 비교 -> index id value 를 데이터에 넣기!
   Impact Factor whether the journal is listed on the JCR table
   # Elsearch에서 검색해서 넣어야함.

'''
