"""
自动获取豆包 Session 信息脚本
打开浏览器，自动提取所需的 session 配置并保存到 session.json
"""
import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright


async def auto_get_session():
  """自动获取豆包 session 信息"""
  print("=" * 60)
  print("豆包 Session 自动获取工具")
  print("=" * 60)
  
  session_data = {
    'cookie': None,
    'device_id': None,
    'tea_uuid': None,
    'web_id': None,
    'room_id': None,
    'x_flow_trace': None
  }
  
  captured = False
  
  async def capture_request(request):
    """捕获请求信息"""
    nonlocal captured, session_data
    
    # 捕获聊天 API 请求
    if 'https://www.doubao.com/samantha/chat/completion' in request.url:
      print("\n✓ 捕获到聊天请求，正在提取信息...")
      
      # 解析 URL 参数
      url_parts = urllib.parse.urlparse(request.url)
      query_params = dict(urllib.parse.parse_qsl(url_parts.query))
      
      # 提取请求头
      headers = request.headers
      
      # 提取所需参数
      session_data['device_id'] = query_params.get('device_id')
      session_data['web_id'] = query_params.get('web_id')
      session_data['tea_uuid'] = query_params.get('tea_uuid')
      session_data['x_flow_trace'] = headers.get('x-flow-trace', '')
      
      # 从 referer 提取 room_id（去除 URL 参数）
      referer = headers.get('referer', '')
      if referer:
        room_id_with_params = referer.split('/')[-1]
        # 去除 ?type=2 等参数
        session_data['room_id'] = room_id_with_params.split('?')[0]
      
      captured = True
      print("✓ 信息提取完成！")
  
  page_context = None
  
  async with async_playwright() as p:
    # 启动浏览器（显示界面）
    print("\n正在启动浏览器...")
    browser = await p.chromium.launch(
      headless=False,
      args=['--disable-blink-features=AutomationControlled']
    )
    
    # 创建新上下文
    context = await browser.new_context(
      user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    
    # 创建新页面
    page = await context.new_page()
    page_context = context
    
    # 监听请求
    page.on('request', capture_request)
    
    try:
      # 访问豆包网站
      print("正在访问 www.doubao.com...")
      await page.goto('https://www.doubao.com', wait_until='networkidle')
      
      print("\n" + "=" * 60)
      print("请在浏览器中完成以下操作：")
      print("=" * 60)
      print("1. 如果未登录，请先登录豆包账号")
      print("2. 登录后，在聊天框中发送任意消息（如：你好）")
      print("3. 等待消息发送完成（地址栏会显示真实的 room_id）")
      print("4. 脚本将自动捕获所有信息...")
      print("=" * 60)
      print("\n提示：room_id 是地址栏 /chat/ 后面的数字")
      print("例如：https://www.doubao.com/chat/24863689854610946")
      print("=" * 60)
      
      # 等待捕获完成（最多等待 5 分钟）
      timeout = 300
      elapsed = 0
      while not captured and elapsed < timeout:
        await asyncio.sleep(1)
        elapsed += 1
      
      if not captured:
        print("\n✗ 超时：未能捕获到请求信息")
        print("请确保你在浏览器中发送了消息")
        await browser.close()
        return None
      
      # 从浏览器上下文获取 cookies
      print("\n正在获取 Cookie...")
      cookies = await context.cookies()
      cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
      session_data['cookie'] = cookie_str
      print(f"✓ Cookie 已获取 ({len(cookies)} 个)")
      
      # 从浏览器地址栏获取真正的 room_id
      current_url = page.url
      if '/chat/' in current_url:
        # 提取 /chat/ 后面的 ID（去除参数）
        room_id_part = current_url.split('/chat/')[-1].split('?')[0]
        # 如果是 local_ 开头，尝试从 referer 获取真实 room_id
        if not room_id_part.startswith('local_'):
          session_data['room_id'] = room_id_part
          print(f"✓ 从浏览器地址栏获取 room_id: {room_id_part}")
        else:
          print(f"⚠ 当前是本地会话 (local_)，room_id 可能不是永久ID")
      
      # 验证数据完整性
      if all(session_data.values()):
        print("\n✓ 所有信息已成功获取！")
        print("\n获取到的信息：")
        print(f"  - device_id: {session_data['device_id']}")
        print(f"  - web_id: {session_data['web_id']}")
        print(f"  - tea_uuid: {session_data['tea_uuid']}")
        print(f"  - room_id: {session_data['room_id']}")
        print(f"  - x_flow_trace: {session_data['x_flow_trace'][:50]}...")
        print(f"  - cookie: {session_data['cookie'][:100]}...")
        
        # 保存到 session.json
        try:
          # 读取现有的 session.json
          try:
            with open('session.json', 'r', encoding='utf-8') as f:
              sessions = json.load(f)
          except FileNotFoundError:
            sessions = []
          
          # 添加新的 session
          sessions.append(session_data)
          
          # 保存
          with open('session.json', 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=4, ensure_ascii=False)
          
          print("\n✓ Session 信息已保存到 session.json")
          print(f"✓ 当前共有 {len(sessions)} 个 session 配置")
          
        except Exception as e:
          print(f"\n✗ 保存失败: {str(e)}")
        
        # 等待 20 秒后关闭
        print("\n浏览器将在 200 秒后自动关闭...")
        await asyncio.sleep(30)
        
      else:
        print("\n✗ 信息不完整，请重试")
        missing = [k for k, v in session_data.items() if not v]
        print(f"缺少的字段: {', '.join(missing)}")
      
      await browser.close()
      return session_data
      
    except Exception as e:
      print(f"\n✗ 发生错误: {str(e)}")
      await browser.close()
      return None


async def main():
  """主函数"""
  result = await auto_get_session()
  
  if result:
    print("\n" + "=" * 60)
    print("✓ Session 获取成功！")
    print("=" * 60)
    print("\n你现在可以：")
    print("1. 启动 API 服务: uv run app.py")
    print("2. 使用新的 session 进行聊天")
  else:
    print("\n" + "=" * 60)
    print("✗ Session 获取失败")
    print("=" * 60)
    print("\n请重新运行脚本并确保：")
    print("1. 已登录豆包账号")
    print("2. 在聊天框中发送了消息")


if __name__ == "__main__":
  asyncio.run(main())
