#!/usr/bin/env python3
"""
电信号码爬虫 - 简化版本
直接使用 Playwright，不依赖 Scrapy
"""

import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright
import argparse


class TelecomCrawler:
    def __init__(self, city='深圳', concurrent=False):
        self.city = city
        self.url = 'https://gd.189.cn/TS/tysj/xhb/index.html#/'
        self.phone_numbers = []  # 存储所有号码（字符串格式）
        self.concurrent = concurrent  # 是否使用并发模式
        
    async def run(self):
        """运行爬虫 - 根据配置选择串行或并发"""
        if self.concurrent:
            await self._run_concurrent()
        else:
            await self._run_serial()
    
    async def _run_serial(self):
        """运行爬虫（串行版本 - 稳定可靠）"""
        async with async_playwright() as p:
            # 启动浏览器（模拟真实用户）
            browser = await p.chromium.launch(
                headless=True,  # 后台运行
                args=['--disable-blink-features=AutomationControlled']
            )
            
            # 创建页面并设置viewport
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # 访问网站
                print(f'正在访问网站: {self.url}')
                await page.goto(self.url, timeout=30000)
                
                # 等待页面完全加载
                print('等待页面加载...')
                await asyncio.sleep(5)
                
                # 等待地区选择弹窗
                print('等待地区选择弹窗...')
                await page.wait_for_selector('text=请确认号码归属地', timeout=10000)
                
                # 选择城市
                print(f'选择城市: {self.city}')
                await page.get_by_text(self.city, exact=True).first.click()
                await asyncio.sleep(1)
                
                # 点击确认按钮
                await page.get_by_text('确认,去选号').click()
                await page.wait_for_load_state('networkidle')
                print('城市选择完成')
                
                # 搜索所有号码模式
                for i in range(10):
                    pattern = f'{i}{i}{i}*'
                    print(f'\n正在搜索模式: {pattern}')
                    
                    # 清空搜索框并输入新模式
                    search_box = page.get_by_placeholder('输入任意1-4位尾号搜索')
                    await search_box.clear()
                    await asyncio.sleep(0.5)
                    await search_box.fill(pattern)
                    await asyncio.sleep(1)
                    
                    # 点击搜索按钮（多次尝试确保点击成功）
                    search_button = page.get_by_text('搜索')
                    await search_button.click()
                    await asyncio.sleep(2)
                    
                    # 再次点击确保搜索执行
                    await search_button.click()
                    await asyncio.sleep(5)  # 等待搜索结果和推荐号码完全加载
                    
                    # 提取号码（包括点击"更多号码"），并验证是否匹配模式
                    search_pattern = f'{i}{i}{i}'  # 要匹配的尾号
                    phones = await self._extract_phones_with_more(page, search_pattern)
                    print(f'找到 {len(phones)} 个符合条件的号码')
                    self.phone_numbers.extend(phones)
                    
                # 保存结果
                self._save_results()
                print(f'\n✅ 爬取完成！共找到 {len(self.phone_numbers)} 个号码')
                
            except Exception as e:
                print(f'❌ 错误: {e}')
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
    
    async def _run_concurrent(self):
        """运行爬虫（并发版本 - 速度快）"""
        async with async_playwright() as p:
            # 启动浏览器（模拟真实用户）
            browser = await p.chromium.launch(
                headless=True,  # 后台运行
                args=['--disable-blink-features=AutomationControlled']
            )
            
            try:
                # 使用信号量限制并发数量（一次最多3个）
                semaphore = asyncio.Semaphore(3)
                
                async def search_with_limit(digit):
                    async with semaphore:
                        return await self._search_pattern(browser, digit)
                
                # 并发执行所有搜索任务
                tasks = [search_with_limit(i) for i in range(10)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 收集结果并去重
                phone_set = set()
                for result in results:
                    if isinstance(result, Exception):
                        continue
                    elif result:
                        pattern, phones = result
                        phone_set.update(phones)
                        # 汇总输出
                        if len(phones) > 0:
                            print(f'\n✓ {pattern}: 找到 {len(phones)} 个号码')
                            for phone in sorted(phones):
                                print(f'    📱 {phone}')
                        else:
                            print(f'\n✓ {pattern}: 找到 0 个号码')
                
                self.phone_numbers = list(phone_set)
                
                # 保存结果
                self._save_results()
                print(f'\n✅ 爬取完成！共找到 {len(self.phone_numbers)} 个号码')
                
            except Exception as e:
                print(f'❌ 错误: {e}')
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
    
    async def _search_pattern(self, browser, digit):
        """搜索单个模式（独立任务，用于并发版本）"""
        pattern = f'{digit}{digit}{digit}*'
        search_pattern = f'{digit}{digit}{digit}'
        
        print(f'正在搜索模式: {pattern}')
        
        # 创建新的context和page
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            # 访问网站
            await page.goto(self.url, timeout=30000)
            await asyncio.sleep(3)
            
            # 等待地区选择弹窗并选择城市
            await page.wait_for_selector('text=请确认号码归属地', timeout=10000)
            await page.get_by_text(self.city, exact=True).first.click()
            await asyncio.sleep(0.5)
            await page.get_by_text('确认,去选号').click()
            await page.wait_for_load_state('networkidle')
            
            # 搜索
            search_box = page.get_by_placeholder('输入任意1-4位尾号搜索')
            await search_box.clear()
            await asyncio.sleep(0.3)
            await search_box.fill(pattern)
            await asyncio.sleep(0.5)
            
            # 点击搜索按钮
            search_button = page.get_by_text('搜索')
            await search_button.click()
            await asyncio.sleep(2)
            await search_button.click()
            await asyncio.sleep(2)
            
            # 提取号码
            phones = await self._extract_phones_with_more(page, search_pattern)
            
            # 返回结果（包含模式信息用于最后汇总输出）
            return (pattern, phones)
            
        except Exception as e:
            return (pattern, [])
        finally:
            await context.close()
    
    async def _extract_phones_with_more(self, page, pattern):
        """提取搜索结果的号码（包括推荐号码和点击"更多号码"后的号码）"""
        all_phones = set()
        
        try:
            # 1. 点击"更多号码"按钮直到没有或达到最大次数
            max_clicks = 10
            for click_count in range(max_clicks):
                # 检查是否有"更多号码"按钮
                more_button = await page.query_selector('div.moreNum')
                if not more_button:
                    break
                
                # 检查按钮是否可见
                is_visible = await more_button.is_visible()
                if not is_visible:
                    break
                
                await more_button.click()
                await asyncio.sleep(2)  # 减少到2秒
            
            # 2. 提取所有搜索结果区域的号码
            search_phones = await self._extract_current_phones(page, pattern)
            all_phones.update(search_phones)
            
            # 3. 等待推荐号码加载完成（推荐号码可能延迟加载）
            await asyncio.sleep(1)  # 减少到0.5秒
            
            # 4. 提取"为您推荐"区域的号码
            recommend_phones = await self._extract_recommend_phones(page, pattern)
            all_phones.update(recommend_phones)
                    
        except Exception as e:
            print(f'提取号码时出错: {e}')
        
        # 打印所有匹配的号码
        if len(all_phones) > 0:
            print(f'  找到 {len(all_phones)} 个号码：')
            for phone in sorted(all_phones):
                print(f'    📱 {phone}')
        
        return list(all_phones)
    
    async def _extract_current_phones(self, page, pattern):
        """提取搜索结果区域的手机号码，只返回匹配指定模式的号码
        
        Args:
            page: Playwright页面对象
            pattern: 要匹配的尾号模式，如 "000"、"111" 等
        
        Returns:
            匹配模式的号码集合
        """
        phones = set()
        
        try:
            # 获取所有号码项
            phone_items = await page.query_selector_all('ul > li')
            
            for item in phone_items:
                try:
                    # 提取号码
                    phone_text = await item.query_selector('p:first-child')
                    if phone_text:
                        phone = await phone_text.inner_text()
                        phone = phone.strip('"')
                        
                        # 验证号码是否匹配搜索模式
                        if self._match_pattern(phone, pattern):
                            phones.add(phone)
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
        
        return phones
    
    async def _extract_recommend_phones(self, page, pattern):
        """提取"为您推荐"区域的手机号码，只返回匹配指定模式的号码
        
        Args:
            page: Playwright页面对象
            pattern: 要匹配的尾号模式，如 "000"、"111" 等
        
        Returns:
            匹配模式的号码集合
        """
        phones = set()
        
        try:
            # 检查是否有"为您推荐"文本
            recommend_section = await page.query_selector('text=为您推荐')
            if not recommend_section:
                return phones
            
            # 直接获取推荐区域所有的p标签（包含data-v-*属性的）
            import re
            
            # 方法1：获取所有可能包含号码的p标签
            all_p_tags = await page.query_selector_all('p')
            
            for p_tag in all_p_tags:
                try:
                    # 获取完整文本（inner_text会自动合并span内的文本）
                    text = await p_tag.inner_text()
                    
                    # 用正则提取11位手机号
                    match = re.search(r'1\d{10}', text)
                    if match:
                        phone = match.group()
                        # 验证是否匹配搜索模式
                        if self._match_pattern(phone, pattern):
                            phones.add(phone)
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
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
        """保存结果到JSON文件（按城市分组格式）"""
        filename = f'phones_{self.city}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # 构建新的数据格式
        result = [
            {
                "city": self.city,
                "phone": sorted(self.phone_numbers)  # 按字母/数字排序
            }
        ]
        
        with open(filename, 'w', encoding='utf-8') as f:
            # 自定义格式：城市信息在一行，每个号码单独一行
            f.write('[\n')
            f.write('  {\n')
            f.write(f'    "city": "{self.city}",\n')
            f.write('    "phone": [\n')
            for i, phone in enumerate(sorted(self.phone_numbers)):
                if i < len(self.phone_numbers) - 1:
                    f.write(f'      "{phone}",\n')
                else:
                    f.write(f'      "{phone}"\n')
            f.write('    ]\n')
            f.write('  }\n')
            f.write(']\n')
        
        print(f'\n📁 结果已保存到: {filename}')


async def main():
    parser = argparse.ArgumentParser(description='电信号码爬虫')
    parser.add_argument('--city', default='深圳', help='要爬取的城市名称（默认：深圳）')
    parser.add_argument('--concurrent', action='store_true', help='使用并发模式（更快但可能不稳定）')
    args = parser.parse_args()
    
    print('=' * 60)
    print('电信号码爬虫 - 启动中...')
    print(f'目标城市: {args.city}')
    print(f'运行模式: {"并发" if args.concurrent else "串行"}')
    print('=' * 60)
    
    crawler = TelecomCrawler(city=args.city, concurrent=args.concurrent)
    await crawler.run()


if __name__ == '__main__':
    asyncio.run(main())

