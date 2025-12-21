import asyncio
import random
import time
from agent import LVPAgent
from graph_utils import create_random_graph
from config import MAX_ITERATIONS

NUM_AGENTS = 15
XMPP_SERVER = "localhost"

async def main():
    print("=" * 60)
    print("МУЛЬТИАГЕНТНАЯ СИСТЕМА С LVP (Local Voting Protocol)")
    print("=" * 60)
    
    numbers = [random.randint(1, 100) for _ in range(NUM_AGENTS)]
    expected_avg = sum(numbers) / len(numbers)
    
    print(f"Числа агентов: {numbers}")
    print(f"Ожидаемое среднее: {expected_avg:.4f}")
    
    # 1. Создаем граф коммуникаций
    edges = create_random_graph(NUM_AGENTS)
    
    # Преобразуем список ребер в список соседей для каждого агента
    neighbors = [[] for _ in range(NUM_AGENTS)]
    for u, v in edges:
        if v not in neighbors[u]: neighbors[u].append(v)
        if u not in neighbors[v]: neighbors[v].append(u)
    
    print("\nГраф коммуникаций (соседи):")
    for i in range(NUM_AGENTS):
        print(f"  Agent{i}: {neighbors[i]}")
    
    # 2. Создаем агентов
    agents = []
    for i in range(NUM_AGENTS):
        jid = f"agent{i}@{XMPP_SERVER}"
        agent = LVPAgent(jid, f"pass{i}", numbers[i], i)
        agents.append(agent)
    
    # 3. Конфигурируем агентов (раздаем соседей)
    for i in range(NUM_AGENTS):
        neighbors_jids = [f"agent{n}@{XMPP_SERVER}" for n in neighbors[i]]
        agents[i].configure(neighbors_jids)
    
    print("\n" + "=" * 60)
    print("ЗАПУСК АГЕНТОВ")
    print("=" * 60)
    
    # Запускаем агентов
    for agent in agents:
        await agent.start()
    
    # Ждем завершения (пока все не выполнят MAX_ITERATIONS)
    # Или просто ждем фиксированное время, так как LVP асимптотический
    
    wait_time = 20 # секунд
    print(f"Ждем сходимости ({wait_time} сек)...")
    
    # Можно мониторить состояние
    for _ in range(wait_time):
        all_done = all(a.done for a in agents)
        if all_done:
            break
        await asyncio.sleep(1)
    
    # Результаты
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ LVP")
    print("=" * 60)
    
    print(f"Ожидаемое среднее:   {expected_avg:.4f}")
    
    total_cost = 0
    final_values = []
    
    print("\n--- Итоговые значения и стоимость ---")
    for i, agent in enumerate(agents):
        val = agent.current_value
        final_values.append(val)
        cost = agent.cost
        total_cost += cost
        
        diff = abs(val - expected_avg)
        print(f"Agent{i}: Val={val:.4f} (Err={diff:.4f}), Cost={cost:.2f}, Iters={agent.iteration}")
    
    avg_result = sum(final_values) / len(final_values)
    print(f"\nСреднее по всем агентам: {avg_result:.4f}")
    print(f"ОБЩАЯ СТОИМОСТЬ: {total_cost:.2f}")
    print("=" * 60)
    
    # Останавливаем агентов
    for agent in agents:
        await agent.stop()

if __name__ == "__main__":
    import spade
    spade.run(main())
