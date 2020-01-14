import os
import shutil
import downloader_pubmed
import combine_data
import es_insert
import constants as const


def clean_up():
    if os.path.exists(const.PUBMED_DIR_UNZIP) and os.path.isdir(const.PUBMED_DIR_UNZIP):
        shutil.rmtree(const.PUBMED_DIR_UNZIP)

    path_article = const.PUBMED_DIR + 'article/'
    if os.path.exists(path_article) and os.path.isdir(path_article):
        shutil.rmtree(path_article)

    path_md5 = const.PUBMED_DIR + 'md5/'
    if os.path.exists(path_md5) and os.path.isdir(path_md5):
        shutil.rmtree(path_md5)

    if os.path.exists(const.COMBINED_JSON) and os.path.isdir(const.COMBINED_JSON):
        shutil.rmtree(const.COMBINED_JSON)


if __name__ == '__main__':
    downloader_pubmed.run()
    combine_data.run()
    es_insert.run()
    clean_up()
