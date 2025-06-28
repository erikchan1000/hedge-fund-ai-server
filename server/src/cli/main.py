#!/usr/bin/env python3
"""Command Line Interface for the AI Hedge Fund System."""

import sys
import argparse
from datetime import datetime
from dateutil.relativedelta import relativedelta
import questionary
from colorama import Fore, Style, init

from ..services.workflow_service import WorkflowService
from ..utils.analysts import ANALYST_ORDER
from ..llm.models import LLM_ORDER, OLLAMA_LLM_ORDER, get_model_info, ModelProvider
from ..utils.ollama import ensure_ollama_and_model
from ..utils.display import print_trading_output
from ..utils.visualize import save_graph_as_png

# Initialize colorama
init(autoreset=True)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the hedge fund trading system")
    parser.add_argument("--initial-cash", type=float, default=100000.0, help="Initial cash position. Defaults to 100000.0)")
    parser.add_argument("--margin-requirement", type=float, default=0.0, help="Initial margin requirement. Defaults to 0.0")
    parser.add_argument("--tickers", type=str, required=True, help="Comma-separated list of stock ticker symbols")
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD). Defaults to 3 months before end date",
    )
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to today")
    parser.add_argument("--show-reasoning", action="store_true", help="Show reasoning from each agent")
    parser.add_argument("--show-agent-graph", action="store_true", help="Show the agent graph")
    parser.add_argument("--ollama", action="store_true", help="Use Ollama for local LLM inference")
    
    return parser.parse_args()


def select_analysts():
    """Interactive analyst selection."""
    choices = questionary.checkbox(
        "Select your AI analysts.",
        choices=[questionary.Choice(display, value=value) for display, value in ANALYST_ORDER],
        instruction="\n\nInstructions: \n1. Press Space to select/unselect analysts.\n2. Press 'a' to select/unselect all.\n3. Press Enter when done to run the hedge fund.\n",
        validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not choices:
        print("\n\nInterrupt received. Exiting...")
        sys.exit(0)
    else:
        print(f"\nSelected analysts: {', '.join(Fore.GREEN + choice.title().replace('_', ' ') + Style.RESET_ALL for choice in choices)}\n")
        return choices


def select_model(use_ollama: bool):
    """Interactive model selection."""
    if use_ollama:
        print(f"{Fore.CYAN}Using Ollama for local LLM inference.{Style.RESET_ALL}")

        # Select from Ollama-specific models
        model_choice = questionary.select(
            "Select your Ollama model:",
            choices=[questionary.Choice(display, value=value) for display, value, _ in OLLAMA_LLM_ORDER],
            style=questionary.Style(
                [
                    ("selected", "fg:green bold"),
                    ("pointer", "fg:green bold"),
                    ("highlighted", "fg:green"),
                    ("answer", "fg:green bold"),
                ]
            ),
        ).ask()

        if not model_choice:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)

        # Ensure Ollama is installed, running, and the model is available
        if not ensure_ollama_and_model(model_choice):
            print(f"{Fore.RED}Cannot proceed without Ollama and the selected model.{Style.RESET_ALL}")
            sys.exit(1)

        model_provider = ModelProvider.OLLAMA.value
        print(f"\nSelected {Fore.CYAN}Ollama{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")
        
        return model_choice, model_provider
    else:
        # Use the standard cloud-based LLM selection
        model_choice = questionary.select(
            "Select your LLM model:",
            choices=[questionary.Choice(display, value=value) for display, value, _ in LLM_ORDER],
            style=questionary.Style(
                [
                    ("selected", "fg:green bold"),
                    ("pointer", "fg:green bold"),
                    ("highlighted", "fg:green"),
                    ("answer", "fg:green bold"),
                ]
            ),
        ).ask()

        if not model_choice:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)
        else:
            # Get model info using the helper function
            model_info = get_model_info(model_choice)
            if model_info:
                model_provider = model_info.provider.value
                print(f"\nSelected {Fore.CYAN}{model_provider}{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")
            else:
                model_provider = "Unknown"
                print(f"\nSelected model: {Fore.GREEN + Style.BRIGHT}{model_choice}{Style.RESET_ALL}\n")
            
            return model_choice, model_provider


def validate_dates(start_date: str = None, end_date: str = None):
    """Validate and process dates."""
    if start_date:
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Start date must be in YYYY-MM-DD format")

    if end_date:
        try:
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("End date must be in YYYY-MM-DD format")

    # Set the start and end dates
    end_date = end_date or datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        # Calculate 3 months before end_date
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")

    return start_date, end_date


def create_portfolio(tickers: list, initial_cash: float, margin_requirement: float):
    """Create initial portfolio structure."""
    return {
        "cash": initial_cash,  # Initial cash amount
        "margin_requirement": margin_requirement,  # Initial margin requirement
        "margin_used": 0.0,  # total margin usage across all short positions
        "positions": {
            ticker: {
                "long": 0,  # Number of shares held long
                "short": 0,  # Number of shares held short
                "long_cost_basis": 0.0,  # Average cost basis for long positions
                "short_cost_basis": 0.0,  # Average price at which shares were sold short
                "short_margin_used": 0.0,  # Dollars of margin used for this ticker's short
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,  # Realized gains from long positions
                "short": 0.0,  # Realized gains from short positions
            }
            for ticker in tickers
        },
    }


def run_hedge_fund_analysis(
    tickers: list,
    start_date: str,
    end_date: str,
    portfolio: dict,
    selected_analysts: list,
    model_name: str,
    model_provider: str,
    show_reasoning: bool = False
):
    """Run the hedge fund analysis using the service layer."""
    workflow_service = WorkflowService()
    
    # Execute analysis and get streaming results
    results = workflow_service.execute_analysis_workflow(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        selected_analysts=selected_analysts,
        show_reasoning=show_reasoning,
        model_name=model_name,
        model_provider=model_provider
    )
    
    # Display results
    print_trading_output(results)


def main():
    """Main CLI entry point."""
    try:
        args = parse_arguments()

        # Parse tickers from comma-separated string
        tickers = [ticker.strip() for ticker in args.tickers.split(",")]

        # Select analysts interactively
        selected_analysts = select_analysts()

        # Select model
        model_name, model_provider = select_model(args.ollama)

        # Validate dates
        start_date, end_date = validate_dates(args.start_date, args.end_date)

        # Create portfolio
        portfolio = create_portfolio(tickers, args.initial_cash, args.margin_requirement)

        # Show agent graph if requested
        if args.show_agent_graph:
            workflow_service = WorkflowService()
            workflow = workflow_service._create_workflow(selected_analysts)
            app = workflow.compile()
            
            file_path = ""
            for selected_analyst in selected_analysts:
                file_path += selected_analyst + "_"
            file_path += "graph.png"
            save_graph_as_png(app, file_path)

        # Run the hedge fund analysis
        run_hedge_fund_analysis(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            portfolio=portfolio,
            selected_analysts=selected_analysts,
            model_name=model_name,
            model_provider=model_provider,
            show_reasoning=args.show_reasoning
        )

    except KeyboardInterrupt:
        print("\n\nInterrupt received. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main() 