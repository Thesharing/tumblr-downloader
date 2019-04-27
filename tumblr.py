import os
import logging
import time
from math import ceil

import yaml
import requests
from pytumblr import TumblrRestClient
from bs4 import BeautifulSoup as Soup
from requests.exceptions import RequestException

from util import oauth

MAX_RETRY = 20


class TumblrDownloader:

    def __init__(self, reblog: bool = True, redownload: bool = False, logging_level: str = 'INFO'):
        """
        :param reblog: Download the reblog posts or not
        :param logging_level: the level of logging information
        """

        logging.basicConfig(format='[%(levelname)s]\t%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                            level=getattr(logging, logging_level))

        self.reblog = reblog
        self.redownload = redownload

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

    def download_likes(self, before_timestamp=None, use_native_filenames=False):
        """
        Download all the posts you liked
        :param before_timestamp: optional, get likes before a certain like-timestamp, instead of the most recent.
        :param use_native_filenames: optional, use raw tumblr names, instead of blog-{filenum}, as filenames.
        """

        # Create likes folder
        download_path = os.path.join(self.download_folder, './likes')
        if not os.path.isdir(download_path):
            os.mkdir(download_path)

        names = BlogName(download_path) if not use_native_filenames else None
        last_timestamp = before_timestamp or int(time.time())

        page = 1
        postnum = 1
        last_post_url = ''
        count = 0
        total = self.user_info['likes']
        logging.info('Likes | {0} ongoing'.format(total))

        while True:
            logging.info('Downloading page {0} before timestamp {1}'.format(page, last_timestamp))

            likes = self.client.likes(limit=20, before=last_timestamp+1)['liked_posts']
            if len(likes) == 1 and last_post_url == likes[0]['post_url']:
                break

            for post in likes:
                last_post_url = post['post_url']

                if len(post['trail']) > 1 and not self.reblog:
                    logging.info('Skip | Reblog post: {0} #{1} @{2} | {3}'.format(
                        post['blog_name'], postnum, post['liked_timestamp'], post['post_url']))

                else:
                    logging.info('Likes | Start post {0} #{1} @{2} | {3}'.format(
                        post['blog_name'], postnum, post['liked_timestamp'], post['post_url']))

                    self._download_post(post=post, path=download_path, names=names)

                    count += 1
                last_timestamp = post['liked_timestamp']
                postnum += 1

            page += 1

        logging.info('Likes | {0} / {1} downloaded'.format(count, total))

    def download_following(self, start_page=0, max_page=50, start_blog=None):
        """
        Download all the posts in the blogs you are following
        :param start_page: optional, the page number to start, default is 0
        :param max_page: optional, limit the max page number, in case it take too much time downloading one blog
        :param start_blog: optional, the blog name to start
        """
        count = 0
        total = self.user_info['following']
        logging.info('Following | {0} blogs total'.format(total))

        start_flag = start_blog is None

        for page in range(start_page, min(ceil(total / 20), max_page)):
            logging.info('Following | Page {0} ongoing'.format(page))

            for blog in self.client.following(limit=20, offset=page * 20)['blogs']:

                # To start from a specified blog
                if not start_flag:
                    if blog['name'] == start_blog:
                        start_flag = True
                    else:
                        continue

                logging.info('Following | Start blog {0} | {1}'.format(blog['name'], blog['url']))

                self.download_blog(blog['name'])
                count += 1

        logging.info('Following | {0} / {1} blogs downloaded'.format(count, total))

    def download_blog(self, blog_identifier, before_timestamp=None):
        """
        Download all the posts in the blog you specified
        :param blog_identifier: name or url of the blog
        :param before_timestamp: optional, get likes before a certain like-timestamp, instead of the most recent.
        """

        # Create a blog folder
        download_path = os.path.join(self.download_folder, blog_identifier)
        if not os.path.isdir(download_path):
            os.mkdir(download_path)

        last_timestamp = before_timestamp or int(time.time())
        page = 1
        postnum = 1
        last_post_url = ''
        count = 0
        total = self.client.posts(blogname=blog_identifier)['total_posts']
        logging.info('Blog | {0} posts total'.format(total))

        while True:
            logging.info('Blog | Page {0} Post {1} Timestamp {2} ongoing'.format(page, postnum, last_timestamp))

            posts = self.client.posts(blogname=blog_identifier, before=last_timestamp+1)['posts']
            if len(posts) == 1 and last_post_url == posts[0]['post_url']:
                break

            for post in posts:
                last_post_url = post['post_url']
                if 'trail' in post and len(post['trail']) > 1 and not self.reblog:
                    logging.info('Skip | Reblog post: {0} #{1} @{2} | {3}'.format(
                        post['post_url'].split('/')[-2], postnum, post['timestamp'], post['post_url']))

                else:
                    logging.info('Blog | Start post {0} #{1} @{2} | {3}'.format(
                        post['post_url'].split('/')[-2], postnum, post['timestamp'], post['post_url']))

                    self._download_post(post, download_path)
                    count += 1

                last_timestamp = post['timestamp']
                postnum += 1
            page += 1

        logging.info('Blog | {0} / {1} posts downloaded'.format(count, total))

    def _download_post(self, post, path, names=None):
        """
        Download the images and videos in one post
        :param post: a dict contains post info
        :param path: the path of folder
        :param names: to specify the file name
        """
        blog_name = post['blog_name']

        if post['type'] == 'photo':
            for photo in post['photos']:
                if names is None:
                    file_name = photo['original_size']['url'].split('/')[-1]
                    self._download_file(photo['original_size']['url'], os.path.join(path, file_name))
                else:
                    file_name = names.get(blog_name, 'jpg')
                    if self._download_file(photo['original_size']['url'], os.path.join(path, file_name)):
                        names.inc(blog_name)

        elif post['type'] == 'video':
            if names is None:
                if 'video_url' in post:
                    file_name = post['video_url'].split('/')[-1]
                    self._download_file(post['video_url'], os.path.join(path, file_name))
            else:
                file_name = names.get(blog_name, 'mp4')
                if self._download_file(post['video_url'], os.path.join(path, file_name)):
                    names.inc(blog_name)

        elif post['type'] == 'text':
            raw = post['body']
            soup = Soup(raw, 'lxml')

            # Find all images
            for img in soup.find_all('img'):
                if names is None:
                    file_name = img['src'].split('/')[-1]
                    if not self._download_file(img['src'].replace('_540', '_1280'), os.path.join(path, file_name)):
                        self._download_file(img['src'], os.path.join(path, file_name))
                else:
                    file_name = names.get(blog_name, 'jpg')
                    if self._download_file(img['src'].replace('_540', '_1280'), os.path.join(path, file_name)):
                        names.inc(blog_name)
                    elif self._download_file(img['src'], os.path.join(path, file_name)):
                        names.inc(blog_name)

            # Find all videos
            for video in soup.find_all('source'):
                if names is None:
                    file_name = video['src'].split('/')[-1]
                    self._download_file(video['src'], os.path.join(path, file_name))
                else:
                    file_name = names.get(blog_name, 'mp4')
                    if self._download_file(video['src'], os.path.join(path, file_name)):
                        names.inc(blog_name)

    def _download_file(self, url, path):
        """
        Download the file and save it to local file
        :param url: url of the target data
        :param path: name of the local file
        """
        if os.path.exists(path) and not self.redownload:
            return True

        while True:
            try:
                r = requests.get(url, timeout=10)
            except RequestException:
                logging.error('Error | {0} | {1}'.format(os.path.basename(path), url))
                continue

            if r.status_code > 400:
                logging.error('{0} | {1} | {2}'.format(r.status_code, os.path.basename(path), url))
                return False

            elif r.status_code != 200:
                logging.warning('{0} | {1} | {2}'.format(r.status_code, os.path.basename(path), url))
                continue

            else:
                logging.info('Download | {0} | {1}'.format(os.path.basename(path), url))
                self._save(r.content, path)
                return True

    @staticmethod
    def _save(content, path):
        """
        :param content: Content of file
        :param path: Path of local file
        """
        with open(path, 'wb') as f:
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
