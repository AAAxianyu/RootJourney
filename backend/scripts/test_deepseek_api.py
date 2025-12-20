"""
DeepSeek API 测试脚本
用于验证API密钥有效性和测试实际业务场景中的AI调用
"""
import asyncio
import sys
import os
import json
import traceback
from typing import Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import AsyncOpenAI
from openai import APIError, AuthenticationError
from app.config import settings
from app.utils.api_key_manager import APIKeyManager
from app.utils.logger import logger


def print_section(title: str):
    """打印测试章节标题"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_success(message: str):
    """打印成功消息"""
    print(f"✅ {message}")


def print_error(message: str, details: Optional[str] = None):
    """打印错误消息"""
    print(f"❌ {message}")
    if details:
        print(f"   详细信息: {details}")


def print_info(message: str):
    """打印信息消息"""
    print(f"ℹ️  {message}")


def print_request_details(client: AsyncOpenAI, model: str, messages: list, temperature: float = 0.7):
    """打印请求详细信息"""
    print("\n[请求详情]")
    print(f"  Base URL: {client.base_url}")
    print(f"  Model: {model}")
    print(f"  Temperature: {temperature}")
    print(f"  Messages: {len(messages)} 条")
    for i, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        preview = content[:100] + "..." if len(content) > 100 else content
        print(f"    {i}. [{role}]: {preview}")


def print_response_details(response: Any):
    """打印响应详细信息"""
    print("\n[响应详情]")
    if hasattr(response, 'choices') and response.choices:
        choice = response.choices[0]
        if hasattr(choice, 'message'):
            content = choice.message.content or ""
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  内容: {preview}")
            print(f"  长度: {len(content)} 字符")
    if hasattr(response, 'usage'):
        usage = response.usage
        print(f"  Token使用: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")


def print_exception_details(e: Exception):
    """打印异常详细信息"""
    print("\n[异常详情]")
    print(f"  类型: {type(e).__name__}")
    print(f"  消息: {str(e)}")
    
    # 如果是OpenAI API错误，显示更多信息
    if isinstance(e, APIError):
        if hasattr(e, 'status_code'):
            print(f"  状态码: {e.status_code}")
        if hasattr(e, 'response'):
            print(f"  响应: {e.response}")
        if hasattr(e, 'body'):
            print(f"  响应体: {e.body}")
        if hasattr(e, 'code'):
            print(f"  错误代码: {e.code}")
    
    # 打印完整堆栈跟踪
    print("\n[堆栈跟踪]")
    traceback.print_exc()


async def test_api_key_config() -> bool:
    """测试API密钥配置"""
    print_section("1. 测试API密钥配置")
    
    try:
        # 检查配置中的密钥
        config_key = settings.deepseek_api_key
        print_info(f"配置文件中的密钥: {'已配置' if config_key else '未配置'}")
        if config_key:
            masked_key = config_key[:8] + "..." + config_key[-4:] if len(config_key) > 12 else "***"
            print_info(f"密钥预览: {masked_key}")
            print_info(f"密钥长度: {len(config_key)} 字符")
        
        # 检查运行时密钥
        runtime_key = APIKeyManager.get_deepseek_key()
        print_info(f"运行时密钥: {'已设置' if runtime_key else '未设置'}")
        
        if not runtime_key:
            print_error("API密钥未配置", "请设置 DEEPSEEK_API_KEY 环境变量或在运行时设置密钥")
            return False
        
        # 验证密钥格式（DeepSeek密钥通常以sk-开头）
        if not runtime_key.startswith("sk-"):
            print_error("API密钥格式可能不正确", "DeepSeek API密钥通常以'sk-'开头")
            return False
        
        print_success("API密钥配置检查通过")
        return True
        
    except Exception as e:
        print_error("API密钥配置检查失败", str(e))
        print_exception_details(e)
        return False


async def test_basic_chat() -> bool:
    """测试基础聊天功能"""
    print_section("2. 测试基础聊天功能")
    
    try:
        # 获取API密钥
        api_key = APIKeyManager.get_deepseek_key()
        if not api_key:
            print_error("API密钥未配置")
            return False
        
        # 创建客户端
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.deepseek_base_url
        )
        
        # 准备测试消息
        messages = [
            {"role": "user", "content": "请用一句话回答：什么是家族历史？"}
        ]
        model = settings.deepseek_model
        
        # 打印请求详情
        print_request_details(client, model, messages, temperature=0.7)
        
        # 发送请求
        print("\n[发送请求...]")
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7
        )
        
        # 打印响应详情
        print_response_details(response)
        
        # 验证响应
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content:
                print_success("基础聊天测试成功")
                print(f"  响应内容: {content[:100]}...")
                return True
            else:
                print_error("响应内容为空")
                return False
        else:
            print_error("响应中没有choices")
            return False
            
    except AuthenticationError as e:
        print_error("认证失败", "API密钥无效或已过期")
        print_exception_details(e)
        return False
    except APIError as e:
        print_error("API调用失败", f"错误代码: {e.code if hasattr(e, 'code') else 'unknown'}")
        print_exception_details(e)
        return False
    except Exception as e:
        print_error("基础聊天测试失败", str(e))
        print_exception_details(e)
        return False


async def test_generate_candidate_questions() -> bool:
    """测试生成候选问题（模拟ai_service中的调用）"""
    print_section("3. 测试生成候选问题")
    
    try:
        # 获取API密钥
        api_key = APIKeyManager.get_deepseek_key()
        if not api_key:
            print_error("API密钥未配置")
            return False
        
        # 创建客户端
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.deepseek_base_url
        )
        
        # 模拟ai_service中的调用
        topic = "用户自己的祖籍/籍贯与家乡印象（允许模糊）"
        collected_data = {
            "user_profile": {
                "name": "测试用户",
                "birth_place": "北京"
            }
        }
        n = 4
        avoid = []
        
        narrative_style = """
你是一位"家族记忆引导者"，不是信息采集器。
你在做的是"陪伴式寻根与家族叙事"，而不是查户口填表。

风格要求：
- 温和、尊重、带一点陪伴感
- 接受信息不完整、模糊或"不知道"
- 鼓励叙述（"你印象里…/你听谁提过…/大概也行"）
- 不要使用"请提供/请填写/必须回答"等表单语气
- 不要责备、不要审问、不要让用户觉得答错了
"""
        
        prompt = f"""
{narrative_style}

基于已收集的家族数据，生成{n}个候选问题来丰富家族信息。

**重要：所有问题必须围绕寻根、寻祖际、寻家族这三个核心主题**

主题：{topic}

已收集数据：{json.dumps(collected_data, ensure_ascii=False)}

已问过的问题（避免重复）：
{json.dumps(avoid, ensure_ascii=False)}

要求：
1. 避免重复已问过的问题
2. 围绕主题"{topic}"，逐步深入询问家族信息
3. **所有问题必须围绕寻根、寻祖际、寻家族这三个核心主题**
4. 问题要自然、友好、温暖，像在陪伴用户寻根
5. 鼓励用户分享任何与寻根、寻祖际、寻家族相关的线索
6. 返回JSON数组格式，例如：["问题1", "问题2", "问题3", "问题4"]
7. 只返回JSON数组，不要其他文字
"""
        
        messages = [{"role": "user", "content": prompt}]
        model = settings.deepseek_model
        temperature = 0.8
        
        # 打印请求详情
        print_request_details(client, model, messages, temperature)
        
        # 发送请求
        print("\n[发送请求...]")
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        
        # 打印响应详情
        print_response_details(response)
        
        # 解析响应
        content = (response.choices[0].message.content or "").strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.replace("json", "", 1).strip()
        
        data = json.loads(content)
        if isinstance(data, list):
            questions = [q.strip() for q in data if isinstance(q, str) and q.strip()]
            if questions:
                print_success(f"成功生成 {len(questions)} 个候选问题")
                for i, q in enumerate(questions[:n], 1):
                    print(f"   {i}. {q}")
                return True
            else:
                print_error("生成的候选问题列表为空")
                return False
        else:
            print_error("响应格式不正确", f"期望JSON数组，得到: {type(data).__name__}")
            return False
            
    except json.JSONDecodeError as e:
        print_error("JSON解析失败", str(e))
        print(f"  响应内容: {content[:500] if 'content' in locals() else 'N/A'}")
        print_exception_details(e)
        return False
    except AuthenticationError as e:
        print_error("认证失败", "API密钥无效或已过期")
        print_exception_details(e)
        return False
    except APIError as e:
        print_error("API调用失败", f"错误代码: {e.code if hasattr(e, 'code') else 'unknown'}")
        print_exception_details(e)
        return False
    except Exception as e:
        print_error("生成候选问题测试失败", str(e))
        print_exception_details(e)
        return False


async def test_extract_family_info() -> bool:
    """测试信息抽取（模拟ai_service中的调用）"""
    print_section("4. 测试信息抽取")
    
    try:
        # 获取API密钥
        api_key = APIKeyManager.get_deepseek_key()
        if not api_key:
            print_error("API密钥未配置")
            return False
        
        # 创建客户端
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.deepseek_base_url
        )
        
        # 模拟ai_service中的调用
        answer = "我爸爸的籍贯是山东枣庄"
        current_question = "你爸爸常提起过他的老家吗？你印象里大概在哪个省市？"
        existing_data = {
            "user_profile": {
                "name": "测试用户"
            }
        }
        
        prompt = f"""
你是"家族信息抽取器"。请结合【当前问题】与【用户回答】抽取结构化信息并输出 JSON。

【当前问题】：
{current_question}

【用户回答】：
{answer}

【已有数据】：
{json.dumps(existing_data, ensure_ascii=False)}

抽取规则：
- 只输出 JSON，不要 markdown，不要解释
- 如果是爸爸籍贯 -> father.origin
- 如果是爷爷籍贯 -> grandfather.origin
- 如果是我自己的籍贯/祖籍 -> self.origin
- 辈分字 -> self.generation_name
- 姓氏 -> self.surname
- 如果无法判断或没有新信息 -> 输出空 JSON：{{}}

示例：
{{"father": {{"origin": "山东枣庄"}}}}
"""
        
        messages = [{"role": "user", "content": prompt}]
        model = settings.deepseek_model
        temperature = 0.0
        
        # 打印请求详情
        print_request_details(client, model, messages, temperature)
        
        # 发送请求
        print("\n[发送请求...]")
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        
        # 打印响应详情
        print_response_details(response)
        
        # 解析响应
        content = (response.choices[0].message.content or "").strip()
        if content.startswith("```"):
            content = content.strip("`")
            content = content.replace("json", "", 1).strip()
        
        data = json.loads(content)
        if isinstance(data, dict):
            if data:
                print_success("成功抽取结构化信息")
                print(f"  抽取结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
                return True
            else:
                print_info("抽取结果为空JSON（可能是正常的，如果无法从回答中提取信息）")
                return True  # 空JSON也是有效响应
        else:
            print_error("响应格式不正确", f"期望JSON对象，得到: {type(data).__name__}")
            return False
            
    except json.JSONDecodeError as e:
        print_error("JSON解析失败", str(e))
        print(f"  响应内容: {content[:500] if 'content' in locals() else 'N/A'}")
        print_exception_details(e)
        return False
    except AuthenticationError as e:
        print_error("认证失败", "API密钥无效或已过期")
        print_exception_details(e)
        return False
    except APIError as e:
        print_error("API调用失败", f"错误代码: {e.code if hasattr(e, 'code') else 'unknown'}")
        print_exception_details(e)
        return False
    except Exception as e:
        print_error("信息抽取测试失败", str(e))
        print_exception_details(e)
        return False


async def test_soft_clarify() -> bool:
    """测试soft clarify生成（模拟ai_service中的调用）"""
    print_section("5. 测试Soft Clarify生成")
    
    try:
        # 获取API密钥
        api_key = APIKeyManager.get_deepseek_key()
        if not api_key:
            print_error("API密钥未配置")
            return False
        
        # 创建客户端
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=settings.deepseek_base_url
        )
        
        # 模拟ai_service中的调用
        current_question = "你爸爸常提起过他的老家吗？你印象里大概在哪个省市？"
        user_answer = "不太清楚"
        topic_hint = "围绕上一问的家族线索（允许模糊、不确定也可以）"
        
        narrative_style = """
你是一位"家族记忆引导者"，不是信息采集器。
你在做的是"陪伴式寻根与家族叙事"，而不是查户口填表。

风格要求：
- 温和、尊重、带一点陪伴感
- 接受信息不完整、模糊或"不知道"
- 鼓励叙述（"你印象里…/你听谁提过…/大概也行"）
- 不要使用"请提供/请填写/必须回答"等表单语气
- 不要责备、不要审问、不要让用户觉得答错了
"""
        
        prompt = f"""
{narrative_style}

用户刚才的回答可能没有提供到我们需要的线索，但不要责备用户。
请用"换个角度聊聊"的方式，给出一个更温柔、更容易回答的追问。

我们想了解的方向：
{topic_hint or "围绕上一问的主题"}

上一问：
{current_question}

用户回答：
{user_answer}

请返回一个更温柔、更容易回答的追问问题。
只返回问题文本，不要其他文字。
"""
        
        messages = [{"role": "user", "content": prompt}]
        model = settings.deepseek_model
        temperature = 0.8
        
        # 打印请求详情
        print_request_details(client, model, messages, temperature)
        
        # 发送请求
        print("\n[发送请求...]")
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        
        # 打印响应详情
        print_response_details(response)
        
        # 解析响应
        question = (response.choices[0].message.content or "").strip()
        if question:
            print_success("成功生成soft clarify问题")
            print(f"  生成的问题: {question}")
            return True
        else:
            print_error("生成的问题为空")
            return False
            
    except AuthenticationError as e:
        print_error("认证失败", "API密钥无效或已过期")
        print_exception_details(e)
        return False
    except APIError as e:
        print_error("API调用失败", f"错误代码: {e.code if hasattr(e, 'code') else 'unknown'}")
        print_exception_details(e)
        return False
    except Exception as e:
        print_error("Soft clarify测试失败", str(e))
        print_exception_details(e)
        return False


async def main():
    """运行所有测试"""
    print("="*70)
    print("  DeepSeek API 测试脚本")
    print("="*70)
    print("\n此脚本将测试：")
    print("  1. API密钥配置")
    print("  2. 基础聊天功能")
    print("  3. 生成候选问题（step2中使用的功能）")
    print("  4. 信息抽取（step2中使用的功能）")
    print("  5. Soft clarify生成（step2中使用的功能）")
    print("\n提示：如果看到401认证错误，请检查API密钥是否正确配置")
    print("-"*70)
    
    results = {}
    
    # 运行所有测试
    try:
        results["api_key_config"] = await test_api_key_config()
        
        # 如果API密钥配置失败，跳过其他测试
        if not results["api_key_config"]:
            print("\n⚠️  API密钥配置失败，跳过其他测试")
        else:
            results["basic_chat"] = await test_basic_chat()
            results["generate_candidates"] = await test_generate_candidate_questions()
            results["extract_info"] = await test_extract_family_info()
            results["soft_clarify"] = await test_soft_clarify()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        return
    except Exception as e:
        print(f"\n❌ 测试过程中发生未预期的错误: {e}")
        print_exception_details(e)
    
    # 输出测试总结
    print("\n" + "="*70)
    print("  测试总结")
    print("="*70)
    
    test_names = {
        "api_key_config": "API密钥配置",
        "basic_chat": "基础聊天功能",
        "generate_candidates": "生成候选问题",
        "extract_info": "信息抽取",
        "soft_clarify": "Soft clarify生成"
    }
    
    for test_key, test_name in test_names.items():
        if test_key in results:
            status = "✅ 通过" if results[test_key] else "❌ 失败"
            print(f"  {status} - {test_name}")
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n总计: {success_count}/{total_count} 测试通过")
    
    if success_count == total_count:
        print("\n🎉 所有测试通过！API配置正确，可以正常使用。")
    else:
        print(f"\n⚠️  有 {total_count - success_count} 个测试失败")
        print("\n建议检查：")
        print("  1. API密钥是否正确配置（DEEPSEEK_API_KEY环境变量）")
        print("  2. API密钥是否有效（未过期、有足够余额）")
        print("  3. 网络连接是否正常")
        print("  4. DeepSeek API服务是否可用")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试已中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        traceback.print_exc()

















