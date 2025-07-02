from typing import Dict, Any, List, Generator
import json
import logging
from datetime import datetime

from langchain_core.messages import HumanMessage
from langgraph.graph import END, StateGraph

from strategies.risk.risk_manager import risk_management_agent
from strategies.portfolio.portfolio_manager import portfolio_management_agent
from core.exceptions import BusinessLogicError
from utils.analysts import get_analyst_nodes
from graph.state import AgentState

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
        """Execute workflow with progress updates."""
        
        # Progress for each analyst
        for i, analyst in enumerate(selected_analysts):
            logger.debug(f"Running {analyst} analysis")
            
            # Yield progress start
            progress_event = {
                "type": "progress",
                "stage": "analysis",
                "message": f"Starting {analyst} analysis...",
                "progress": int(20 + (i * 40 / len(selected_analysts))),
                "current_analyst": analyst,
                "analyst_progress": f"{i + 1}/{len(selected_analysts)}",
                "timestamp": datetime.now().isoformat()
            }
            yield json.dumps(progress_event) + "\n"
            
            # Execute analyst with intermediate progress updates
            try:
                # Yield intermediate progress updates during execution
                yield from self._execute_analyst_with_progress(agent, state, analyst, i, len(selected_analysts))
                
            except Exception as e:
                logger.error(f"Error in {analyst} analysis: {str(e)}")
                error_event = {
                    "type": "error",
                    "message": f"Error in {analyst} analysis: {str(e)}",
                    "stage": "analysis",
                    "current_analyst": analyst,
                    "timestamp": datetime.now().isoformat()
                }
                yield json.dumps(error_event) + "\n"
                raise
        
        # Risk management
        logger.debug("Running risk management")
        risk_event = {
            "type": "progress",
            "stage": "risk_management",
            "message": "Starting risk management...",
            "progress": 70,
            "timestamp": datetime.now().isoformat()
        }
        yield json.dumps(risk_event) + "\n"
        
        try:
            state = agent.invoke(state)
            
            risk_event["message"] = "Completed risk management"
            risk_event["progress"] = 85
            yield json.dumps(risk_event) + "\n"
        except Exception as e:
            logger.error(f"Error in risk management: {str(e)}")
            error_event = {
                "type": "error",
                "message": f"Error in risk management: {str(e)}",
                "stage": "risk_management",
                "timestamp": datetime.now().isoformat()
            }
            yield json.dumps(error_event) + "\n"
            raise
        
        # Portfolio management
        logger.debug("Running portfolio management")
        portfolio_event = {
            "type": "progress",
            "stage": "portfolio_management",
            "message": "Starting portfolio management...",
            "progress": 90,
            "timestamp": datetime.now().isoformat()
        }
        yield json.dumps(portfolio_event) + "\n"
        
        try:
            state = agent.invoke(state)
            
            portfolio_event["message"] = "Completed portfolio management"
            portfolio_event["progress"] = 95
            yield json.dumps(portfolio_event) + "\n"
        except Exception as e:
            logger.error(f"Error in portfolio management: {str(e)}")
            error_event = {
                "type": "error",
                "message": f"Error in portfolio management: {str(e)}",
                "stage": "portfolio_management",
                "timestamp": datetime.now().isoformat()
            }
            yield json.dumps(error_event) + "\n"
            raise
        
        # Final results
        logger.debug("Yielding final results")
        result_event = {
            "type": "result",
            "data": {
                "decisions": self._parse_response(state["messages"][-1].content),
                "analyst_signals": state["data"]["analyst_signals"],
            },
            "timestamp": datetime.now().isoformat()
        }
        yield json.dumps(result_event) + "\n"
    
    def _execute_analyst_with_progress(
        self,
        agent,
        state: Dict[str, Any],
        analyst: str,
        analyst_index: int,
        total_analysts: int
    ) -> Generator[str, None, None]:
        """Execute a single analyst with granular progress updates."""
        
        # Calculate progress range for this analyst
        start_progress = int(20 + (analyst_index * 40 / total_analysts))
        end_progress = int(20 + ((analyst_index + 1) * 40 / total_analysts))
        
        # Yield progress for data fetching phase
        progress_event = {
            "type": "progress",
            "stage": "analysis",
            "message": f"Running {analyst} analysis (fetching data)...",
            "progress": start_progress + 5,
            "current_analyst": analyst,
            "analyst_progress": f"{analyst_index + 1}/{total_analysts}",
            "timestamp": datetime.now().isoformat()
        }
        yield json.dumps(progress_event) + "\n"
        
        # Yield progress for analysis phase
        progress_event["message"] = f"Running {analyst} analysis (processing data)..."
        progress_event["progress"] = start_progress + 15
        yield json.dumps(progress_event) + "\n"
        
        # Execute the analyst
        state = agent.invoke(state)
        
        # Yield progress completion
        progress_event["message"] = f"Completed {analyst} analysis"
        progress_event["progress"] = end_progress
        yield json.dumps(progress_event) + "\n"
    
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