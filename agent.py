import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from config import COST_MSG, COST_MSG_CENTER, COST_OP, COST_MEM, GAMMA, EPSILON, MAX_ITERATIONS

class LVPAgent(Agent):
    def __init__(self, jid, password, my_number, agent_id):
        super().__init__(jid, password)
        self.my_number = float(my_number)
        self.current_value = self.my_number
        self.agent_id = agent_id
        self.neighbors_jids = []
        self.cost = COST_MEM  # Хранение своего числа
        self.done = False
        self.iteration = 0
        
        # Храним последние известные значения соседей
        # key: jid, value: number
        self.neighbors_values = {} 
    
    def configure(self, neighbors_jids):
        self.neighbors_jids = neighbors_jids
        # Инициализируем значения соседей нулями или (лучше) не учитываем пока не получим
        self.neighbors_values = {}

    class LVPBehaviour(CyclicBehaviour):
        async def on_start(self):
            # При старте отправляем свое значение всем соседям
            await self.agent.broadcast_value()

        async def run(self):
            agent = self.agent
            
            if agent.done:
                await asyncio.sleep(1)
                return

            # 1. Получаем сообщения от соседей
            # Читаем все доступные сообщения
            while True:
                msg = await self.receive(timeout=0.1)
                if msg:
                    try:
                        val = float(msg.body)
                        agent.neighbors_values[str(msg.sender)] = val
                        agent.cost += COST_MSG # Прием
                        agent.cost += COST_MEM # Хранение значения соседа
                        # print(f"[Agent{agent.agent_id}] Получил {val} от {msg.sender}")
                    except ValueError:
                        pass
                else:
                    break
            
            # 2. Если у нас есть данные хотя бы от кого-то (или просто идем по итерациям)
            # Для корректности LVP лучше ждать данных от всех, но в асинхроне это сложно.
            # Будем обновляться раз в N секунд, используя последние известные данные.
            
            await asyncio.sleep(0.5) # Пауза между итерациями
            
            if agent.iteration >= MAX_ITERATIONS:
                if not agent.done:
                    print(f"[Agent{agent.agent_id}] Завершил работу (макс итераций). Значение: {agent.current_value:.4f}")
                    agent.done = True
                return

            # 3. Шаг обновления (Consensus Step)
            # x_i(t+1) = x_i(t) + gamma * sum(x_j - x_i)
            
            control_input = 0.0
            
            # Считаем сумму разностей только для тех соседей, от кого получили данные
            # (или считаем, что если не получили, то используем старое, если есть)
            
            active_neighbors = 0
            for neighbor_jid in agent.neighbors_jids:
                # neighbor_jid это строка "agentX@localhost"
                # msg.sender может быть "agentX@localhost/resource"
                # Надо аккуратно матчить. Для простоты будем считать, что ключи совпадают
                # или искать вхождение.
                
                # Попробуем найти значение
                n_val = None
                for key, val in agent.neighbors_values.items():
                    if neighbor_jid in key:
                        n_val = val
                        break
                
                if n_val is not None:
                    diff = n_val - agent.current_value
                    agent.cost += COST_OP # Вычитание
                    
                    control_input += diff
                    agent.cost += COST_OP # Сложение (накапливаем сумму)
                    active_neighbors += 1
            
            if active_neighbors > 0:
                # Обновляем значение
                delta = GAMMA * control_input
                agent.cost += COST_OP # Умножение
                
                old_value = agent.current_value
                agent.current_value += delta
                agent.cost += COST_OP # Сложение
                
                agent.iteration += 1
                
                # Проверка сходимости (локальная)
                if abs(agent.current_value - old_value) < EPSILON:
                    # Можно считать, что сошлись, но в LVP надо продолжать, 
                    # пока соседи тоже не успокоятся.
                    pass

                # 4. Рассылаем новое значение
                await agent.broadcast_value()
                
                print(f"[Agent{agent.agent_id}] Iter {agent.iteration}: {agent.current_value:.4f} (neighbors: {active_neighbors})")

    async def broadcast_value(self):
        for neighbor in self.neighbors_jids:
            msg = Message(to=neighbor)
            msg.body = str(self.current_value)
            await self.send(msg)
            self.cost += COST_MSG # Отправка

    async def setup(self):
        print(f"[Agent{self.agent_id}] Запущен LVP с числом {self.my_number}")
        b = self.LVPBehaviour()
        self.add_behaviour(b)
