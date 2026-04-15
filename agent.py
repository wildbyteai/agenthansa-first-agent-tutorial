import os
import re
import requests
from pprint import pprint

BASE_URL = "https://www.agenthansa.com"
API_KEY = os.environ.get("AGENTHANSA_API_KEY", "YOUR_API_KEY_HERE")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def checkin():
    r = requests.post(f"{BASE_URL}/api/agents/checkin", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def red_packets():
    r = requests.get(f"{BASE_URL}/api/red-packets", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def get_packet_challenge(packet_id: str):
    r = requests.get(f"{BASE_URL}/api/red-packets/{packet_id}/challenge", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def naive_math_solver(question: str) -> str:
    nums = list(map(int, re.findall(r"-?\d+", question)))
    q = question.lower()
    if len(nums) >= 2:
        if any(word in q for word in ["total", "sum", "altogether", "in all", "more"]):
            return str(sum(nums))
        if any(word in q for word in ["left", "remain", "gives away", "give away"]):
            if len(nums) == 2:
                return str(nums[0] - nums[1])
        if any(word in q for word in ["evenly", "per", "split"]):
            if len(nums) == 2 and nums[1] != 0:
                return str(nums[0] // nums[1])
    raise ValueError(f"Could not solve challenge automatically: {question}")


def join_packet(packet_id: str):
    challenge = get_packet_challenge(packet_id)
    question = challenge.get("question", "")
    answer = naive_math_solver(question)
    r = requests.post(
        f"{BASE_URL}/api/red-packets/{packet_id}/join",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"answer": answer},
        timeout=30,
    )
    r.raise_for_status()
    return {"challenge": challenge, "answer": answer, "result": r.json()}


def list_quests():
    r = requests.get(f"{BASE_URL}/api/alliance-war/quests", headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("quests", data)


def submit_quest(quest_id: str, content: str, proof_url: str | None = None, challenge_answer: str | None = None):
    payload = {"content": content}
    if proof_url:
        payload["proof_url"] = proof_url
    if challenge_answer:
        payload["challenge_answer"] = challenge_answer
    r = requests.post(
        f"{BASE_URL}/api/alliance-war/quests/{quest_id}/submit",
        headers={**HEADERS, "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def set_fluxa_agent_id(fluxa_agent_id: str):
    r = requests.put(
        f"{BASE_URL}/api/agents/fluxa-wallet",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={"fluxa_agent_id": fluxa_agent_id},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def main():
    print("=== Daily check-in ===")
    pprint(checkin())

    print("\n=== Red packet status ===")
    packets = red_packets()
    pprint(packets)

    active = packets.get("active", [])
    if active:
        packet = active[0]
        packet_id = packet["id"]
        print(f"\n=== Joining active packet {packet_id} ===")
        pprint(join_packet(packet_id))

    print("\n=== Open quests ===")
    quests = [q for q in list_quests() if q.get("status") == "open"]
    for q in quests[:5]:
        print(f"- {q.get('id')} | {q.get('title')} | status={q.get('status')}")


if __name__ == "__main__":
    main()
