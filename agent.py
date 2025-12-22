import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template
from config import COST_MSG, COST_OP, COST_MEM, GAMMA, EPSILON, MAX_ITERATIONS, CONVERGENCE_PATIENCE


def normalize_jid(jid_str):
    return str(jid_str).split('/')[0]


class LVPAgent(Agent):
    def __init__(self, jid, password, my_number, agent_id):
        super().__init__(jid, password)
        self.my_number = float(my_number)
        self.current_value = self.my_number
        self.agent_id = agent_id
        self.neighbors_jids = []
        self.cost = COST_MEM
        self.done = False
        self.iteration = 0
        self.convergence_counter = 0
        self.converged = False
        self.neighbors_values = {}
    
    def configure(self, neighbors_jids):
        self.neighbors_jids = neighbors_jids
        self.neighbors_values = {}

    class LVPBehaviour(CyclicBehaviour):
        async def on_start(self):
            await self.broadcast_value()

        async def run(self):
            agent = self.agent
            
            if agent.done:
                await asyncio.sleep(1)
                return

            while True:
                msg = await self.receive(timeout=0.1)
                if msg:
                    try:
                        val = float(msg.body)
                        normalized_sender = normalize_jid(msg.sender)
                        agent.neighbors_values[normalized_sender] = val
                        agent.cost += COST_MSG
                        agent.cost += COST_MEM
                    except ValueError:
                        pass
                else:
                    break
            
            await asyncio.sleep(0.5)
            
            if agent.iteration >= MAX_ITERATIONS:
                if not agent.done:
                    print(f"[Agent{agent.agent_id}] Достигнут лимит итераций. Значение: {agent.current_value:.4f}")
                    agent.done = True
                return
            
            if agent.converged:
                await asyncio.sleep(1)
                return

            control_input = 0.0
            active_neighbors = 0
            
            for neighbor_jid in agent.neighbors_jids:
                normalized_neighbor = normalize_jid(neighbor_jid)
                n_val = agent.neighbors_values.get(normalized_neighbor)
                
                if n_val is not None:
                    diff = n_val - agent.current_value
                    agent.cost += COST_OP
                    
                    control_input += diff
                    agent.cost += COST_OP
                    active_neighbors += 1
            
            if active_neighbors > 0:
                delta = GAMMA * control_input
                agent.cost += COST_OP
                
                old_value = agent.current_value
                agent.current_value += delta
                agent.cost += COST_OP
                
                agent.iteration += 1
                
                if abs(agent.current_value - old_value) < EPSILON:
                    agent.convergence_counter += 1
                    if agent.convergence_counter >= CONVERGENCE_PATIENCE:
                        agent.converged = True
                        print(f"[Agent{agent.agent_id}] Сошелся на итерации {agent.iteration}. Значение: {agent.current_value:.4f}")
                        agent.done = True
                        return
                else:
                    agent.convergence_counter = 0

                await self.broadcast_value()
                
                if agent.iteration % 10 == 0:
                    print(f"[Agent{agent.agent_id}] Iter {agent.iteration}: {agent.current_value:.4f} (neighbors: {active_neighbors})")

        async def broadcast_value(self):
            for neighbor in self.agent.neighbors_jids:
                msg = Message(to=neighbor)
                msg.body = str(self.agent.current_value)
                await self.send(msg)
                self.agent.cost += COST_MSG

    async def setup(self):
        print(f"[Agent{self.agent_id}] Запущен LVP с числом {self.my_number}")
        b = self.LVPBehaviour()
        template = Template()
        self.add_behaviour(b, template)
