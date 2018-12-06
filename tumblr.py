import os
import logging
from math import ceil

import yaml
import requests
from pytumblr import TumblrRestClient
from bs4 import BeautifulSoup as Soup
from requests.exceptions import RequestException

from util import oauth

MAX_RETRY = 20


class TumblrDownloader:

    def __init__(self, reblog: bool = True, logging_level: str = 'INFO'):
        """
        :param reblog: Download the reblog posts or not
        :param logging_level: the level of logging information
        """

        logging.basicConfig(format='[%(levelname)s]\t%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                            level=getattr(logging, logging_level))

        self.reblog = reblog

        # Get Token from file or interactive console
        yaml_path = '.tumblr'
        if not os.path.exists(yaml_path):
            logging.info('Tokens not found, will redirect to interactive oauth procedure')
            tokens = oauth(yaml_path)
        else:
            yaml_file = open(yaml_path, "r")
            tokens = yaml.safe_load(yaml_file)
            yaml_file.close()
        logging.info('Tokens ready')

        # Init client
        self.client = TumblrClient(
            consumer_key=tokens['consumer_key'],
            consumer_secret=tokens['consumer_secret'],
            oauth_token=tokens['oauth_token'],
            oauth_secret=tokens['oauth_token_secret']
        )

        # Get user info
        self.user_info = self.client.info()['user']
        logging.info('User Name: {0} | Likes: {1} | Following: {2}'.format(
            self.user_info['name'], self.user_info['likes'], self.user_info['following']))

        # Init download folder
        self.download_folder = './download'
        if not os.path.isdir(self.download_folder):
            os.mkdir(self.download_folder)

        # Scan files in the download folder
        self.names = BlogName(self.download_folder)

    def download_likes(self, start=0, max_page=50):
        """
        Download all the posts you liked
        :param start: optional, the page number to start, default is 0
        :param max_page: optional, limit the max page number, in case it take too much time downloading one blog
        """
        count = 0
        total = self.user_info['likes']
        logging.info('Likes | {0} ongoing'.format(total))

        for page in range(start, min(ceil(total / 20), max_page)):
            logging.info('Downloading page {0}'.format(page))

            for post in self.client.likes(limit=20, offset=page * 20)['liked_posts']:

                if len(post['trail']) > 1 and not self.reblog:
                    logging.info('Skip | Reblog post: {0} | {1}'.format(post['blog_name'], post['post_url']))

                else:
                    logging.info('Likes | Start post {0} | {1}'.format(post['blog_name'], post['post_url']))

                    self._download_post(post)

                    count += 1

        logging.info('Likes | {0} / {1} downloaded'.format(count, total))

    def download_following(self, start=0, max_page=50):
        """
        Download all the posts in the blogs you are following
        :param start: optional, the page number to start, default is 0
        :param max_page: optional, limit the max page number, in case it take too much time downloading one blog
        """
        count = 0
        total = self.user_info['following']
        logging.info('Following | {0} blogs total'.format(total))

        for page in range(start, min(ceil(total / 20), max_page)):
            logging.info('Following | Page {0} ongoing'.format(page))

            for blog in self.client.following(limit=20, offset=page * 20)['blogs']:
                logging.info('Following | Start blog {0} | {1}'.format(blog['name'], blog['url']))

                self.download_blog(blog['name'])
                count += 1

        logging.info('Following | {0} / {1} blogs downloaded'.format(count, total))

    def download_blog(self, blog_identifier, start=0, max_page=50):
        """
        Download all the posts in the blog you specified
        :param blog_identifier: name or url of the blog
        :param start: page number to start
        :param max_page: optional, limit the max page number, in case it take too much time downloading one blog
        """
        count = 0
        total = self.client.posts(blogname=blog_identifier)['total_posts']
        logging.info('Blog | {0} posts total'.format(total))

        for page in range(start, min(ceil(total / 20), max_page)):
            logging.info('Blog | Page {0} ongoing'.format(page))

            for post in self.client.posts(blogname=blog_identifier, limit=20, offset=page * 20)['posts']:

                if len(post['trail']) > 1 and not self.reblog:
                    logging.info('Skip | Reblog post: {0} | {1}'.format(
                        post['post_url'].split('/')[-2], post['post_url']))

                else:
                    logging.info('Blog | Start post {0} | {1}'.format(
                        post['post_url'].split('/')[-2], post['post_url']))

                    self._download_post(post)
                    count += 1

        logging.info('Blog | {0} / {1} posts downloaded'.format(count, total))

    def _download_post(self, post):
        """
        Download the images and videos in one post
        :param post: a dict contains post info
        """
        blog_name = post['blog_name']

        if post['type'] == 'photo':
            for photo in post['photos']:
                file_name = self.names.get(blog_name, 'jpg')
                if self._download_file(photo['original_size']['url'], file_name):
                    self.names.inc(blog_name)

        elif post['type'] == 'video':
            file_name = self.names.get(blog_name, 'mp4')
            if self._download_file(post['video_url'], file_name):
                self.names.inc(blog_name)

        elif post['type'] == 'text':
            raw = post['body']
            soup = Soup(raw, 'lxml')

            # Find all images
            for img in soup.find_all('img'):
                file_name = self.names.get(blog_name, 'jpg')
                if self._download_file(img['src'].replace('_540', '_1280'), file_name):
                    self.names.inc(blog_name)
                elif self._download_file(img['src'], file_name):
                    self.names.inc(blog_name)

            # Find all videos
            for video in soup.find_all('source'):
                file_name = self.names.get(blog_name, 'mp4')
                if self._download_file(video['src'], file_name):
                    self.names.inc(blog_name)

    def _download_file(self, url, file_name):
        """
        Download the file and save it to local file
        :param url: url of the target data
        :param file_name: name of the local file
        """
        while True:
            try:
                r = requests.get(url, timeout=10)
            except RequestException:
                logging.error('Error | {0} | {1}'.format(file_name, url))
                continue

            if r.status_code > 400:
                logging.error('{0} | {1} | {2}'.format(r.status_code, file_name, url))
                return False

            elif r.status_code != 200:
                logging.warning('{0} | {1} | {2}'.format(r.status_code, file_name, url))
                continue

            else:
                logging.info('Download | {0} | {1}'.format(file_name, url))
                self._save(file_name, r.content)
                return True

    def _save(self, file_name, content):
        with open(os.path.join(self.download_folder, file_name), 'wb') as f:
            f.write(content)


class TumblrClient:
    def __init__(self, **kwargs):
        self.client = TumblrRestClient(**kwargs)
        self.dummy = {
            'likes': {'liked_posts': []},
            'following': {'blogs': []},
            'posts': {'total_posts': 0, 'posts': []}
        }

    def info(self):
        return self.client.info()

    def posts(self, **kwargs):
        retry = MAX_RETRY
        while retry:
            try:
                return self.client.posts(**kwargs)
            except RequestException:
                retry -= 1
        return self.dummy['posts']

    def following(self, **kwargs):
        retry = MAX_RETRY
        while retry:
            try:
                return self.client.following(**kwargs)
            except RequestException:
                retry -= 1
        return self.dummy['following']

    def likes(self, **kwargs):
        retry = MAX_RETRY
        while retry:
            try:
                return self.client.likes(**kwargs)
            except RequestException:
                retry -= 1
        return self.dummy['likes']


class BlogName:

    def __init__(self, path):
        self.path = path
        self.dict = {}
        for item in os.listdir(path):
            split = os.path.splitext(item)[0].split('-')
            name = split[0]

            if name in self.dict:
                self.dict[name] += 1
            else:
                self.dict[name] = 2

    def get(self, name, ext):
        return '{}-{}.{}'.format(name, self.dict[name] if name in self.dict else 1, ext)

    def inc(self, name):
        if name in self.dict:
            self.dict[name] += 1
        else:
            self.dict[name] = 2
