@echo off
setlocal
chcp 65001

set gitUrl=https://gitee.com/Tloml-Starry/SkyAutoMusic
set localDir=score

if not exist %localDir% (
    echo 正在从Git拉取库...
    git clone --depth=1 -b score %gitUrl% %localDir%
    echo 拉取完成
    echo 正在删除LICENSE和README.md文件...
    cd %localDir%
    del LICENSE
    del README.md
    echo 删除完成
) else (
    echo 正在更新本地库...
    cd %localDir%
    git pull
    echo 更新完成
)
echo 按下任意键继续
pause