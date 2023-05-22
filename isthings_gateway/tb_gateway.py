
from os import kill, path, listdir, mkdir, curdir

import sys

from gateway.tb_client import TBClient
from gateway.tb_gateway_service import TBGatewayService

def main():
    if "logs" not in listdir(curdir):
        mkdir("logs")
    TBGatewayService(path.dirname(path.abspath(__file__)) + '/config/gateway.yaml'.replace('/', path.sep))


def daemon():
    TBGatewayService("/etc/isthings_gateway/config/gateway.yaml".replace('/', path.sep))


if __name__ == '__main__':
    main()
