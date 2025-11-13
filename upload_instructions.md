# DoubaoFreeApi 上传到GitHub指南

## 仓库信息
- GitHub仓库: https://github.com/bigbear0079/DoubaoFreeApi
- 仓库类型: 私有仓库

## 上传步骤

### 1. 确保Git已安装
如果Git未安装，请从 https://git-scm.com/download/win 下载并安装。

### 2. 打开Git Bash或命令提示符
在项目目录 `e:\project\DoubaoFreeApi` 中右键选择 "Git Bash Here" 或打开命令提示符。

### 3. 执行以下命令

```bash
# 初始化Git仓库
git init

# 配置用户信息（请替换邮箱为你的GitHub邮箱）
git config user.name "bigbear0079"
git config user.email "你的GitHub邮箱@example.com"

# 添加所有文件到暂存区
git add .

# 创建初始提交
git commit -m "Initial commit: DoubaoFreeApi project"

# 添加远程仓库
git remote add origin https://github.com/bigbear0079/DoubaoFreeApi.git

# 设置主分支并推送
git branch -M main
git push -u origin main
```

### 4. 如果需要身份验证
GitHub可能要求你输入用户名和密码（或Personal Access Token）。

## 已准备的文件
- ✅ `.gitignore` - 排除敏感文件和缓存
- ✅ 项目源代码和配置文件
- ✅ README.md 和 LICENSE 文件

## 排除的文件（不会上传）
- `session.json` 和其他敏感配置
- `__pycache__/` 缓存目录
- `.venv/` 和 `venv/` 虚拟环境
- `.history/` 历史文件
- 图片和视频文件

## 完成后验证
上传完成后，访问 https://github.com/bigbear0079/DoubaoFreeApi 查看你的私有仓库。
