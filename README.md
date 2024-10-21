# Yande_Downloader
基于python的 yande.re图片爬取程序
## Requirement
- beautifulsoup4==4.12.2
- fake-useragent==1.2.0
- Pillow==10.0.1
- requests==2.31.0
- urllib3==2.0.7

使用以下指令安装需求库
```
pip install -r requirements.txt
```
## How to use
创建YandeDownloader()类
```
H = YandeDownloader()
```
输入标签和页数进行下载
```
H.main()
```
或者使用批量下载
```
tags = [["tag1", "tag2", ...], ["tag3", "tag4", ..], ["tag5"], ....]
pages = [[1, 5], [7, 9]]
H.auto_main(tags, pages)
```
