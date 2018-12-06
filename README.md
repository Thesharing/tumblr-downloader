# Tumblr Downloader

Download and archive all your likes and following in your tumblr blog using tumblr API.

[中文版本](./README-zh.md)

## Install

Require Python >= 3.5, you can install the python from [official website](https://www.python.org/downloads/) or install [Anaconda 3](https://www.anaconda.com/download/) instead.

\* You can use [virtualenv](https://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000/001432712108300322c61f256c74803b43bfd65c6f8d0d0000), [conda create](https://conda.io/docs/user-guide/tasks/manage-python.html) or [pipenv](https://pipenv.readthedocs.io/) to create an isolated running environment.

Install the requirement by: 

```bash
pip install -i requirements.txt
```

Or install the requirements manually: 

| Package Name                                   |
| ---------------------------------------------- |
| [pytumblr](https://github.com/tumblr/pytumblr) |
| requests                                       |
| yaml                                           |
| beautifulsoup4                                 |
| lxml                                           |

## Execution

> In some regions you will need a proxy to use this downloader. If the downloader is not running with proxy, try to set the proxy `Global Mode` and re

1. Enter https://www.tumblr.com/oauth/apps to register an application and get a OAuth Key. OAuth 2.0 is the way to authentication and access the content of your blog via tumblr API. ([Get to know about OAuth](https://en.wikipedia.org/wiki/OAuth))

   But note that Tumblr API has rate limits, so don't overuse it or spread your OAuth Key to public.

   > Rate Limits
   >
   > Newly registered consumers are rate limited to 1,000 requests per hour, and 5,000 requests per day. If your application requires more requests for either of these periods, please use the *'Request rate limit removal'* link on an app above.

2. After you registration you will get a OAuth Consumer Key and a Secret Key. 
3. Config the functions you need in main.py, currently three functions are provided:

| Function Name                            | Explanation                                           |
| ---------------------------------------- | ----------------------------------------------------- |
| download_likes()                         | Download all the posts you liked                      |
| download_following()                     | Download all the posts in the blogs you are following |
| download_blog(`name or url of the blog`) | Download all the posts in the blog you specified      |

- The functions has two optional parameters: `start` and `max_page`. `start` is the page number to start; `max_page` is the max page number to download in case it takes too much time downloading one blog. `max_page` cannot be larger than 50, since downloader cannot access 50 and more pages via tumblr API. 

  > When using the offset parameter the maximum limit on the offset is 1000. If you would like to get more results than that use either before or after.

- the parameter of `download_blog` is the name or URL of the blog. Take [support](https://support.tumblr.com/) blog as an example, the blog name should be `support`, and the URL should be `support.tumblr.com`.

- Set the downloader to not download reblog posts by setting`downloader.reblog = False`.

4. Run `python main.py` to start the first-time config, you will be redirected to a interactive console provided by pytumblr. 
   1. First input the OAuth Consumer Key and Secret Key you get before.
   2. The console will return <u>an authorize url</u> to authorize your own tumblr account to the downloader. Copy and paste it in web browser and visit it. The page will ask you to authorize. Allow it. Then the url will be redirected to another url, which contains the `oauth_verifier` token, copy and paste it back to the console.
   3. Finally the downloader will get `oauth_token` and `oauth_token_secret` and continue to download your blog.

## Reference

[API | Tumblr](https://www.tumblr.com/docs/en/api/v2)

[Applications | Tumblr](https://www.tumblr.com/oauth/apps)

[PyTumblr | Github](https://github.com/tumblr/pytumblr)
