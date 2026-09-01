FROM modelscope-registry.cn-beijing.cr.aliyuncs.com/modelscope-repo/python:3.12
WORKDIR /home/user/app
COPY ./ /home/user/app
RUN pip install -r "requirements.txt"
ENTRYPOINT ["python", "-u", "main.py"]