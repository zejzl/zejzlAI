import asyncio
from src.usage_analytics import UsageAnalytics

async def test_analytics():
    analytics = UsageAnalytics()

    # Test usage report
    print('Generating usage report...')
    report = await analytics.get_usage_report(days=7)
    print(f'Period: {report.period}')
    print(f'Total requests: {report.total_requests}')
    print(f'Total tokens: {report.total_tokens}')
    print(f'Total cost: ${report.total_cost_usd:.4f}')
    print(f'Average response time: {report.avg_response_time:.2f}s')
    print(f'Success rate: {report.success_rate:.2%}')
    print(f'Providers: {list(report.provider_breakdown.keys())}')

    # Test cost analysis
    print('\nGenerating cost analysis...')
    cost_analysis = await analytics.get_cost_analysis(days=30)
    print(f'Period: {cost_analysis.period_days} days')
    print(f'Total cost: ${cost_analysis.total_cost:.4f}')
    print(f'Avg daily cost: ${cost_analysis.avg_daily_cost:.4f}')
    print(f'Avg request cost: ${cost_analysis.avg_request_cost:.6f}')
    print(f'Most expensive provider: {cost_analysis.most_expensive_provider}')
    print(f'Cost trend: {cost_analysis.cost_trend}')
    print(f'Projected monthly cost: ${cost_analysis.projected_monthly_cost:.2f}')

    # Test top expensive requests
    print('\nTop expensive requests:')
    expensive = await analytics.get_top_expensive_requests(3)
    for req in expensive:
        print(f'  ${req["cost_usd"]:.4f} - {req["content"][:50]}...')

    print('\nAnalytics test completed successfully!')

if __name__ == "__main__":
    asyncio.run(test_analytics())