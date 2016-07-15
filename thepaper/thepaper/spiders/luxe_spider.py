#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'yinzishao'
import re
from scrapy.exceptions import CloseSpider
import scrapy
from bs4 import BeautifulSoup
import logging
from thepaper.items import NewsItem
import json
logger = logging.getLogger("LuxeSpider")
from thepaper.settings import *

class LuxeSpider(scrapy.spiders.Spider):
    domain = "http://luxe.co/"
    name = "luxe"
    allowed_domains = ["luxe.co"]
    end_day = END_DAY
    end_now = END_NOW
    index_page = 1
    crawl_page = 5
    page_url = "http://luxe.co/page/%s/"
    start_urls =[
        page_url % index_page
    ]
    def parse(self, response):
        soup = BeautifulSoup(response.body)
        search = soup.find("section",id="omc-main")
        if search:
            news_list = search.find_all("article")
            if news_list:
                for news in news_list:
                    abstract,author,news_date = None,None,None
                    #find date and author
                    if news.find("p",class_="omc-date-time-one"):
                        date_aut = list(news.find("p",class_="omc-date-time-one").strings)
                        author = date_aut[1]
                        news_date = date_aut[2][5:]
                        #结束条件
                        struct_date = datetime.datetime.strptime(news_date,"%Y-%m-%d")
                        delta = self.end_now-struct_date
                        if delta.days == self.end_day:
                            pass
                            # raise CloseSpider('today scrapy end')
                    titile = news.h2.text if news.h2 else None
                    news_url= news.h2.a.get("href",None) if news.h2.a else None
                    news_no = news_url.rsplit("/")[-2]
                    topic_group = news.find("h3",class_="omc-blog-one-cat")
                    topics = []
                    if topic_group:
                        for topic in topic_group.find_all("a"):
                            topics.append(topic.string)

                    #中间会有空隙
                    # topic = list(news.find("h3",class_="omc-blog-one-cat").strings) if news.find("h3",class_="omc-blog-one-cat") else None

                    if news.find("p",class_="omc-blog-one-exceprt"):
                        abstract = news.find("p",class_="omc-blog-one-exceprt").text.strip()
                    pic = news.img.get("src",None) if news.img else None
                    #生成新闻item 并抛向解析内容
                    item = NewsItem(news_url=news_url,title=titile,abstract=abstract,pic=pic,author=author,news_date=news_date,crawl_date=NOW,news_no=news_no,topic=topics)
                    request =  scrapy.Request(news_url,callback=self.parse_news)
                    request.meta["item"]=item
                    if news_url:
                        yield request
                    else:
                        logger.info("can't find news url")
            else:
                logger.info("can't find news list")

        else:
            logger.info("can't find main container")
        #获取下一页链接
        origin_url = response.url
        next_page_number = 2
        if "page" in origin_url:
            next_page_number = int(origin_url.rsplit('/')[-2])+1
        if next_page_number <self.crawl_page:
            next_url = self.page_url % next_page_number
            yield scrapy.Request(next_url,callback=self.parse)
    def parse_news(self,response):
        item = response.meta["item"]
        soup = BeautifulSoup(response.body)
        news_content_group = soup.find("div",class_="entry-content group")
        #去除相关阅读
        news_content_group.find("div",class_="related_posts").replace_with("")
        content = news_content_group.text.strip()
        item["content"] = content
        yield item

