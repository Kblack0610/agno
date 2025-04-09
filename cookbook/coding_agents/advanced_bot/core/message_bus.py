"""
Message Bus Module

This module provides a robust communication system for agents to exchange
messages and data across the multi-agent system.
"""

import logging
import uuid
import time
from typing import Dict, List, Any, Callable, Optional
from queue import Queue
from threading import Lock

# Message priority levels
PRIORITY_LOW = 0
PRIORITY_NORMAL = 1
PRIORITY_HIGH = 2
PRIORITY_CRITICAL = 3

class Message:
    """
    Message class for inter-agent communication.
    
    Messages contain:
    - A unique identifier
    - Sender and recipient information
    - Message type and content
    - Priority and timestamp
    - Optional correlation ID for request-response patterns
    """
    
    def __init__(
            self,
            sender_id: str,
            recipient_id: str = None,
            message_type: str = "default",
            content: Dict[str, Any] = None,
            priority: int = PRIORITY_NORMAL,
            correlation_id: str = None
        ):
        """
        Initialize a new message.
        
        Args:
            sender_id: ID of the sending agent
            recipient_id: ID of the receiving agent (None for broadcast)
            message_type: Type of message (e.g., 'request', 'response', 'notification')
            content: Dictionary containing the message data
            priority: Message priority (0-3, with 3 being highest)
            correlation_id: ID linking requests and responses (generated if None)
        """
        self.message_id = str(uuid.uuid4())
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.message_type = message_type
        self.content = content or {}
        self.priority = priority
        self.timestamp = time.time()
        self.correlation_id = correlation_id or str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message_type': self.message_type,
            'content': self.content,
            'priority': self.priority,
            'timestamp': self.timestamp,
            'correlation_id': self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from dictionary representation."""
        msg = cls(
            sender_id=data['sender_id'],
            recipient_id=data['recipient_id'],
            message_type=data['message_type'],
            content=data['content'],
            priority=data['priority'],
            correlation_id=data['correlation_id']
        )
        msg.message_id = data['message_id']
        msg.timestamp = data['timestamp']
        return msg
    
    def create_response(self, content: Dict[str, Any] = None) -> 'Message':
        """
        Create a response message to this message.
        
        Args:
            content: Dictionary containing the response data
            
        Returns:
            A new Message object configured as a response
        """
        return Message(
            sender_id=self.recipient_id,
            recipient_id=self.sender_id,
            message_type='response',
            content=content or {},
            correlation_id=self.correlation_id
        )
    
    def __lt__(self, other: 'Message') -> bool:
        """Compare messages for priority queue ordering."""
        return self.priority < other.priority


class MessageBus:
    """
    Message Bus facilitates communication between agents in the system.
    
    Features:
    - Send/receive messages between agents
    - Subscribe to specific message types
    - Prioritized message delivery
    - Message filtering
    - Request-response pattern support
    """
    
    def __init__(self):
        """Initialize the message bus."""
        self.logger = logging.getLogger('core.message_bus')
        
        # Message queue by recipient
        self.queues: Dict[str, Queue] = {}
        
        # Subscription registry for topics/message types
        # Format: {message_type: [agent_ids]}
        self.subscriptions: Dict[str, List[str]] = {}
        
        # Registry of response callbacks
        # Format: {correlation_id: (callback_fn, expiry_time)}
        self.response_callbacks: Dict[str, tuple] = {}
        
        # Locks for thread safety
        self.queue_lock = Lock()
        self.subscription_lock = Lock()
        self.callback_lock = Lock()
        
        self.logger.info("Message bus initialized")
    
    def register_agent(self, agent_id: str) -> None:
        """
        Register an agent with the message bus.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        with self.queue_lock:
            if agent_id not in self.queues:
                self.queues[agent_id] = Queue()
                self.logger.debug(f"Registered agent: {agent_id}")
    
    def unregister_agent(self, agent_id: str) -> None:
        """
        Unregister an agent from the message bus.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        with self.queue_lock:
            if agent_id in self.queues:
                del self.queues[agent_id]
                
        with self.subscription_lock:
            for message_type, subscribers in list(self.subscriptions.items()):
                if agent_id in subscribers:
                    subscribers.remove(agent_id)
                    # Remove the message type if no subscribers
                    if not subscribers:
                        del self.subscriptions[message_type]
        
        self.logger.debug(f"Unregistered agent: {agent_id}")
    
    def subscribe(self, agent_id: str, message_type: str) -> None:
        """
        Subscribe an agent to a specific message type.
        
        Args:
            agent_id: Unique identifier for the subscribing agent
            message_type: Type of messages to subscribe to
        """
        with self.subscription_lock:
            if message_type not in self.subscriptions:
                self.subscriptions[message_type] = []
            
            if agent_id not in self.subscriptions[message_type]:
                self.subscriptions[message_type].append(agent_id)
                self.logger.debug(f"Agent {agent_id} subscribed to {message_type}")
    
    def unsubscribe(self, agent_id: str, message_type: str) -> None:
        """
        Unsubscribe an agent from a specific message type.
        
        Args:
            agent_id: Unique identifier for the subscribing agent
            message_type: Type of messages to unsubscribe from
        """
        with self.subscription_lock:
            if message_type in self.subscriptions and agent_id in self.subscriptions[message_type]:
                self.subscriptions[message_type].remove(agent_id)
                self.logger.debug(f"Agent {agent_id} unsubscribed from {message_type}")
                
                # Remove the message type if no subscribers
                if not self.subscriptions[message_type]:
                    del self.subscriptions[message_type]
    
    def send(self, message: Message) -> bool:
        """
        Send a message to the specified recipient(s).
        
        Args:
            message: Message object to send
            
        Returns:
            True if the message was delivered, False otherwise
        """
        recipients = []
        
        # Determine recipients based on direct addressing or subscriptions
        if message.recipient_id:
            # Direct message to specific recipient
            recipients = [message.recipient_id]
        else:
            # Broadcast to all subscribers of this message type
            with self.subscription_lock:
                if message.message_type in self.subscriptions:
                    recipients = self.subscriptions[message.message_type].copy()
        
        # Deliver to all recipients
        delivered = False
        for recipient_id in recipients:
            with self.queue_lock:
                if recipient_id in self.queues:
                    self.queues[recipient_id].put(message)
                    delivered = True
                    self.logger.debug(
                        f"Message {message.message_id} from {message.sender_id} " 
                        f"delivered to {recipient_id}"
                    )
        
        return delivered
    
    def send_and_wait(
            self,
            message: Message,
            timeout: float = 5.0
        ) -> Optional[Message]:
        """
        Send a message and wait for a response.
        
        Args:
            message: Message object to send
            timeout: Maximum time to wait for response in seconds
            
        Returns:
            Response message if received within timeout, None otherwise
        """
        response_queue: Queue = Queue()
        
        # Register callback for the response
        def response_callback(resp_message: Message) -> None:
            response_queue.put(resp_message)
        
        self.register_response_callback(
            message.correlation_id,
            response_callback,
            timeout
        )
        
        # Send the message
        if not self.send(message):
            self.logger.warning(f"Failed to deliver message {message.message_id}")
            return None
        
        # Wait for response
        try:
            return response_queue.get(timeout=timeout)
        except Exception:
            self.logger.warning(
                f"Timeout waiting for response to message {message.message_id}"
            )
            return None
        finally:
            # Clean up the callback
            self.unregister_response_callback(message.correlation_id)
    
    def register_response_callback(
            self,
            correlation_id: str,
            callback: Callable[[Message], None],
            timeout: float = 60.0
        ) -> None:
        """
        Register a callback for a response to a specific message.
        
        Args:
            correlation_id: Correlation ID of the original message
            callback: Function to call when response is received
            timeout: Time in seconds after which the callback expires
        """
        with self.callback_lock:
            expiry = time.time() + timeout
            self.response_callbacks[correlation_id] = (callback, expiry)
    
    def unregister_response_callback(self, correlation_id: str) -> None:
        """
        Unregister a response callback.
        
        Args:
            correlation_id: Correlation ID of the original message
        """
        with self.callback_lock:
            if correlation_id in self.response_callbacks:
                del self.response_callbacks[correlation_id]
    
    def receive(self, agent_id: str, timeout: float = 0.1) -> Optional[Message]:
        """
        Receive the next message for a specific agent.
        
        Args:
            agent_id: ID of the agent receiving messages
            timeout: Maximum time to wait for a message
            
        Returns:
            Next message for the agent, or None if no messages are available
        """
        with self.queue_lock:
            if agent_id not in self.queues:
                self.logger.warning(f"Agent {agent_id} not registered with message bus")
                return None
            
            try:
                message = self.queues[agent_id].get(timeout=timeout)
                
                # If this is a response message, check for callbacks
                if message.message_type == 'response':
                    self._handle_response(message)
                
                return message
            except Exception:
                # Queue.get timeout exception is expected
                return None
    
    def _handle_response(self, message: Message) -> None:
        """
        Handle response messages and execute registered callbacks.
        
        Args:
            message: Response message
        """
        with self.callback_lock:
            if message.correlation_id in self.response_callbacks:
                callback, expiry = self.response_callbacks[message.correlation_id]
                
                # Check if callback is still valid
                if time.time() <= expiry:
                    try:
                        callback(message)
                    except Exception as e:
                        self.logger.error(
                            f"Error in response callback for {message.correlation_id}: {e}"
                        )
                
                # Remove the callback after execution
                del self.response_callbacks[message.correlation_id]
    
    def clean_expired_callbacks(self) -> None:
        """Remove expired response callbacks."""
        with self.callback_lock:
            current_time = time.time()
            expired = [
                cid for cid, (_, expiry) in self.response_callbacks.items()
                if current_time > expiry
            ]
            
            for cid in expired:
                del self.response_callbacks[cid]
                self.logger.debug(f"Removed expired callback for {cid}")
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """
        Get the current size of each agent's message queue.
        
        Returns:
            Dictionary of {agent_id: queue_size}
        """
        with self.queue_lock:
            return {agent_id: q.qsize() for agent_id, q in self.queues.items()}
    
    def reset(self) -> None:
        """Reset the message bus to its initial state."""
        with self.queue_lock:
            for q in self.queues.values():
                while not q.empty():
                    try:
                        q.get_nowait()
                    except Exception:
                        pass
            
        with self.subscription_lock:
            self.subscriptions.clear()
            
        with self.callback_lock:
            self.response_callbacks.clear()
            
        self.logger.info("Message bus reset")


# Global instance for singleton access
_global_message_bus = None

def get_message_bus() -> MessageBus:
    """
    Get the global message bus instance.
    
    Returns:
        Global MessageBus instance
    """
    global _global_message_bus
    if _global_message_bus is None:
        _global_message_bus = MessageBus()
    return _global_message_bus

def reset_message_bus() -> None:
    """
    Reset the global message bus instance.
    
    This is useful for testing and for starting fresh in new sessions.
    """
    global _global_message_bus
    _global_message_bus = None
    logging.getLogger('core.message_bus').info("Message bus reset")
