import random


def create_random_graph(n):
    """Создает случайный связный граф с n узлами (БЕЗ весов)"""
    edges = []
    
    # Сначала создаем дерево чтобы граф был связным
    for i in range(1, n):
        parent = random.randint(0, i - 1)
        edges.append((i, parent))
    
    # Добавляем дополнительные ребра (создаем циклы)
    extra_edges = n // 2
    for _ in range(extra_edges):
        u = random.randint(0, n - 1)
        v = random.randint(0, n - 1)
        if u != v:
            edges.append((u, v))
    
    return edges


def build_spanning_tree(n, edges):
    """Строит остовное дерево из графа с помощью DFS"""
    # Создаем список смежности
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    
    # DFS для построения дерева
    visited = [False] * n
    parent = [-1] * n
    children = [[] for _ in range(n)]
    
    def dfs(node, par):
        visited[node] = True
        parent[node] = par
        
        for neighbor in adj[node]:
            if not visited[neighbor]:
                children[node].append(neighbor)
                dfs(neighbor, node)
    
    dfs(0, -1)
    
    return children, parent
