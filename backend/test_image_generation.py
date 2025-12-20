"""
快速测试生图功能（即梦4.0）
专门用于测试图片生成功能
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_api_config():
    """检查即梦API配置"""
    print_section("1. 检查即梦4.0 API配置")
    try:
        response = requests.get(f"{BASE_URL}/health/api-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            seedream = data.get("services", {}).get("seedream", {})
            
            if seedream.get("configured"):
                print("✅ 即梦4.0 API Key 已配置")
                return True
            else:
                print("❌ 即梦4.0 API Key 未配置")
                print("   请设置环境变量 SEEDREAM_API_KEY")
                return False
        else:
            print(f"❌ 无法获取API状态，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查API配置时出错: {e}")
        return False

def test_generate_images(session_id: str, num_images: int = 1):
    """测试生成图片"""
    print_section("2. 生成图片测试")
    
    print(f"会话ID: {session_id}")
    print(f"生成图片数: {num_images}")
    print("⏳ 开始生成，请稍候...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/images",
            json={
                "session_id": session_id,
                "num_images": num_images,
                "size": "2K"
            },
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])
            
            print(f"\n✅ 图片生成成功！")
            print(f"生成图片数: {len(images)}")
            print("\n图片URL:")
            for i, image_url in enumerate(images, 1):
                print(f"  {i}. {image_url}")
                print(f"     可以在浏览器中打开查看")
            
            return True
        else:
            error_detail = response.json().get("detail", response.text)
            print(f"\n❌ 生成图片失败")
            print(f"状态码: {response.status_code}")
            print(f"错误信息: {error_detail}")
            
            if "Report not found" in str(error_detail):
                print("\n💡 提示：需要先生成报告")
                print("   请先调用: POST /generate/report")
                print(f"   或运行: python test_all_features.py")
            
            return False
    except requests.exceptions.Timeout:
        print("\n❌ 生成图片超时（超过3分钟）")
        return False
    except Exception as e:
        print(f"\n❌ 生成图片时出错: {e}")
        return False

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("  即梦4.0 生图功能快速测试")
    print("=" * 60)
    
    # 1. 检查API配置
    if not test_api_config():
        print("\n❌ API配置检查失败，退出测试")
        sys.exit(1)
    
    # 2. 获取session_id
    print_section("2. 输入会话ID")
    session_id = input("请输入 session_id（或按回车使用测试会话）: ").strip()
    
    if not session_id:
        # 创建测试会话
        print("创建测试会话...")
        try:
            response = requests.post(
                f"{BASE_URL}/user/input",
                json={
                    "name": "测试用户",
                    "birth_place": "北京"
                },
                timeout=10
            )
            if response.status_code == 200:
                session_id = response.json().get("session_id")
                print(f"✅ 测试会话创建成功: {session_id}")
                
                # 快速问答
                answers = ["我的祖籍是山东", "我姓张", "我爷爷叫张建国"]
                for answer in answers:
                    requests.post(
                        f"{BASE_URL}/ai/chat",
                        json={"session_id": session_id, "answer": answer},
                        timeout=30
                    )
                
                # 生成报告
                print("生成报告（生图需要先有报告）...")
                report_response = requests.post(
                    f"{BASE_URL}/generate/report",
                    json={"session_id": session_id},
                    timeout=600
                )
                if report_response.status_code == 200:
                    print("✅ 报告生成成功")
                else:
                    print("⚠️  报告生成失败，但继续测试生图功能...")
            else:
                print("❌ 创建测试会话失败")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 创建测试会话时出错: {e}")
            sys.exit(1)
    
    # 3. 获取图片数量
    num_images_input = input("\n生成几张图片？(1-2，默认1): ").strip()
    try:
        num_images = int(num_images_input) if num_images_input else 1
        num_images = max(1, min(2, num_images))
    except ValueError:
        num_images = 1
    
    # 4. 测试生图
    test_generate_images(session_id, num_images)
    
    print("\n" + "=" * 60)
    print("  测试完成")
    print("=" * 60)

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
