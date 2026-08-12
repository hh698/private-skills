# 现场实操题答案模板

以下示例用于组织答案，变量名和接口字段必须按用户简历、岗位和题目调整。代码要能解释每一行，不能声称已在生产运行，除非简历事实或用户补充可以证明。

## 1. Pytest + Requests 接口自动化

```python
import os

import pytest
import requests


BASE_URL = os.getenv("BASE_URL", "http://example.test")


@pytest.fixture(scope="session")
def session():
    client = requests.Session()
    response = client.post(
        f"{BASE_URL}/api/login",
        json={"username": "demo", "password": "demo-password"},
        timeout=10,
    )
    assert response.status_code == 200
    token = response.json()["data"]["token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


def test_create_order(session):
    response = session.post(
        f"{BASE_URL}/api/orders",
        json={"sku_id": 1001, "quantity": 1},
        timeout=10,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["order_id"]
```

现场说明要补充：鉴权是前置 fixture；状态码、业务码和关键字段分层断言；环境地址和密码从环境变量读取；失败时保留请求参数、响应和日志；真实项目会把公共请求封装、测试数据参数化，并在 CI 中使用测试账号。

## 2. Postman Tests

```javascript
pm.test("HTTP 状态码为 200", function () {
  pm.response.to.have.status(200);
});

const body = pm.response.json();
pm.test("业务码为 0 且返回订单号", function () {
  pm.expect(body.code).to.eql(0);
  pm.expect(body.data.order_id).to.be.a("string").and.not.empty;
});

pm.collectionVariables.set("order_id", body.data.order_id);
```

要说明环境变量、前置脚本、数据清理和断言失败如何让集合在 CI 中返回失败。

## 3. SQL 查询与数据一致性

```sql
-- 查询同一用户的重复有效订单
SELECT user_id, business_no, COUNT(*) AS duplicate_count
FROM orders
WHERE deleted = 0
GROUP BY user_id, business_no
HAVING COUNT(*) > 1;

-- 校验订单主表与明细表金额是否一致
SELECT o.id,
       o.total_amount,
       COALESCE(SUM(i.quantity * i.unit_price), 0) AS detail_amount
FROM orders o
LEFT JOIN order_items i ON i.order_id = o.id
GROUP BY o.id, o.total_amount
HAVING o.total_amount <> COALESCE(SUM(i.quantity * i.unit_price), 0);
```

说明索引、NULL、金额精度、事务隔离和只读账号；业务代码中的 SQL 使用参数化，不能拼接用户输入。

## 4. Playwright Page Object

```python
from playwright.sync_api import Page, expect


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.get_by_label("用户名")
        self.password = page.get_by_label("密码")
        self.submit = page.get_by_role("button", name="登录")

    def login(self, username: str, password: str):
        self.username.fill(username)
        self.password.fill(password)
        self.submit.click()


def test_login_success(page: Page):
    page.goto("http://example.test/login")
    LoginPage(page).login("tester", "safe-password")
    expect(page.get_by_text("首页")).to_be_visible()
```

要说明优先使用稳定语义定位，避免固定等待；失败保留截图、视频或 trace；Page Object 只封装页面行为，断言可放在测试层。

## 5. Jenkinsfile 与 Allure

```groovy
pipeline {
    agent any
    stages {
        stage('安装依赖') {
            steps { sh 'python -m pip install -r requirements.txt' }
        }
        stage('执行测试') {
            steps {
                sh 'pytest -q --alluredir=allure-results'
            }
        }
    }
    post {
        always {
            allure includeProperties: false, results: [[path: 'allure-results']]
            junit allowEmptyResults: true, testResults: 'junit.xml'
        }
    }
}
```

若用 Windows 节点，将 `sh` 换成 `bat` 或 PowerShell；需要补充凭据管理、环境变量、失败退出码、定时任务和并发构建隔离。

## 6. JMeter 参数化与关联

现场回答顺序：线程组和场景目标 -> CSV Data Set Config 参数化用户 -> 登录响应 JSON Extractor 提取 token -> HTTP Header Manager 引用 `${token}` -> 响应断言 -> 聚合报告看吞吐、平均响应时间、P90/P95、错误率 -> 结合服务端 CPU、内存、线程池和数据库指标定位瓶颈。

```text
CSV Data Set Config: users.csv
JSON Extractor: $.data.token -> token
Header: Authorization: Bearer ${token}
```

说明监听器不在高并发压测时大量开启，结果必须结合压测机和服务端资源，否则只看一张聚合报告容易误判。

## 7. Linux 与 K8S 排障

```bash
# 查看服务日志和最近的错误
kubectl logs deploy/test-api --since=10m | tail -n 100

# 查看 Pod、事件和容器重启次数
kubectl get pods -o wide
kubectl describe pod <pod-name>

# 检查端口和进程
ss -lntp | grep 8080
ps -ef | grep test-api
```

排查链路：先确认现象和影响范围，再看 Pod 状态/事件/日志，区分配置、镜像、探针、资源、网络和依赖问题；变更前保留现场，回滚要有版本和验证步骤。

## 8. 测试设计题

登录、上传、分页、权限和接口幂等至少从以下维度展开：正常、空值、边界、类型、重复提交、超时、网络中断、越权、并发、重试、数据落库、日志审计和兼容性。回答要选出最高风险的几条先测，并说明为什么，而不是罗列几十条没有优先级的用例。
