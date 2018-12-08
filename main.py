from tumblr import TumblrDownloader

if __name__ == '__main__':
    # Init a downloader
    d = TumblrDownloader()

    # Do not download content already downloaded
    d.redownload = False

    # Download all the posts you liked
    d.download_likes()

    # Set downloader to not download reblog posts
    d.reblog = False

    # Download all the posts in the blogs you are following
    d.download_following()

    # Download all the posts in the blog you specified
    d.download_blog('Name or URL of Blog')
