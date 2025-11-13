"""
视频链接获取服务
使用 Playwright 从豆包网页获取视频链接（无头模式，优化速度）
"""
import asyncio
import os
import glob
import sys
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from loguru import logger
import json
import re
from src.pool.session_pool import session_pool


async def get_video_url(conversation_id: str, message_id: str = None, timeout: int = 15000):
  """
  从豆包网页获取视频链接（无头模式，优化速度）
  
  Args:
    conversation_id: 会话ID
    message_id: 消息ID（可选）
    timeout: 超时时间（毫秒），默认15秒
  
  Returns:
    dict: 包含视频URL列表和相关信息
  """
  video_urls = []
  
  async with async_playwright() as p:
    try:
      # 尝试查找系统中已安装的 Playwright Chromium
      chromium_path = None
      
      # 检查多个可能的安装位置
      search_paths = [
        # venv 环境
        os.path.join(os.getcwd(), 'venv', 'Lib', 'site-packages', 'playwright', 'driver', 'package', '.local-browsers', 'chromium-*', 'chrome-win', 'chrome.exe'),
        # .venv 环境
        os.path.join(os.getcwd(), '.venv', 'Lib', 'site-packages', 'playwright', 'driver', 'package', '.local-browsers', 'chromium-*', 'chrome-win', 'chrome.exe'),
        # 用户目录
        os.path.expanduser('~\\AppData\\Local\\ms-playwright\\chromium-*\\chrome-win\\chrome.exe'),
        # Python site-packages
        os.path.join(sys.prefix, 'Lib', 'site-packages', 'playwright', 'driver', 'package', '.local-browsers', 'chromium-*', 'chrome-win', 'chrome.exe'),
      ]
      
      for pattern in search_paths:
        matches = glob.glob(pattern)
        if matches:
          chromium_path = matches[0]
          logger.info(f"找到 Chromium 浏览器: {chromium_path}")
          break
      
      # 启动浏览器配置
      launch_options = {
        'headless': True,  # 无头模式
        'args': [
          '--disable-blink-features=AutomationControlled',
          '--disable-dev-shm-usage',
          '--no-sandbox',
          '--disable-setuid-sandbox'
        ]
      }
      
      if chromium_path and os.path.exists(chromium_path):
        launch_options['executable_path'] = chromium_path
        logger.info(f"使用指定路径启动浏览器")
      else:
        logger.warning("未找到 Chromium，尝试使用默认路径")
      
      browser = await p.chromium.launch(**launch_options)
      
      # 创建上下文
      context = await browser.new_context(
        viewport={'width': 1280, 'height': 720},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      )
      
      # 不拦截资源，确保视频能正常加载
      page = await context.new_page()
      
      # 获取 session 配置
      session = session_pool.get_session()
      if not session:
        raise Exception("无可用的 session 配置")
      
      # 设置 cookie
      cookies = []
      for cookie_str in session.cookie.split('; '):
        if '=' in cookie_str:
          name, value = cookie_str.split('=', 1)
          cookies.append({
            'name': name,
            'value': value,
            'domain': '.doubao.com',
            'path': '/'
          })
      
      await context.add_cookies(cookies)
      
      # 监听网络请求，捕获视频URL
      captured_urls = []
      
      def handle_response(response):
        url = response.url
        # 只捕获真正的视频播放链接，排除 API 端点
        if any(ext in url for ext in ['.mp4', '.webm', '.m3u8', 'douyinvod']):
          # 排除 API 端点
          if 'get_play_info' not in url and url not in captured_urls:
            captured_urls.append(url)
            logger.info(f"捕获到视频URL: {url[:100]}...")
      
      page.on('response', handle_response)
      
      # 访问会话页面
      url = f"https://www.doubao.com/chat/{conversation_id}"
      logger.info(f"正在访问: {url}")
      
      try:
        await page.goto(url, wait_until='networkidle', timeout=timeout)
      except PlaywrightTimeout:
        logger.warning("页面加载超时，继续尝试获取视频")
      
      # 等待页面初始化（与脚本一致）
      await page.wait_for_timeout(5000)
      
      # 尝试点击视频缩略图触发加载
      try:
        # 查找视频缩略图（多种选择器）
        video_selectors = [
          'img[src*="tplv-a9rns2rl98-web-thumb"]',
          'img[src*="video"]',
          'img[src*="douyinvod"]',
          '[class*="video"] img',
          '[class*="VideoCard"] img'
        ]
        
        video_thumbnail = None
        for selector in video_selectors:
          try:
            video_thumbnail = await page.wait_for_selector(selector, timeout=3000)
            if video_thumbnail:
              logger.info(f"找到视频缩略图: {selector}")
              break
          except:
            continue
        
        if video_thumbnail:
          # 滚动到元素可见
          await video_thumbnail.scroll_into_view_if_needed()
          await page.wait_for_timeout(500)
          
          # 点击缩略图
          await page.evaluate('(element) => element.click()', video_thumbnail)
          logger.info("已点击视频缩略图，等待视频加载...")
          await page.wait_for_timeout(5000)  # 增加等待时间
        else:
          logger.warning("未找到视频缩略图")
      except Exception as e:
        logger.warning(f"点击视频缩略图失败: {str(e)}")
      
      # 滚动页面触发懒加载
      await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
      await page.wait_for_timeout(2000)
      await page.evaluate('window.scrollTo(0, 0)')
      await page.wait_for_timeout(1000)
      
      # 获取 video 标签的 src
      video_elements = await page.query_selector_all('video')
      logger.info(f"找到 {len(video_elements)} 个 video 元素")
      
      for video in video_elements:
        src = await video.get_attribute('src')
        current_src = await video.get_attribute('currentSrc')
        video_url = src or current_src
        if video_url and video_url not in video_urls:
          video_urls.append(video_url)
          logger.info(f"从 video 标签获取: {video_url[:100]}...")
      
      # 使用 JavaScript 获取性能API中的视频请求
      performance_urls = await page.evaluate('''() => {
        return performance.getEntriesByType('resource')
          .filter(entry => 
            entry.name.includes('.mp4') || 
            entry.name.includes('.webm') || 
            entry.name.includes('.m3u8') ||
            entry.name.includes('douyinvod')
          )
          .map(entry => entry.name);
      }''')
      
      for url in performance_urls:
        if url not in video_urls:
          video_urls.append(url)
      
      # 从页面内容提取视频URL（只要真正的视频链接）
      page_content = await page.content()
      video_url_pattern = r'https://[^"\'<>\s]+\.(?:mp4|webm|m3u8)'
      found_urls = re.findall(video_url_pattern, page_content)
      
      for url in found_urls:
        # 排除 API 端点
        if 'get_play_info' not in url and url not in video_urls:
          video_urls.append(url)
      
      # 添加从网络请求捕获的URL
      for url in captured_urls:
        if url not in video_urls:
          video_urls.append(url)
      
      # 最终过滤：只保留真正的视频播放链接
      filtered_urls = []
      for url in video_urls:
        # 只保留包含 douyinvod 或视频文件扩展名的链接
        if ('douyinvod.com' in url or url.endswith('.mp4') or url.endswith('.webm') or url.endswith('.m3u8')):
          if 'get_play_info' not in url:  # 排除 API 端点
            filtered_urls.append(url)
      
      video_urls = filtered_urls
      
      await browser.close()
      
      logger.info(f"共找到 {len(video_urls)} 个视频URL")
      
      return {
        'success': True,
        'conversation_id': conversation_id,
        'video_count': len(video_urls),
        'video_urls': video_urls
      }
      
    except Exception as e:
      logger.error(f"获取视频URL失败: {str(e)}")
      if 'browser' in locals():
        await browser.close()
      return {
        'success': False,
        'error': str(e),
        'conversation_id': conversation_id,
        'video_count': 0,
        'video_urls': []
      }


__all__ = ['get_video_url']
