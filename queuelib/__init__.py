__version__ = "1.6.1"

from queuelib.queue import FifoDiskQueue, LifoDiskQueue, FifoMemoryQueue, LifoMemoryQueue
from queuelib.pqueue import PriorityQueue
from queuelib.rrqueue import RoundRobinQueue
