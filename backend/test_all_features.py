"""
完整功能测试脚本 - RootJourney API
测试所有功能，包括生图功能（即梦4.0）
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str, color: str = Colors.BLUE):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(f"{color}{Colors.BOLD}  {title}{Colors.RESET}")
    print("=" * 70)

def print_success(msg: str):
    """打印成功消息"""
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")

def print_error(msg: str):
    """打印错误消息"""
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")

def print_warning(msg: str):
    """打印警告消息"""
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")

def print_info(msg: str):
    """打印信息消息"""
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")

def print_result(status_code: int, data: dict, show_full: bool = False):
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
                elif isinstance(value, list) and len(value) > 3:
                    print(f"  {key}: {value[:3]}... (共{len(value)}项)")
                else:
                    print(f"  {key}: {value}")

def test_health():
    """测试健康检查"""
    print_section("1. 健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health/", timeout=5)
        if response.status_code == 200:
            print_success("服务运行正常")
            return True
        else:
            print_error(f"服务返回状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("无法连接到服务器，请确保服务已启动")
        print_info("启动命令: docker-compose up 或 python -m uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"检查服务时出错: {e}")
        return False

def test_api_status():
    """测试API配置状态"""
    print_section("2. API 配置状态检查")
    try:
        response = requests.get(f"{BASE_URL}/health/api-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            services = data.get("services", {})
            
            # 检查各个服务
            deepseek = services.get("deepseek", {})
            mongodb = services.get("mongodb", {})
            redis = services.get("redis", {})
            seedream = services.get("seedream", {})
            
            print_info("服务配置状态：")
            print(f"  DeepSeek: {'✅ 已配置' if deepseek.get('configured') else '❌ 未配置'}")
            print(f"  MongoDB: {'✅ 已配置' if mongodb.get('configured') else '❌ 未配置'}")
            print(f"  Redis: {'✅ 已配置' if redis.get('configured') else '❌ 未配置'}")
            print(f"  即梦4.0: {'✅ 已配置' if seedream.get('configured') else '❌ 未配置'}")
            
            if not seedream.get('configured'):
                print_warning("即梦4.0 API Key 未配置，生图功能将无法使用")
                print_info("请设置环境变量 SEEDREAM_API_KEY")
            
            return True
        else:
            print_error(f"获取API状态失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"检查API状态时出错: {e}")
        return False

def test_create_session():
    """创建测试会话"""
    print_section("3. 创建测试会话")
    test_data = {
        "name": "张三",
        "birth_date": "1990-01-01",
        "birth_place": "北京",
        "current_location": "上海"
    }
    print_info(f"测试数据: {json.dumps(test_data, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{BASE_URL}/user/input", json=test_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            if session_id:
                print_success(f"会话创建成功: {session_id}")
                return session_id
            else:
                print_error("响应中未找到 session_id")
                return None
        else:
            print_error(f"创建会话失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"创建会话时出错: {e}")
        return None

def test_ai_chat(session_id: str):
    """测试AI问答"""
    print_section("4. AI 问答测试")
    
    answers = [
        "我的祖籍是山东",
        "我姓张",
        "我爷爷叫张建国",
        "我爸爸的老家在山东济南",
        "我们家的辈分字是'建'字辈"
    ]
    
    for i, answer in enumerate(answers, 1):
        print_info(f"[第 {i} 轮] 回答: {answer}")
        try:
            response = requests.post(
                f"{BASE_URL}/ai/chat",
                json={"session_id": session_id, "answer": answer},
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                next_question = result.get("question")
                print_success(f"提交成功，状态: {status}")
                if next_question:
                    print_info(f"下一个问题: {next_question[:60]}...")
                if status == "complete":
                    print_success("对话已完成")
                    break
            else:
                print_error(f"提交失败，状态码: {response.status_code}")
            time.sleep(1)
        except Exception as e:
            print_error(f"提交答案时出错: {e}")
    
    return True

def test_search_family(session_id: str):
    """测试家族搜索"""
    print_section("5. 家族搜索测试")
    print_info("开始搜索，这可能需要3-6分钟...")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/search/family?session_id={session_id}",
            timeout=600
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            results = result.get("results", {})
            families = results.get("possible_families", [])
            
            print_success(f"搜索完成（耗时: {elapsed_time:.1f}秒）")
            print_info(f"找到家族数: {len(families)}")
            for i, family in enumerate(families[:3], 1):
                print_info(f"  {i}. {family.get('family_name')} (关联度: {family.get('relevance', '未知')})")
            
            return True
        else:
            print_error(f"搜索失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"搜索时出错: {e}")
        return False

def test_generate_report(session_id: str):
    """测试生成报告"""
    print_section("6. 生成家族报告")
    print_info("开始生成报告，这可能需要4-7分钟...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/generate/report",
            json={"session_id": session_id},
            timeout=600
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            report = result.get("report", {})
            
            print_success(f"报告生成完成（耗时: {elapsed_time:.1f}秒）")
            print_info(f"标题: {report.get('title', 'N/A')}")
            print_info(f"报告长度: {len(report.get('report_text', ''))} 字符")
            print_info(f"找到家族数: {len(report.get('possible_families', []))}")
            
            # 显示报告预览
            report_text = report.get("report_text", "")
            if report_text:
                print_info("\n报告预览（前300字符）:")
                print(f"{Colors.CYAN}{report_text[:300]}...{Colors.RESET}")
            
            return True
        else:
            print_error(f"生成报告失败，状态码: {response.status_code}")
            print_error(f"响应: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"生成报告时出错: {e}")
        return False

def test_generate_images(session_id: str, num_images: int = 1):
    """测试生成图片（即梦4.0）"""
    print_section("7. 生成图片测试（即梦4.0）")
    print_info(f"准备生成 {num_images} 张图片...")
    print_warning("注意：需要先生成报告才能生成图片")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/generate/images",
            json={
                "session_id": session_id,
                "num_images": num_images,
                "size": "2K"
            },
            timeout=180  # 生图可能需要较长时间
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            
            print_success(f"图片生成完成（耗时: {elapsed_time:.1f}秒）")
            print_info(f"生成图片数: {len(images)}")
            
            for i, image_url in enumerate(images, 1):
                print_success(f"图片 {i}: {image_url}")
                print_info(f"  可以在浏览器中打开查看")
            
            return True
        else:
            error_detail = response.json().get("detail", response.text)
            print_error(f"生成图片失败，状态码: {response.status_code}")
            print_error(f"错误信息: {error_detail}")
            
            if "Report not found" in str(error_detail):
                print_warning("提示：需要先调用 /generate/report 生成报告")
            
            return False
    except requests.exceptions.Timeout:
        print_error("生成图片超时（超过3分钟）")
        return False
    except Exception as e:
        print_error(f"生成图片时出错: {e}")
        return False

def test_generate_timeline(session_id: str):
    """测试生成时间轴"""
    print_section("8. 生成时间轴")
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/timeline",
            json={"session_id": session_id},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            timeline = result.get("timeline", [])
            
            print_success(f"时间轴生成成功")
            print_info(f"时间轴事件数: {len(timeline)}")
            
            if timeline:
                print_info("\n时间轴预览（前3个事件）:")
                for i, event in enumerate(timeline[:3], 1):
                    print_info(f"  {i}. {event.get('year', 'N/A')} - {event.get('event', 'N/A')[:50]}...")
            
            return True
        else:
            print_error(f"生成时间轴失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"生成时间轴时出错: {e}")
        return False

def test_generate_biography(session_id: str):
    """测试生成传记"""
    print_section("9. 生成个人传记")
    print_info("开始生成传记，这可能需要2-4分钟...")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/generate/biography",
            json={"session_id": session_id},
            timeout=300
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            biography = result.get("biography", {})
            
            print_success(f"传记生成完成（耗时: {elapsed_time:.1f}秒）")
            print_info(f"传记长度: {len(biography.get('biography_text', ''))} 字符")
            
            # 显示传记预览
            bio_text = biography.get("biography_text", "")
            if bio_text:
                print_info("\n传记预览（前300字符）:")
                print(f"{Colors.CYAN}{bio_text[:300]}...{Colors.RESET}")
            
            return True
        else:
            print_error(f"生成传记失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"生成传记时出错: {e}")
        return False

def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.BLUE}  RootJourney API 完整功能测试{Colors.RESET}")
    print("=" * 70)
    print("\n本测试将验证所有功能，包括：")
    print("  1. 健康检查和API配置")
    print("  2. 用户会话管理")
    print("  3. AI问答对话")
    print("  4. 家族搜索")
    print("  5. 报告生成")
    print("  6. 图片生成（即梦4.0）⭐")
    print("  7. 时间轴生成")
    print("  8. 传记生成")
    
    # 1. 健康检查
    if not test_health():
        print_error("\n服务未启动，请先启动服务")
        sys.exit(1)
    
    # 2. API状态检查
    test_api_status()
    
    # 3. 创建会话
    session_id = test_create_session()
    if not session_id:
        print_error("\n创建会话失败，退出测试")
        sys.exit(1)
    
    # 4. AI问答
    test_ai_chat(session_id)
    
    # 等待数据保存
    print_info("\n等待数据保存...")
    time.sleep(3)
    
    # 5. 搜索家族
    user_input = input("\n是否执行家族搜索？(y/n，默认y): ").strip().lower()
    if user_input != 'n':
        search_success = test_search_family(session_id)
        if not search_success:
            print_warning("搜索失败，但继续测试其他功能...")
    
    # 6. 生成报告（生图功能需要先有报告）
    user_input = input("\n是否生成报告？（生图功能需要先有报告）(y/n，默认y): ").strip().lower()
    report_success = False
    if user_input != 'n':
        report_success = test_generate_report(session_id)
        if not report_success:
            print_warning("报告生成失败，生图功能将无法使用")
    
    # 7. 生成图片（即梦4.0）⭐
    if report_success:
        user_input = input("\n是否测试生图功能（即梦4.0）？(y/n，默认y): ").strip().lower()
        if user_input != 'n':
            num_images = input("生成几张图片？(1-2，默认1): ").strip()
            try:
                num_images = int(num_images) if num_images else 1
                num_images = max(1, min(2, num_images))  # 限制在1-2之间
            except ValueError:
                num_images = 1
            
            print_info(f"将生成 {num_images} 张图片")
            test_generate_images(session_id, num_images)
    else:
        print_warning("跳过生图测试（需要先成功生成报告）")
    
    # 8. 生成时间轴
    user_input = input("\n是否生成时间轴？(y/n，默认y): ").strip().lower()
    if user_input != 'n':
        test_generate_timeline(session_id)
    
    # 9. 生成传记
    user_input = input("\n是否生成传记？(y/n，默认y): ").strip().lower()
    if user_input != 'n':
        test_generate_biography(session_id)
    
    # 总结
    print_section("测试总结", Colors.GREEN)
    print_success(f"会话ID: {session_id}")
    print_info("你可以使用这个 session_id 继续测试或查看结果")
    print_info("查看报告: GET /session/{session_id}/report")
    print_info("查看图片: 在浏览器中打开生成的图片URL")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  测试被用户中断{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
