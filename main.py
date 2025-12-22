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
    
    edges = create_random_graph(NUM_AGENTS)
    
    neighbors = [[] for _ in range(NUM_AGENTS)]
    for u, v in edges:
        if v not in neighbors[u]: neighbors[u].append(v)
        if u not in neighbors[v]: neighbors[v].append(u)
    
    print("\nГраф коммуникаций (соседи):")
    for i in range(NUM_AGENTS):
        print(f"  Agent{i}: {neighbors[i]}")
    
    agents = []
    for i in range(NUM_AGENTS):
        jid = f"agent{i}@{XMPP_SERVER}"
        agent = LVPAgent(jid, f"pass{i}", numbers[i], i)
        agents.append(agent)
    
    for i in range(NUM_AGENTS):
        neighbors_jids = [f"agent{n}@{XMPP_SERVER}" for n in neighbors[i]]
        agents[i].configure(neighbors_jids)
    
    print("\n" + "=" * 60)
    print("ЗАПУСК АГЕНТОВ")
    print("=" * 60)
    
    for agent in agents:
        await agent.start()
    
    wait_time = 20
    print(f"Ждем сходимости ({wait_time} сек)...")
    
    for _ in range(wait_time):
        all_done = all(a.done for a in agents)
        if all_done:
            break
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ LVP")
    print("=" * 60)
    
    print(f"Ожидаемое среднее: {expected_avg:.4f}")
    
    total_cost = 0
    final_values = []
    converged_count = 0
    max_error = 0
    
    print("\n--- Итоговые значения и стоимость ---")
    for i, agent in enumerate(agents):
        val = agent.current_value
        final_values.append(val)
        cost = agent.cost
        total_cost += cost
        
        diff = abs(val - expected_avg)
        max_error = max(max_error, diff)
        
        if agent.converged:
            converged_count += 1
            status = "✓"
        else:
            status = "✗"
        
        print(f"Agent{i:2d}: Val={val:7.4f} Err={diff:6.4f} Cost={cost:6.2f} Iters={agent.iteration:2d} [{status}]")
    
    avg_result = sum(final_values) / len(final_values)
    
    print("\n" + "=" * 60)
    print("СТАТИСТИКА")
    print("=" * 60)
    print(f"Среднее по агентам:     {avg_result:.4f}")
    print(f"Ожидаемое среднее:      {expected_avg:.4f}")
    print(f"Максимальная ошибка:    {max_error:.4f}")
    print(f"Сошлось агентов:        {converged_count}/{NUM_AGENTS}")
    print(f"ОБЩАЯ СТОИМОСТЬ:        {total_cost:.2f}")
    print("=" * 60)
    
    for agent in agents:
        await agent.stop()

if __name__ == "__main__":
    import spade
    spade.run(main())
