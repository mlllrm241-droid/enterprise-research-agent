from dotenv import load_dotenv

load_dotenv()

from app.agents.baseline_agent import build_baseline_agent


def main():
    agent = build_baseline_agent()

    print("=" * 60)
    print("Enterprise Research Agent")
    print("Baseline Version")
    print("=" * 60)

    while True:
        query = input("\n请输入研究任务：")

        if query.lower() in ["exit", "quit", "q"]:
            break

        # result = agent.invoke(
        #     {
        #         "messages": [
        #             {
        #                 "role": "user",
        #                 "content": query,
        #             }
        #         ]
        #     }
        # )

        # final_message = result["messages"][-1]

        # print("\nAgent：")
        # print(final_message.content)

        for chunk in agent.stream(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": query,
                    }
                ]
            },
            stream_mode="updates",
        ):
            print(chunk)
            print("=" * 80)


if __name__ == "__main__":
    main()