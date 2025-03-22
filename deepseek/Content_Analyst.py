from utils.chat import Deepseek_Generate
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
    result = Deepseek_Generate(prompt_text, system_text)
    print("===========主题===========")
    print(result)
    return result
if __name__ == '__main__':
    Lines = open('../data/第一章2.txt', 'r', encoding='utf-8').read()
    # abstract = make_abs(Lines)
    topic = make_topic(Lines)
    # print(preamble)
