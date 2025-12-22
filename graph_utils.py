import random


def create_random_graph(n):
    """Создает случайный связный граф с n узлами (БЕЗ весов)"""
    edges = []
    
    for i in range(1, n):
        parent = random.randint(0, i - 1)
        edges.append((i, parent))
    
    extra_edges = n // 2
    for _ in range(extra_edges):
        u = random.randint(0, n - 1)
        v = random.randint(0, n - 1)
        if u != v:
            edges.append((u, v))
    
    return edges

