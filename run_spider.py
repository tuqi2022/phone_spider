#!/usr/bin/env python3
"""
电信号码爬虫运行脚本

使用方法:
    python run_spider.py               # 默认爬取深圳地区
    python run_spider.py --city 广州   # 指定爬取广州地区
"""

import sys
import argparse
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def main():
    parser = argparse.ArgumentParser(description='电信号码爬虫')
    parser.add_argument('--city', default='深圳', help='要爬取的城市名称')
    args = parser.parse_args()
    
    # 获取Scrapy项目设置
    settings = get_project_settings()
    
    # 创建爬虫进程
    process = CrawlerProcess(settings)
    
    # 启动爬虫
    process.crawl('telecom', city=args.city)
    process.start()


if __name__ == '__main__':
    main()

