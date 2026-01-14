#!/usr/bin/env python3
"""
电信号码爬虫 - 多城市版本
支持一次爬取多个城市
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import argparse


class TelecomMultiCityCrawler:
    def __init__(self, cities=['深圳']):
        self.cities = cities if isinstance(cities, list) else [cities]
        self.url = 'https://gd.189.cn/TS/tysj/xhb/index.html#/'
        self.results = []  # 存储所有城市的结果
        
    async def run(self):
        """运行爬虫"""
        async with async_playwright() as p:
            # 启动浏览器
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # 访问网站
                print(f'正在访问网站: {self.url}')
                await page.goto(self.url, timeout=30000)
                await asyncio.sleep(5)
                
                # 爬取每个城市
                for city in self.cities:
                    print(f'\n{"="*60}')
                    print(f'开始爬取城市: {city}')
                    print(f'{"="*60}')
                    
                    city_phones = await self._crawl_city(page, city)
                    self.results.append({
                        "city": city,
                        "phone": sorted(city_phones)
                    })
                    
                    print(f'\n✅ {city} 完成，共找到 {len(city_phones)} 个号码')
                
                # 保存结果
                self._save_results()
                print(f'\n\n🎉 全部完成！共爬取 {len(self.cities)} 个城市，{sum(len(r["phone"]) for r in self.results)} 个号码')
                
            except Exception as e:
                print(f'❌ 错误: {e}')
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
    
    async def _crawl_city(self, page, city):
        """爬取指定城市的号码"""
        all_phones = set()
        
        try:
            # 等待并选择城市
            await page.wait_for_selector('text=请确认号码归属地', timeout=10000)
            await page.get_by_text(city, exact=True).first.click()
            await asyncio.sleep(1)
            await page.get_by_text('确认,去选号').click()
            await page.wait_for_load_state('networkidle')
            print(f'城市 {city} 选择完成')
            
            # 搜索所有号码模式
            for i in range(10):
                pattern = f'{i}{i}{i}*'
                print(f'\n正在搜索模式: {pattern}')
                
                # 清空搜索框并输入新模式
                search_box = page.get_by_placeholder('输入任意1-4位尾号搜索')
                await search_box.clear()
                await search_box.fill(pattern)
                
                # 点击搜索按钮
                await page.get_by_text('搜索').click()
                await asyncio.sleep(3)
                
                # 提取号码（包括点击"更多号码"），并验证是否匹配模式
                search_pattern = f'{i}{i}{i}'  # 要匹配的尾号
                phones = await self._extract_phones_with_more(page, search_pattern)
                print(f'找到 {len(phones)} 个符合条件的号码')
                all_phones.update(phones)
            
            # 切换回城市选择（为下一个城市做准备）
            if self.cities.index(city) < len(self.cities) - 1:
                print(f'\n准备切换到下一个城市...')
                change_button = page.locator('text=更换')
                if await change_button.count() > 0:
                    await change_button.click()
                    await asyncio.sleep(2)
                    
        except Exception as e:
            print(f'爬取城市 {city} 时出错: {e}')
        
        return list(all_phones)
    
    async def _extract_phones_with_more(self, page, pattern):
        """提取搜索结果的号码（不包括推荐号码）"""
        all_phones = set()
        
        try:
            # 先检查是否有"查不到号码信息"
            no_result = await page.query_selector('text=查不到号码信息')
            if no_result:
                return list(all_phones)
            
            # 等待号码列表加载
            try:
                await page.wait_for_selector('ul > li', timeout=5000)
            except:
                return list(all_phones)
            
            # 提取所有号码（搜索结果本身就是全部，不需要点击"更多号码"）
            phones = await self._extract_current_phones(page, pattern)
            all_phones.update(phones)
                    
        except Exception as e:
            print(f'提取号码时出错: {e}')
        
        return list(all_phones)
    
    async def _extract_current_phones(self, page, pattern):
        """提取当前页面的手机号码，只返回匹配指定模式的号码
        
        Args:
            page: Playwright页面对象
            pattern: 要匹配的尾号模式，如 "000"、"111" 等
        
        Returns:
            匹配模式的号码集合
        """
        phones = set()
        try:
            phone_items = await page.query_selector_all('ul > li')
            
            for item in phone_items:
                try:
                    phone_text = await item.query_selector('p:first-child')
                    if phone_text:
                        phone = await phone_text.inner_text()
                        phone = phone.strip('"')
                        
                        # 验证号码是否匹配搜索模式
                        if self._match_pattern(phone, pattern):
                            phones.add(phone)
                except:
                    continue
        except:
            pass
        
        return phones
    
    def _match_pattern(self, phone, pattern):
        """检查号码是否匹配搜索模式
        
        搜索 "000*" 应该匹配以下情况：
        - 尾号包含连续的 "000"，如 "xxx0004" (包含000)
        - 尾号是 "x000", "xx000", "xxx000" 等
        
        Args:
            phone: 11位手机号
            pattern: 3位重复数字，如 "000", "111", "444"
        
        Returns:
            是否匹配
        """
        if len(phone) < 11:
            return False
        
        # 获取后7位号码用于匹配
        last_digits = phone[-7:]
        
        # 检查是否包含连续的3位重复数字
        return pattern in last_digits
    
    def _save_results(self):
        """保存结果到JSON文件"""
        filename = f'phones_multi_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('[\n')
            for idx, city_data in enumerate(self.results):
                f.write('  {\n')
                f.write(f'    "city": "{city_data["city"]}",\n')
                f.write('    "phone": [\n')
                phones = city_data["phone"]
                for i, phone in enumerate(phones):
                    if i < len(phones) - 1:
                        f.write(f'      "{phone}",\n')
                    else:
                        f.write(f'      "{phone}"\n')
                f.write('    ]\n')
                if idx < len(self.results) - 1:
                    f.write('  },\n')
                else:
                    f.write('  }\n')
            f.write(']\n')
        
        print(f'\n📁 结果已保存到: {filename}')


async def main():
    parser = argparse.ArgumentParser(description='电信号码爬虫 - 多城市版')
    parser.add_argument('--cities', nargs='+', default=['深圳'], 
                       help='要爬取的城市名称（可以指定多个，用空格分隔）')
    args = parser.parse_args()
    
    print('=' * 60)
    print('电信号码爬虫 - 多城市版 - 启动中...')
    print(f'目标城市: {", ".join(args.cities)}')
    print('=' * 60)
    
    crawler = TelecomMultiCityCrawler(cities=args.cities)
    await crawler.run()


if __name__ == '__main__':
    asyncio.run(main())

