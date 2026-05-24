@echo off
REM ============================================
REM Opera Daily - 推送到 GitHub 一键脚本
REM 用法：双击运行，或在此目录执行 deploy.bat
REM ============================================

echo 🎭 Opera Daily - GitHub 部署助手
echo ====================================
echo.
echo 第一步：请在浏览器打开以下网址创建仓库：
echo   https://github.com/new
echo.
echo 仓库名称: opera-daily
echo 描述: 全球歌剧院演出排期日报工具
echo 类型: Public （不要勾选任何初始化选项）
echo.
pause
echo.
echo 第二步：正在推送到 GitHub...
cd /d D:\opera-daily
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ✅ 推送成功！
    echo.
    echo 第三步：在 GitHub 上打开仓库页面
    echo   https://github.com/lishwin/opera-daily
    echo.
    echo 第四步：启用 GitHub Pages
    echo   仓库 → Settings → Pages
    echo   Source 选择 "GitHub Actions"
    echo.
    echo 第五步：手动触发工作流
    echo   仓库 → Actions → "🎭 Opera Daily Report"
    echo   → Run workflow
    echo.
    echo 完成后访问：
    echo   https://lishwin.github.io/opera-daily/
) else (
    echo ❌ 推送失败。请确认：
    echo   1. 已在 https://github.com/new 创建 opera-daily 仓库
    echo   2. 网络连接正常
    echo   3. 已登录 GitHub（可能需要输入用户名密码）
    echo.
    echo 手动解决后重试：
    echo   git push -u origin main
)
pause