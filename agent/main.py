import os
import json
import anthropic
from datetime import datetime
import pytz

from agent.prompts import build_system_prompt
from agent.tools import TOOL_DEFINITIONS, dispatch_tool, get_client
from agent.risk import RiskGuard
from data.portfolio import log_cycle_summary


def run_trading_cycle() -> dict:
    """
    One full trading cycle: research → stop-loss enforcement → decide → act → log.
    Returns a summary dict.
    """
    client = get_client()
    guard = RiskGuard(client)

    et = pytz.timezone("America/New_York")
    now_et = datetime.now(et)
    print(f"\n{'='*60}")
    print(f"Trading cycle starting at {now_et.strftime('%Y-%m-%d %H:%M:%S ET')}")
    print(f"{'='*60}")

    # Enforce stop-losses before calling the LLM
    closed = guard.enforce_stop_losses()
    if closed:
        print(f"Stop-loss triggered for: {[c['symbol'] for c in closed]}")

    # Build context message for this cycle
    is_open = client.is_market_open()
    market_status = "OPEN" if is_open else "CLOSED"
    user_message = f"""
Market status: {market_status}
Current time: {now_et.strftime('%I:%M %p ET on %A, %B %d, %Y')}
Stop-losses enforced this cycle: {closed if closed else 'none'}

Run your full trading cycle now:
1. Check portfolio and positions
2. Research opportunities (movers, earnings, news)
3. Make decisions and execute trades
4. Log each trade with reasoning

Be aggressive. Look for high-conviction setups.
""".strip()

    anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = [{"role": "user", "content": user_message}]
    system = build_system_prompt()

    cycle_actions = []
    iteration = 0
    max_iterations = 30

    while iteration < max_iterations:
        iteration += 1
        print(f"\n[Iteration {iteration}] Calling Claude...")

        response = anthropic_client.messages.create(
            model="claude-opus-4-7",
            max_tokens=8096,
            system=system,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Append assistant response to messages
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            print("[Agent] Cycle complete.")
            final_text = next(
                (b.text for b in response.content if hasattr(b, "text")),
                "No summary provided."
            )
            print(f"\n[Agent Summary]\n{final_text}")
            # Post cycle summary to Vercel dashboard
            try:
                acct = client.get_account()
                session = client.get_market_session()
                log_cycle_summary(
                    reasoning=final_text,
                    actions_taken=cycle_actions,
                    portfolio_state=acct,
                    session=session,
                )
            except Exception:
                pass
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_name = block.name
                tool_inputs = block.input
                print(f"  → Tool: {tool_name}({json.dumps(tool_inputs, default=str)[:120]})")

                try:
                    result = dispatch_tool(tool_name, tool_inputs)
                except Exception as e:
                    result = f"ERROR: {e}"
                    print(f"  ✗ Error: {e}")

                print(f"  ← Result: {str(result)[:200]}")

                if tool_name in ("place_market_order", "place_limit_order", "close_position"):
                    cycle_actions.append({"tool": tool_name, "inputs": tool_inputs, "result": result})

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })

            messages.append({"role": "user", "content": tool_results})

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "actions": cycle_actions,
        "stop_losses_enforced": closed,
        "iterations": iteration,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    result = run_trading_cycle()
    print(f"\nCycle result: {json.dumps(result, default=str, indent=2)}")
