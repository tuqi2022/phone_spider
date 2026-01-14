#!/usr/bin/env python3
"""
测试两个模式：000* 和 111* - 带调试信息
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright


class TestCrawler:
    def __init__(self):
        self.url = 'https://gd.189.cn/TS/tysj/xhb/index.html#/'
        self.phone_numbers = []
        
    async def run(self):
        async with async_playwright() as p:
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
                print('访问网站...')
                await page.goto(self.url, timeout=30000)
                await asyncio.sleep(5)
                
                print('选择深圳...')
                await page.wait_for_selector('text=请确认号码归属地', timeout=10000)
                await page.get_by_text('深圳', exact=True).first.click()
                await asyncio.sleep(1)
                await page.get_by_text('确认,去选号').click()
                await asyncio.sleep(3)
                
                # 只测试两个模式
                for i in [0, 1]:
                    pattern = f'{i}{i}{i}*'
                    print(f'\n{"="*60}')
                    print(f'搜索模式: {pattern}')
                    print(f'{"="*60}')
                    
                    search_box = page.get_by_placeholder('输入任意1-4位尾号搜索')
                    await search_box.clear()
                    await search_box.fill(pattern)
                    await page.get_by_text('搜索').click()
                    await asyncio.sleep(3)
                    
                    search_pattern = f'{i}{i}{i}'
                    phones = await self._extract_with_debug(page, search_pattern)
                    print(f'\n✅ 模式 {pattern} 共找到 {len(phones)} 个匹配号码')
                    self.phone_numbers.extend(phones)
                
                print(f'\n\n总计找到 {len(self.phone_numbers)} 个号码')
                
            except Exception as e:
                print(f'错误: {e}')
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
    
    async def _extract_with_debug(self, page, pattern):
        all_phones = set()
        
        try:
            no_result = await page.query_selector('text=查不到号码信息')
            if no_result:
                print('❌ 查不到号码信息')
                return list(all_phones)
            
            try:
                await page.wait_for_selector('ul > li', timeout=5000)
            except:
                print('❌ 等待号码列表超时')
                return list(all_phones)
            
            # 第一批
            print('\n提取第一批号码：')
            phone_items = await page.query_selector_all('ul > li')
            print(f'  页面上有 {len(phone_items)} 个号码项')
            
            for i, item in enumerate(phone_items):
                try:
                    phone_text = await item.query_selector('p:first-child')
                    if phone_text:
                        phone = await phone_text.inner_text()
                        phone = phone.strip('"')
                        
                        last_7 = phone[-7:] if len(phone) >= 7 else phone
                        match = pattern in last_7
                        
                        if match:
                            all_phones.add(phone)
                            print(f'  [{i+1}] {phone} (后7位:{last_7}) ✅ 匹配')
                        elif i < 3:  # 只打印前3个不匹配的
                            print(f'  [{i+1}] {phone} (后7位:{last_7}) ❌ 不匹配')
                except:
                    continue
            
            print(f'\n第一批找到 {len(all_phones)} 个匹配的号码')
            
        except Exception as e:
            print(f'错误: {e}')
        
        return list(all_phones)


async def main():
    crawler = TestCrawler()
    await crawler.run()


if __name__ == '__main__':
    asyncio.run(main())

