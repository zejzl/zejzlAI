import asyncio
from ai_framework import TokenUsage
from src.cost_calculator import CostCalculator

def test_cost_calculation():
    """Test the cost calculator directly"""

    # Test ChatGPT pricing
    usage = TokenUsage(
        provider='ChatGPT',
        model='gpt-3.5-turbo',
        prompt_tokens=1000,
        completion_tokens=500
    )
    cost = CostCalculator.calculate_cost(usage)
    print(f'ChatGPT GPT-3.5 cost for 1000 input + 500 output tokens: ${cost:.6f}')
    expected = (0.0015 * 1000/1000) + (0.002 * 500/1000)
    print(f'Expected: ${expected:.6f}')

    # Test Claude pricing
    usage2 = TokenUsage(
        provider='Claude',
        model='claude-3-5-sonnet-20241022',
        prompt_tokens=2000,
        completion_tokens=1000
    )
    cost2 = CostCalculator.calculate_cost(usage2)
    print(f'Claude 3.5 Sonnet cost for 2000 input + 1000 output tokens: ${cost2:.6f}')
    expected2 = (0.003 * 2000/1000) + (0.015 * 1000/1000)
    print(f'Expected: ${expected2:.6f}')

    # Test Grok pricing
    usage3 = TokenUsage(
        provider='Grok',
        model='grok-1',
        prompt_tokens=500,
        completion_tokens=300
    )
    cost3 = CostCalculator.calculate_cost(usage3)
    print(f'Grok cost for 500 input + 300 output tokens: ${cost3:.6f}')

    print('Cost calculation test completed successfully!')

if __name__ == "__main__":
    test_cost_calculation()