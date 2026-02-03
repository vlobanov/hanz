from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

from config import GOOGLE_API_KEY, LLM_MODEL
from prompts import SYSTEM_PROMPT
from tools.study import get_study_tools


class ConversationAgent:
    """LangChain agent for German B1 exam tutoring."""

    def __init__(self):
        self._llm = None
        self._agent = None

        # Store conversation history per user
        self.conversations: dict[int, list] = {}

    @property
    def llm(self):
        """Lazy initialization of the LLM."""
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=LLM_MODEL,
                google_api_key=GOOGLE_API_KEY,
            )
        return self._llm

    @property
    def tools(self):
        """Get study tools."""
        return get_study_tools()

    @property
    def agent(self):
        """Lazy initialization of the agent."""
        if self._agent is None:
            self._agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                prompt=ChatPromptTemplate.from_messages(
                    [
                        ("system", SYSTEM_PROMPT),
                        MessagesPlaceholder(variable_name="messages"),
                    ]
                ),
            )
        return self._agent

    def get_history(self, user_id: int) -> list:
        """Get conversation history for a user."""
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]

    async def chat(self, user_id: int, message: str) -> str:
        """Process a message and return the agent's response."""
        history = self.get_history(user_id)

        # Add user message to history
        history.append(HumanMessage(content=message))

        # Invoke the agent
        result = await self.agent.ainvoke({"messages": history})

        # Extract the response
        response_messages = result["messages"]

        # Find the last AI message (the final response)
        ai_response = None
        for msg in reversed(response_messages):
            if isinstance(msg, AIMessage) and msg.content:
                content = msg.content
                # Handle structured content (list of blocks)
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if isinstance(block, str):
                            text_parts.append(block)
                        elif isinstance(block, dict) and "text" in block:
                            text_parts.append(block["text"])
                    ai_response = "".join(text_parts)
                elif isinstance(content, str):
                    ai_response = content
                else:
                    ai_response = str(content)
                break

        if not ai_response:
            ai_response = "Entschuldigung, ich habe keine Antwort. Kannst du das wiederholen?"

        # Update history with the full conversation
        self.conversations[user_id] = response_messages

        return ai_response

    def clear_history(self, user_id: int) -> None:
        """Clear conversation history for a user."""
        self.conversations[user_id] = []


# Global agent instance
agent = ConversationAgent()
