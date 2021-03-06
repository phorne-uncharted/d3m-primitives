FROM registry.gitlab.com/datadrivendiscovery/images/primitives:ubuntu-bionic-python36-v2020.5.18

RUN sudo apt-get update -y && \ 
    sudo apt-get install -y zlib1g-dev && \ 
    sudo apt-get install -y liblzo2-dev && \ 
    pip install python-lzo

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN pip install -e git+https://github.com/kungfuai/d3m-primitives@rs/pipeline#egg=kf-d3m-primitives --upgrade --exists-action=w
COPY . .
RUN pip install -e .[gpu]

# RUN pip install git+https://github.com/uncharted-distil/distil-primitives#egg=distil-primitives --upgrade --exists-action=w
