# Tumblr Downloader

通过Tumblr API下载Tumblr中Likes的所有帖文，以及关注的所有博主的帖文.

[English Version](./README.md)

## 安装

需要安装Python >= 3.5. 可以在[官方网站](https://www.python.org/downloads/)安装，或者安装[Anaconda 3](https://www.anaconda.com/download/).

\* 在配置环境前，可以通过[virtualenv](https://www.liaoxuefeng.com/wiki/0014316089557264a6b348958f449949df42a6d3a2e542c000/001432712108300322c61f256c74803b43bfd65c6f8d0d0000), [conda create](https://conda.io/docs/user-guide/tasks/manage-python.html) 或者 [pipenv](https://pipenv.readthedocs.io/) 配置虚拟环境以避免影响主开发环境.

运行以下命令来安装依赖项：

```bash
pip install -i requirements.txt
```

或者手动安装依赖项：

| Package Name                                   |
| ---------------------------------------------- |
| [pytumblr](https://github.com/tumblr/pytumblr) |
| requests                                       |
| yaml                                           |
| beautifulsoup4                                 |
| lxml                                           |

## 运行

> ~~可能~~需要代理下载Tumblr的帖文. 如果已经开启了代理还是无法正常运行，请尝试将代理设置为`全局模式`.

1. 访问 https://www.tumblr.com/oauth/apps 注册应用程序，注册完成后会得到一个OAuth密钥. OAuth 2.0 是一种加密认证方式，可以用于API账号认证，通过OAuth 2.0可以访问Tumblr API进而下载帖文. （[了解更多关于OAuth 2.0的知识](http://www.ruanyifeng.com/blog/2014/05/oauth_2_0.html)）

   不过要注意Tumblr API有流量限制，因此避免一次下载过多帖文，并且不要泄露你的OAuth密钥.

   > Rate Limits
   >
   > Newly registered consumers are rate limited to 1,000 requests per hour, and 5,000 requests per day. If your application requires more requests for either of these periods, please use the *'Request rate limit removal'* link on an app above.

2. 注册完成后可以看到  OAuth Consumer Key 和 Secret Key，下面会用到.

3. 根据需要在 main.py 中配置你需要的功能，目前一共有三个功能：

| 方法名                                   | 注释                         |
| ---------------------------------------- | ---------------------------- |
| download_likes()                         | 下载所有喜欢的帖文           |
| download_following()                     | 下载所有关注的博客的帖文     |
| download_blog(`name or url of the blog`) | 下载指定某一个博客的所有帖文 |

如果不想下载转帖的帖文（即只下载原创帖文），可以设置`downloader.reblog = False`.

4. 运行 `python main.py` ，如果是第一次运行的话需要进行授权操作. 
   1. 首先输入 OAuth Consumer Key 和 Secret Key.
   2. 命令行会返回一个认证链接（authorize url），将其复制到浏览器中进行访问，在访问的页面中选择“允许”，然后浏览器会跳转到下一个URL，在其中找到`oauth_verifier`字段，复制粘贴到命令行中.
   3. 下载器会继续获得`oauth_token` 和 `oauth_token_secret`，并自动开始下载.

## 参考


[API | Tumblr](https://www.tumblr.com/docs/en/api/v2)

[Applications | Tumblr](https://www.tumblr.com/oauth/apps)

[PyTumblr | Github](https://github.com/tumblr/pytumblr)
