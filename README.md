# BuptScoreSpider
北邮教务系统成绩爬虫，支持验证码自动识别，保存为 JSON 格式。
## 使用说明
```bash
python main.py username password
```
也可以在源码中指定用户名和密码。
## 安装
```bash
git clone --recursive git@github.com:imtsuki/BuptScoreSpider.git
```
## 依赖
Python 依赖项：
* requests
* requests-html
* pytesseract
* Pillow

同时还需要安装 Tesseract OCR。这里有[安装教程](https://github.com/tesseract-ocr/tesseract/wiki#installation)。
## TODO
* 可选手动输入验证码