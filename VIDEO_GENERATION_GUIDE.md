# 视频生成功能使用指南

## 功能概述

本项目支持两种视频生成方式：
1. **图生视频**：上传图片 + 提示词，生成基于图片的视频
2. **文生视频**：仅提供提示词，生成纯文本描述的视频

## 快速开始

### 1. 启动服务

```bash
python app.py
```

服务将运行在 `http://localhost:8000`

### 2. 使用演示脚本

```bash
python video_gen_demo.py
```

按照菜单提示操作即可。

## API 接口说明

### 📤 上传图片（图生视频必需）

```http
POST /api/file/upload?file_type=2&file_name=image.jpg
Content-Type: application/octet-stream

[图片二进制数据]
```

**响应示例：**
```json
{
  "key": "tos-cn-i-xxx/xxx.jpeg",
  "name": "image.jpg",
  "type": "vlm_image",
  "file_review_state": 3,
  "file_parse_state": 3,
  "identifier": "xxx-xxx-xxx"
}
```

### 🎬 生成视频

```http
POST /api/video-gen/generate
Content-Type: application/json

{
  "prompt": "请将这张图片生成一个5秒的视频",
  "image_attachment": {
    "key": "tos-cn-i-xxx/xxx.jpeg",
    "name": "image.jpg",
    "type": "vlm_image",
    "file_review_state": 3,
    "file_parse_state": 3,
    "identifier": "xxx-xxx-xxx"
  },
  "guest": false
}
```

**图生视频：** 包含 `image_attachment` 参数  
**文生视频：** 不包含 `image_attachment` 参数

**响应示例：**
```json
{
  "success": true,
  "message": "视频生成任务已创建，正在处理中...",
  "conversation_id": "12345678901234567",
  "message_id": "98765432109876543",
  "section_id": "xxx",
  "task_status": "pending",
  "estimated_time": "预计3-15分钟完成"
}
```

### 🔍 查询视频状态

```http
GET /api/video-gen/status?conversation_id=xxx&message_id=xxx
```

**响应示例：**
```json
{
  "success": true,
  "task": {
    "conversation_id": "12345678901234567",
    "message_id": "98765432109876543",
    "status": "completed",
    "video_urls": [
      "https://v26-show.douyinvod.com/xxx/video.mp4"
    ],
    "retry_count": 1,
    "max_retries": 5,
    "created_at": "2025-11-17T23:00:00",
    "updated_at": "2025-11-17T23:03:00",
    "error": null
  }
}
```

**状态说明：**
- `pending`: 等待中（任务已创建，等待首次尝试）
- `processing`: 处理中（正在尝试获取视频）
- `completed`: 已完成（视频已生成，可获取链接）
- `failed`: 失败（达到最大重试次数）

### 📋 查看所有任务

```http
GET /api/video-gen/list
```

或查看特定会话的任务：

```http
GET /api/video-gen/list?conversation_id=xxx
```

## Python 代码示例

### 图生视频完整流程

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. 上传图片
with open('image.jpg', 'rb') as f:
    image_data = f.read()

upload_response = requests.post(
    f"{BASE_URL}/api/file/upload",
    params={"file_type": 2, "file_name": "image.jpg"},
    data=image_data,
    headers={"Content-Type": "application/octet-stream"}
)
attachment = upload_response.json()

# 2. 创建视频生成任务
gen_response = requests.post(
    f"{BASE_URL}/api/video-gen/generate",
    json={
        "prompt": "请将这张图片生成一个5秒的视频",
        "image_attachment": attachment,
        "guest": False
    }
)
result = gen_response.json()
conversation_id = result['conversation_id']
message_id = result['message_id']

# 3. 等待并查询视频状态
while True:
    status_response = requests.get(
        f"{BASE_URL}/api/video-gen/status",
        params={
            "conversation_id": conversation_id,
            "message_id": message_id
        }
    )
    task = status_response.json()['task']
    
    print(f"状态: {task['status']}")
    
    if task['status'] == 'completed':
        print(f"视频链接: {task['video_urls']}")
        break
    elif task['status'] == 'failed':
        print(f"失败: {task['error']}")
        break
    
    time.sleep(30)  # 每30秒查询一次
```

### 文生视频完整流程

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# 1. 创建视频生成任务（不需要上传图片）
gen_response = requests.post(
    f"{BASE_URL}/api/video-gen/generate",
    json={
        "prompt": "生成一个海边日落的5秒视频",
        "guest": False
    }
)
result = gen_response.json()
conversation_id = result['conversation_id']
message_id = result['message_id']

# 2. 等待并查询视频状态（同上）
# ...
```

## 异步机制说明

### 工作流程

1. **创建任务**：调用 `/api/video-gen/generate` 立即返回任务信息
2. **后台处理**：系统自动启动后台任务
3. **首次尝试**：3分钟后开始第一次尝试获取视频
4. **自动重试**：如果失败，每3分钟重试一次
5. **最大重试**：最多重试5次
6. **查询状态**：通过 `/api/video-gen/status` 随时查询

### 时间线示例

```
00:00 - 创建任务 (status: pending)
03:00 - 首次尝试 (status: processing, retry: 1/5)
06:00 - 第2次尝试 (retry: 2/5)
09:00 - 第3次尝试 (retry: 3/5)
09:30 - 获取成功 (status: completed) ✅
```

### 为什么要等待3分钟？

豆包生成视频需要时间，立即查询通常获取不到结果。等待3分钟后再开始查询可以：
- 减少无效请求
- 提高成功率
- 避免频繁请求被限流

## 注意事项

1. **登录账号**：视频生成需要登录账号，游客账号可能无法使用
2. **文件大小**：上传图片建议不超过10MB
3. **提示词**：提供清晰的提示词可以提高视频质量
4. **等待时间**：视频生成通常需要3-15分钟
5. **任务持久化**：所有任务信息保存在 `video_links.json` 文件中

## 常见问题

### Q: 为什么一直是 pending 状态？
A: 任务创建后需要等待3分钟才会开始首次尝试，请耐心等待。

### Q: 视频生成失败怎么办？
A: 检查：
- session 是否过期（重新运行 `python auto_get_session.py`）
- 提示词是否合理
- 网络连接是否正常

### Q: 可以同时创建多个任务吗？
A: 可以，每个任务独立处理，互不影响。

### Q: 视频链接有效期多久？
A: 豆包返回的视频链接通常有时效性，建议及时下载保存。

## API 文档

启动服务后访问：`http://localhost:8000/docs`

可以看到完整的交互式 API 文档。
