## OCR和人脸识别服务

### 创建项目环境
* `conda create -n paddlepaddle python=3.7`
* `conda activate paddlepaddle`
  
### 项目环境依赖
* ` pip install flask`
* ` paddleOcr:pip install "paddleocr>=2.0.1" `
* ` paddlepaddle: python -m pip install paddlepaddle==2.0.0rc1 `
* ` face_recognition:pip install face_recognition`
* ` pymysql:pip install pymysql `
* ` pip install DBUtils`
* ` jieba:pip install jieba`
* ` apscheduler:pip install apscheduler`
* ` pip install uwsgi`
* ` pip install concurrent_log_handler`
* ` pip install python-dotenv`
  

### 项目运行注意项
* linux对应目录运行：
* 1、ubuntu安装uwsgi:
* 1)`apt-get install python3-dev`/`apt-get install libpython3.7-dev`
* 2)`apt-get install python3-pip `
* 3)`pip3 install uwsgi`/`apt install uwsgi uwsgi-plugin-python3`

***注意事项:启动uwsgi失败时，# vim ~/.bash_profile

* 2、启动uwsgi
* 1)启动uwsgi:`uwsgi --ini uwsgi.ini`
* 2)重启uwsgi:`uwsgi --reload uwsgi.pid`
* 3)停止uwsgi:`uwsgi --stop uwsgi.pid`



### 项目流程
* 