"""Example Microsoft Teams notification hook.

This demonstrates how to create a hook that sends notifications to Microsoft Teams
after reports are generated.

Setup:
    1. In Microsoft Teams, navigate to the channel where you want notifications
    2. Click the "..." menu and select "Connectors"
    3. Find "Incoming Webhook" and click "Configure"
    4. Give it a name (e.g., "Test Reports") and click "Create"
    5. Copy the webhook URL
    6. Set the TEAMS_WEBHOOK_URL environment variable:
       export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/..."

Usage:
    # Import this module to register the hook
    import examples.hooks.teams_notifier

    # The @register_hook decorator automatically registers it
    # It will be called automatically at the post_write hook point
"""

import logging
import os
from typing import Any

from qa_report_generator.plugins import register_hook

logger = logging.getLogger(__name__)

# Pass rate thresholds for color coding
PASS_RATE_EXCELLENT = 90.0  # Green threshold
PASS_RATE_WARNING = 75.0  # Orange threshold

# Try to import requests, set to None if not available
try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]


def _get_theme_color(pass_rate: float) -> str:
    """Get theme color based on pass rate.

    Args:
        pass_rate: Pass rate as percentage (0-100)

    Returns:
        Hex color code for Teams message card

    """
    if pass_rate >= PASS_RATE_EXCELLENT:
        return "00FF00"  # Green - excellent
    if pass_rate >= PASS_RATE_WARNING:
        return "FFA500"  # Orange - warning
    return "FF0000"  # Red - critical


@register_hook("post_write")
def notify_teams(context: dict[str, Any]) -> None:
    """Send Microsoft Teams notification after reports are written.

    Args:
        context: Hook context containing:
            - summary_path: Path to summary report
            - signoff_path: Path to sign-off report
            - facts: ReportFacts object
            - timestamp: Generation timestamp

    """
    logger.info("Teams notification hook triggered")

    # Check if webhook URL is configured
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("TEAMS_WEBHOOK_URL not configured, skipping Teams notification. See examples/hooks/teams_notifier.py for setup instructions.")
        return

    # Extract context data
    summary_path = context.get("summary_path")
    signoff_path = context.get("signoff_path")
    facts = context.get("facts")

    if not facts:
        logger.warning("No facts in context, skipping Teams notification")
        return

    # Build notification message using MessageCard format
    metrics = facts.metrics
    pass_rate = metrics.pass_rate.formatted
    pass_rate_value = metrics.pass_rate.value

    # Prepare message card
    message = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": "Test Report Generated",
        "themeColor": _get_theme_color(pass_rate_value),
        "sections": [
            {
                "activityTitle": "📊 Test Report Generated",
                "activitySubtitle": f"Pass Rate: {pass_rate}",
                "facts": [
                    {"name": "Total Tests", "value": str(metrics.total)},
                    {"name": "Passed", "value": f"{metrics.passed} ✅"},
                    {"name": "Failed", "value": f"{metrics.failed} ❌"},
                    {"name": "Errors", "value": f"{metrics.errors} 🔥"},
                    {"name": "Skipped", "value": f"{metrics.skipped} ⏭️"},
                    {"name": "Pass Rate", "value": pass_rate},
                ],
            }
        ],
    }

    # Add report paths if available
    if summary_path or signoff_path:
        message["sections"].append(
            {
                "title": "📄 Generated Reports",
                "facts": [
                    {"name": "Summary Report", "value": str(summary_path or "N/A")},
                    {"name": "Sign-off Report", "value": str(signoff_path or "N/A")},
                ],
            }
        )

    # Send notification
    if requests is None:
        logger.error("requests library not installed. Install with: pip install requests")
        return

    try:
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
        logger.info("Successfully sent Teams notification")
    except requests.exceptions.RequestException:
        logger.exception("Failed to send Teams notification")
