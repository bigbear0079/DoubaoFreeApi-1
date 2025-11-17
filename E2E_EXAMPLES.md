# 视频生成 E2E 示例

## 🚀 快速开始

```bash
# 运行 E2E 示例
python e2e_video_generation.py
```

## 📋 示例列表

### 示例 1: 图生视频（本地图片）
使用本地图片文件生成视频

```python
# 1. 读取本地图片
with open('image.jpg', 'rb') as f:
    image_data = f.read()

# 2. 上传图片
attachment = upload_image(image_data, 'image.jpg')

# 3. 创建视频任务
result = create_video_task("将这张图片生成视频", attachment)

# 4. 等待完成
video_urls = wait_for_video(result['conversation_id'], result['message_id'])
```

### 示例 2: 图生视频（图片链接）⭐ 新功能
直接使用图片 URL，无需手动下载

```python
# 方式1: 手动下载并上传
image_data = download_image_from_url("https://example.com/image.jpg")
attachment = upload_image(image_data, "image.jpg")
result = create_video_task("生成视频", attachment)

# 方式2: 使用 API 自动处理（推荐）
response = requests.post(
    "http://localhost:8000/api/video-gen/generate",
    json={
        "prompt": "将这张图片生成视频",
        "image_url": "https://your-real-image-url.com/image.jpg",  # 替换为真实的图片链接
        "guest": False
    }
)

# 可用的测试图片链接示例：
# "https://picsum.photos/800/600"  # 随机图片
# "https://images.unsplash.com/photo-xxx"  # Unsplash 图片
```

### 示例 3: 文生视频
纯文本描述生成视频

```python
result = create_video_task("生成一个海边日落的5秒视频")
video_urls = wait_for_video(result['conversation_id'], result['message_id'])
```

### 示例 4: 快速测试
创建任务后立即返回，不等待完成

```python
result = create_video_task("生成星空视频")
print(f"任务已创建: {result['conversation_id']}")
# 稍后查询状态
```

## 🎯 三种使用图片的方式

### 方式 1: 本地图片文件
```python
with open('image.jpg', 'rb') as f:
    image_data = f.read()
attachment = upload_image(image_data, 'image.jpg')
```

### 方式 2: 图片链接（手动）
```python
image_data = download_image_from_url("https://example.com/image.jpg")
attachment = upload_image(image_data, "image.jpg")
```

### 方式 3: 图片链接（自动）⭐ 推荐
```python
# API 自动下载并上传（需要真实可访问的图片链接）
requests.post(
    "http://localhost:8000/api/video-gen/generate",
    json={
        "prompt": "生成视频",
        "image_url": "https://your-real-image-url.com/image.jpg",  # 替换为真实链接
        "guest": False
    }
)
```

## 📊 完整流程图

```
图生视频（本地）:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 读取本地图片 │ -> │  上传图片   │ -> │  创建任务   │ -> │  等待完成   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

图生视频（链接）:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 提供图片URL │ -> │ 自动下载上传 │ -> │  创建任务   │ -> │  等待完成   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘

文生视频:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  提供提示词  │ -> │  创建任务   │ -> │  等待完成   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🔧 API 接口

### 生成视频
```http
POST /api/video-gen/generate
Content-Type: application/json

{
  "prompt": "提示词",
  "image_url": "https://your-image-url.com/image.jpg",  // 可选：真实的图片链接
  "image_attachment": {...},                             // 可选：已上传的图片
  "guest": false
}
```

### 查询状态
```http
GET /api/video-gen/status?conversation_id=xxx&message_id=xxx
```

### 查看所有任务
```http
GET /api/video-gen/list
```

## 💡 使用技巧

1. **图片链接最方便**：直接传 `image_url`，系统自动处理
2. **提示词要清晰**：描述具体的视频效果
3. **耐心等待**：视频生成需要 3-15 分钟
4. **及时下载**：视频链接有时效性

## 🎬 运行示例

```bash
# 交互式菜单
python e2e_video_generation.py

# 或直接运行特定示例
python -c "from e2e_video_generation import example_3_text_to_video; example_3_text_to_video()"
```

## 📝 示例输出

```
============================================================
示例 2: 图生视频（图片链接）
============================================================

📥 从 URL 下载图片: https://example.com/image.jpg...
✅ 下载成功，大小: 588988 字节
📤 上传图片到豆包服务器...
✅ 上传成功!
   Key: tos-cn-i-xxx/xxx.jpeg
   Type: vlm_image

🎬 创建图生视频任务...
   提示词: 请将这张图片生成一个5秒的视频
✅ 任务创建成功!
   会话ID: 12345678901234567
   消息ID: 98765432109876543
   预计时间: 预计3-15分钟完成

⏳ 等待视频生成...
   提示：首次尝试在3分钟后开始

📊 状态更新: processing (重试 1/5)
⏳ 等待中... 3.5分钟 | 状态: processing

✅ 视频生成完成!
   获取到 1 个视频链接:
   1. https://v26-show.douyinvod.com/xxx/video.mp4

🎉 完成！视频已生成
```

## 🆘 常见问题

**Q: 图片链接下载失败？**
A: 确保链接可访问，支持 HTTP/HTTPS

**Q: 支持哪些图片格式？**
A: JPG, PNG, WEBP 等常见格式

**Q: 图片大小限制？**
A: 建议不超过 10MB

**Q: 视频一直是 pending 状态？**
A: 正常，需要等待 3 分钟后才开始处理
