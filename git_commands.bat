@echo off
echo 正在初始化Git仓库...
git init

echo 配置Git用户信息（请替换为你的GitHub用户名和邮箱）...
git config user.name "bigbear0079"
git config user.email "89118969@qq.com"

echo 添加所有文件到暂存区...
git add .

echo 创建初始提交...
git commit -m "Initial commit: DoubaoFreeApi project"

echo 添加远程仓库...
git remote add origin https://github.com/bigbear0079/DoubaoFreeApi.git

echo 推送到GitHub...
git branch -M main
git push -u origin main

echo 完成！项目已上传到GitHub私有仓库
pause
