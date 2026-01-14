#!/usr/bin/env python3
"""
测试 000* 搜索 - 调试版本
打印所有找到的号码，无论是否匹配
"""

import asyncio
from playwright.async_api import async_playwright


async def test_000_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            print('访问网站...')
            await page.goto('https://gd.189.cn/TS/tysj/xhb/index.html#/', timeout=30000)
            await asyncio.sleep(5)
            
            print('选择深圳...')
            await page.wait_for_selector('text=请确认号码归属地', timeout=10000)
            await page.get_by_text('深圳', exact=True).first.click()
            await asyncio.sleep(1)
            await page.get_by_text('确认,去选号').click()
            await asyncio.sleep(3)
            
            print('\n搜索 000*...')
            search_box = page.get_by_placeholder('输入任意1-4位尾号搜索')
            await search_box.clear()
            await search_box.fill('000*')
            await page.get_by_text('搜索').click()
            await asyncio.sleep(3)
            
            # 检查是否有"查不到号码信息"
            no_result = await page.query_selector('text=查不到号码信息')
            if no_result:
                print('❌ 查不到号码信息')
                return
            
            print('\n提取所有号码（第一批）：')
            await page.wait_for_selector('ul > li', timeout=5000)
            phone_items = await page.query_selector_all('ul > li')
            
            all_phones = []
            for item in phone_items:
                phone_text = await item.query_selector('p:first-child')
                if phone_text:
                    phone = await phone_text.inner_text()
                    phone = phone.strip('"')
                    all_phones.append(phone)
                    
                    # 检查是否匹配
                    last_7 = phone[-7:] if len(phone) >= 7 else phone
                    match = '000' in last_7
                    print(f'  {phone} (后7位: {last_7}, 匹配: {"✅" if match else "❌"})')
            
            print(f'\n第一批共找到 {len(all_phones)} 个号码')
            print(f'匹配 000* 的号码数: {sum(1 for p in all_phones if "000" in p[-7:])}')
            
            # 检查是否有"更多号码"按钮
            more_button = await page.query_selector('text=更多号码')
            if more_button and await more_button.is_visible():
                print('\n有"更多号码"按钮，但为了调试，这里不点击')
            
        except Exception as e:
            print(f'错误: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(test_000_search())

