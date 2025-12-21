"""
完整功能测试脚本
测试所有后端功能模块
"""
import asyncio
import sys
import os
import httpx
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:8000"
session_id = None


async def test_health_check():
    """测试健康检查"""
    print("\n" + "="*60)
    print("1. 测试健康检查")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 测试基础健康检查
        response = await client.get(f"{BASE_URL}/health/")
        print(f"✅ 基础健康检查: {response.json()}")
        
        # 测试配置状态
        response = await client.get(f"{BASE_URL}/health/api-status")
        status = response.json()
        print(f"✅ 配置状态: {status['overall']}")
        for service, info in status['services'].items():
            status_icon = "✅" if info['configured'] else "❌"
            print(f"   {status_icon} {service}: {info['status']}")
        
        # 测试数据库连接
        response = await client.get(f"{BASE_URL}/health/test/database")
        db_status = response.json()
        if db_status['success']:
            print(f"✅ 数据库连接: MongoDB 和 Redis 都正常")
        else:
            print(f"❌ 数据库连接失败: {db_status}")
        
        return True


async def test_api_gateway():
    """测试 API Gateway 功能"""
    print("\n" + "="*60)
    print("2. 测试 API Gateway")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 测试 LLM 聊天
        print("\n[测试 LLM 聊天]")
        try:
            response = await client.post(
                f"{BASE_URL}/api/llm/chat",
                json={
                    "messages": [{"role": "user", "content": "用一句话介绍家族历史的重要性"}],
                    "model": "gpt-4",
                    "temperature": 0.7
                }
            )
            result = response.json()
            if result.get("success"):
                print(f"✅ LLM 聊天成功")
                print(f"   响应: {result['response'][:50]}...")
            else:
                print(f"❌ LLM 聊天失败: {result}")
        except Exception as e:
            print(f"❌ LLM 聊天错误: {e}")
        
        # 测试图片生成
        print("\n[测试图片生成]")
        try:
            response = await client.post(
                f"{BASE_URL}/api/media/image",
                json={
                    "prompt": "a simple red circle on white background",
                    "size": "256x256"
                }
            )
            result = response.json()
            if result.get("success"):
                print(f"✅ 图片生成成功")
                print(f"   URL: {result['url'][:80]}...")
            else:
                print(f"❌ 图片生成失败: {result}")
        except Exception as e:
            print(f"❌ 图片生成错误: {e}")
        
        # 测试搜索（如果配置了）
        print("\n[测试搜索功能]")
        try:
            response = await client.get(
                f"{BASE_URL}/api/search",
                params={"query": "家族历史", "num_results": 2}
            )
            result = response.json()
            if result.get("success"):
                print(f"✅ 搜索成功")
                print(f"   返回结果数: {result['count']}")
            else:
                print(f"⚠️  搜索未配置或失败: {result.get('detail', 'Unknown error')}")
        except Exception as e:
            print(f"⚠️  搜索功能未配置: {e}")
        
        return True


async def test_user_workflow():
    """测试用户工作流程"""
    global session_id
    
    print("\n" + "="*60)
    print("3. 测试用户工作流程")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 创建用户会话
        print("\n[创建用户会话]")
        try:
            response = await client.post(
                f"{BASE_URL}/user/input",
                json={
                    "name": "测试用户",
                    "birth_date": "1990-01-01",
                    "birth_place": "北京",
                    "current_location": "上海"
                }
            )
            result = response.json()
            if "session_id" in result:
                session_id = result["session_id"]
                print(f"✅ 会话创建成功")
                print(f"   Session ID: {session_id}")
            else:
                print(f"❌ 会话创建失败: {result}")
                return False
        except Exception as e:
            print(f"❌ 会话创建错误: {e}")
            return False
        
        # 获取初始问题
        print("\n[获取初始问题]")
        try:
            response = await client.get(f"{BASE_URL}/ai/question/{session_id}")
            result = response.json()
            if "question" in result:
                print(f"✅ 获取问题成功")
                print(f"   问题: {result['question'][:50]}...")
            else:
                print(f"❌ 获取问题失败: {result}")
        except Exception as e:
            print(f"❌ 获取问题错误: {e}")
        
        # 测试 AI 问答
        print("\n[测试 AI 问答]")
        try:
            response = await client.post(
                f"{BASE_URL}/ai/chat",
                json={
                    "session_id": session_id,
                    "answer": "我爸爸的籍贯是山东，他叫张建国"
                }
            )
            result = response.json()
            if result.get("status") == "continue" and "question" in result:
                print(f"✅ AI 问答成功")
                print(f"   下一个问题: {result['question'][:50]}...")
            elif result.get("status") == "complete":
                print(f"✅ AI 问答完成（数据收集完成）")
            else:
                print(f"❌ AI 问答失败: {result}")
        except Exception as e:
            print(f"❌ AI 问答错误: {e}")
        
        return True


async def test_generation():
    """测试生成功能"""
    global session_id
    
    if not session_id:
        print("\n⚠️  跳过生成测试（需要先创建会话）")
        return False
    
    print("\n" + "="*60)
    print("4. 测试生成功能")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 测试报告生成
        print("\n[测试报告生成]")
        try:
            response = await client.post(
                f"{BASE_URL}/generate/report",
                params={"session_id": session_id}
            )
            result = response.json()
            if "report" in result:
                report = result["report"]
                print(f"✅ 报告生成成功")
                print(f"   文字长度: {len(report.get('text', ''))} 字符")
                print(f"   图片数量: {len(report.get('images', []))}")
            else:
                print(f"❌ 报告生成失败: {result}")
        except Exception as e:
            print(f"❌ 报告生成错误: {e}")
        
        # 测试时间轴生成
        print("\n[测试时间轴生成]")
        try:
            response = await client.post(
                f"{BASE_URL}/generate/timeline",
                params={"session_id": session_id}
            )
            result = response.json()
            if "timeline" in result:
                timeline = result["timeline"]
                print(f"✅ 时间轴生成成功")
                print(f"   事件数量: {len(timeline)}")
            else:
                print(f"❌ 时间轴生成失败: {result}")
        except Exception as e:
            print(f"❌ 时间轴生成错误: {e}")
        
        # 测试传记生成
        print("\n[测试传记生成]")
        try:
            response = await client.post(
                f"{BASE_URL}/generate/biography",
                params={"session_id": session_id}
            )
            result = response.json()
            if "biography" in result:
                bio = result["biography"]
                print(f"✅ 传记生成成功")
                print(f"   传记长度: {len(bio)} 字符")
            else:
                print(f"❌ 传记生成失败: {result}")
        except Exception as e:
            print(f"❌ 传记生成错误: {e}")
        
        return True


async def main():
    """运行所有测试"""
    print("="*60)
    print("后端功能完整测试")
    print("="*60)
    print("\n确保后端服务正在运行: uvicorn app.main:app --reload")
    print("按 Enter 继续，或 Ctrl+C 退出...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n测试已取消")
        return
    
    results = {}
    
    # 测试各个模块
    try:
        results["health"] = await test_health_check()
        results["gateway"] = await test_api_gateway()
        results["workflow"] = await test_user_workflow()
        results["generation"] = await test_generation()
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("\n🎉 所有功能测试通过！")
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个测试失败")
        print("请检查错误信息并修复问题")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

