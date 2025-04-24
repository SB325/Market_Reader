## Imports
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from langchain import hub
from langchain.agents import 
from langchain_ollama import OllamaLLM

from langchain.agents import initialize_agent
from langchain.agents import Tool

from tool_definitions import get_news_articles, get_technical_info, get_filing_info
from tool_schemas import news_article_model, technical_model, fundamentals_model
from dotenv import load_dotenv

## Env Variables
load_dotenv(override=True)
LLM_MODEL = os.environ.get("LLM_MODEL")

## LLM Framework
llm = OllamaLLM(model=LLM_MODEL)

# Prompt Template
prompt = hub.pull("hwchase17/openai-functions-agent")

# Tools
news_tool = Tool(
    name="get_news_for_company",
    func=get_news_articles,
    description="given the name of a company and starting date, return historical news articles",
    args_schema = news_article_model
)
technicals_tool = Tool(
    name="get_company_stock_price_and_volume_data",
    func=get_technical_info,
    description="given the name of a company and starting date, return the daily price per share and volume information",
    args_schema = technical_model
)
fundamentals_tool = Tool(
    name="get_SEC_filing_reports_for_company",
    func=get_filing_info,
    description="given the name of a company and starting date, return the relevant SEC filing information.",
    args_schema = fundamentals_model
)

tools = [
    news_tool,
    technicals_tool,
    fundamentals_tool
]

# Define logic that will be used to determine which conditional edge to go down
def should_continue(data_:
    if isinstance(data['agent_outcome'], AgentFinish)):
        return 
            "exit"
        else:
            return "continue"

# Define the Langgraph
from langgraph.graph import END, Graph

workflow = Graph()
workflow.add_node("agent", agent)
workflow.add_node("tools", execute_tools)
workflow.set_entry_point("agent")
workkflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "exit": END
    }
)
workflow.add_edge('tools', 'agent')
chain = workflow.compile()

result = chain.invoke({
        "input": "What has been AAPL's daily closing price between Feb 20th, 2025 and March 10th 2025?",
        "intermediate_steps": []
    }
)
output = result['agent_coutcome'].return_values["output"]
print(output)