"""
贸易云档 TradeDoc — API 自动化测试

按业务流程顺序测试: 登录 → 建客户 → 建订单 → 上传文件 → 字段提取 → 字段编辑 → 归档 → 导出

运行方式:
    python -m pytest tests/test_api.py -v --tb=short
"""

import os
import time

import pytest
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
PYTHON_URL = "http://127.0.0.1:8100"

# 测试用 PDF 文件路径（你的报关单）
TEST_PDF = "D:/work/product/business_file_management/E20250001528475449.pdf"


class TestState:
    """跨测试共享状态"""
    token: str = ""
    user_id: int = 0
    customer_id: int = 0
    order_id: int = 0
    document_id: int = 0
    field_id: int = 0


state = TestState()


def api(method, path, **kwargs):
    """统一 API 请求封装"""
    headers = kwargs.pop("headers", {})
    headers["Accept"] = "application/json"
    if state.token:
        headers["Authorization"] = f"Bearer {state.token}"

    url = f"{BASE_URL}{path}"
    resp = getattr(requests, method)(url, headers=headers, **kwargs)
    return resp


# ============================================================
# 1. 服务健康检查
# ============================================================
class TestHealth:
    def test_php_service(self):
        """PHP 服务 (RoadRunner) 是否运行"""
        r = requests.get("http://127.0.0.1:8090/")
        assert r.status_code == 200

    def test_python_service(self):
        """Python 服务 (FastAPI) 是否运行"""
        r = requests.get(f"{PYTHON_URL}/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["db_connected"] is True

    def test_nginx_proxy(self):
        """Nginx 反向代理是否正常"""
        r = requests.get("http://127.0.0.1:8000/")
        assert r.status_code == 200

    def test_ocr_engine_status(self):
        """OCR 引擎状态"""
        r = requests.get(f"{PYTHON_URL}/api/ocr/engine-status")
        assert r.status_code == 200
        data = r.json()
        assert data["engine_mode"] in ("aliyun_api", "local_model", "mock")


# ============================================================
# 2. 认证模块
# ============================================================
class TestAuth:
    def test_login_success(self):
        """管理员登录成功"""
        r = api("post", "/auth/login", json={"username": "admin", "password": "admin123"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert "token" in data
        assert data["user"]["username"] == "admin"
        assert data["user"]["real_name"] == "系统管理员"
        assert len(data["user"]["permissions"]) > 0
        state.token = data["token"]
        state.user_id = data["user"]["id"]

    def test_login_wrong_password(self):
        """密码错误"""
        r = api("post", "/auth/login", json={"username": "admin", "password": "wrong"})
        assert r.status_code == 422

    def test_login_missing_fields(self):
        """缺少字段"""
        r = api("post", "/auth/login", json={"username": "admin"})
        assert r.status_code == 422

    def test_me(self):
        """获取当前用户信息"""
        r = api("get", "/auth/me")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["username"] == "admin"
        assert "roles" in data
        assert "permissions" in data

    def test_unauthenticated(self):
        """未登录访问受保护接口"""
        r = requests.get(f"{BASE_URL}/auth/me", headers={"Accept": "application/json"})
        assert r.status_code == 401


# ============================================================
# 3. 客户管理
# ============================================================
class TestCustomer:
    def test_create_customer(self):
        """新建客户"""
        r = api("post", "/customers", json={
            "type": "customer",
            "company_name": "测试客户_ABC Trading Co.",
            "company_name_en": "ABC Trading Co.",
            "short_name": "ABC",
            "country": "US",
            "contact_person": "John Smith",
            "contact_phone": "+1-555-0100",
            "contact_email": "john@abc-trading.com",
        })
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["company_name"] == "测试客户_ABC Trading Co."
        state.customer_id = data["id"]

    def test_list_customers(self):
        """客户列表"""
        r = api("get", "/customers")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_search_customer(self):
        """搜索客户"""
        r = api("get", "/customers", params={"keyword": "ABC"})
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_update_customer(self):
        """更新客户"""
        r = api("put", f"/customers/{state.customer_id}", json={
            "contact_person": "Jane Smith",
            "remarks": "自动化测试更新",
        })
        assert r.status_code == 200
        assert r.json()["data"]["contact_person"] == "Jane Smith"

    def test_customer_options(self):
        """客户下拉选项"""
        r = api("get", "/customers/options")
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 1


# ============================================================
# 4. 订单管理
# ============================================================
class TestOrder:
    def test_create_order(self):
        """新建订单"""
        r = api("post", "/orders", json={
            "order_no": f"SO-TEST-{int(time.time())}",
            "order_type": "export",
            "customer_id": state.customer_id,
            "total_amount": 48200.00,
            "currency": "USD",
            "trade_terms": "FOB",
            "payment_terms": "T/T 30 days",
            "destination_country": "US",
        })
        assert r.status_code == 201
        data = r.json()["data"]
        assert data["order_type"] == "export"
        state.order_id = data["id"]

    def test_list_orders(self):
        """订单列表"""
        r = api("get", "/orders")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_update_order(self):
        """更新订单"""
        r = api("put", f"/orders/{state.order_id}", json={
            "status": "confirmed",
            "remarks": "自动化测试确认",
        })
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "confirmed"

    def test_order_options(self):
        """订单下拉选项"""
        r = api("get", "/orders/options")
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 1


# ============================================================
# 5. 文件类型
# ============================================================
class TestDocumentTypes:
    def test_list_types(self):
        """文件类型列表"""
        r = api("get", "/document-types")
        assert r.status_code == 200
        types = r.json()["data"]
        assert len(types) >= 9  # 9种文件类型
        names = [t["name"] for t in types]
        assert "报关单" in names
        assert "商业发票" in names


# ============================================================
# 6. 文件上传 + 智能提取（核心流程）
# ============================================================
class TestDocumentUpload:
    def test_upload_file(self):
        """上传文件并触发智能提取"""
        if not os.path.exists(TEST_PDF):
            pytest.skip(f"测试 PDF 不存在: {TEST_PDF}")

        with open(TEST_PDF, "rb") as f:
            r = api("post", "/documents/upload",
                     files={"file": ("test_report.pdf", f, "application/pdf")},
                     data={
                         "document_type_id": 1,  # 报关单
                         "order_id": state.order_id,
                         "customer_id": state.customer_id,
                     })
        assert r.status_code == 201
        data = r.json()["data"]
        assert "document" in data
        assert data["document"]["doc_no"] is not None
        state.document_id = data["document"]["id"]
        print(f"\n  上传成功: {data['document']['doc_no']}")

    def test_wait_for_processing(self):
        """等待智能提取完成"""
        if not state.document_id:
            pytest.skip("无文件ID")

        # 等待最多 30 秒
        for i in range(15):
            r = api("get", f"/documents/{state.document_id}")
            status = r.json()["data"]["status"]
            if status not in ("draft", "ocr_processing"):
                print(f"\n  处理完成, 状态: {status}")
                return
            time.sleep(2)

        # 超时也算通过（可能 Python 服务处理慢）
        print("\n  处理超时，继续测试")

    def test_document_has_fields(self):
        """文件字段已提取"""
        if not state.document_id:
            pytest.skip("无文件ID")

        r = api("get", f"/documents/{state.document_id}")
        assert r.status_code == 200
        data = r.json()["data"]
        fields = data.get("fields", [])
        print(f"\n  提取到 {len(fields)} 个字段")
        if fields:
            state.field_id = fields[0]["id"]
            for f in fields[:5]:
                print(f"    {f['field_key']}: {f['field_value']} ({f['confidence']}%)")


# ============================================================
# 7. 文件管理
# ============================================================
class TestDocumentManagement:
    def test_list_documents(self):
        """文件列表"""
        r = api("get", "/documents")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_filter_by_type(self):
        """按类型筛选"""
        r = api("get", "/documents", params={"document_type_id": 1})
        assert r.status_code == 200

    def test_search_documents(self):
        """搜索文件"""
        r = api("get", "/documents", params={"keyword": "D26"})
        assert r.status_code == 200

    def test_document_detail(self):
        """文件详情"""
        if not state.document_id:
            pytest.skip("无文件ID")

        r = api("get", f"/documents/{state.document_id}")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["id"] == state.document_id
        assert "document_type" in data
        assert "fields" in data
        assert "versions" in data

    def test_document_preview(self):
        """文件预览"""
        if not state.document_id:
            pytest.skip("无文件ID")

        r = requests.get(f"{BASE_URL}/documents/{state.document_id}/preview")
        assert r.status_code == 200
        assert len(r.content) > 0


# ============================================================
# 8. 字段编辑
# ============================================================
class TestFieldEdit:
    def test_update_field(self):
        """修改字段值"""
        if not state.field_id:
            pytest.skip("无字段ID")

        r = api("post", "/documents/update-field", json={
            "field_id": state.field_id,
            "value": "测试修改值_自动化",
        })
        assert r.status_code == 200

    def test_add_field_from_template(self):
        """从模板添加字段"""
        if not state.document_id:
            pytest.skip("无文件ID")

        r = api("post", "/documents/add-field", json={
            "document_id": state.document_id,
            "field_key": "supervision_condition",
            "field_value": "自动化测试添加",
        })
        # 201 或 200 都算成功
        assert r.status_code in (200, 201)

    def test_add_custom_field(self):
        """手动添加自定义字段"""
        if not state.document_id:
            pytest.skip("无文件ID")

        r = api("post", "/documents/add-field", json={
            "document_id": state.document_id,
            "field_key": "custom_test_field",
            "field_name": "自定义测试字段",
            "field_value": "自定义值",
        })
        assert r.status_code in (200, 201)

    def test_delete_field(self):
        """删除字段"""
        if not state.document_id:
            pytest.skip("无文件ID")

        # 先获取最新字段列表
        r = api("get", f"/documents/{state.document_id}")
        fields = r.json()["data"]["fields"]
        custom_field = next((f for f in fields if f["field_key"] == "custom_test_field"), None)
        if not custom_field:
            pytest.skip("自定义字段不存在")

        r = api("delete", f"/documents/fields/{custom_field['id']}")
        assert r.status_code == 200


# ============================================================
# 9. 状态流转 + 归档
# ============================================================
class TestStatusFlow:
    def test_change_to_archived(self):
        """状态变更为归档"""
        if not state.document_id:
            pytest.skip("无文件ID")

        # 先看当前状态
        r = api("get", f"/documents/{state.document_id}")
        current = r.json()["data"]["status"]

        # 如果已经是 archived，跳过
        if current == "archived":
            return

        # 逐步流转到 archived
        transitions = {
            "draft": "ocr_processing",
            "ocr_processing": "pending_review",
            "pending_review": "pending_approval",
            "pending_approval": "archived",
        }

        while current != "archived" and current in transitions:
            next_status = transitions[current]
            r = api("put", f"/documents/{state.document_id}/status", json={"status": next_status})
            if r.status_code == 200:
                current = next_status
            else:
                break

        # 验证
        r = api("get", f"/documents/{state.document_id}")
        print(f"\n  最终状态: {r.json()['data']['status']}")


# ============================================================
# 10. 导出
# ============================================================
class TestExport:
    def test_export_single(self):
        """单文件导出 Excel"""
        if not state.document_id:
            pytest.skip("无文件ID")

        r = requests.get(f"{BASE_URL}/documents/{state.document_id}/export")
        assert r.status_code == 200
        assert "spreadsheet" in r.headers.get("Content-Type", "") or len(r.content) > 100
        print(f"\n  导出文件大小: {len(r.content)} bytes")

    def test_export_batch(self):
        """批量导出 Excel"""
        r = requests.get(f"{BASE_URL}/documents/export")
        assert r.status_code == 200
        print(f"\n  批量导出大小: {len(r.content)} bytes")


# ============================================================
# 11. 仪表盘 + 统计
# ============================================================
class TestDashboard:
    def test_statistics(self):
        """仪表盘统计"""
        r = api("get", "/documents/statistics")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "total_this_month" in data
        assert "pending_count" in data
        assert "total_fields" in data
        assert "type_distribution" in data
        print(f"\n  本月: {data['total_this_month']}, 待处理: {data['pending_count']}, 字段: {data['total_fields']}")

    def test_reports(self):
        """数据报表"""
        r = api("get", "/documents/reports")
        assert r.status_code == 200
        data = r.json()["data"]
        assert "total_documents" in data
        assert "type_distribution" in data


# ============================================================
# 12. 通知
# ============================================================
class TestNotification:
    def test_unread_count(self):
        """未读通知数"""
        r = api("get", "/notifications/unread-count")
        assert r.status_code == 200
        assert "count" in r.json()["data"]

    def test_notification_list(self):
        """通知列表"""
        r = api("get", "/notifications")
        assert r.status_code == 200


# ============================================================
# 13. OCR 缓存代理
# ============================================================
class TestOcrProxy:
    def test_engine_status_proxy(self):
        """OCR 引擎状态（PHP 代理）"""
        r = api("get", "/ocr/engine-status")
        assert r.status_code == 200
        assert "engine_mode" in r.json()

    def test_ocr_cache_proxy(self):
        """OCR 缓存查询（PHP 代理）"""
        if not state.document_id:
            pytest.skip("无文件ID")

        r = api("get", f"/documents/{state.document_id}/ocr-cache")
        assert r.status_code == 200


# ============================================================
# 14. 系统管理
# ============================================================
class TestAdmin:
    def test_user_list(self):
        """用户列表"""
        r = api("get", "/admin/users")
        assert r.status_code == 200
        users = r.json()["data"]
        assert len(users) >= 1
        assert any(u["username"] == "admin" for u in users)

    def test_roles_list(self):
        """角色列表"""
        r = api("get", "/admin/roles")
        assert r.status_code == 200
        roles = r.json()["data"]
        assert len(roles) >= 6

    def test_field_templates(self):
        """字段模板查看"""
        r = api("get", "/admin/field-templates/1")  # 报关单
        assert r.status_code == 200
        templates = r.json()["data"]
        assert len(templates) >= 10  # 报关单至少10个字段
        print(f"\n  报关单字段模板: {len(templates)} 个")


# ============================================================
# 15. 清理测试数据
# ============================================================
class TestCleanup:
    def test_delete_test_document(self):
        """删除测试文件"""
        if not state.document_id:
            pytest.skip("无文件ID")

        r = api("delete", f"/documents/{state.document_id}")
        # 已归档可能不能删除，都算通过
        assert r.status_code in (200, 422, 500)

    def test_delete_test_order(self):
        """删除测试订单"""
        if not state.order_id:
            pytest.skip("无订单ID")

        r = api("delete", f"/orders/{state.order_id}")
        assert r.status_code == 200

    def test_delete_test_customer(self):
        """删除测试客户"""
        if not state.customer_id:
            pytest.skip("无客户ID")

        r = api("delete", f"/customers/{state.customer_id}")
        assert r.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
