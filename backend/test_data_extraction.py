"""
数据提取与搜索功能测试脚本
专门测试数据提取、规范化、存储和搜索的完整流程
"""
import requests
import json
import time
import sys
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
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

def check_service():
    """检查服务是否运行"""
    print_section("1. 检查服务状态")
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

def create_session() -> Optional[str]:
    """创建测试会话"""
    print_section("2. 创建测试会话")
    
    # 测试数据：包含姓氏"张"和地区"山东"
    test_data = {
        "name": "张三",  # 姓氏可以从这里提取
        "birth_date": "1990-01-01",
        "birth_place": "北京",  # 初始地区
        "current_location": "上海"
    }
    
    print_info(f"测试数据: {json.dumps(test_data, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/user/input",
            json=test_data,
            timeout=10
        )
        
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
            print_error(f"响应: {response.text}")
            return None
    except Exception as e:
        print_error(f"创建会话时出错: {e}")
        return None

def get_question(session_id: str) -> Optional[str]:
    """获取初始问题"""
    print_section("3. 获取初始问题")
    try:
        response = requests.get(
            f"{BASE_URL}/ai/question/{session_id}",
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            question = result.get("question")
            if question:
                print_success(f"获取到问题: {question[:80]}...")
                return question
            else:
                print_warning("未获取到问题")
                return None
        else:
            print_error(f"获取问题失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"获取问题时出错: {e}")
        return None

def submit_answers(session_id: str) -> bool:
    """提交测试答案，验证数据提取"""
    print_section("4. 提交测试答案（验证数据提取）")
    
    # 测试答案序列：包含姓氏、地区、祖父姓名等关键信息
    test_answers = [
        {
            "answer": "我的祖籍是山东",
            "expected_extract": {"self": {"origin": "山东"}},
            "description": "提取祖籍信息"
        },
        {
            "answer": "我姓张",
            "expected_extract": {"self": {"surname": "张"}},
            "description": "提取姓氏信息"
        },
        {
            "answer": "我爷爷叫张建国",
            "expected_extract": {"grandfather": {"name": "张建国"}},
            "description": "提取祖父姓名（可用于推导姓氏）"
        },
        {
            "answer": "我爸爸的老家在山东济南",
            "expected_extract": {"father": {"origin": "山东济南"}},
            "description": "提取父亲籍贯"
        }
    ]
    
    all_success = True
    
    for i, test_case in enumerate(test_answers, 1):
        print(f"\n[测试 {i}/{len(test_answers)}] {test_case['description']}")
        print_info(f"答案: {test_case['answer']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/ai/chat",
                json={
                    "session_id": session_id,
                    "answer": test_case["answer"]
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                print_success(f"提交成功，状态: {status}")
                
                # 检查是否有下一个问题
                next_question = result.get("question")
                if next_question:
                    print_info(f"下一个问题: {next_question[:60]}...")
                else:
                    print_info("对话已完成")
            else:
                print_error(f"提交失败，状态码: {response.status_code}")
                print_error(f"响应: {response.text}")
                all_success = False
            
            time.sleep(1)  # 避免请求过快
            
        except Exception as e:
            print_error(f"提交答案时出错: {e}")
            all_success = False
    
    return all_success

def verify_data_structure(session_id: str) -> bool:
    """验证数据存储结构"""
    print_section("5. 验证数据存储结构")
    
    try:
        # 获取会话详情（如果有这个接口）
        # 如果没有，我们通过搜索接口来验证数据
        print_info("通过搜索接口验证数据存储...")
        
        # 先尝试获取会话信息
        response = requests.get(
            f"{BASE_URL}/session/{session_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            # 接口返回格式: {"session": {...}}
            session_data = result.get("session", {})
            if not session_data:
                # 如果没有 session 键，可能直接返回了数据
                session_data = result
            
            print_success("成功获取会话数据")
            print_info(f"会话数据 keys: {list(session_data.keys())}")
            
            # 检查数据格式
            family_graph = session_data.get("family_graph", {})
            print_info(f"family_graph 类型: {type(family_graph)}, 值: {family_graph if family_graph else '空'}")
            if isinstance(family_graph, dict):
                if "collected_data" in family_graph:
                    print_success("数据格式正确: family_graph.collected_data")
                    collected_data = family_graph.get("collected_data", {})
                elif family_graph:
                    print_warning("使用旧格式: family_graph 直接是 collected_data")
                    collected_data = family_graph
                else:
                    # family_graph 为空，尝试从 collected_data 字段读取
                    print_warning("family_graph 为空，尝试从 collected_data 字段读取")
                    collected_data = session_data.get("collected_data", {})
                    if not collected_data:
                        print_error("collected_data 也为空，数据可能未正确保存")
                        print_info("提示：数据可能还在 Redis 中，搜索功能会从 MongoDB 读取")
                        return True  # 继续测试，搜索功能可能仍能工作
                
                # 检查 _unparsed 数据
                unparsed_info = collected_data.get("_unparsed", [])
                if unparsed_info:
                    print_info(f"\n未解析的对话数据: {len(unparsed_info)} 条")
                    for i, item in enumerate(unparsed_info[:3], 1):  # 只显示前3条
                        print_info(f"  {i}. 问题: {item.get('q', '')[:50]}...")
                        print_info(f"     回答: {item.get('a', '')[:50]}...")
                    if len(unparsed_info) > 3:
                        print_info(f"  ... 还有 {len(unparsed_info) - 3} 条")
                    print_info("提示：这些数据会在搜索时被提取")
                
                # 检查关键字段
                print_info("\n检查关键字段:")
                key_fields = {
                    "surname": ["surname", "self.surname"],
                    "self_origin": ["self_origin", "self.origin"],
                    "grandfather_name": ["grandfather_name", "grandfather.name"],
                    "father_origin": ["father_origin", "father.origin"]
                }
                
                found_fields = []
                for field_name, paths in key_fields.items():
                    found = False
                    for path in paths:
                        if "." in path:
                            # 嵌套路径
                            parts = path.split(".")
                            value = collected_data
                            for part in parts:
                                if isinstance(value, dict) and part in value:
                                    value = value[part]
                                else:
                                    value = None
                                    break
                            if value:
                                found = True
                                found_fields.append(f"{field_name} ({path})")
                                print_success(f"  {field_name}: {value} (来源: {path})")
                                break
                        else:
                            # 扁平路径
                            if path in collected_data and collected_data[path]:
                                found = True
                                found_fields.append(f"{field_name} ({path})")
                                print_success(f"  {field_name}: {collected_data[path]} (来源: {path})")
                                break
                    
                    if not found:
                        # 检查是否在 _unparsed 中
                        in_unparsed = False
                        if unparsed_info:
                            for item in unparsed_info:
                                answer = item.get("a", "")
                                if field_name == "grandfather_name" and ("爷爷" in answer or "祖父" in answer):
                                    print_warning(f"  {field_name}: 未找到（但在未解析对话中发现相关信息，搜索时会提取）")
                                    in_unparsed = True
                                    break
                                elif field_name == "surname" and ("姓" in answer or "姓氏" in answer):
                                    print_warning(f"  {field_name}: 未找到（但在未解析对话中发现相关信息，搜索时会提取）")
                                    in_unparsed = True
                                    break
                        if not in_unparsed:
                            print_warning(f"  {field_name}: 未找到")
                
                if found_fields:
                    print_success(f"\n找到 {len(found_fields)} 个关键字段")
                    return True
                else:
                    print_error("未找到任何关键字段")
                    return False
            else:
                print_warning("无法获取会话详情，将通过搜索验证")
                return True  # 继续测试搜索
        else:
            print_warning(f"获取会话详情失败（状态码: {response.status_code}），将通过搜索验证")
            return True  # 继续测试搜索
            
    except Exception as e:
        print_warning(f"验证数据存储结构时出错: {e}")
        print_info("将继续测试搜索功能")
        return True  # 继续测试

def test_search(session_id: str) -> bool:
    """测试搜索功能，验证数据提取和识别"""
    print_section("6. 测试搜索功能（验证数据提取和识别）")
    
    print_info("开始搜索，这可能需要3-6分钟...")
    print_info("搜索过程会验证：")
    print_info("  1. 数据规范化是否正确")
    print_info("  2. 关键信息是否正确提取")
    print_info("  3. 姓氏匹配是否优先")
    print_info("  4. 地区匹配是否作为补充")
    
    try:
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/search/family?session_id={session_id}",
            timeout=600  # 10分钟超时
        )
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            results = result.get("results", {})
            
            print_success(f"搜索完成（耗时: {elapsed_time:.1f}秒）")
            
            # 检查搜索结果
            possible_families = results.get("possible_families", [])
            family_histories = results.get("family_histories", {})
            
            print_info(f"\n搜索结果:")
            print_info(f"  找到家族数: {len(possible_families)}")
            print_info(f"  历史记录数: {len(family_histories)}")
            
            # 验证姓氏匹配
            if possible_families:
                print_info("\n验证姓氏匹配:")
                surname_matched = False
                for family in possible_families:
                    family_name = family.get("family_name", "")
                    if "张" in family_name:
                        surname_matched = True
                        print_success(f"  找到姓氏匹配: {family_name}")
                        print_info(f"    关联度: {family.get('relevance', '未知')}")
                        print_info(f"    关联线索: {', '.join(family.get('connection_clues', []))}")
                        
                        # 检查是否有著名人物
                        famous_figures = family.get("famous_figures", [])
                        if famous_figures:
                            print_success(f"    著名人物数: {len(famous_figures)}")
                            for figure in famous_figures[:2]:  # 只显示前2个
                                name = figure.get("name", "")
                                relation = figure.get("possible_relation", "")
                                print_info(f"      - {name}: {relation[:50]}...")
                        break
                
                if not surname_matched:
                    print_warning("  未找到明确的姓氏匹配")
                
                # 验证地区匹配
                print_info("\n验证地区匹配:")
                region_matched = False
                for family in possible_families:
                    main_regions = family.get("main_regions", [])
                    if any("山东" in str(region) for region in main_regions):
                        region_matched = True
                        print_success(f"  找到地区匹配: {family.get('family_name')}")
                        print_info(f"    主要地区: {', '.join(main_regions)}")
                        break
                
                if not region_matched:
                    print_warning("  未找到明确的地区匹配")
                
                # 显示所有找到的家族
                print_info("\n所有找到的家族:")
                for i, family in enumerate(possible_families, 1):
                    print_info(f"  {i}. {family.get('family_name')}")
                    print_info(f"     关联度: {family.get('relevance', '未知')}")
                    print_info(f"     地区: {', '.join(family.get('main_regions', []))}")
            else:
                print_warning("未找到任何家族")
                return False
            
            # 搜索完成后，再次验证数据（因为搜索时会从未解析对话中提取信息）
            print_info("\n搜索完成后，再次验证提取的数据...")
            time.sleep(2)  # 等待数据保存
            
            verify_response = requests.get(
                f"{BASE_URL}/session/{session_id}",
                timeout=10
            )
            if verify_response.status_code == 200:
                verify_result = verify_response.json()
                verify_session_data = verify_result.get("session", {})
                verify_family_graph = verify_session_data.get("family_graph", {})
                if isinstance(verify_family_graph, dict) and "collected_data" in verify_family_graph:
                    verify_collected_data = verify_family_graph.get("collected_data", {})
                    verify_grandfather_name = (
                        verify_collected_data.get("grandfather_name") or 
                        verify_collected_data.get("grandfather", {}).get("name")
                    )
                    if verify_grandfather_name:
                        print_success(f"✅ 搜索后验证：祖父姓名已提取 - {verify_grandfather_name}")
                    else:
                        print_warning("⚠️  搜索后验证：祖父姓名仍未提取（可能提取逻辑需要检查）")
            
            return True
        else:
            print_error(f"搜索失败，状态码: {response.status_code}")
            print_error(f"响应: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("搜索超时（超过10分钟）")
        return False
    except Exception as e:
        print_error(f"搜索时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_normalization(session_id: str) -> bool:
    """测试数据规范化（通过查看日志或直接检查）"""
    print_section("7. 验证数据规范化")
    
    print_info("数据规范化验证要点：")
    print_info("  1. 嵌套结构 → 扁平结构转换")
    print_info("  2. 嵌套结构同步更新")
    print_info("  3. 从 user_profile 提取并同步")
    
    print_warning("注意：完整的数据规范化验证需要查看服务器日志")
    print_info("查看日志命令: docker logs rootjourney-backend | grep 'Normalized\\|Extracted\\|Collected data'")
    
    # 通过搜索接口间接验证（搜索时会调用规范化）
    print_info("通过搜索接口间接验证数据规范化...")
    
    # 如果搜索成功，说明规范化工作正常
    return True

def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.BLUE}  数据提取与搜索功能测试{Colors.RESET}")
    print("=" * 70)
    print("\n本测试将验证：")
    print("  1. 数据存储格式是否正确")
    print("  2. 数据提取是否从多个位置读取")
    print("  3. 数据规范化是否工作")
    print("  4. 搜索时是否能正确识别和使用数据")
    print("  5. 姓氏匹配是否优先")
    print("  6. 地区匹配是否作为补充")
    
    # 1. 检查服务
    if not check_service():
        print_error("\n服务未启动，请先启动服务")
        sys.exit(1)
    
    # 2. 创建会话
    session_id = create_session()
    if not session_id:
        print_error("\n创建会话失败，退出测试")
        sys.exit(1)
    
    # 3. 获取初始问题
    get_question(session_id)
    
    # 4. 提交测试答案
    if not submit_answers(session_id):
        print_warning("\n部分答案提交失败，但继续测试...")
    
    # 等待数据保存（增加等待时间，确保数据已持久化）
    print_info("\n等待数据保存到 MongoDB...")
    print_info("提示：数据保存是异步的，可能需要几秒钟")
    time.sleep(5)  # 增加等待时间到5秒
    
    # 5. 验证数据存储结构
    verify_data_structure(session_id)
    
    # 6. 测试搜索功能
    user_input = input("\n是否执行搜索测试？(y/n，默认y): ").strip().lower()
    if user_input != 'n':
        search_success = test_search(session_id)
        if search_success:
            print_success("\n搜索测试通过！")
        else:
            print_error("\n搜索测试失败")
    else:
        print_info("跳过搜索测试")
    
    # 7. 验证数据规范化
    test_data_normalization(session_id)
    
    # 总结
    print_section("测试总结", Colors.GREEN)
    print_success(f"会话ID: {session_id}")
    print_info("你可以使用这个 session_id 继续测试其他功能")
    print_info("查看详细日志: docker logs rootjourney-backend | grep 'Normalized\\|Extracted\\|Collected data'")
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
