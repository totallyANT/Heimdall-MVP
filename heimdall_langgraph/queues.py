import queue

# Queue containing Tier-1 anomaly signals
anomaly_queue = queue.PriorityQueue(maxsize=50)