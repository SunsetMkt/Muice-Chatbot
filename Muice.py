from Tools import divede_sentences
import logging,time,random,json,os,shutil


class Muice():
    '''
    Muice交互类
    '''

    def __init__(self, Model, read_memory_from_file:bool=True, known_topic_probability:float=0.003, time_topic_probability:float=0.75):
        self.model = Model
        self.read_memory_from_file = read_memory_from_file
        self.known_topic_probability = known_topic_probability
        self.time_topic_probability = time_topic_probability
        self.known_topic = ['（分享一下你的一些想法）','（创造一个新话题）']
        self.time_topic = {'07':'（发起一个早晨问候）','12':'（发起一个中午问候）','18':'（发起一个傍晚问候）','00':'（发起一个临睡问候）'}
        self.time_topics = self.time_topic.copy()
        self.last_message_time = time.time()
        self.is_command = False
        if self.read_memory_from_file:
            self.history = self.get_recent_chat_memory()
        else:
            self.history = []

    def ask(self, text: str) -> str:
        '''发送信息'''
        if text == '':
            return ''
        
        command_check_result = self.command_runner(text)
        if command_check_result == True:
            self.is_command = True
            return ["操作已完成"]
        elif type(command_check_result) == str:
            self.is_command = True
            return [command_check_result]

        self.is_command = False
        self.user_text = text

        logging.info(f'收到消息: {text}')
        start_time = time.time()
        self.reply = self.model.ask(self.user_text, self.history)
        end_time = time.time()
        logging.info(f'模型调用时长: {end_time - start_time} s')
        new_reply = divede_sentences(self.reply)
        return new_reply

    def CreateANewTopic(self):
        '''
        主动发起对话
        '''
        current_time = time.strftime("%H:%M", time.localtime())
        TimeDifference = time.time() - self.last_message_time
        if TimeDifference < 60 * 60:
            return ''
        if random.random() < self.time_topic_probability:
            for hour,topic in self.time_topic.items():
                event_time = hour + ':' + str(random.randint(0,59))
                if event_time == current_time:
                    del self.time_topic[hour]
                    return topic
        if not current_time.split(':')[0] in ['23','00','01','02','03','04','05','06'] and random.random() < self.known_topic_probability:
            return random.choice(self.known_topic)
        if len(self.time_topic) <= 3 and not time.strftime("%H", time.localtime()) in self.time_topics.keys():
            self.time_topic = self.time_topics.copy()
        return ''

    def finish_ask(self, reply: list):
        '''结束对话并保存记忆'''
        if (reply != [] and reply != [""]) and self.is_command == False:
            reply = "".join(reply)
            self.save_chat_memory(reply)
            self.last_message_time = time.time()

    def get_recent_chat_memory(self):
        '''
        获取最近一条记忆
        '''
        try:
            with open('./memory/chat_memory.json', 'r', encoding='utf-8') as f:
                data = f.readlines()
                return json.loads(data[-1])['history']
        except:
            return []

    def save_chat_memory(self, reply:str):
        '''
        保存至记忆数据库'''
        self.history.append([self.user_text, reply])
        if not os.path.isdir('memory'):
            os.mkdir('memory')
        with open('./memory/chat_memory.json', 'a', encoding='utf-8') as f:
            json.dump({'prompt': self.user_text, 'completion': reply, 'history': self.history}, f, ensure_ascii=False)
            f.write('\n')

    def remove_last_chat_memory(self):
        '''
        删除最后一条记忆
        '''
        with open('./memory/chat_memory.json', 'r', encoding='utf-8') as f:
            data = f.readlines()
            del data[-1]
        with open('./memory/chat_memory.json', 'w', encoding='utf-8') as f:
            f.writelines(data)

    def refresh(self):
        '''
        刷新对话
        '''
        logging.info("Start refresh")
        self.remove_last_chat_memory()
        self.history = self.get_recent_chat_memory()
        response = self.model.ask(self.user_text, self.history)
        return response
    
    def command_runner(self,text:str) -> bool|str:
        '''
        执行可能存在的命令, 否则正常对话
        '''
        text
        if text == '/help':
            help_text = "/clean 清空本轮对话历史 \n /help 显示所有可用的命令列表 \n /refresh 刷新本次对话回复 \n /reset 重置所有对话数据(将存档对话数据) \n /undo 撤销上一次对话"
            return help_text
        
        elif text == '/refresh':
            reply = self.refresh()
            self.save_chat_memory(reply)
            return reply
        
        elif text == '/clean':
            self.history = []
            return True
        
        elif text == '/reset':
            shutil.copy('./memory/chat_memory.json','./memory/chat_memory_backup.json')
            os.remove('./memory/chat_memory.json')
            self.history = []
            return True
        
        elif text == '/undo':
            self.remove_last_chat_memory()
            self.history = self.get_recent_chat_memory()
            return True

        else:
            return False