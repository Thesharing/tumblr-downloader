import os
import logging
from math import ceil

import requests
from bs4 import BeautifulSoup as Soup
from requests.exceptions import RequestException

from tumblr import TumblrDownloader

MAX_RETRY = 20


class MultiThreadDownloader(TumblrDownloader):

    def __init__(self, reblog: bool = True, logging_level: str = 'INFO'):
        """
        :param reblog: Download the reblog posts or not
        :param logging_level: the level of logging information
        """

        super(MultiThreadDownloader, self).__init__(reblog, logging_level)

    def download_likes(self, start=0):
        """
        Download all the posts you liked
        :param start: optional, the page number to start, default is 0
        """
        raise NotImplementedError

    def download_following(self, start=0):
        """
        Download all the posts in the blogs you are following
        :param start: optional, the page number to start, default is 0
        """
        raise NotImplementedError

    def download_blog(self, blog_identifier, start=0):
        """
        Download all the posts in the blog you specified
        :param blog_identifier: name or url of the blog
        :param start: page number to start
        """
        raise NotImplementedError

    def _download_post(self, post):
        """
        Download the images and videos in one post
        :param post: a dict contains post info
        """
        raise NotImplementedError

    def _download_file(self, url, file_name):
        """
        Download the file and save it to local file
        :param url: url of the target data
        :param file_name: name of the local file
        """
        raise NotImplementedError
