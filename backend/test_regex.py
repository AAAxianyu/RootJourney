"""测试祖父姓名提取的正则表达式"""
import re

# 测试用例
test_cases = [
    "我爷爷叫张建国",
    "我祖父是张建国",
    "爷爷张建国",
    "我爷爷叫李四",
    "祖父叫王五",
]

# 正则表达式模式
pattern1 = r'(?:爷爷|祖父|外公|外祖父)[叫是]\s*([张李王刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤][\u4e00-\u9fa5]{1,2})'
pattern2 = r'(?:爷爷|祖父)[\s，,。]?([张李王刘陈杨黄赵吴周徐孙马朱胡郭何高林罗郑梁谢宋唐许韩冯邓曹彭曾肖田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾夏韦付方白邹孟熊秦邱江尹薛闫段雷侯龙史陶黎贺顾毛郝龚邵万钱严覃武戴莫孔向汤][\u4e00-\u9fa5]{1,2})'

print("测试正则表达式匹配：")
print("=" * 60)

for answer in test_cases:
    print(f"\n测试: {answer}")
    
    # 方法1
    match1 = re.search(pattern1, answer)
    if match1:
        print(f"  方法1匹配: {match1.group(1)}")
    else:
        print(f"  方法1: 未匹配")
    
    # 方法2（如果方法1失败）
    if not match1 and ("爷爷" in answer or "祖父" in answer):
        match2 = re.search(pattern2, answer)
        if match2:
            print(f"  方法2匹配: {match2.group(1)}")
        else:
            print(f"  方法2: 未匹配")
