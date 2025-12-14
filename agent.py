import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from config import COST_MSG, COST_MSG_CENTER, COST_OP, COST_MEM


class TreeAgent(Agent):
    def __init__(self, jid, password, my_number, agent_id):
        super().__init__(jid, password)
        self.my_number = my_number
        self.agent_id = agent_id
        self.parent_jid = None
        self.children_jids = []
        self.is_root = False
        self.cost = COST_MEM  # Хранение своего числа
        self.done = False
        self.final_result = None
        
        self.children_data = {}
        self.received_count = 0
    
    def configure(self, parent_jid, children_jids, is_root):
        self.parent_jid = parent_jid
        self.children_jids = children_jids
        self.is_root = is_root
    
    class AggregationBehaviour(CyclicBehaviour):
        async def run(self):
            agent = self.agent
            
            if agent.done:
                await asyncio.sleep(0.1)
                return
            
            if len(agent.children_jids) == 0 and agent.parent_jid and not agent.done:
                await asyncio.sleep(0.5) 
                
                msg = Message(to=agent.parent_jid)
                msg.body = f"{agent.my_number},{1}"
                await self.send(msg)
                agent.cost += COST_MSG
                
                print(f"[Agent{agent.agent_id}] Лист: отправил {agent.my_number} родителю")
                agent.done = True
                return
            
            if len(agent.children_jids) > 0:
                msg = await self.receive(timeout=1)
                if msg:
                    parts = msg.body.split(",")
                    child_sum = float(parts[0])
                    child_count = int(parts[1])
                    
                    agent.children_data[str(msg.sender)] = (child_sum, child_count)
                    agent.received_count += 1
                    agent.cost += COST_MSG  
                    agent.cost += COST_MEM  
                    
                    print(f"[Agent{agent.agent_id}] Получил от {msg.sender}: sum={child_sum}, count={child_count}")
                    
                    if agent.received_count == len(agent.children_jids):
                        total_sum = agent.my_number
                        total_count = 1
                        
                        for child_sum, child_count in agent.children_data.values():
                            total_sum += child_sum
                            agent.cost += COST_OP  # Сложение
                            total_count += child_count
                            agent.cost += COST_OP  # Сложение
                        
                        if agent.is_root:
                            # Корень вычисляет среднее
                            average = total_sum / total_count
                            agent.cost += COST_OP  # Деление
                            agent.cost += COST_MSG_CENTER  # Отправка центру
                            
                            agent.final_result = average
                            print(f"\n{'='*50}")
                            print(f"[Agent{agent.agent_id}] КОРЕНЬ: среднее = {average:.4f}")
                            print(f"[Agent{agent.agent_id}] sum={total_sum}, count={total_count}")
                            print(f"{'='*50}\n")
                            agent.done = True
                        else:
                            # Отправляем родителю
                            msg = Message(to=agent.parent_jid)
                            msg.body = f"{total_sum},{total_count}"
                            await self.send(msg)
                            agent.cost += COST_MSG
                            
                            print(f"[Agent{agent.agent_id}] Агрегировал и отправил родителю: sum={total_sum}, count={total_count}")
                            agent.done = True
    
    async def setup(self):
        print(f"[Agent{self.agent_id}] Запущен с числом {self.my_number}")
        b = self.AggregationBehaviour()
        self.add_behaviour(b)
