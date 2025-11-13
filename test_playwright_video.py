"""
使用 Playwright 从豆包网页获取视频链接
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def get_video_url_from_page(conversation_id: str, message_id: str = None):
    """
    使用 Playwright 从豆包网页获取视频链接
    
    Args:
        conversation_id: 会话ID
        message_id: 消息ID（可选，如果不提供则获取页面上的第一个视频）
    
    Returns:
        dict: 包含视频URL和相关信息
    """
    async with async_playwright() as p:
        # 启动浏览器（使用 headless 模式）
        browser = await p.chromium.launch(headless=False)
        
        # 创建新页面
        page = await browser.new_page()
        
        # 读取 session.json 获取 cookie
        with open('session.json', 'r', encoding='utf-8') as f:
            sessions = json.load(f)
            session = sessions[0]
        
        # 设置 cookie
        await page.context.add_cookies([
            {
                'name': 'sessionid',
                'value': session['cookie'].split('sessionid=')[1].split(';')[0] if 'sessionid=' in session['cookie'] else '',
                'domain': '.doubao.com',
                'path': '/'
            }
        ])
        
        # 访问会话页面
        url = f"https://www.doubao.com/chat/{conversation_id}"
        print(f"正在访问: {url}")
        await page.goto(url, wait_until='networkidle')
        
        # 等待页面加载
        await page.wait_for_timeout(5000)
        
        print("正在查找视频元素...")
        
        # 方法1: 查找所有可能的视频容器
        # 查找包含视频播放按钮的元素
        play_buttons = await page.query_selector_all('[class*="video"], [class*="player"], button[aria-label*="播放"]')
        print(f"找到 {len(play_buttons)} 个可能的视频容器")
        
        # 方法2: 点击视频缩略图，触发视频加载
        print("\n尝试点击视频缩略图...")
        # 查找视频封面图（包含 tplv-a9rns2rl98-web-thumb 的图片）
        video_thumbnail = await page.query_selector('img[src*="tplv-a9rns2rl98-web-thumb"]')
        
        if video_thumbnail:
            print("找到视频缩略图，正在点击...")
            try:
                # 使用 JavaScript 强制点击，绕过遮挡元素
                await page.evaluate('(element) => element.click()', video_thumbnail)
                print("已点击视频缩略图（使用 JS），等待视频加载...")
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"点击失败: {e}")
                # 尝试点击父元素
                try:
                    parent = await video_thumbnail.evaluate_handle('el => el.parentElement')
                    await page.evaluate('(element) => element.click()', parent)
                    print("已点击父元素，等待视频加载...")
                    await page.wait_for_timeout(3000)
                except Exception as e2:
                    print(f"点击父元素也失败: {e2}")
        else:
            print("未找到视频缩略图")
        
        # 方法3: 查找 video 标签（点击后可能出现）
        video_elements = await page.query_selector_all('video')
        print(f"\n找到 {len(video_elements)} 个 video 元素")
        
        videos = []
        for idx, video in enumerate(video_elements):
            src = await video.get_attribute('src')
            current_src = await video.get_attribute('currentSrc')
            video_url = src or current_src
            if video_url:
                print(f"视频 {idx + 1}: {video_url}")
                videos.append({
                    'index': idx + 1,
                    'url': video_url,
                    'type': 'video_tag'
                })
        
        # 方法4: 使用 JavaScript 直接获取 video 元素的 src
        print("\n使用 JavaScript 获取视频源...")
        js_video_info = await page.evaluate('''() => {
            const videos = Array.from(document.querySelectorAll('video'));
            return videos.map(v => ({
                src: v.src,
                currentSrc: v.currentSrc,
                poster: v.poster
            }));
        }''')
        
        print(f"JavaScript 找到 {len(js_video_info)} 个视频:")
        for info in js_video_info:
            print(f"  src: {info['src']}")
            print(f"  currentSrc: {info['currentSrc']}")
        
        # 方法5: 检查页面的所有网络请求
        print("\n检查网络请求...")
        video_urls_from_network = []
        
        # 获取所有性能条目（包括资源加载）
        performance_entries = await page.evaluate('''() => {
            return performance.getEntriesByType('resource')
                .filter(entry => entry.name.includes('.mp4') || 
                               entry.name.includes('.webm') || 
                               entry.name.includes('video') ||
                               entry.name.includes('.m3u8') ||
                               entry.name.includes('douyinvod'))
                .map(entry => entry.name);
        }''')
        
        print(f"从性能API找到 {len(performance_entries)} 个视频相关请求:")
        for url in performance_entries:
            print(f"  - {url[:100]}...")
            video_urls_from_network.append(url)
        
        # 滚动页面触发懒加载
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(2000)
        
        # 方法3: 从页面内容中提取视频信息
        page_content = await page.content()
        
        # 查找可能包含视频URL的JSON数据
        import re
        video_url_pattern = r'https://[^"\']+\.(?:mp4|webm|m3u8)'
        found_urls = re.findall(video_url_pattern, page_content)
        
        print(f"\n从页面内容中找到 {len(found_urls)} 个可能的视频URL:")
        for url in found_urls[:5]:  # 只显示前5个
            print(f"  - {url}")
        
        # 截图保存
        await page.screenshot(path='doubao_page.png')
        print("\n页面截图已保存到: doubao_page.png")
        
        await browser.close()
        
        return {
            'video_elements': videos,
            'network_urls': video_urls_from_network,
            'content_urls': found_urls[:10]
        }

async def main():
    # 测试：获取视频链接
    conversation_id = "24863689854610946"  # 生成小猫视频的会话
    
    print(f"开始获取会话 {conversation_id} 的视频链接...\n")
    result = await get_video_url_from_page(conversation_id)
    
    print("\n" + "="*60)
    print("结果汇总:")
    print("="*60)
    print(f"\n1. Video 标签: {len(result['video_elements'])} 个")
    for v in result['video_elements']:
        print(f"   {v}")
    
    print(f"\n2. 网络请求: {len(result['network_urls'])} 个")
    for url in result['network_urls']:
        print(f"   {url}")
    
    print(f"\n3. 页面内容: {len(result['content_urls'])} 个")
    for url in result['content_urls'][:5]:
        print(f"   {url}")

if __name__ == "__main__":
    asyncio.run(main())
