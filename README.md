# Enterprise Gateway Test App
> Enterprise Gateway Test App은 Jupyter Enterprise Gateway(https://jupyter-enterprise-gateway.readthedocs.io/en/latest/index.html) 파이썬 커널의 생성/삭제/실행 테스트 할수 있는 웹 기반 도구

## 화면 설명 

![Enterprise Gateway Test App UI](https://github.com/bulgemi/enterprise_gateway_app_tester/blob/main/docs/eg_test_layout.png)

1. 커널 관리
   * `Create Kernel`: 커널(python kubernetes) 생성
   * `Delete Kernel`:  커널 삭제
   * `Interrupt Kernel`: 커널 인터럽트
   * `Upgrade Websocket`: 웹소켓 업그레이드
2. 커널 목록
   * 생성된 커널 목록
3. 파이썬 코드 편집기
   * Syntax Highlight
   * Line Number
   * 자동 들여쓰기
4. 코드 실행
   * `Run`: 코드 시행 (코드 실행 완료 후 결과 출력)
   * `Async Run`: 코드 실행 (비동기)
   * `Async Res`: 비동기 코드 실행 결과 받아오기
5. 결과 출력 
   * 실행결과 출력

## 환경 설정
* `config.py` 수정
```python
EG_HTTP_URL = "http://localhost:8800"  # Enterprise Gateway URL
EG_WS_URL = "ws://localhost:8800"  # Enterprise Gateway Websocket
```

## 실행
```bash
flask --app . --debug run
```
