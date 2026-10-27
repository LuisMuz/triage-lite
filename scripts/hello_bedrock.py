"""Week 0 check: send "hello" to a Claude model on Bedrock and print usage and stop_reason.

Run with your SSO profile (credentials come from the standard AWS chain, never from keys):

    AWS_PROFILE=triage uv run --python 3.12 --with 'anthropic[bedrock]' \
        scripts/hello_bedrock.py --model global.anthropic.claude-haiku-4-5-20251001-v1:0
"""

import argparse

from anthropic import AnthropicBedrock

MAX_TOKENS = 64


def main() -> None:
    """Parse arguments, call the model once and print what the plan's Week 0 gate asks for."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model", required=True, help="Bedrock model or inference profile ID")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    client = AnthropicBedrock(aws_region=args.region)
    message = client.messages.create(
        model=args.model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": "hello"}],
    )

    print("reply:      ", "".join(b.text for b in message.content if b.type == "text"))
    print("stop_reason:", message.stop_reason)
    print("usage:      ", message.usage.model_dump_json())


if __name__ == "__main__":
    main()
