"""
贸易云档 TradeDoc — UI 自动化测试 (Playwright)

模拟真实用户操作: 打开浏览器 → 登录 → 逐个页面测试 → 截图存证

运行方式:
    python -m pytest tests/test_ui.py -v --tb=short -s

截图保存在: tests/screenshots/
"""

import os
import time

import pytest
from playwright.sync_api import Page, expect, sync_playwright

BASE_URL = "http://127.0.0.1:8000"
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "screenshots")
TEST_PDF = "D:/work/product/business_file_management/E20250001528475449.pdf"


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def page(browser):
    context = browser.new_context(viewport={"width": 1440, "height": 900}, locale="zh-CN")
    page = context.new_page()
    yield page
    context.close()


def screenshot(page: Page, name: str):
    """保存截图"""
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=False)
    print(f"\n  截图: {path}")


# ============================================================
# 1. 登录页面
# ============================================================
class TestLogin:
    def test_login_page_loads(self, page: Page):
        """登录页面正常显示"""
        page.goto(BASE_URL)
        # 等待重定向到登录页
        page.wait_for_url("**/login", timeout=5000)
        screenshot(page, "01_login_page")

        # 验证页面元素
        expect(page.locator("text=贸易云档")).to_be_visible()
        expect(page.locator("text=TradeDoc")).to_be_visible()
        expect(page.get_by_placeholder("用户名")).to_be_visible()
        expect(page.get_by_placeholder("密码")).to_be_visible()

    def test_login_empty_validation(self, page: Page):
        """空表单提交验证"""
        page.get_by_role("button", name="登 录").click()
        page.wait_for_timeout(500)
        # 应该显示验证提示
        expect(page.locator("text=请输入用户名")).to_be_visible()

    def test_login_success(self, page: Page):
        """登录成功进入仪表盘"""
        page.get_by_placeholder("用户名").fill("admin")
        page.get_by_placeholder("密码").fill("admin123")
        page.get_by_role("button", name="登 录").click()

        # 等待跳转到仪表盘
        page.wait_for_url("**/dashboard", timeout=10000)
        page.wait_for_timeout(1000)
        screenshot(page, "02_dashboard")

        # 验证仪表盘内容
        expect(page.locator(".page-title:has-text('概览仪表盘')")).to_be_visible()
        expect(page.locator(".user-name")).to_be_visible()


# ============================================================
# 2. 仪表盘
# ============================================================
class TestDashboard:
    def test_dashboard_stats(self, page: Page):
        """仪表盘统计卡片"""
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_timeout(2000)

        # 验证四个统计卡片存在
        expect(page.locator("text=本月文件数")).to_be_visible()
        expect(page.locator("text=待处理文件")).to_be_visible()
        expect(page.locator("text=字段提取准确率")).to_be_visible()
        expect(page.locator("text=已提取字段数")).to_be_visible()

    def test_dashboard_sections(self, page: Page):
        """仪表盘各区域"""
        expect(page.locator("text=近期上传文件")).to_be_visible()
        expect(page.locator("text=本月文件类型分布")).to_be_visible()
        expect(page.locator("text=快捷操作")).to_be_visible()
        screenshot(page, "03_dashboard_full")


# ============================================================
# 3. 客户管理
# ============================================================
class TestCustomerUI:
    def test_customer_page(self, page: Page):
        """客户管理页面"""
        page.goto(f"{BASE_URL}/customers")
        page.wait_for_timeout(1500)
        screenshot(page, "04_customer_list")

        expect(page.locator("text=新建客户")).to_be_visible()

    def test_create_customer(self, page: Page):
        """新建客户"""
        page.get_by_role("button", name="新建客户").click()
        page.wait_for_timeout(500)

        # 填写表单
        page.locator("label:has-text('公司名称') + div input, .el-form-item:has-text('公司名称') input").first.fill("UI测试客户公司")
        page.wait_for_timeout(300)
        screenshot(page, "05_customer_form")

        # 保存
        page.get_by_role("button", name="保存").click()
        page.wait_for_timeout(1500)

        # 验证列表中出现
        expect(page.locator("text=UI测试客户公司").first).to_be_visible(timeout=5000)
        screenshot(page, "06_customer_created")


# ============================================================
# 4. 订单管理
# ============================================================
class TestOrderUI:
    def test_order_page(self, page: Page):
        """订单管理页面"""
        page.goto(f"{BASE_URL}/orders")
        page.wait_for_timeout(1500)
        screenshot(page, "07_order_list")

        expect(page.locator("text=新建订单")).to_be_visible()

    def test_create_order(self, page: Page):
        """新建订单"""
        page.get_by_role("button", name="新建订单").click()
        page.wait_for_timeout(500)

        # 填写订单号
        dialog = page.locator(".el-dialog:visible")
        dialog.locator("input").first.fill(f"SO-UI-{int(time.time()) % 10000}")
        page.wait_for_timeout(300)
        screenshot(page, "08_order_form")

        # 保存
        page.get_by_role("button", name="保存").click()
        page.wait_for_timeout(1500)
        screenshot(page, "09_order_created")


# ============================================================
# 5. 文件上传
# ============================================================
class TestUploadUI:
    def test_upload_page(self, page: Page):
        """上传页面"""
        page.goto(f"{BASE_URL}/upload")
        page.wait_for_timeout(1500)
        screenshot(page, "10_upload_page")

        expect(page.locator("text=拖拽文件至此")).to_be_visible()
        expect(page.locator("text=支持 PDF")).to_be_visible()

    def test_upload_file(self, page: Page):
        """上传文件"""
        if not os.path.exists(TEST_PDF):
            pytest.skip(f"测试 PDF 不存在: {TEST_PDF}")

        # 找到文件上传 input
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(TEST_PDF)
        page.wait_for_timeout(1000)

        # 应该显示文件列表和类型选择
        expect(page.locator("text=选择文件类型")).to_be_visible()
        screenshot(page, "11_upload_file_selected")

        # 选择报关单类型
        page.locator("text=Customs Declaration").first.click()
        page.wait_for_timeout(500)
        screenshot(page, "12_upload_type_selected")

    def test_submit_upload(self, page: Page):
        """提交上传"""
        if not os.path.exists(TEST_PDF):
            pytest.skip("无测试文件")

        btn = page.get_by_role("button", name="确认上传并智能提取")
        if btn.is_visible():
            btn.click()
            page.wait_for_timeout(5000)  # 等待上传+处理
            screenshot(page, "13_upload_complete")


# ============================================================
# 6. 文件管理
# ============================================================
class TestDocumentUI:
    def test_document_list(self, page: Page):
        """文件管理列表"""
        page.goto(f"{BASE_URL}/documents")
        page.wait_for_timeout(2000)
        screenshot(page, "14_document_list")

        # 验证有数据
        expect(page.locator("text=文件编号")).to_be_visible()

    def test_type_filter(self, page: Page):
        """类型筛选标签"""
        # 点击报关单标签
        tag = page.locator("text=报关单").first
        if tag.is_visible():
            tag.click()
            page.wait_for_timeout(1000)
            screenshot(page, "15_document_filtered")

    def test_click_document(self, page: Page):
        """点击文件进入详情"""
        # 点击第一个文件编号链接
        first_doc = page.locator(".doc-no").first
        if first_doc.is_visible():
            first_doc.click()
            page.wait_for_url("**/documents/*", timeout=5000)
            page.wait_for_timeout(2000)
            screenshot(page, "16_document_detail")


# ============================================================
# 7. 文件详情
# ============================================================
class TestDocumentDetailUI:
    def test_detail_sections(self, page: Page):
        """详情页各区域"""
        # 可能已经在详情页了
        if "/documents/" not in page.url:
            page.goto(f"{BASE_URL}/documents")
            page.wait_for_timeout(1500)
            first = page.locator(".doc-no").first
            if first.is_visible():
                first.click()
                page.wait_for_timeout(2000)

        if "/documents/" in page.url:
            expect(page.locator("text=文件预览")).to_be_visible()
            expect(page.locator("text=提取字段")).to_be_visible()
            expect(page.locator("text=基本信息")).to_be_visible()
            screenshot(page, "17_detail_full")

    def test_fullscreen_preview(self, page: Page):
        """全屏预览"""
        if "/documents/" not in page.url:
            pytest.skip("不在详情页")

        btn = page.locator("text=全屏预览")
        if btn.is_visible():
            btn.click()
            page.wait_for_timeout(1500)
            screenshot(page, "18_fullscreen_preview")
            # 关闭弹窗
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)


# ============================================================
# 8. 人工核对
# ============================================================
class TestReviewUI:
    def test_review_page(self, page: Page):
        """人工核对页面"""
        page.goto(f"{BASE_URL}/review")
        page.wait_for_timeout(1500)
        screenshot(page, "19_review_page")

        expect(page.locator("text=紧急待核对")).to_be_visible()


# ============================================================
# 9. 数据管道
# ============================================================
class TestPipelineUI:
    def test_pipeline_page(self, page: Page):
        """数据管道页面"""
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_timeout(2000)
        screenshot(page, "20_pipeline_page")

        expect(page.locator("text=文件处理流程")).to_be_visible()
        expect(page.locator("text=数据质量指标")).to_be_visible()
        expect(page.locator("text=服务状态")).to_be_visible()


# ============================================================
# 10. 业务大模型
# ============================================================
class TestAiUI:
    def test_ai_page(self, page: Page):
        """AI 问答页面"""
        page.goto(f"{BASE_URL}/ai")
        page.wait_for_timeout(1500)
        screenshot(page, "21_ai_page")

        expect(page.locator("text=智能文件问答").first).to_be_visible()
        expect(page.locator("text=异常预警").first).to_be_visible()

    def test_ai_chat(self, page: Page):
        """AI 对话测试"""
        input_box = page.get_by_placeholder("输入问题")
        if input_box.is_visible():
            input_box.fill("本月上传了多少份文件？")
            page.get_by_role("button", name="发送").click()
            page.wait_for_timeout(5000)
            screenshot(page, "22_ai_chat")


# ============================================================
# 11. 数据报表
# ============================================================
class TestReportsUI:
    def test_reports_page(self, page: Page):
        """数据报表页面"""
        page.goto(f"{BASE_URL}/reports")
        page.wait_for_timeout(2000)
        screenshot(page, "23_reports_page")

        expect(page.locator("text=文件总数")).to_be_visible()


# ============================================================
# 12. 系统设置
# ============================================================
class TestSettingsUI:
    def test_settings_page(self, page: Page):
        """系统设置页面"""
        page.goto(f"{BASE_URL}/settings")
        page.wait_for_timeout(2000)
        screenshot(page, "24_settings_users")

        expect(page.locator("text=用户管理")).to_be_visible()
        expect(page.locator("text=字段模板")).to_be_visible()

    def test_field_templates_tab(self, page: Page):
        """字段模板标签页"""
        page.locator("text=字段模板").first.click()
        page.wait_for_timeout(1000)
        screenshot(page, "25_settings_templates")

    def test_ocr_engine_tab(self, page: Page):
        """识别引擎标签页"""
        page.locator("text=识别引擎").first.click()
        page.wait_for_timeout(1000)
        screenshot(page, "26_settings_ocr")
        expect(page.locator("text=引擎模式")).to_be_visible()

    def test_system_info_tab(self, page: Page):
        """系统信息标签页"""
        page.locator("text=系统信息").first.click()
        page.wait_for_timeout(500)
        screenshot(page, "27_settings_system")


# ============================================================
# 13. 侧边栏导航
# ============================================================
class TestNavigation:
    def test_all_menu_items(self, page: Page):
        """所有菜单项可点击"""
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_timeout(1000)

        menus = [
            ("概览仪表盘", "/dashboard"),
            ("文件管理", "/documents"),
            ("上传录入", "/upload"),
            ("订单管理", "/orders"),
            ("客户管理", "/customers"),
            ("数据管道", "/pipeline"),
            ("业务大模型", "/ai"),
            ("数据报表", "/reports"),
            ("系统设置", "/settings"),
        ]

        for name, path in menus:
            menu_item = page.locator(f".el-menu-item:has-text('{name}')").first
            if menu_item.is_visible():
                menu_item.click()
                page.wait_for_timeout(800)
                assert path in page.url, f"点击 {name} 后 URL 应包含 {path}，实际: {page.url}"

        screenshot(page, "28_navigation_final")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
