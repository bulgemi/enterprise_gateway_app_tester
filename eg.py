# _*_ coding: utf-8 _*_
import logging
import json
from typing import Dict, List
import requests
from requests.exceptions import ReadTimeout, ConnectTimeout
import ast

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
    jsonify
)
from werkzeug.exceptions import abort
from strip_ansi import strip_ansi

from .gateway_client_v2 import (
    KernelClient,
    AccuKernelClient
)


bp = Blueprint('eg', __name__)

kernel_client_map = dict()
async_kernel_client_map = dict()


@bp.route('/', methods=('GET', 'POST'))
def render_eg():
    retry_cnt = 0
    while True:
        try:
            resp = requests.get(f"{current_app.config['EG_HTTP_URL']}/api/kernels")
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return render_template('eg/eg_sample.html', kernels_opened=[], res=str(e))
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return render_template('eg/eg_sample.html', kernels_opened=[], res=str(e))
        else:
            break
    kernels_opened: List[Dict] = resp.json()
    current_app.logger.info(f"kernels_opened: {kernels_opened}")

    return render_template('eg/eg_sample.html', kernels_opened=kernels_opened, res=None)


@bp.route('/create_eg', methods=('GET', 'POST'))
def create_eg():
    retry_cnt = 0
    while True:
        try:
            resp = requests.post(f"{current_app.config['EG_HTTP_URL']}/api/kernels",
                                 data=json.dumps(
                                     {'name': "python_kubernetes",
                                      'env': {
                                          'KERNEL_USERNAME': "guest_user",
                                          # 'KERNEL_NAMESPACE': "project-namespace"
                                      }})
                                 )
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            current_app.logger.error(f"Error: {e}")
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    kernels_opened: List[Dict] = resp.json()
    current_app.logger.info(f"kernels_opened: {kernels_opened}")

    return {"kernels_opened": [kernels_opened], "res": None}


@bp.route('/run_eg', methods=('GET', 'POST'))
def run_eg():
    global kernel_client_map
    retry_cnt = 0
    while True:
        try:
            resp = requests.get(f"{current_app.config['EG_HTTP_URL']}/api/kernels")
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    kernels_opened: List[Dict] = resp.json()

    kernel_id = request.json['kernel_id']
    timeout = request.json['timeout']
    code = request.json['code'].replace('\t', '    ')

    current_app.logger.debug(f"code: {code}")
    try:
        if kernel_id not in kernel_client_map:
            logger = logging.getLogger("KernelClient")
            # logger.setLevel("DEBUG")
            kernel_client = KernelClient(
                http_api_endpoint=f"{current_app.config['EG_HTTP_URL']}/api/kernels",
                ws_api_endpoint=f"{current_app.config['EG_WS_URL']}/api/kernels",
                kernel_id=kernel_id,
                timeout=timeout,
                logger=logger
            )
            kernel_client_map[kernel_id] = kernel_client
        # res = kernel_client.execute(code, timeout=timeout)
        res = kernel_client_map[kernel_id].execute(code, timeout=timeout)
    except Exception as e:
        res = str(e)
    current_app.logger.info(f"kernels_opened: {kernels_opened}")
    res = strip_ansi(ast.literal_eval(f"b'''{res}'''").decode())
    current_app.logger.info(f"res: {res}")
    current_app.logger.debug(f"kernel_client_map: {kernel_client_map}")

    # kernel_client.shutdown()
    # kernel_client_map[kernel_id].shutdown()  # 평균 응답 시간: 평균 1.7s
    # del kernel_client_map[kernel_id]
    # kernel_client_map[kernel_id].restart(timeout=timeout)  # 평균 응답 시간: 평균 3.5s, timeout 0.1 설정시 응답 시간 더 늘어남.

    current_app.logger.debug(f"kernel_client_map: {kernel_client_map}")

    return {"kernels_opened": kernels_opened, "res": res}


@bp.route('/run_eg_async', methods=('GET', 'POST'))
def run_eg_async():
    global async_kernel_client_map
    retry_cnt = 0
    while True:
        try:
            resp = requests.get(f"{current_app.config['EG_HTTP_URL']}/api/kernels")
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    kernels_opened: List[Dict] = resp.json()

    kernel_id = request.json['kernel_id']
    timeout = request.json['timeout']
    code = request.json['code'].replace('\t', '    ')

    current_app.logger.debug(f"code: {code}")
    try:
        if kernel_id not in async_kernel_client_map:
            logger = logging.getLogger("AccuKernelClient")
            logger.setLevel("DEBUG")
            kernel_client = AccuKernelClient(
                http_api_endpoint=f"{current_app.config['EG_HTTP_URL']}/api/kernels",
                ws_api_endpoint=f"{current_app.config['EG_WS_URL']}/api/kernels",
                kernel_id=kernel_id,
                timeout=timeout,
                logger=logger
            )
            async_kernel_client_map[kernel_id]: AccuKernelClient = kernel_client
        res = async_kernel_client_map[kernel_id].run(code)
    except Exception as e:
        res = str(e)
    current_app.logger.info(f"kernels_opened: {kernels_opened}")
    res = strip_ansi(ast.literal_eval(f"b'''{res}'''").decode())
    current_app.logger.info(f"res: {res}")
    current_app.logger.debug(f"kernel_client_map: {async_kernel_client_map}")

    return {"kernels_opened": kernels_opened, "res": res}


@bp.route('/res_eg_async', methods=('GET', 'POST'))
def res_eg_async():
    global async_kernel_client_map
    retry_cnt = 0
    while True:
        try:
            resp = requests.get(f"{current_app.config['EG_HTTP_URL']}/api/kernels")
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    kernels_opened: List[Dict] = resp.json()

    kernel_id = request.json['kernel_id']
    msg_id = request.json['msg_id']
    timeout = request.json['timeout']

    try:
        kernel_client: AccuKernelClient = async_kernel_client_map[kernel_id]
        res = kernel_client.pull_response(msg_id=msg_id, timeout=timeout)
    except Exception as e:
        res = str(e)
    current_app.logger.info(f"kernels_opened: {kernels_opened}")
    res = strip_ansi(ast.literal_eval(f"b'''{res}'''").decode())
    current_app.logger.info(f"res: {res}")
    current_app.logger.debug(f"kernel_client_map: {async_kernel_client_map}")

    return {"kernels_opened": kernels_opened, "res": res}


@bp.route('/delete_eg', methods=['DELETE'])
def delete_eg():
    global kernel_client_map
    retry_cnt = 0
    while True:
        try:
            kernel_id = request.json['kernel_id']
            resp = requests.delete(f"{current_app.config['EG_HTTP_URL']}/api/kernels/{kernel_id}")

            if kernel_id in kernel_client_map:
                kernel_client_map[kernel_id].shutdown()
                del kernel_client_map[kernel_id]

            if kernel_id in async_kernel_client_map:
                async_kernel_client_map[kernel_id].shutdown()
                del async_kernel_client_map[kernel_id]
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    if resp.status_code == 200:
        current_app.logger.info(f"Delete")
    else:
        current_app.logger.info(f"No Content")

    retry_cnt = 0
    while True:
        try:
            resp = requests.get(f"{current_app.config['EG_HTTP_URL']}/api/kernels")
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    kernels_opened: List[Dict] = resp.json()
    current_app.logger.info(f"kernels_opened: {kernels_opened}")

    return {"kernels_opened": kernels_opened, "res": "성공"}


@bp.route('/interrupt_eg', methods=['POST'])
def interrupt_eg():
    retry_cnt = 0
    while True:
        try:
            kernel_id = request.json['kernel_id']
            resp = requests.post(f"{current_app.config['EG_HTTP_URL']}/api/kernels/{kernel_id}/interrupt")
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    if resp.status_code == 200:
        current_app.logger.info(f"Restart")
    else:
        current_app.logger.info(f"No Content")

    retry_cnt = 0
    while True:
        try:
            resp = requests.get(f"{current_app.config['EG_HTTP_URL']}/api/kernels")
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    kernels_opened: List[Dict] = resp.json()
    current_app.logger.info(f"kernels_opened: {kernels_opened}")

    return {"kernels_opened": kernels_opened, "res": "성공"}


@bp.route('/upgrade_ws', methods=['POST'])
def upgrade_websocket():
    retry_cnt = 0
    while True:
        try:
            kernel_id = request.json['kernel_id']
            resp = requests.get(f"{current_app.config['EG_HTTP_URL']}/api/kernels/{kernel_id}/channels")
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    if resp.status_code == 200:
        current_app.logger.info(f"res: {resp}")
    else:
        current_app.logger.info(f"No Content({resp.status_code})")

    retry_cnt = 0
    while True:
        try:
            resp = requests.get(f"{current_app.config['EG_HTTP_URL']}/api/kernels")
        except (ConnectTimeout, ReadTimeout) as e:
            if retry_cnt >= 3:
                return {"kernels_opened": [], "res": str(e)}
            current_app.logger.info(f"retry: {retry_cnt}")
            retry_cnt += 1
        except Exception as e:
            return {"kernels_opened": [], "res": str(e)}
        else:
            break
    kernels_opened: List[Dict] = resp.json()
    current_app.logger.info(f"kernels_opened: {kernels_opened}")

    return {"kernels_opened": kernels_opened, "res": "성공"}
