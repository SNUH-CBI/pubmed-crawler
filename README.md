# PubMed Crawler

Get journal data from PubMed & JCR and insert them into Elastic Search.


## Dependencies

Python 3.6 or higher needed.

```
pip install -r requirements.txt
```

Constants can be found in `constants.py`


## Download data from PubMed

[Link to PubMed](https://www.nlm.nih.gov/databases/download/pubmed_medline.html)

```
python downloader_pubmed.py
python downloader_pubmed.py --annual 1 --daily 0 --unzip 1
```


## Download data from JCR

[Link to JCR](https://jcr.clarivate.com)

```
python downloader_jcr.py --email jcr@tmpmail.org --pw password1!
python downloader_jcr.py --email jcr@tmpmail.org --pw password1! --fyear 1997 --lyear 2018
```


## Combine PubMed & JCR data

```
python combine_data.py
```


## Insert into Elastic Search

```
python es_insert.py
```


## Scheduled Execution

Download PubMed daily &rarr; Combine data &rarr; Insert into Elastic Search &rarr; Clean up

(JCR data and PubMed annual data should be manually downloaded.)

Example for executing once a week
```
crontab -e
0 3 * * 3 python scheduled_run.py
```
