@echo off
setlocal

:: 建立虛擬環境
if not exist venv (
    echo 建立虛擬環境...
    python -m venv venv
)

:: 啟動虛擬環境
call venv\Scripts\activate

:: 安裝套件
echo 安裝 Python 套件...
pip install flask flask-cors sympy numpy plotly

:: 產生 requirements.txt
pip freeze > requirements.txt

:: 啟動 Flask 後端（新開視窗執行）
echo 啟動後端伺服器...
start cmd /k "cd backend && venv\Scripts\activate && python app.py"

:: 延遲幾秒等待伺服器啟動
timeout /t 3 >nul

:: 開啟前端 HTML 頁面
echo 開啟前端頁面...
start frontend\index.html

echo 所有程序完成。
endlocal