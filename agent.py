from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

from config import GOOGLE_API_KEY, LLM_MODEL
from prompts import SYSTEM_PROMPT
from tools.grammar import get_grammar_tools


class ConversationAgent:
    """LangChain agent for German tutoring conversations."""

    def __init__(self):
        self._llm = None
        self._agent = None

        # Store conversation history per user
        self.conversations: dict[int, list] = {}

        # Store user preferences
        self.user_preferences: dict[int, dict] = {}

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
        """Get grammar tools."""
        return get_grammar_tools()

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

    def get_preferences(self, user_id: int) -> dict:
        """Get preferences for a user."""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                "voice_enabled": False,
                "level": "A1",
                "language": "mixed",  # german, english, or mixed
            }
        return self.user_preferences[user_id]

    def set_preference(self, user_id: int, key: str, value) -> None:
        """Set a preference for a user."""
        prefs = self.get_preferences(user_id)
        prefs[key] = value

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
                ai_response = msg.content
                break

        if ai_response is None:
            ai_response = "Entschuldigung, ich habe keine Antwort. Kannst du das wiederholen?"

        # Update history with the full conversation
        self.conversations[user_id] = response_messages

        return ai_response

    def clear_history(self, user_id: int) -> None:
        """Clear conversation history for a user."""
        self.conversations[user_id] = []


# Global agent instance
agent = ConversationAgent()
