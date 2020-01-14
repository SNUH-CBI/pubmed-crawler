import os
import ftplib
from ftplib import FTP
import sqlite3
import gzip
import shutil
import argparse
import constants as const


url = 'ftp.ncbi.nlm.nih.gov'
annual = '/pubmed/baseline'
daily = '/pubmed/updatefiles/'
path_md5 = const.PUBMED_DIR + 'md5/'
path_article = const.PUBMED_DIR + 'article/'
database = const.PUBMED_DIR + 'pubmed.db'


def set_path():
    # create directories
    if not os.path.isdir(const.PUBMED_DIR):
        os.mkdir(const.PUBMED_DIR)
    if not os.path.isdir(path_md5):
        os.mkdir(path_md5)
    if not os.path.isdir(path_article):
        os.mkdir(path_article)


def set_db():
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute('CREATE TABLE IF NOT EXISTS hash (num INTEGER PRIMARY KEY, md5 TEXT)')

    conn.commit()
    conn.close()

    return


def compare_hash(num, md5):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    params = (num,)
    cursor.execute('SELECT * FROM hash WHERE num = ?', params)
    result = cursor.fetchone()

    if result is None:
        print(f'{num} does not exist. Need to be downloaded.')
        params = (num, md5,)
        cursor.execute('INSERT INTO hash VALUES (?, ?)', params)

        conn.commit()
        conn.close()
        return True
    elif result[1] != md5:
        print(f'{num} hash changed. Need to be downloaded. {result[1]} -> {md5}')
        params = (md5, num,)
        cursor.execute('UPDATE hash SET md5 = ? WHERE num = ?', params)

        conn.commit()
        conn.close()
        return True
    else:
        print(f'{num} no difference. {md5}')

        conn.close()
        return False


def download(path):
    # connect ftp
    print('Connecting to FTP...')

    ftp = FTP(url)
    ftp.login('anonymous', 'anonymous')

    print('Connected to FTP!\n')

    # move to path
    try:
        ftp.cwd(path)
    except OSError:
        pass
    except ftplib.error_perm:
        print('Error: could not change to ' + path)

    # list of files
    print('Retrieving files...')

    file_list = ftp.nlst()
    file_list_md5 = []
    file_list_article = []
    file_to_download = []

    print('Retrieved files!\n')

    # separate files
    for file in file_list:
        if file.endswith('.xml.gz.md5'):
            file_list_md5.append(file)
        elif file.endswith('.xml.gz'):
            file_list_article.append(file)

    # download md5
    print('Downloading MD5...')

    i = 0                                   # ! FOR TEST !
    for file in file_list_md5:
        i = i + 1                           # ! FOR TEST !
        if i > 5:                           # ! FOR TEST !
            break                           # ! FOR TEST !

        try:
            print(f'{file} ... ', end='', flush=True)
            ftp.retrbinary("RETR " + file, open(os.path.join(path_md5, file), "wb").write)
            print('SUCCESS')
        except:
            print('FAIL')

    print('Downloaded MD5!\n')

    # check md5 with db
    print('Checking MD5...')

    for file in os.listdir(path_md5):
        if file.endswith('.xml.gz.md5') and file in file_list_md5:
            with open(path_md5 + file, 'r') as file_opened:
                line = file_opened.readline().replace('\n', '')

                num = line[13:17]
                md5 = line[line.find('=')+2:]

                if compare_hash(num, md5):
                    file_to_download.append(num)

    print('Checked MD5!\n')

    # download articles
    print('Downloading articles...')

    for num in file_to_download:
        file = f'pubmed20n{num}.xml.gz'

        if file in file_list_article:
            try:
                print(f'{file} ... ', end='', flush=True)
                ftp.retrbinary("RETR " + file, open(os.path.join(path_article, file), "wb").write)
                print('SUCCESS')
            except:
                print('FAIL')

        else:
            print(f'{file} ... NOT FOUND')

    print('Downloaded articles!\n')

    return


def unzip():
    # create directory
    if not os.path.isdir(const.PUBMED_DIR_UNZIP):
        os.mkdir(const.PUBMED_DIR_UNZIP)

    print('Unzipping articles...')

    for file in os.listdir(path_article):
        if file.endswith('.xml.gz'):
            print(f'{file} ... ', end='', flush=True)
            with gzip.open(path_article + file, 'rb') as f_in:
                with open(const.PUBMED_DIR_UNZIP + file[:-3], 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            print('SUCCESS')

    print('Unzipped articles!\n')


def main():
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--annual", type=int, default=1)
    parser.add_argument("--daily", type=int, default=1)
    parser.add_argument("--unzip", type=int, default=1)
    args = parser.parse_args()

    set_path()
    set_db()

    if args.annual:
        print('< Download from annual >\n')
        download(annual)

    if args.daily:
        print('< Download from daily >\n')
        download(daily)

    if args.unzip:
        unzip()


def run():
    set_path()
    set_db()

    download(daily)

    unzip()


if __name__ == '__main__':
    main()
