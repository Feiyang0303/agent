from utils.chat import Qwen_Generate
import ollama

from openai import OpenAI

client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
    api_key="",
    base_url="",
)


prompt_sys = f"""你是一个经验丰富的书本解读者。你的任务是根据输入的书本名称，前言内容，写一个简短、亲切、轻松、富有吸引力的开头语，为后续章节内容的解读做铺垫。
你需要做到以下几点：
1. 开头语的语气必须是口语化、亲切的，贴近听众的生活和实际需求。内容必须通俗易懂，引起听众的共鸣。
2. 开头语必须清晰地指出书本的背景，要解决的问题，以及它对听众的意义。
3. 内容必须连贯，无明显的逻辑错误、突兀的转折或不合理的结构。
4. 结尾不能是呼吁性质的内容，不要出现任何形式的呼吁、号召或建议。能够顺利连接到后续章节内容的解读。
----输出要求----
请务必生成纯文本格式的内容，不能带有任何形式的标题或项目符号列表。
----示例输出----
各位好，今天我们来讲一本你一定会用得上的书啊，这书名叫抱怨的艺术。呃，这本书进过我的直播间，原名呢特别长，叫做不委屈自己，不伤害他人的说话之道。我当时一看完，我说这名儿不好卖呀，因为大家记不住啊，你如果叫抱怨的艺术应该就好卖多了。哎呀，出版社真是从善如流啊，立刻就把这书改成了抱怨的艺术，它的英文文字呢叫做the Squeaky wheel就是吱吱叫的轮子。呃，英语里边有一个谚语，说吱吱叫的轮子也能被加油。就像我们中国人讲会哭的孩子有奶吃啊是一个道理。
所以有时候如果一个人永远不抱怨，有什么问题都埋在心里边，很有可能你的需求不会被别人看到，而且还容易憋出病来。所以抱怨这件事呢有其功能，也有其方法啊，过去有一本书很流行，叫做《不抱怨的世界》，对吧？那时候买了很多册，而且随那个书呢还附赠一个紫色的手环。这样的话你把它套在手上，今天抱怨了一次，就把它拿下来，套在右手，又抱怨了一次，再套到左手，每次用这个动作提醒你要减少抱怨。如果你能够减少抱怨的话，你的世界就会好很多。但后来发现能坚持下来的人很少。原因是如果你总是不抱怨的话，很容易成为D形人格的人啊，这个所谓D形人格就是不说全憋着，最后憋出内伤啊，有人可能会得很严重的心血管疾病、高血压、心脏病啊，甚至更严重的病。所以这个作者就认为说呃有问题你要说出来，但是这事儿有艺术，不要说完了之后给自己惹很多的麻烦，而是更建设性的使得这个世界变得更好。
"""


raw_doc = open('../data/不安的哲学/前言.txt', 'r', encoding='utf-8').read()
prompt_text = f"""----书本名称----
《不安的哲学》
----前言----
{raw_doc}
"""
prompt_text = prompt_text.replace('\n\n', '\n')
# res = ollama.generate(model="qwen2.5:72b-instruct", prompt=prompt_text, system=prompt_sys, options={"num_ctx": 8192,"num_predict":-1})
# result = res['response']
# result = result.replace('\n\n', '\n')
# print(f'===========引导语===========')
# print(result)



completion = client.chat.completions.create(
    model="qwen2.5-72b-instruct",
    messages=[
        {"role": "system", "content": prompt_sys},
        {"role": "user", "content": prompt_text},
    ])
print(completion)
res = completion['choices'][0]['message']['content']
res = res.replace('\n\n', '\n')
print(f'===========引导语===========')
print(res)