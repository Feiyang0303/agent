from utils.chat import askQwen
from utils.chat import Qwen_Generate
import ollama
def do_action(raw_doc):
    prompt_sys = """####说明####
你是一个书本解读者，你的任务是以深入浅出的解读方式，让用户能够在短时间内掌握一本书的核心内容。现在你会得到一个章节内容，你需要提炼该章节的主题，为用户进行解读。
####要求####
1. 讲解章节的主题以及作者试图解决或探讨的主要问题是什么。
2. 通过观点+具体案例的方式，向用户解释作者的观点是如何得出的。讲述案例的时候，可以适当增加一些细节，让用户更容易理解。
3. 通过自然、口语化的表达，向用户解释这些事实、数据或案例如何支持作者的观点。
4. 对某些适用群体不同的例子，可以更改案例与情境，让读者对这些情境产生共鸣。
5. 字数在章节内容的十分之一左右。
"""
    tmp = """
    # ####要求####
# 1. 着重讲解章节的主题以及作者试图解决或探讨的主要问题是什么。
# 2. 通过观点+具体案例的方式，向用户解释作者的观点是如何得出的。讲述案例的时候，可以适当增加一些细节，让用户更容易理解。
# 3. 通过自然、口语化的表达，向用户解释这些事实、数据或案例如何支持作者的观点。
# 4. 对某些适用群体不同的例子，可以更改案例与情境，让读者对这些情境产生共鸣。
    """
    prompt_user = f"""章节内容：{raw_doc}
章节摘要："""

    message = [
        {
            "role": "system",
            "content": prompt_sys,
        },
        {
            "role": "user",
            "content": prompt_user,
        }
    ]
    result = askQwen(message)
    return result


tmp = """
[日常抱怨指南<如何挑选抱怨的时机<用抱怨三明治进行有效抱怨<如何向上级抱怨]
"""
def do_topic(raw_doc):
    prompt_sys = f"""----任务说明----
你是一个内容分析师，你的任务是根据输入的章节内容凝练该章节的核心主题，核心主题应当是对章节内容的高度概括，能够反映章节的主要议题或作者试图传达的主要思想。
直接返回主题列表，主题间用"<"间隔，不要返回任何书本内容。
章节内容：{raw_doc}
"""
    prompt_user = f"""----任务----
请按照要求输出章节的主题列表，话题间用"<"间隔，不要返回任何书本内容，直接返回话题列表。
"""
    message = [
        {
            "role": "system",
            "content": prompt_sys,
        },
        {
            "role": "user",
            "content": prompt_user,
        }
    ]
    result = askQwen(message)
    return result
def do_topic2(raw_doc):
    prompt_text = f''''''
    prompt_sys = f"""----任务说明----
你是一个内容分析师，你的任务是根据输入的章节内容凝练该章节的一级核心主题，核心主题应当是对章节内容的高度概括，能够反映章节的主要议题或作者试图传达的主要思想。
----输入----
章节内容：{raw_doc}
"""
    prompt_text+=prompt_sys
    prompt_user = f"""----任务----
请按照要求输出章节的核心主题列表，主题间用"<"间隔，不要返回任何书本内容或者任何二级主题，直接返回主题列表。
"""
    prompt_text+=prompt_user
    # print(prompt_text)




    result = ollama.generate(model='qwen2.5:72b-instruct', system="你是一个内容分析师，你的任务是根据输入的章节内容凝练该章节的一级核心主题，核心主题应当是对章节内容的高度概括，能够反映章节的主要议题或作者试图传达的主要思想。",prompt=prompt_text,keep_alive='1h')
    return result['response']
# def make_topic(raw_doc):
#     # topic = do_topic(raw_doc)
#     topic = do_topic2(raw_doc)
#     print('===========make_topic===========')
#     print(topic)
#     return topic


# def make_topic(raw_doc):
#     prompt_text = f'''----章节内容----
# {raw_doc}'''
#     system_text = f"""你是一个内容分析师，你的任务是根据章节内容按以下要求提炼核心主题。
# ----要求----
# 1. 请将章节内容
# 为不多于三个主题，每个主题应准确反映章节的重点内容的主要议题或作者试图传达的主要思想。
# 核心主题应高度概括章节的重点内容，具有抽象性、深刻性。
# 2. 核心主题应准确反映章节重点内容的主要议题或作者试图传达的主要思想。
# 3. 对于来源于同一案例或片段的多个主题，应合并为一个综合主题，以避免重复或过度细化。
# ----格式要求----
# 请根据输入的章节内容输出该章节的核心主题，若存在多个主题，请用"<"间隔，不要返回任何书本内容或者任何二级主题，直接返回主题列表。
# """
#     prompt_text = prompt_text.replace('\n\n', '\n')
#     # print(prompt_text)
#     result = Qwen_Generate(prompt_text, system_text)
#     print("===========主题===========")
#     print(result)
#     return result
def make_topic(raw_doc):
    prompt_text = f'''----章节内容----
{raw_doc}'''
    system_text = f"""你是一个内容分析师，擅长根据章节内容提炼章节核心主题，你的任务是根据以下步骤提炼核心主题。
----步骤---- 
1. 仔细阅读并理解章节内容，确保对章节的重点内容有全面把握。
2. 根据重点内容提炼章节核心主题，核心主题应准确反映章节重点内容的主要议题或作者试图传达的主要思想，具有抽象性、深刻性。
3. 对于来源于同一案例或片段的多个主题，应合并为一个综合主题，以避免重复或过度细化。
4. 最终形成不多于三个的核心主题，每个主题都能很好反映章节重点信息且主题反映的思想不重复。
----格式要求----
请根据输入的章节内容输出该章节的核心主题，若存在多个主题，请用"<"间隔，不要返回任何书本内容或者任何二级主题，直接返回主题列表。
"""
    prompt_text = prompt_text.replace('\n\n', '\n')
    # print(prompt_text)
    result = Qwen_Generate(prompt_text, system_text)
    print("===========主题===========")
    print(result)
    return result
if __name__ == '__main__':
    Lines = open('../data/第一章2.txt', 'r', encoding='utf-8').read()
    # abstract = make_abs(Lines)
    topic = make_topic(Lines)
    # print(preamble)
