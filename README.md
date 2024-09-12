# inTIME: A Machine Learning-Based Framework for Gathering and Leveraging Web Data to Cyber-Threat Intelligence

DOI: [10.3390/electronics10070818](https://doi.org/10.3390/electronics10070818)

## Key Functionality

* **Crawling from different web sources**:
  * **Focused crawl**: for discovering new sources of information
    * Uses machine-learning model
  * **In-depth crawl**: for following the links in a specific domain e.g. forums
    * Uses link filters to limit the non-useful pages on each domain
* **Content Ranking & Classification of Harvested data**:
  * Calculation of relevance scores for the harvested web content with the help of machine-learning language models
  * Classification of the harvested web content based on the relevance scores
* **Named Entity Recognition for finding actionable CTI in the harvested data**:
  * Uses rules and trained data to extract named entities from the relevant web content

## Wikis

1. [**Focused Crawls**](https://gitlab.com/cybertrust/tool-development/crawling-service/-/wikis/1.-Focused-Crawls)
2. [**In-Depth Crawls**](https://gitlab.com/cybertrust/tool-development/crawling-service/-/wikis/2.-Indepth-Crawls)
3. [**Dark Web Crawls**](https://gitlab.com/cybertrust/tool-development/crawling-service/-/wikis/3.-Dark-Web-Crawls)
4. [**Configuration of Parsers**](https://gitlab.com/cybertrust/tool-development/crawling-service/-/wikis/4.-Configuration-of-Parsers)
5. [**Configuration of MongoDB**](https://gitlab.com/cybertrust/tool-development/crawling-service/-/wikis/5.-Configuration-of-MongoDB)
6. [**Configuration of the Content Ranking component**](https://gitlab.com/cybertrust/tool-development/crawling-service/-/wikis/6.-Configuration-of-the-Content-Ranking-component)
7. [**Configuration of the Named Entity Recognition component**](https://gitlab.com/cybertrust/tool-development/crawling-service/-/wikis/7.-Configuration-of-the-Named-Entity-Recognition-component)
8. [**REST API Reference**](https://gitlab.com/cybertrust/tool-development/crawling-service/-/wikis/REST-API-Reference)

## Who do I talk to?

This repository is maintained by **Paris Koloveas** from UoP

* Email: pkoloveas@uop.gr

## Citing this work

If you utilize any of the processes and scripts in this repository, please cite us in the following way:
```bibtex
@Article{KCAST2021,
   AUTHOR     = {Koloveas, Paris
               AND Chantzios, Thanasis
               AND Alevizopoulou, Sofia
               AND Skiadopoulos, Spiros
               AND Tryfonopoulos, Christos},
   TITLE      = {inTIME: A Machine Learning-Based Framework for Gathering and Leveraging Web Data to Cyber-Threat Intelligence},
   JOURNAL    = {Electronics},
   VOLUME     = {10},
   YEAR       = {2021},
   NUMBER     = {7},
   ARTICLE-NUM= {818},
   URL        = {https://www.mdpi.com/2079-9292/10/7/818},
   ISSN       = {2079-9292},
   DOI        = {10.3390/electronics10070818}
}
```
