"""
快速测试脚本 - RootJourney API
用于快速验证所有核心功能
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_result(status_code, data, show_full=False):
    """打印结果"""
    status_icon = "✅" if status_code == 200 else "❌"
    print(f"{status_icon} 状态码: {status_code}")
    if show_full:
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"响应: {data}")

def test_health():
    """测试健康检查"""
    print_section("1. 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health/", timeout=5)
        print_result(response.status_code, response.json())
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务已启动")
        print("   启动命令: docker-compose up 或 python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_api_status():
    """测试API状态"""
    print_section("2. API 配置状态")
    try:
        response = requests.get(f"{BASE_URL}/health/api-status", timeout=5)
        data = response.json()
        print_result(response.status_code, data)
        
        # 检查关键服务
        services = data.get("services", {})
        deepseek_ok = services.get("deepseek", {}).get("configured", False)
        mongodb_ok = services.get("mongodb", {}).get("configured", False)
        redis_ok = services.get("redis", {}).get("configured", False)
        
        if not deepseek_ok:
            print("⚠️  警告: DeepSeek API Key 未配置")
        if not mongodb_ok:
            print("⚠️  警告: MongoDB 未配置")
        if not redis_ok:
            print("⚠️  警告: Redis 未配置")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_create_session():
    """创建会话"""
    print_section("3. 创建会话")
    try:
        data = {
            "name": "张三",
            "birth_date": "1990-01-01",
            "birth_place": "北京",
            "current_location": "上海"
        }
        response = requests.post(f"{BASE_URL}/user/input", json=data, timeout=10)
        result = response.json()
        print_result(response.status_code, result)
        
        session_id = result.get("session_id")
        if session_id:
            print(f"✅ 会话ID: {session_id}")
            return session_id
        else:
            print("❌ 未获取到 session_id")
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_get_question(session_id):
    """获取初始问题"""
    print_section("4. 获取初始问题")
    try:
        response = requests.get(f"{BASE_URL}/ai/question/{session_id}", timeout=10)
        result = response.json()
        print_result(response.status_code, result)
        
        question = result.get("question")
        if question:
            print(f"✅ 问题: {question}")
            return question
        else:
            print("⚠️  未获取到问题")
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_chat(session_id, answer, round_num):
    """提交回答"""
    print_section(f"5.{round_num} 提交回答 (第 {round_num} 轮)")
    try:
        print(f"回答: {answer}")
        data = {
            "session_id": session_id,
            "answer": answer
        }
        response = requests.post(f"{BASE_URL}/ai/chat", json=data, timeout=30)
        result = response.json()
        
        status = result.get("status")
        question = result.get("question")
        
        print(f"状态: {status}")
        if question:
            print(f"下一个问题: {question[:100]}...")
        else:
            print("对话已结束")
        
        return result
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_search(session_id):
    """搜索家族历史"""
    print_section("6. 搜索家族历史")
    try:
        print("⏳ 搜索中，请稍候...")
        print("   提示：搜索可能需要3-6分钟，请耐心等待...")
        response = requests.get(
            f"{BASE_URL}/search/family?session_id={session_id}",
            timeout=600  # 搜索可能需要较长时间（增加到10分钟）
        )
        result = response.json()
        
        results = result.get("results", {})
        families = results.get("possible_families", [])
        print_result(response.status_code, {
            "找到家族数": len(families),
            "家族列表": [f.get("family_name") for f in families[:3]]
        })
        
        return result
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_generate_report(session_id):
    """生成报告"""
    print_section("7. 生成家族报告")
    try:
        print("⏳ 生成中，请稍候...")
        print("   提示：报告生成可能需要4-7分钟，请耐心等待...")
        data = {"session_id": session_id}
        response = requests.post(
            f"{BASE_URL}/generate/report",
            json=data,
            timeout=600  # 生成报告可能需要较长时间（增加到10分钟）
        )
        result = response.json()
        
        report = result.get("report", {})
        print_result(response.status_code, {
            "标题": report.get("title"),
            "报告长度": len(report.get("report_text", "")),
            "找到家族数": len(report.get("possible_families", []))
        })
        
        # 显示报告前200字符
        report_text = report.get("report_text", "")
        if report_text:
            print(f"\n报告预览（前200字符）:")
            print(f"{report_text[:200]}...")
        
        return result
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("  RootJourney API 快速测试")
    print("=" * 60)
    
    # 1. 健康检查
    if not test_health():
        print("\n❌ 服务未启动，请先启动服务")
        sys.exit(1)
    
    # 2. API状态
    test_api_status()
    
    # 3. 创建会话
    session_id = test_create_session()
    if not session_id:
        print("\n❌ 创建会话失败，退出测试")
        sys.exit(1)
    
    # 4. 获取初始问题
    question = test_get_question(session_id)
    
    # 5. 进行至少5轮对话
    answers = [
        "我的祖籍是山东",
        "我爸爸的老家在山东济南",
        "我爷爷叫张建国，是1950年出生的",
        "我们家的辈分字是'建'字辈",
        "我记得小时候听长辈说过，我们是从山西迁过来的"
    ]
    
    print_section("5. 进行对话（至少5轮）")
    for i, answer in enumerate(answers, 1):
        result = test_chat(session_id, answer, i)
        if result and result.get("status") == "complete":
            print("✅ 对话已完成")
            break
        time.sleep(1)  # 避免请求过快
    
    # 6. 搜索家族历史（可选）
    user_input = input("\n是否搜索家族历史？(y/n，默认n): ").strip().lower()
    if user_input == 'y':
        test_search(session_id)
    
    # 7. 生成报告
    user_input = input("\n是否生成报告？(y/n，默认y): ").strip().lower()
    if user_input != 'n':
        test_generate_report(session_id)
    
    print("\n" + "=" * 60)
    print("  ✅ 测试完成！")
    print("=" * 60)
    print(f"\n会话ID: {session_id}")
    print("你可以使用这个 session_id 继续测试其他功能\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
