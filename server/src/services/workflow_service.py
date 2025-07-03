from typing import Dict, Any, List, Generator
import json
import logging
from datetime import datetime

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from src.strategies.risk.risk_manager import risk_management_agent
from src.strategies.portfolio.portfolio_manager import portfolio_management_agent
from src.core.exceptions import BusinessLogicError
from src.utils.analysts import get_analyst_nodes
from src.graph.state import AgentState

logger = logging.getLogger(__name__)

class WorkflowService:
    """Service for managing analysis workflows."""
    
    def __init__(self):
        self._compiled_workflows = {}
    
    def execute_analysis_workflow(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        portfolio: Dict[str, Any],
        selected_analysts: List[str],
        show_reasoning: bool = False,
        model_name: str = "gpt-4o",
        model_provider: str = "OpenAI"
    ) -> Generator[str, None, None]:
        """Execute the complete analysis workflow."""
        
        # Debug yield to ensure generator is working
        debug_event = {
            "type": "debug",
            "message": "Workflow generator started",
            "timestamp": datetime.now().isoformat()
        }
        yield json.dumps(debug_event) + "\n"
        
        try:
            # Create or get compiled workflow
            workflow_key = "_".join(sorted(selected_analysts))
            if workflow_key not in self._compiled_workflows:
                workflow = self._create_workflow(selected_analysts)
                self._compiled_workflows[workflow_key] = workflow.compile()
            
            agent = self._compiled_workflows[workflow_key]
            
            # Initialize state
            state = self._create_initial_state(
                tickers, portfolio, start_date, end_date,
                show_reasoning, model_name, model_provider
            )
            
            # Execute workflow with progress tracking
            yield from self._execute_with_progress(agent, state, selected_analysts)
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}", exc_info=True)
            raise BusinessLogicError(f"Workflow execution failed: {str(e)}")
    
    def _create_workflow(self, selected_analysts: List[str]) -> StateGraph:
        """Create workflow graph with selected analysts."""
        workflow = StateGraph(AgentState)
        workflow.add_node("start_node", self._start_node)
        
        # Get analyst nodes
        analyst_nodes = get_analyst_nodes()
        
        # Add selected analyst nodes
        for analyst_key in selected_analysts:
            if analyst_key in analyst_nodes:
                node_name, node_func = analyst_nodes[analyst_key]
                workflow.add_node(node_name, node_func)
                workflow.add_edge("start_node", node_name)
        
        # Add management nodes
        workflow.add_node("risk_management_agent", risk_management_agent)
        workflow.add_node("portfolio_management_agent", portfolio_management_agent)
        
        # Connect analysts to risk management
        for analyst_key in selected_analysts:
            if analyst_key in analyst_nodes:
                node_name = analyst_nodes[analyst_key][0]
                workflow.add_edge(node_name, "risk_management_agent")
        
        workflow.add_edge("risk_management_agent", "portfolio_management_agent")
        workflow.add_edge("portfolio_management_agent", END)
        
        workflow.set_entry_point("start_node")
        return workflow
    
    def _create_initial_state(
        self,
        tickers: List[str],
        portfolio: Dict[str, Any],
        start_date: str,
        end_date: str,
        show_reasoning: bool,
        model_name: str,
        model_provider: str
    ) -> Dict[str, Any]:
        """Create initial state for workflow execution."""
        return {
            "messages": [
                HumanMessage(
                    content="Make trading decisions based on the provided data."
                )
            ],
            "data": {
                "tickers": tickers,
                "portfolio": portfolio,
                "start_date": start_date,
                "end_date": end_date,
                "analyst_signals": {},
            },
            "metadata": {
                "show_reasoning": show_reasoning,
                "model_name": model_name,
                "model_provider": model_provider,
            },
        }
    
    def _execute_with_progress(
        self,
        agent,
        state: Dict[str, Any],
        selected_analysts: List[str]
    ) -> Generator[str, None, None]:
        """Execute workflow with progress updates using LangGraph's streaming API."""
        
        # Initial progress
        progress_event = {
            "type": "progress",
            "stage": "initialization",
            "message": "Starting analysis workflow...",
            "progress": 10,
            "timestamp": datetime.now().isoformat()
        }
        yield json.dumps(progress_event) + "\n"
        
        try:
            # Execute the workflow using LangGraph's streaming API
            logger.debug("Executing workflow with LangGraph streaming")
            
            # Track progress through the workflow
            total_steps = len(selected_analysts) + 3  # analysts + risk + portfolio + start
            current_step = 0
            
            # Use LangGraph's stream method with "custom" stream_mode to get custom progress updates
            for step in agent.stream(state, stream_mode="custom"):
                current_step += 1
                progress_percent = int(10 + (current_step * 80 / total_steps))
                
                # Extract the node name from the step
                if step and len(step) > 0:
                    node_name = list(step.keys())[0]
                    
                    if node_name == "start_node":
                        progress_event = {
                            "type": "progress",
                            "stage": "start",
                            "message": "Initializing workflow...",
                            "progress": progress_percent,
                            "timestamp": datetime.now().isoformat()
                        }
                    elif node_name.endswith("_agent") and node_name != "risk_management_agent" and node_name != "portfolio_management_agent":
                        # This is an analyst step
                        analyst_name = node_name.replace("_agent", "")
                        progress_event = {
                            "type": "progress",
                            "stage": "analysis",
                            "message": f"Running {analyst_name} analysis...",
                            "progress": progress_percent,
                            "current_analyst": analyst_name,
                            "analyst_progress": f"{current_step}/{total_steps}",
                            "timestamp": datetime.now().isoformat()
                        }
                    elif node_name == "risk_management_agent":
                        progress_event = {
                            "type": "progress",
                            "stage": "risk_management",
                            "message": "Running risk management...",
                            "progress": progress_percent,
                            "timestamp": datetime.now().isoformat()
                        }
                    elif node_name == "portfolio_management_agent":
                        progress_event = {
                            "type": "progress",
                            "stage": "portfolio_management",
                            "message": "Running portfolio management...",
                            "progress": progress_percent,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        progress_event = {
                            "type": "progress",
                            "stage": "execution",
                            "message": f"Executing {node_name}...",
                            "progress": progress_percent,
                            "timestamp": datetime.now().isoformat()
                        }
                    
                    yield json.dumps(progress_event) + "\n"
            
            # Yield completion
            completion_event = {
                "type": "progress",
                "stage": "completion",
                "message": "Analysis completed",
                "progress": 95,
                "timestamp": datetime.now().isoformat()
            }
            yield json.dumps(completion_event) + "\n"
            
            # Get the final results using invoke
            final_state = agent.invoke(state)
            
            # Final results
            logger.debug("Yielding final results")
            result_event = {
                "type": "result",
                "data": {
                    "decisions": self._parse_response(final_state["messages"][-1].content),
                    "analyst_signals": final_state["data"]["analyst_signals"],
                },
                "timestamp": datetime.now().isoformat()
            }
            yield json.dumps(result_event) + "\n"
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}")
            error_event = {
                "type": "error",
                "message": f"Error in workflow execution: {str(e)}",
                "stage": "execution",
                "timestamp": datetime.now().isoformat()
            }
            yield json.dumps(error_event) + "\n"
            raise
    
    def _start_node(self, state: AgentState) -> AgentState:
        """Initialize the workflow with the input message."""
        return state
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response safely."""
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decoding error: {e}")
            return {"error": "Failed to parse response", "raw_response": response}
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return {"error": "Unexpected parsing error", "raw_response": response} 