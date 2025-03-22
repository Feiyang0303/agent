import asyncio
import re
from metagpt.actions import Action, UserRequirement
from metagpt.context import Context
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.roles.role import RoleReactMode
from metagpt.schema import Message
from tqdm import tqdm
# from scripts.Case_Analyst import find_case,Case_Description
# from scripts.proofreader import case_feedback3,compare_result,organize_case_feedback_content,organize_case_feedback_logic,organize_case_feedback_enlightening,oral_feedback,organize_refine,final_feedback_consistent,final_feedback_expression,final_refine
# from scripts.Topic_Researcher import topic_demonstrate,topic_expansion
# from scripts.compiler import case_organize,case_change_style,case_assemble3,oral_refine

from deepseek.Case_Analyst import find_case,Case_Description
from deepseek.proofreader import case_feedback3,compare_result,organize_case_feedback_content,organize_case_feedback_logic,organize_case_feedback_enlightening,oral_feedback,organize_refine,final_feedback_consistent,final_feedback_expression,final_refine
from deepseek.Topic_Researcher import topic_demonstrate,topic_expansion
from deepseek.compiler import case_organize,case_change_style,case_assemble3,oral_refine



from pydantic import BaseModel

class dict_message(BaseModel):
    content: dict

class FindKeyCase(Action):
    name: str = "FindKeyCase"
    async def run(self, content: str):
        rsp = await find_case(content)
        return rsp

class GetDetailCase(Action):
    name: str = "GetDetailCase"
    async def run(self, content: str,case_dict:dict):
        rsp = await Case_Description(content,case_dict)
        return rsp

'''
文本分析agent:文本分析agent用于识别句子中的复杂词------->接收原始句子作为输入，输出复杂词汇
'''
class CaseAnalyst(Role):
    name: str = "Case-Analyst-1"
    profile: str = "Case Analyst Agent"
    case_dict: dict_message = None
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._watch([UserRequirement,KeyCaseFeedback])
        self.set_actions([FindKeyCase,GetDetailCase])
    async def _think(self):
        lst_message = self.get_memories()[-1].content
        lst_role = self.get_memories()[-1].role
        if lst_message.startswith('是') and lst_role == "Proof Reader Agent":
            self.rc.todo = GetDetailCase()
        else:
            self.rc.todo = FindKeyCase()
    async def _act(self) -> Message:
        todo = self.rc.todo
        print(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        context = self.get_memories()
        Lines = context[0].content
        msg = None
        if todo.name == "FindKeyCase":
            rsp_text = await todo.run(Lines)
            mes = dict_message(content=rsp_text)
            self.case_dict = mes
            msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo), send_to=ProofReader)
        if todo.name == "GetDetailCase":
            rsp_text = await todo.run(Lines,self.case_dict.content)  # 得到的是dict
            mes = dict_message(content=rsp_text)
            msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo))  # 把详细案例传给下一个agent
        self.rc.env.publish_message(msg)
        return msg

class TopicDemonstrate(Action):
    name: str = "TopicDemonstrate"
    async def run(self, content: str,case_dict:dict):
        rsp = await topic_demonstrate(content,case_dict)
        return rsp

class TopicExpansion(Action):
    name: str = "TopicExpansion"
    async def run(self, content: str,case_dict:dict,demonstrate_dict:dict):
        rsp = await topic_expansion(content,case_dict,demonstrate_dict)
        return rsp

'''
文本分析agent:文本分析agent用于识别句子中的复杂词------->接收原始句子作为输入，输出复杂词汇
'''
class TopicResearch(Role):
    name: str = "Topic-Research"
    profile: str = "Topic Research Agent"
    detail_case: dict = None
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._watch([GetDetailCase,TopicDemonstrate])
        self.set_actions([TopicDemonstrate,TopicExpansion])
    async def _think(self):
        lst_role = self.get_memories()[-1].role
        if lst_role == "Case Analyst Agent":
            self.rc.todo = TopicDemonstrate()
        else:
            self.rc.todo = TopicExpansion()
    async def _act(self) -> Message:
        todo = self.rc.todo
        print(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        context = self.get_memories()
        Lines = context[0].content
        if todo.name == "TopicDemonstrate":
            case_dict = context[-1].instruct_content.content   # 详细案例
            self.detail_case = case_dict
            rsp_text = await todo.run(Lines,case_dict)  # 得到的是dict
            mes = dict_message(content=rsp_text)
            msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo))  # 把详细案例传给下一个agent
        else:
            case_dict = self.detail_case
            demonstrate_dict = context[-1].instruct_content.content
            rsp_text = await todo.run(Lines, case_dict,demonstrate_dict)  # 得到的是dict
            mes = dict_message(content=rsp_text)
            msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo))  # 把详细案例传给下一个agent
        self.rc.env.publish_message(msg)
        return msg

class KeyCaseFeedback(Action):
    name: str = "KeyCaseFeedback"
    async def run(self, content: str,case_dict:dict):
        rsp = await case_feedback3(content,case_dict)
        return rsp
class CaseOrganizeContent(Action):
    name: str = "CaseOrganizeContent"
    async def run(self, content: str,case_dict:dict,demonstrate_dict:dict,insight_dict:dict,organize_dict:dict):
        rsp = await organize_case_feedback_content(content,case_dict,demonstrate_dict,insight_dict,organize_dict)
        return rsp
class CaseOrganizeLogic(Action):
    name: str = "CaseOrganizeLogic"
    async def run(self, content: str,case_dict:dict,demonstrate_dict:dict,insight_dict:dict,organize_dict:dict):
        rsp = await organize_case_feedback_logic(content,case_dict,demonstrate_dict,insight_dict,organize_dict)
        return rsp

# class CaseOrganizeEnlighten(Action):
#     name: str = "CaseOrganizeEnlighten"
#     async def run(self, content: str,case_dict:dict,demonstrate_dict:dict,insight_dict:dict,organize_dict:dict):
#         rsp = await organize_case_feedback_enlightening(content,case_dict,demonstrate_dict,insight_dict,organize_dict)
#         return rsp

class OralFeedback(Action):
    name: str = "OralFeedback"
    async def run(self, organize_dict:dict,oral_dict:dict):
        rsp = await oral_feedback(organize_dict,oral_dict)
        # rsp = {'租房者的有效投诉': '是', '情感宣泄的重要性': '是', '投诉的有效性和社会问题': '是'}
        return rsp


class FinalFeedbackConsistent(Action):
    name: str = "FinalFeedbackConsistent"
    async def run(self, content: str,final_text:str):
        rsp = await final_feedback_consistent(content,final_text)
        return rsp

class FinalFeedbackExpression(Action):
    name: str = "FinalFeedbackExpression"
    async def run(self, content: str,final_text:str):
        rsp = await final_feedback_expression(content,final_text)
        return rsp

class str_message(BaseModel):
    content: str

class RefineCompare(Action):
    name: str = "RefineCompare"
    async def run(self, content: str,final_text1:str,final_text2:str):
        rsp = await compare_result(content,final_text1,final_text2)
        return rsp


class ProofReaderFinal(Role):
    name: str = "Proof-Reader-Final"
    profile: str = "Proof Reader Final Agent"
    consistent_cnt:int = 0
    expression_cnt:int = 0
    final_text:str = ""
    # enlighten_cnt:int = 0
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._watch([CaseAssemble,FinalFeedbackRefine,RefineCompare])
        # self.set_actions([KeyCaseFeedback,CaseOrganizeContent,CaseOrganizeLogic,CaseOrganizeEnlighten])
        self.set_actions([FinalFeedbackConsistent,FinalFeedbackExpression,RefineCompare])

    async def _think(self):
        lst_role = self.get_memories()[-1].role
        lst_case_by = self.get_memories()[-1].cause_by
        lst_msg = self.get_memories()[-1].content
        if lst_case_by == "__main__.CaseAssemble":
            self.rc.todo = FinalFeedbackConsistent()
        elif lst_case_by == "__main__.FinalFeedbackRefine":
            self.rc.todo = RefineCompare()
        else:
            self.rc.todo = FinalFeedbackExpression()

    async def _act(self) -> Message:
        todo = self.rc.todo
        print(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        context = self.get_memories()
        Lines = context[0].content
        if todo.name == "FinalFeedbackConsistent":
            if self.consistent_cnt == 0:
                final_text = context[-1].content
                self.final_text = final_text
                mes2 = str_message(content=self.final_text)
                rsp_text = await todo.run(Lines,final_text)   # 得到反馈结果str
                self.consistent_cnt += 1
                msg = Message(content=rsp_text, instruct_content=mes2,role=self.profile, cause_by=type(todo), send_to=FinalCompiler)
                self.rc.env.publish_message(msg)
                return msg
            # else:
            #     if self.consistent_cnt < 2:
            #         final_text = context[-1].instruct_content.content
            #         self.final_text = final_text
            #         mes2 = str_message(content=self.final_text)
            #         rsp_text = await todo.run(Lines, final_text)  # 得到反馈结果str
            #         self.consistent_cnt += 1
            #         msg = Message(content=rsp_text, instruct_content=mes2, role=self.profile, cause_by=type(todo),
            #                       send_to=FinalCompiler)
            #         self.rc.env.publish_message(msg)
            #         return msg
            #     else:
            #         mes2 = str_message(content=self.final_text)
            #         msg = Message(content="是", instruct_content=mes2, role=self.profile, cause_by=type(todo),
            #                       send_to=FinalCompiler)
            #         self.rc.env.publish_message(msg)
            #         return msg
        if todo.name == "FinalFeedbackExpression":
            final_text = context[-1].instruct_content.content
            mes2 = str_message(content=self.final_text)
            rsp_text = await todo.run(Lines, final_text)  # 得到反馈结果str
            if rsp_text == "是":
                self.expression_cnt += 1
                print("-------------------Final---------------------")
                # f3 = open("result/园丁与木匠.txt", "a", encoding="utf-8", errors="ignore")
                # f3.write(self.final_text+'\n')
                # f3.close()
                print(self.final_text)
            else:
                self.expression_cnt += 1
                msg = Message(content=rsp_text, instruct_content=mes2, role=self.profile, cause_by=type(todo),
                              send_to=FinalCompiler)
                self.rc.env.publish_message(msg)
                return msg
        if todo.name == "RefineCompare":
            final_text2 = context[-1].instruct_content.content
            rsp_text = await todo.run(Lines,self.final_text,final_text2)
            if rsp_text == "讲稿2":
                self.final_text = final_text2
            mes2 = str_message(content=self.final_text)
            if self.expression_cnt == 0:
                msg = Message(instruct_content=mes2, role=self.profile, cause_by=type(todo),
                              send_to=ProofReaderFinal)
                self.rc.env.publish_message(msg)
                return msg
            else:
                print("-------------------Final---------------------")
                print(self.final_text)
                print("-------------------Final---------------------")
                # f3 = open("result/园丁与木匠.txt", "a", encoding="utf-8", errors="ignore")
                # f3.write(self.final_text+'\n')
                # f3.close()
class FinalFeedbackRefine(Action):
    name: str = "FinalFeedbackRefine"
    async def run(self, final_text: str,final_feedback:str):
        rsp,flag = await final_refine(final_text,final_feedback)
        return rsp,flag
class FinalCompiler(Role):
    name: str = "Final-Compiler"
    profile: str = "Final Compiler Agent"
    save_oral_dict:dict = None
    start_content: bool = False
    start_logic:bool = False
    content_cnt:int = 0

    # enlighten_cnt:int = 0
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._watch([FinalFeedbackConsistent,FinalFeedbackExpression])
        # self.set_actions([KeyCaseFeedback,CaseOrganizeContent,CaseOrganizeLogic,CaseOrganizeEnlighten])
        self.set_actions([FinalFeedbackRefine])

    async def _act(self) -> Message:
        todo = self.rc.todo
        print(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        context = self.get_memories()
        feedback_text = context[-1].content
        final_text = context[-1].instruct_content.content
        if todo.name == "FinalFeedbackRefine":
            rsp_text,flag = await todo.run(final_text,feedback_text)
            mes2 = str_message(content=rsp_text)
            # flag 为 “是” 的话进入下一步
            msg = Message(content=flag,instruct_content=mes2,role=self.profile, cause_by=type(todo), send_to=ProofReaderFinal)
            self.rc.env.publish_message(msg)
            return msg

'''
校对Agent
'''

class ProofReader(Role):
    name: str = "Proof-Reader-1"
    profile: str = "Proof Reader Agent"
    case_dict: dict = None
    case_demonstrate: dict = None
    case_expansion: dict = None
    case_organize_dict: dict = None
    save_oral_dict:dict = None
    start_content: bool = False
    start_logic:bool = False
    start_oral:bool = False
    # start_enlighten:bool = False
    content_cnt:int = 0
    logic_cnt:int = 0
    oral_cnt:int = 0
    # enlighten_cnt:int = 0
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._watch([FindKeyCase,CaseOrganize,CaseOrganizeRefine,OralRewrite,OralRefine])
        # self.set_actions([KeyCaseFeedback,CaseOrganizeContent,CaseOrganizeLogic,CaseOrganizeEnlighten])
        self.set_actions([KeyCaseFeedback,CaseOrganizeContent,CaseOrganizeLogic,OralFeedback])

    async def _think(self):
        lst_role = self.get_memories()[-1].role
        lst_case_by = self.get_memories()[-1].cause_by
        lst_msg = self.get_memories()[-1].content
        if lst_role == "Case Analyst Agent":
            self.rc.todo = KeyCaseFeedback()
        elif lst_case_by == "__main__.CaseOrganize" or (self.start_content and self.start_logic == False and lst_msg != ""):
            self.rc.todo = CaseOrganizeContent()
        # elif (lst_case_by == "checkContent" and lst_msg == "") or (lst_case_by == "checkLogic" and lst_msg!= ""):
        elif ((lst_msg == "" and self.start_logic == False and self.start_content) or
              (self.start_logic and lst_role!="Oralisation Specialists Agent")):
              # (self.start_logic and self.start_enlighten == False and lst_msg != "")):
            self.rc.todo = CaseOrganizeLogic()
        elif lst_role == "Oralisation Specialists Agent":
            self.rc.todo = OralFeedback()

    async def _act(self) -> Message:
        todo = self.rc.todo
        print(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        context = self.get_memories()
        Lines = context[0].content
        if todo.name == "KeyCaseFeedback":
            key_case = context[-1].instruct_content.content
            rsp_text = await todo.run(Lines,key_case)
            msg = Message(content=rsp_text, role=self.profile, cause_by=type(todo), send_to=CaseAnalyst)
            self.rc.env.publish_message(msg)
            return msg
        elif todo.name == "CaseOrganizeContent":
            context2 = self.get_memories()
            case_dict = context2[-4].instruct_content.content
            self.case_dict = case_dict
            case_demonstrate = context2[-3].instruct_content.content
            self.case_demonstrate = case_demonstrate
            case_expansion = context2[-2].instruct_content.content
            self.case_expansion = case_expansion
            # 第一次反馈
            if self.start_content == False:
                case_organize_dict = context2[-1].instruct_content.content
                self.case_organize_dict = case_organize_dict
                rsp_text = await todo.run(Lines,case_dict,case_demonstrate,case_expansion,case_organize_dict)  # 反馈结果 dict
                mes = dict_message(content=rsp_text)
                self.start_content = True
                self.content_cnt += 1
            # 第二次反馈,只对错误的key进行反馈
            else:
                wrong_key = context2[-1].content
                wrong_key_list = wrong_key.split('<')
                case_organize_dict = context2[-1].instruct_content.content
                self.case_organize_dict = case_organize_dict
                new_case_dict = {key:self.case_dict[key] for key in wrong_key_list}
                new_case_demonstrate = {key:self.case_demonstrate[key] for key in wrong_key_list}
                new_case_expansion = {key:self.case_expansion[key] for key in wrong_key_list}
                new_case_organize_dict = {key:case_organize_dict[key] for key in wrong_key_list}
                return_dict = {}
                if self.content_cnt<2:
                    rsp_text = await todo.run(Lines, new_case_dict, new_case_demonstrate, new_case_expansion,
                                              new_case_organize_dict)  # 反馈结果 dict
                    for key,value in self.case_dict.items():
                        if key in wrong_key_list:
                            return_dict[key] = rsp_text[key]
                        else:
                            return_dict[key] = "是"
                    mes = dict_message(content=return_dict)
                else:
                    for key,value in self.case_dict.items():
                            return_dict[key] = "是"
                    mes = dict_message(content=return_dict)
                self.content_cnt += 1

            msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo),send_to=Compiler)  # 把详细案例传给下一个agent
            self.rc.env.publish_message(msg)
            return msg
        elif todo.name == "CaseOrganizeLogic":
            context2 = self.get_memories()
            if self.start_logic == False:  # 第一次
                case_organize_dict = context2[-1].instruct_content.content
                self.case_organize_dict = case_organize_dict
                rsp_text = await todo.run(Lines,self.case_dict,self.case_demonstrate,self.case_expansion,self.case_organize_dict)  # 反馈结果 dict
                mes = dict_message(content=rsp_text)
                self.start_logic = True
                self.logic_cnt += 1
            else:
                wrong_key = context2[-1].content
                wrong_key_list = wrong_key.split('<')
                case_organize_dict = context2[-1].instruct_content.content

                if wrong_key == "":
                    mes2 = dict_message(content=self.case_organize_dict)
                    msg = Message(instruct_content=mes2, role=self.profile, cause_by=type(todo),
                                  send_to=OralisationSpecialists)  # 把详细案例传给下一个agent
                    self.rc.env.publish_message(msg)
                    return msg

                self.case_organize_dict = case_organize_dict
                new_case_dict = {key: self.case_dict[key] for key in wrong_key_list}
                new_case_demonstrate = {key: self.case_demonstrate[key] for key in wrong_key_list}
                new_case_expansion = {key: self.case_expansion[key] for key in wrong_key_list}
                new_case_organize_dict = {key: case_organize_dict[key] for key in wrong_key_list}
                # 反馈结果 dict
                return_dict = {}
                if self.logic_cnt<2:
                    rsp_text = await todo.run(Lines, new_case_dict, new_case_demonstrate, new_case_expansion,
                                              new_case_organize_dict)
                    for key, value in self.case_dict.items():
                        if key in wrong_key_list:
                            return_dict[key] = rsp_text[key]
                        else:
                            return_dict[key] = "是"
                    mes = dict_message(content=return_dict)
                else:
                    for key, value in self.case_dict.items():
                        return_dict[key] = "是"
                    mes = dict_message(content=return_dict)
                self.logic_cnt += 1
                # 如果return_dict中的value全是"是"，则不再进行逻辑反馈

            msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo),
                          send_to=Compiler)  # 把详细案例传给下一个agent
            self.rc.env.publish_message(msg)
            return msg
        # elif todo.name == "CaseOrganizeEnlighten":
        #     context2 = self.get_memories()
        #     if self.start_enlighten == False:  # 第一次
        #         case_organize_dict = context2[-1].instruct_content.content
        #         self.case_organize_dict = case_organize_dict
        #         rsp_text = await todo.run(Lines,self.case_dict,self.case_demonstrate,self.case_expansion,self.case_organize_dict)  # 反馈结果 dict
        #         mes = dict_message(content=rsp_text)
        #         self.start_enlighten = True
        #         self.enlighten_cnt += 1
        #     else:
        #         wrong_key = context2[-1].content
        #         wrong_key_list = wrong_key.split('<')
        #         case_organize_dict = context2[-1].instruct_content.content
        #         self.case_organize_dict = case_organize_dict
        #         new_case_dict = {key: self.case_dict[key] for key in wrong_key_list}
        #         new_case_demonstrate = {key: self.case_demonstrate[key] for key in wrong_key_list}
        #         new_case_expansion = {key: self.case_expansion[key] for key in wrong_key_list}
        #         new_case_organize_dict = {key: case_organize_dict[key] for key in wrong_key_list}
        #         return_dict = {}
        #         if self.enlighten_cnt<2:
        #             rsp_text = await todo.run(Lines, new_case_dict, new_case_demonstrate, new_case_expansion,
        #                                       new_case_organize_dict)  # 反馈结果 dict
        #             for key, value in self.case_dict.items():
        #                 if key in wrong_key_list:
        #                     return_dict[key] = rsp_text[key]
        #                 else:
        #                     return_dict[key] = "是"
        #             mes = dict_message(content=return_dict)
        #         else:
        #             for key, value in self.case_dict.items():
        #                 return_dict[key] = "是"
        #             mes = dict_message(content=return_dict)
        #         self.enlighten_cnt += 1
        #     msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo),
        #                   send_to=Compiler)  # 把详细案例传给下一个agent
        #     self.rc.env.publish_message(msg)
        #     return msg
        elif todo.name == "OralFeedback":
            context2 = self.get_memories()
            if self.start_oral == False:  # 第一次
                oral_dict = context2[-1].instruct_content.content
                self.save_oral_dict = oral_dict
                rsp_text = await todo.run( self.case_organize_dict,oral_dict)  # 反馈结果 dict
                mes = dict_message(content=rsp_text)
                self.start_oral = True
                self.oral_cnt += 1
            else:
                wrong_key = context2[-1].content
                wrong_key_list = wrong_key.split('<')
                oral_dict = context2[-1].instruct_content.content
                self.save_oral_dict = oral_dict
                if wrong_key == "":
                    mes2 = dict_message(content=self.save_oral_dict)
                    msg = Message(instruct_content=mes2, role=self.profile, cause_by=type(todo),
                                  send_to=Compiler)  # 把详细案例传给下一个agent
                    self.rc.env.publish_message(msg)
                    return msg
                new_case_organize_dict = {key: self.case_organize_dict[key] for key in wrong_key_list}
                new_oral_dict = {key: self.save_oral_dict[key] for key in wrong_key_list}
                # 反馈结果 dict
                return_dict = {}
                if self.oral_cnt < 2:
                    rsp_text = await todo.run(new_case_organize_dict, new_oral_dict)
                    for key, value in self.case_dict.items():
                        if key in wrong_key_list:
                            return_dict[key] = rsp_text[key]
                        else:
                            return_dict[key] = "是"
                    mes = dict_message(content=return_dict)
                else:
                    for key, value in self.case_dict.items():
                        return_dict[key] = "是"
                    mes = dict_message(content=return_dict)
                self.oral_cnt += 1
                # 如果return_dict中的value全是"是"，则不再进行逻辑反馈

            msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo),
                          send_to=OralisationSpecialists)  # 把详细案例传给下一个agent
            self.rc.env.publish_message(msg)
            return msg

class CaseOrganize(Action):
    name: str = "CaseOrganize"
    async def run(self, content: str,case_dict:dict,demonstrate_dict:dict,insight_dict:dict):
        rsp = await case_organize(content,case_dict,demonstrate_dict,insight_dict)
        # rsp ={'租房者的有效投诉': '在租房者的有效投诉这个核心主题下，我们看到了一个极具启发性的例子：如何通过具体的行动和合理的沟通来达成目标。故事的主角是一位因旧公寓被转手而被迫寻找新住处的租户，在搬进了一套阳光充足、视野开阔的新公寓后不久，发现窗外即将新建一座高楼，这意味着清晨的阳光会被遮挡。噪音问题很快随之而来，挖掘机开始了工作，每天早上六点半就开始钻孔作业。\n面对这些问题，他首先尝试与物业沟通但未取得成果。这表明了无效的抱怨或求助并不能解决问题。在意识到直接投诉无果之后，这位租户采取了一个关键步骤：撰写一封有效且表达出感激之情的信件给房东要求减租。这封信不同于普通抱怨的地方在于它不仅指出了问题，还表达了对物业潜在帮助的感激和希望得到一个解决方案的动机。\n最终，物业公司经理亲自给他打电话，并同意减少租金并延长几个月的租期。这一结果超出了他的预期，也证明了有效投诉的重要性。具体来说，通过具体的行动和合理的沟通来达成目标的关键支撑点在于：\n1. **充分信息获取**：在采取行动前，他咨询了自己的建筑行业朋友，获得了关于新建筑高度和阳光遮挡情况的具体信息。\n2. **理性沟通策略**：面对物业无果后，并未放弃，而是选择了一种更具有建设性的沟通方式。这表明有效的投诉不仅需要明确表达问题，还需要提出合理的解决方案。\n3. **积极态度与感激**：在信中强调对解决方案的感激之情，而非一味抱怨和指责，这种方式更容易引起对方共鸣并促使其采取行动。\n通过这个案例，我们可以进一步理解有效投诉的重要性：\n1. **避免负面情绪的传递**：面对问题时应尽量保持冷静和理性，避免将不满直接转化为愤怒和指责，以免影响最终的结果。\n2. **积极寻求解决方案**：当遇到困境时，要以解决问题为导向，通过多种尝试找到最适合的方法，并保持乐观态度。\n综上所述，在租房过程中，我们可以通过充分信息获取、合理诉求提出以及建设性沟通策略来应对各种问题。案例中的租户不仅成功地保护了自己的权益，也为其他租房者提供了有效的参考与借鉴。', '情感宣泄的重要性': '是否有人有资格对我们当前的抱怨有效性做出评估？答案是肯定的，心理学家和研究人员为我们揭示了很多关于抱怨背后的心理机制。其中一个关键点在于情感宣泄的重要性，这在瑞秋的经历中得到了充分展现。\n在一次与男友一起前往酒吧的过程中，瑞秋发现男友一直盯着另一个女人，并且当众与她争吵后直接去找那个女人搭讪，留下她慌张而难以置信地站在那里。冲进女厕所后，她忍不住失声痛哭起来。这时，一个正在补妆的女人看到瑞秋的情绪激动，便问道：“天啊，男人真他妈的浑蛋！”然而，这位女人接着说了一句无情的话：“哦，是吗？那我又怎么知道你不是浑蛋呢？”说完便离开了。\n瑞秋本以为会得到一些同情和安慰，但没想到对方却回应道：“哦，是吗？那我又怎么知道你不是浑蛋呢？”这种冷漠的反应令她哑口无言，并且没有减轻她内心的痛苦。这次经历凸显了情感宣泄时需要的情感支持和理解的重要性。如果当时有人能够给予一些简单的同情或安慰，哪怕只是一个同情的眼神或是递上纸巾，都可能让瑞秋感到些许慰藉。\n这个案例直接支持了情感宣泄主题的核心思想：有效的倾听和支持在情感宣泄过程中至关重要。当一个人感到情绪低落或遭受打击时，能够获得他人的理解、同情甚至是简单安慰的情感支持可以帮助他们从负面情绪中解脱出来。相反地，如果这些期望得不到满足或者遇到冷漠的回应，则会进一步加剧个体的情绪负担，并且无法实现通过抱怨来宣泄情感的目标。\n因此，在面对生活中的挫折时，拥有一个能够提供情感理解和支持的对象对于成功的情感宣泄非常重要。这一案例不仅强调了有效倾听和同情的重要性，还揭示了现代社会中人们往往忽视或未能正确处理他人情感需求的现象。瑞秋的经历说明了在遇到生活中的挫折时，获得适当的反馈和支持对个体的心理健康有多么重要。\n这个案例进一步强调了情感宣泄的重要性以及有效倾听在其中扮演的角色。通过理解和支持，个体可以释放负面情绪，并从中得到心理上的放松和宽慰。现代生活中，我们需要认识到这种支持的必要性，并学会如何给予他人有效的倾听与安慰，以帮助他们在面对生活中的挫折时更好地处理自己的情绪。', '投诉的有效性和社会问题': '为什么有效的投诉在现代社会中变得如此重要？约翰·A.古德曼的研究揭示了一个令人震惊的事实：95%不满意的消费者从未向相关公司投诉。这揭示了现代社会中存在的一个普遍问题——人们作为消费者的抱怨几乎完全无效，并且可能在个人或家庭关系中也存在类似的问题。\n根据古德曼及其团队的研究，他们发现当产品或服务质量不达标时，大多数消费者的反应往往是转向竞争对手或者简单地向朋友家人抱怨。这种无效的投诉模式不仅无法促使企业改进服务，还会导致消费者自身的负面情绪积累，进而影响心理健康。实际上，这些障碍阻碍了有效的沟通和问题解决过程。古德曼的研究还指出，消费者们没有进行有效投诉的原因包括时间精力不足、不知晓正确的投诉途径、害怕报复以及认为投诉不会带来任何改变。\n这种无效的抱怨模式在个人或家庭关系中同样存在类似的问题：夫妻间未能有效沟通和解决矛盾会导致双方的不满情绪累积，进而影响彼此的关系质量。如果只有不到5%的消费者通过正式渠道向公司反映问题，那么企业难以收集到足够的反馈信息来改进产品和服务。长此以往，这将导致产品质量下滑、客户满意度下降，并最终损害企业的声誉及市场竞争力。\n因此，有效的抱怨技巧不仅在商业领域至关重要，在维护人际关系方面也同样重要。只有当我们学会正确表达不满并采取行动时，才能真正推动社会的进步和发展。例如，在商业环境中，消费者的投诉是企业改进产品和服务的重要信息来源；而在人际关系中，通过有效的沟通和表达不满情绪可以帮助夫妻或朋友解决矛盾，维持关系质量。\n综上所述，约翰·A.古德曼的研究揭示了当前消费者投诉机制中存在的严重缺陷，并提醒我们抱怨不仅仅是情感宣泄的过程，更是一种促进改进的有效手段。只有当我们学会正确表达不满并采取行动时，才能真正推动社会的进步和发展。'}
        return rsp

class CaseOrganizeRefine(Action):
    name: str = "CaseOrganizeRefine"
    async def run(self, content: str,case_dict:dict,demonstrate_dict:dict,insight_dict:dict,organize_dict:dict,feedback_dict:dict):
        new_dict,wrong_key = await organize_refine(content,case_dict,demonstrate_dict,insight_dict,organize_dict,feedback_dict)
        return new_dict,wrong_key
class CaseAssemble(Action):
    name: str = "CaseAssemble"
    async def run(self, content: str,oral_dict:dict):
        rsp = await case_assemble3(content,oral_dict)
        return rsp
class Compiler(Role):
    name: str = "Compiler"
    profile: str = "Compiler Agent"
    organize_dict: dict = None
    first_flag: bool = False
    final_text :str = ""
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        # self._watch([TopicExpansion,CaseOrganizeContent,CaseOrganizeLogic,CaseOrganizeEnlighten,OralRewrite])
        # self._watch([TopicExpansion,CaseOrganizeContent,CaseOrganizeLogic,CaseOrganizeEnlighten])
        self._watch([TopicExpansion,CaseOrganizeContent,CaseOrganizeLogic,OralFeedback])
        self.set_actions([CaseOrganize,CaseAssemble,CaseOrganizeRefine])
    async def _think(self):
        lst_role = self.get_memories()[-1].role
        lst_cause_by = self.get_memories()[-1].cause_by
        if lst_cause_by == "__main__.OralFeedback":
            self.rc.todo = CaseAssemble()
        elif lst_role == "Topic Research Agent":
            self.rc.todo = CaseOrganize()
        elif lst_role == "Proof Reader Agent":
            self.rc.todo = CaseOrganizeRefine()
    async def _act(self) -> Message:
        todo = self.rc.todo
        print(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        context = self.get_memories()
        Lines = context[0].content
        if todo.name == "CaseOrganize":
            case_dict = context[1].instruct_content.content
            demonstrate_dict = context[2].instruct_content.content
            insight_dict = context[3].instruct_content.content
            rsp_text = await todo.run(Lines,case_dict,demonstrate_dict,insight_dict)  # 得到的是dict
            mes = dict_message(content=rsp_text)
            # msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo),send_to=OralisationSpecialists)  # 把详细案例传给下一个agent
            msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo),send_to=ProofReader)  # 把详细案例传给下一个agent
            self.organize_dict = rsp_text

            self.rc.env.publish_message(msg)
            return msg
        elif todo.name == "CaseAssemble":
            oral_dict = context[-1].instruct_content.content
            rsp_text = await todo.run(Lines,oral_dict)
            self.final_text = rsp_text
            msg = Message(content=rsp_text, role=self.profile, cause_by=type(todo),
                          send_to=ProofReaderFinal)
            self.rc.env.publish_message(msg)
            return msg
        # elif todo.name == "CaseOrganizeRefine" and context[-1].cause_by == "__main__.CaseOrganizeContent":  # 反馈内容完整性
        elif todo.name == "CaseOrganizeRefine":  # 反馈内容完整性
            feedback_dict = context[-1].instruct_content.content  # 这是一个dict包含了反馈信息
            case_dict = context[1].instruct_content.content
            case_demonstrate = context[2].instruct_content.content
            case_expansion = context[3].instruct_content.content
            # if self.organize_dict is None:
            #     rsp_text,wrong_key = await todo.run(Lines, case_dict, case_demonstrate, case_expansion, case_organize_dict,
            #                                         feedback_dict)  #得到的是修改后的case_organize
            # else:
            #     rsp_text,wrong_key = await todo.run(Lines, case_dict, case_demonstrate, case_expansion, self.organize_dict,
            #                                         feedback_dict)
            rsp_text, wrong_key = await todo.run(Lines, case_dict, case_demonstrate, case_expansion, self.organize_dict,
                                                                                         feedback_dict)
            self.organize_dict = rsp_text
            mes = dict_message(content=rsp_text)
            msg = Message(content=wrong_key,instruct_content=mes, role=self.profile, cause_by=type(todo), send_to=ProofReader)
            self.rc.env.publish_message(msg)
            return msg
        # elif todo.name == "CaseOrganizeRefine" and context[-1].cause_by == "__main__.CaseOrganizeLogic":  # 反馈逻辑性
        #     feedback_dict = context[-1].instruct_content.content  # 这是一个dict包含了反馈信息
        #     case_dict = context[1].instruct_content.content
        #     case_demonstrate = context[2].instruct_content.content
        #     case_expansion = context[3].instruct_content.content
        #     rsp_text,wrong_key = await todo.run(Lines, case_dict, case_demonstrate, case_expansion, self.organize_dict,
        #                               feedback_dict)  # 得到的是修改后的case_organize
        #     self.organize_dict = rsp_text
        #     mes = dict_message(content=rsp_text)
        #     msg = Message(content=wrong_key,instruct_content=mes, role=self.profile, cause_by=type(todo), send_to=ProofReader)
        #     self.rc.env.publish_message(msg)
        #     return msg
        # elif todo.name == "CaseOrganizeRefine" and context[-1].cause_by == "__main__.CaseOrganizeEnlighten":
        #     feedback_dict = context[-1].instruct_content.content  # 这是一个dict包含了反馈信息
        #     case_dict = context[1].instruct_content.content
        #     case_demonstrate = context[2].instruct_content.content
        #     case_expansion = context[3].instruct_content.content
        #     rsp_text,wrong_key = await todo.run(Lines, case_dict, case_demonstrate, case_expansion, self.organize_dict,
        #                               feedback_dict)  # 得到的是修改后的case_organize
        #     self.organize_dict = rsp_text
        #     mes = dict_message(content=rsp_text)
        #     msg = Message(content=wrong_key,instruct_content=mes, role=self.profile, cause_by="checkEnlighten", send_to=ProofReader)
        #     self.rc.env.publish_message(msg)
        #     return msg


class OralRewrite(Action):
    name: str = "OralRewrite"
    async def run(self, case_organize:dict):
        rsp = await case_change_style(case_organize)
        # rsp = {'租房者的有效投诉': '嗯，咱们说个故事吧，有位租户因为旧公寓被转手了，不得不赶紧找新住处。他搬进了一个阳光充足、视野开阔的新地方，但没过几天就发现窗外要新建一座高楼，这样一来早上就没太阳晒了。更糟糕的是，施工噪音也开始了，每天六点半就开始钻孔。\n开始时，这位租户试着去找物业沟通这些问题，但是没有结果。这就像是说，只是抱怨或求助是解决不了问题的。后来他意识到直接投诉不管用，就采取了一个重要的步骤：给房东写了一封信要求减租，并且在信里表达了感激之情。这封信不仅仅是抱怨，还提出了解决方案，希望得到帮助。\n最终，物业经理给他回了电话，同意减少租金并延长几个月的租期。结果比他预想的好多了，这也证明了一个有效的投诉是多么重要啊。具体来说：\n1. **充分信息获取**：在行动之前，他问了自己的建筑行业朋友，得到了关于新楼高度和阳光遮挡的具体情况。\n2. **理性沟通策略**：面对物业的无动于衷，他没有放弃，而是用了一种更建设性的方法来沟通。这意味着投诉时不仅要指出问题，还要提出合理解决方案。\n3. **积极态度与感激**：在信里表达出对解决问题的态度是感谢而不是抱怨，这种方式更容易让人愿意帮助你。\n通过这个例子，大家也能学到几点：\n1. **避免负面情绪的传递**：遇到事情要冷静、理性，不要把不满直接变成愤怒和指责。\n2. **积极寻求解决方案**：面对问题时，以解决为目标，尝试不同的方法，并保持乐观态度。\n总之，在租房过程中，咱们可以通过获取信息、合理提出诉求以及用建设性的方式沟通来处理各种问题。这位租户不仅保护了自己的权益，还给其他租房者提供了很好的参考和借鉴呢。', '情感宣泄的重要性': '你知道吗？心理学家告诉我们抱怨背后其实有它的道理。比如瑞秋的一次经历就很能说明问题。\n那天她跟男友去酒吧玩，结果发现他一直盯着另一个女人看，还当着她的面和那个女的搭讪。这下可把瑞秋气坏了，她冲进了女厕所哭了起来。这时旁边有个在补妆的女人看到她难过的样子，就问：“天啊，男人真他妈的浑蛋！”瑞秋心想终于有人能理解我了，结果那人又说了句无情的话，“哦，是吗？那我又怎么知道你不是浑蛋呢？”说完人就走了。\n这下可把瑞秋给震惊到了，她本想得到点安慰，没想到还遇到了这么冷漠的人。这件事说明，在我们情绪低落的时候，真的需要有人能理解并给予支持啊。哪怕只是一个同情的眼神或者递上纸巾都能让人感到好受一些。\n所以说情感宣泄很重要，而在这个过程中有效的倾听和理解是非常关键的。当你遇到不开心的事，能够有个人听你倾诉并且给你安慰，这对走出负面情绪很有帮助。如果碰到了冷漠的态度，那只会让你更难受，甚至达不到通过抱怨来缓解心情的目的。\n这告诉我们，在生活中我们不仅需要找到能提供情感支持的人，也要学会去理解他人的情绪需求，给予他们必要的倾听和同情。这样才能在遇到困难时更好地处理自己的情绪。现代生活节奏这么快，大家压力都挺大的，互相理解和关怀真的很重要。', '投诉的有效性和社会问题': '你知道吗？现在有效的投诉变得超级重要。约翰·A.古德曼研究发现了一个很惊人的数据：95%的不满意消费者根本没去投诉啊。这说明什么呢？就是人们作为消费者的抱怨几乎是无效的，甚至在家庭关系中也存在类似的问题。\n根据他的团队的研究，当产品或服务质量有问题时，大多数消费者往往会选择转向别的公司或者只是跟朋友家人抱怨一番。这样做不仅不能帮助企业改进服务，还可能让自己的负面情绪积累起来，影响心理健康啊。古德曼和他的研究团队指出，人们不进行有效投诉的原因有很多，比如说没时间、不知道怎么投诉、害怕报复或者是觉得投诉也没啥用。\n这种无效的抱怨模式在家庭关系中也挺常见的。比如夫妻俩如果不能好好沟通问题，矛盾就会越积越多，最终影响彼此的关系质量啊。你说如果只有不到5%的人通过正式渠道向公司反馈意见，那企业怎么能收集到足够的信息来改进产品和服务呢？长期这样，产品质量会下降，客户满意度也会降低，最后企业的声誉和市场竞争力都会受损。\n所以你看，不管是商业领域还是人际关系方面，有效的抱怨技巧都非常重要。比如说，在工作中消费者的投诉可以帮助企业改进；而在家庭里通过有效沟通解决问题，则能维护良好的关系质量。总的来说，古德曼的研究告诉我们当前的消费者投诉机制存在严重缺陷，我们不能把抱怨当成简单的发泄，它应该是一种推动进步的有效手段啊。只有当我们学会正确表达不满并采取行动时，才能真正让社会变得更好。'}
        return rsp
class OralRefine(Action):
    name: str = "OralRefine"
    async def run(self,org_dict:dict,oral_dict:dict,feedback:dict):
        new_dict,wrong_key  = await oral_refine(org_dict,oral_dict,feedback)
        return new_dict,wrong_key


class OralisationSpecialists(Role):
    name: str = "OralisationSpecialists"
    profile: str = "Oralisation Specialists Agent"
    detail_case: dict = None
    oral_dict: dict = None
    organize_dict: dict = None
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._watch([CaseOrganizeLogic,OralFeedback])
        self.set_actions([OralRewrite,OralRefine])
    async def _think(self):
        lst_case_by = self.get_memories()[-1].cause_by
        if lst_case_by == "__main__.CaseOrganizeLogic":
            self.rc.todo = OralRewrite()
        elif lst_case_by == "__main__.OralFeedback":
            self.rc.todo = OralRefine()
    async def _act(self) -> Message:
        todo = self.rc.todo
        print(f"{self._setting}: to do {self.rc.todo}({self.rc.todo.name})")
        context = self.get_memories()
        msg = None
        Lines = context[0].content
        if todo.name == "OralRewrite":
            case_org = context[-1].instruct_content.content
            self.organize_dict = case_org
            rsp_text = await todo.run(case_org)  # 得到的是dict
            self.oral_dict = rsp_text
            mes = dict_message(content=rsp_text)
            msg = Message(instruct_content=mes, role=self.profile, cause_by=type(todo),send_to=ProofReader)  # 把详细案例传给下一个agent
            self.rc.env.publish_message(msg)
            return msg
        elif todo.name == "OralRefine":
            feedback_dict = context[-1].instruct_content.content  # 这是一个dict包含了反馈信息
            rsp_text, wrong_key = await todo.run(self.organize_dict,self.oral_dict,feedback_dict)
            self.organize_dict = rsp_text
            mes = dict_message(content=rsp_text)
            msg = Message(content=wrong_key, instruct_content=mes, role=self.profile, cause_by=type(todo),
                          send_to=ProofReader)
            self.rc.env.publish_message(msg)
            return msg

async def main(Lines):
    context = Context()  # Load config2.yaml
    env = Environment(context=context)
    env.add_roles([CaseAnalyst(),ProofReader(),TopicResearch(),Compiler(),OralisationSpecialists(),ProofReaderFinal(),FinalCompiler()])
    # env.add_roles([CaseAnalyst(),ProofReader(),TopicResearch(),Compiler()])
    env.publish_message(
        Message(content=Lines))  # 将用户的消息发送个所有agent，
    while not env.is_idle:  # env.is_idle要等到所有Agent都没有任何新消息要处理后才会为True
        await env.run()

if __name__ == "__main__":
    """
   "第一章","第二章","第三章","第四章","第五章","第六章","第七章","第八章","第九章","第十章","第十一章","第十二章","第十三章","第十四章"
   "第一部分","第二部分","第三部分","第四部分","第五部分","第六部分", ,"第九部分","第十部分","第十一部分","第十二部分","第十三部分","第十四部分"
    """
    chap_list = ["第一章","第二章","第三章","第四章","第五章","第六章","第七章","第八章","第九章","第十章"]
    # for x in chap_list:
    #     Lines = open(f'../data/园丁与木匠/{x}.txt', 'r', encoding='utf-8').read()
    #     f3 = open("result/园丁与木匠.txt", "a", encoding="utf-8", errors="ignore")
    #     f3.write(x+'\n')
    #     f3.close()
    #     asyncio.run(main(Lines))
    Lines = open(f'../data/自卑与超越/第十章.txt', 'r', encoding='utf-8').read()
    asyncio.run(main(Lines))
