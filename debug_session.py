"""
调试脚本 - 查看请求详细信息
"""
import asyncio
import urllib.parse
from playwright.async_api import async_playwright


async def debug_requests():
  """调试请求信息"""
  print("=" * 80)
  print("调试模式 - 等待你发送消息...")
  print("=" * 80)
  
  async def handle_request(request):
    """处理所有请求"""
    # 只关注豆包的聊天请求
    if 'samantha/chat/completion' in request.url:
      print("\n" + "=" * 80)
      print("捕获到聊天请求！")
      print("=" * 80)
      
      # URL 信息
      print(f"\n【URL】")
      print(f"{request.url[:150]}...")
      
      # URL 参数
      url_parts = urllib.parse.urlparse(request.url)
      query_params = dict(urllib.parse.parse_qsl(url_parts.query))
      print(f"\n【URL 参数】")
      for key, value in query_params.items():
        print(f"  {key}: {value}")
      
      # 请求头
      print(f"\n【请求头】")
      headers = request.headers
      for key, value in headers.items():
        if key.lower() in ['cookie', 'referer', 'x-flow-trace', 'user-agent']:
          if key.lower() == 'cookie':
            print(f"  {key}: {value[:100]}...")
          else:
            print(f"  {key}: {value}")
      
      print("\n" + "=" * 80)
  
  async def handle_response(response):
    """处理响应（可选）"""
    if 'samantha/chat/completion' in response.url:
      print(f"\n【响应状态】{response.status}")
  
  async with async_playwright() as p:
    print("\n正在启动浏览器...")
    browser = await p.chromium.launch(
      headless=False,
      args=['--disable-blink-features=AutomationControlled']
    )
    
    page = await browser.new_page()
    
    # 监听请求和响应
    page.on('request', handle_request)
    page.on('response', handle_response)
    
    print("正在访问豆包...")
    await page.goto('https://www.doubao.com', wait_until='networkidle')
    
    print("\n" + "=" * 80)
    print("浏览器已打开，请：")
    print("1. 登录账号（如果需要）")
    print("2. 在聊天框中发送任意消息")
    print("3. 查看下方打印的请求信息")
    print("\n按 Ctrl+C 退出")
    print("=" * 80)
    
    # 保持浏览器打开
    try:
      while True:
        await asyncio.sleep(1)
    except KeyboardInterrupt:
      print("\n\n正在关闭浏览器...")
      await browser.close()


if __name__ == "__main__":
  asyncio.run(debug_requests())
