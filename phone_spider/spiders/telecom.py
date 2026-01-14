import scrapy
from scrapy_playwright.page import PageMethod
import json
import asyncio
from datetime import datetime


class TelecomSpider(scrapy.Spider):
    name = 'telecom'
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        'CONCURRENT_REQUESTS': 1,  # 降低并发请求数
        'DOWNLOAD_DELAY': 2,  # 添加延迟
    }
    
    def __init__(self, city='深圳', *args, **kwargs):
        super(TelecomSpider, self).__init__(*args, **kwargs)
        self.city = city
        self.start_urls = ['https://gd.189.cn/TS/tysj/xhb/index.html#/']
        self.phone_numbers = []
        
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'networkidle'),
                    ],
                },
                errback=self.errback_close_page,
            )
    
    async def parse(self, response):
        page = response.meta['playwright_page']
        
        try:
            # 等待地区选择弹窗出现
            await page.wait_for_selector('text=请确认号码归属地', timeout=10000)
            self.logger.info(f'地区选择弹窗已出现')
            
            # 点击目标城市
            await page.get_by_text(self.city, exact=True).first.click()
            self.logger.info(f'已选择城市: {self.city}')
            
            # 点击确认按钮
            await page.get_by_text('确认,去选号').click()
            await page.wait_for_load_state('networkidle')
            self.logger.info('已确认城市选择')
            
            # 搜索所有号码模式 000* 到 999*
            for i in range(10):
                pattern = f'{i}{i}{i}*'
                self.logger.info(f'开始搜索模式: {pattern}')
                
                # 清空搜索框并输入新模式
                search_box = page.get_by_placeholder('输入任意1-4位尾号搜索')
                await search_box.clear()
                await search_box.fill(pattern)
                
                # 点击搜索按钮
                await page.get_by_text('搜索').click()
                await asyncio.sleep(3)  # 等待搜索结果加载
                
                # 提取号码
                phones = await self._extract_phones(page)
                self.logger.info(f'模式 {pattern} 找到 {len(phones)} 个号码')
                self.phone_numbers.extend(phones)
                
            # 保存结果
            self._save_results()
            
        except Exception as e:
            self.logger.error(f'爬取过程中出错: {e}')
        finally:
            await page.close()
    
    async def _extract_phones(self, page):
        """提取页面上的所有手机号码"""
        phones = []
        try:
            # 等待号码列表加载
            await page.wait_for_selector('ul > li', timeout=5000)
            
            # 获取所有号码项
            phone_items = await page.query_selector_all('ul > li')
            
            for item in phone_items:
                try:
                    # 提取号码
                    phone_text = await item.query_selector('p:first-child')
                    if phone_text:
                        phone = await phone_text.inner_text()
                        phone = phone.strip('"')
                        
                        # 提取最低消费
                        min_cost_elem = await item.query_selector('p:nth-child(2)')
                        min_cost = await min_cost_elem.inner_text() if min_cost_elem else ''
                        
                        # 提取预存话费
                        deposit_elem = await item.query_selector('p:nth-child(3)')
                        deposit = await deposit_elem.inner_text() if deposit_elem else ''
                        
                        phones.append({
                            'phone': phone,
                            'min_cost': min_cost,
                            'deposit': deposit,
                            'city': self.city,
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                except Exception as e:
                    self.logger.error(f'提取单个号码信息时出错: {e}')
                    continue
                    
            # 检查是否有"更多号码"按钮，如果有则点击加载更多
            more_button = await page.query_selector('text=更多号码')
            if more_button:
                await more_button.click()
                await asyncio.sleep(2)
                # 递归提取新加载的号码
                new_phones = await self._extract_phones(page)
                phones.extend(new_phones)
                
        except Exception as e:
            self.logger.warning(f'提取号码时出错: {e}')
        
        return phones
    
    def _save_results(self):
        """保存结果到JSON文件"""
        filename = f'phones_{self.city}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.phone_numbers, f, ensure_ascii=False, indent=2)
        self.logger.info(f'保存了 {len(self.phone_numbers)} 个号码到 {filename}')
    
    async def errback_close_page(self, failure):
        page = failure.request.meta.get('playwright_page')
        if page:
            await page.close()
