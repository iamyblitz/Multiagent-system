import asyncio
import random
from agent import TreeAgent
from graph_utils import create_random_graph, build_spanning_tree


async def main():
    random.seed(42)
    
    NUM_AGENTS = 15
    
    print("=" * 60)
    print("МУЛЬТИАГЕНТНАЯ СИСТЕМА С MST")
    print("=" * 60)
    
    # Генерируем числа для агентов
    numbers = [random.randint(1, 100) for _ in range(NUM_AGENTS)]
    expected_avg = sum(numbers) / len(numbers)
    
    print(f"\nЧисла агентов: {numbers}")
    print(f"Ожидаемое среднее: {expected_avg:.4f}")
    print(f"Сумма: {sum(numbers)}, Количество: {len(numbers)}")
    
    # Создаем граф и остовное дерево
    edges = create_random_graph(NUM_AGENTS)
    children, parent = build_spanning_tree(NUM_AGENTS, edges)
    
    print(f"\nСтруктура дерева (parent -> children):")
    for i in range(NUM_AGENTS):
        if children[i]:
            print(f"  Agent{i} -> {['Agent'+str(c) for c in children[i]]}")
    
    print("\n" + "=" * 60)
    print("ЗАПУСК АГЕНТОВ")
    print("=" * 60 + "\n")
    
    # Создаем агентов
    agents = []
    for i in range(NUM_AGENTS):
        jid = f"agent{i}@localhost"
        agent = TreeAgent(jid, f"pass{i}", numbers[i], i)
        agents.append(agent)
    
    # Запускаем агентов
    for agent in agents:
        await agent.start()
    
    # Конфигурируем топологию
    for i in range(NUM_AGENTS):
        parent_jid = f"agent{parent[i]}@localhost" if parent[i] != -1 else None
        children_jids = [f"agent{c}@localhost" for c in children[i]]
        is_root = (parent[i] == -1)
        agents[i].configure(parent_jid, children_jids, is_root)
    
    # Ждем завершения
    timeout = 30
    for _ in range(timeout * 2):
        if all(a.done for a in agents):
            break
        await asyncio.sleep(0.5)
    
    # Результаты
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 60)
    
    root = agents[0]
    if root.final_result:
        print(f"Вычисленное среднее: {root.final_result:.4f}")
        print(f"Ожидаемое среднее:   {expected_avg:.4f}")
    
    total_cost = sum(a.cost for a in agents)
    print(f"\n--- Стоимость по агентам ---")
    for a in agents:
        print(f"Agent{a.agent_id}: {a.cost:.2f}")
    
    print(f"\nОБЩАЯ СТОИМОСТЬ: {total_cost:.2f}")
    print("=" * 60)
    
    # Останавливаем агентов
    for agent in agents:
        await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
