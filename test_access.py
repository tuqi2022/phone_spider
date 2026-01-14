#!/usr/bin/env python3
"""
测试网站访问 - 调试版本
"""

import asyncio
from playwright.async_api import async_playwright


async def test_access():
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
            print('访问网站...')
            response = await page.goto('https://gd.189.cn/TS/tysj/xhb/index.html#/', timeout=30000)
            print(f'响应状态: {response.status}')
            
            # 等待一段时间让JS加载
            print('等待JS加载...')
            await asyncio.sleep(5)
            
            # 获取页面内容
            content = await page.content()
            print(f'\n页面HTML长度: {len(content)} 字符')
            
            # 保存HTML
            with open('page_content.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print('HTML已保存到 page_content.html')
            
            # 拍截图
            await page.screenshot(path='test_screenshot.png', full_page=True)
            print('截图已保存到 test_screenshot.png')
            
            # 尝试查找元素
            print('\n查找关键元素...')
            
            # 尝试不同的选择器
            selectors = [
                'text=请确认号码归属地',
                'text=当前定位',
                'text=广州',
                'text=深圳',
                '.van-overlay',
                '[class*="city"]',
                '[class*="popup"]',
            ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        print(f'✓ 找到 [{selector}]: {text[:50]}')
                    else:
                        print(f'✗ 未找到 [{selector}]')
                except Exception as e:
                    print(f'✗ 查找 [{selector}] 出错: {e}')
            
            print('\n\n测试完成！')
            
        except Exception as e:
            print(f'错误: {e}')
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(test_access())

