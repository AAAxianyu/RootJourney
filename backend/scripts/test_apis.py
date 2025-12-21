"""
API 连接测试脚本
用于验证所有第三方 API 的连接状态
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.gateway_service import GatewayService
from app.dependencies.db import get_mongodb_db, get_redis


async def test_openai():
    """测试 OpenAI API"""
    print("\n[测试 OpenAI]")
    if not settings.openai_api_key:
        print("❌ OpenAI API key 未配置")
        return False
    
    try:
        gateway = GatewayService()
        response = await gateway.llm_chat(
            messages=[{"role": "user", "content": "Say 'test successful' in one word"}],
            model="gpt-4"
        )
        print(f"✅ OpenAI 连接成功")
        print(f"   响应: {response[:50]}...")
        return True
    except Exception as e:
        print(f"❌ OpenAI 连接失败: {e}")
        return False


async def test_dalle():
    """测试 DALL·E API"""
    print("\n[测试 DALL·E]")
    if not settings.openai_api_key:
        print("❌ OpenAI API key 未配置")
        return False
    
    try:
        gateway = GatewayService()
        image_url = await gateway.generate_image(
            prompt="a simple red circle",
            size="256x256"
        )
        print(f"✅ DALL·E 连接成功")
        print(f"   图片URL: {image_url[:80]}...")
        return True
    except Exception as e:
        print(f"❌ DALL·E 连接失败: {e}")
        return False


async def test_google_search():
    """测试 Google Search API"""
    print("\n[测试 Google Search]")
    if not (settings.google_search_api_key and settings.google_search_engine_id):
        print("❌ Google Search API 未配置")
        return False
    
    try:
        gateway = GatewayService()
        results = await gateway.search("test", num_results=2)
        print(f"✅ Google Search 连接成功")
        print(f"   返回结果数: {len(results)}")
        if results:
            print(f"   第一个结果: {results[0].get('title', 'N/A')[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Google Search 连接失败: {e}")
        return False


async def test_xunfei():
    """测试讯飞 API 配置"""
    print("\n[测试 讯飞 API]")
    if not all([settings.xunfei_app_id, settings.xunfei_api_key, settings.xunfei_api_secret]):
        print("❌ 讯飞 API 配置不完整")
        print("   需要: XUNFEI_APP_ID, XUNFEI_API_KEY, XUNFEI_API_SECRET")
        return False
    
    print("✅ 讯飞 API 配置完整")
    print("   注意: 实际测试需要音频文件，请使用 /api/voice/transcribe 接口")
    return True


async def test_mongodb():
    """测试 MongoDB 连接"""
    print("\n[测试 MongoDB]")
    try:
        db = await get_mongodb_db()
        await db.command("ping")
        print(f"✅ MongoDB 连接成功")
        print(f"   数据库: {settings.mongodb_db_name}")
        return True
    except Exception as e:
        print(f"❌ MongoDB 连接失败: {e}")
        print(f"   请检查 MONGODB_URL: {settings.mongodb_url}")
        return False


async def test_redis():
    """测试 Redis 连接"""
    print("\n[测试 Redis]")
    try:
        redis = await get_redis()
        await redis.ping()
        print(f"✅ Redis 连接成功")
        print(f"   URL: {settings.redis_url}")
        return True
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        print(f"   请检查 REDIS_URL: {settings.redis_url}")
        return False


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("API 连接测试")
    print("=" * 60)
    
    results = {}
    
    # 测试各个服务
    results["openai"] = await test_openai()
    results["dalle"] = await test_dalle()
    results["google_search"] = await test_google_search()
    results["xunfei"] = await test_xunfei()
    results["mongodb"] = await test_mongodb()
    results["redis"] = await test_redis()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    for service, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {service.upper()}")
    
    print(f"\n成功: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 所有服务连接正常！")
        return 0
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个服务连接失败")
        print("请检查配置和网络连接")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


