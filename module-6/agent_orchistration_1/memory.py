
import os

from langchain.agents import create_agent
from langchain.tools import tool


# ------------------------------------------
# SAMPLE DATA
# ------------------------------------------

# 1. EPISODIC MEMORY: past customer experiences
episodic_memory = {
    "Ravi": [
        "Last week, Ravi reported a delayed order.",
        "A refund of Rs. 200 was offered for an earlier delay."
    ]
}


# 2. SEMANTIC MEMORY: general business knowledge
semantic_memory = {
    "refund_policy": (
        "An eligible delayed order may qualify for a refund. "
        "Eligibility must be verified before requesting a refund."
    ),
    "delivery_policy": (
        "Customers can check the latest delivery status "
        "using their order ID."
    )
}


# Mock business database used by the demo
orders = {
    "ORD101": {
        "customer": "Ravi",
        "status": "Delayed",
        "refund_eligible": True
    },
    "ORD102": {
        "customer": "Ravi",
        "status": "Delivered",
        "refund_eligible": False
    }
}


# ------------------------------------------
# EPISODIC MEMORY TOOL
# ------------------------------------------

@tool
def recall_customer_history(customer_name: str) -> str:
    """Retrieve past interactions for a customer."""

    events = episodic_memory.get(customer_name, [])

    if not events:
        return f"No past interactions found for {customer_name}."

    return "\n".join(events)


# ------------------------------------------
# SEMANTIC MEMORY TOOLS
# ------------------------------------------

@tool
def retrieve_refund_policy() -> str:
    """Retrieve the company's refund policy."""

    return semantic_memory["refund_policy"]


@tool
def retrieve_delivery_policy() -> str:
    """Retrieve the company's delivery policy."""

    return semantic_memory["delivery_policy"]


# ------------------------------------------
# PROCEDURAL MEMORY TOOL
# ------------------------------------------

@tool
def handle_delayed_order(order_id: str) -> str:
    """
    Follow the procedure for handling a delayed order.
    Verify the order and eligibility before requesting a refund.
    """

    # Step 1: Find and verify the order
    order = orders.get(order_id)

    if order is None:
        return "Order not found. Ask the customer to verify the order ID."

    # Step 2: Check order status
    if order["status"] != "Delayed":
        return (
            f"Order {order_id} is {order['status']}. "
            "The delayed-order refund procedure cannot proceed."
        )

    # Step 3: Check refund eligibility
    if not order["refund_eligible"]:
        return f"Order {order_id} is not eligible for a refund."

    # Step 4: Simulate submission, not an actual payment/refund
    return (
        f"Order {order_id} was verified and is eligible. "
        "A refund request has been submitted for approval. "
        "No money has been refunded by this demo."
    )


# ------------------------------------------
# CREATE THE LANGCHAIN AGENT
# ------------------------------------------

from dotenv import load_dotenv

load_dotenv()

print("API Key is:  ", os.getenv("OPENAI_API_KEY"))

if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError(
        "Please set the OPENAI_API_KEY environment variable."
    )

agent = create_agent(
    model="openai:gpt-4o-mini",
    tools=[
        recall_customer_history,
        retrieve_refund_policy,
        retrieve_delivery_policy,
        handle_delayed_order
    ],
    system_prompt="""
    You are a customer support AI agent.

    You have access to three kinds of memory:

    1. Episodic memory:
       Use recall_customer_history to retrieve past events.

    2. Semantic memory:
       Use the policy tools to retrieve company facts and rules.

    3. Procedural memory:
       Use handle_delayed_order to follow the delayed-order
       verification and refund-request procedure.

    Instructions:
    - Understand the customer's request before choosing tools.
    - Use the available tools when they are relevant.
    - Never invent customer history, order status, or eligibility.
    - Never claim that money was refunded unless a trusted system
      confirms the actual refund.
    - Explain the result clearly and politely.
    """
)


# ------------------------------------------
# RUN THE AGENT
# ------------------------------------------

if __name__ == "__main__":

    user_message = """
    I am Ravi. My order ORD101 is delayed again.
    Can you check my history and help me?
    """

    result = agent.invoke({
        "messages": [
            {"role": "user", "content": user_message}
        ]
    })

    print("\n========== AI AGENT RESPONSE ==========\n")
    print(result["messages"][-1].content)
