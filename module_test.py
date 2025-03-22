from scripts.proofreader import case_feedback3
from scripts.Case_Analyst import find_case,Case_Description
from scripts.Topic_Researcher import topic_demonstrate,topic_expansion
from scripts.compiler import case_organize,case_change_style,case_assemble2


Lines = open('../data/抱怨的艺术/第一章2.txt', 'r', encoding='utf-8').read()
tmp_json_dict = find_case(Lines)
'''
案例怎么样
'''
c_feedback = case_feedback3(Lines,tmp_json_dict)
while c_feedback.startswith('否'):
    tmp_json_dict = find_case(Lines)
    c_feedback = case_feedback3(Lines,tmp_json_dict)

'''
将tmp_json_dict中的key，value交换，案例已经找到
'''
# tmp_json_dict2 = dict([(value, key) for key, value in tmp_json_dict.items()])
'''
主题怎么样
'''
# t_feedback_dict = topic_feedback4(Lines,tmp_json_dict2)   # key = 案例，value为主题反馈
# tmp_json_dict = case_refine(Lines,tmp_json_dict,t_feedback_dict)


# 将案例补充详细
case_dict = Case_Description(Lines,tmp_json_dict)
# detail_c_feedback = detail_case_feedback(Lines,case_dict)


# loop_flag = True if c_feedback.startswith('是') else False
# while not loop_flag:
#     tmp_json_dict = find_case(Lines)
#     t_feedback = topic_feedback3(Lines,tmp_json_dict)
#     loop_flag = True if t_feedback.startswith('是') else False

# 案例如何论证主题？
t_demonstrate = topic_demonstrate(Lines,case_dict)
#
# # 案例拓展
topic_insight = topic_expansion(Lines,case_dict,t_demonstrate)
#
# # 案例写作
case_org = case_organize(Lines,case_dict,t_demonstrate,topic_insight)
#
# # 风格改写
style_change = case_change_style(case_org)
#
# # 合并
final_result = case_assemble2(Lines,style_change)

