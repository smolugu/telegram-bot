
def format_ping_alert(
    instrument,
    direction,
    timestamp,
    zone_label,
    zone_low,
    zone_high,
    entry,
    stop,
    targets,
    risk_points,
    reward_risk,
):
    lines = [
        "⚡ PING TIME — FLUSH",
        "",
        f"{'🔻' if direction.upper() == 'BEARISH' else '🔺'} "
        f"{instrument} · {direction.title()}",
        f"🕒 {timestamp}",
        "",
        f"{zone_label}: {zone_low} – {zone_high}",
        f"Entry: {entry}",
        f"Stop: {stop}",
        "",
    ]

    for index, target in enumerate(targets, start=1):
        lines.append(f"🎯 TP{index}: {target}")

    lines.extend([
        "",
        f"Risk: {risk_points} pts",
        f"Reward : Risk: {reward_risk}",
        "",
        "No charts. No noise. Just Ping. ⚡",
    ])

    return "\n".join(lines)


def run_test(name, alert):
    message = format_ping_alert(**alert)

    print("\n" + "=" * 38)
    print(name)
    print("=" * 38)
    print(message)

    # Basic output checks
    assert "PING TIME — FLUSH" in message
    assert "Entry:" in message
    assert "Stop:" in message
    assert "Risk:" in message
    assert "Reward : Risk:" in message
    assert "No charts. No noise. Just Ping." in message

    for index in range(1, len(alert["targets"]) + 1):
        assert f"TP{index}:" in message

    print("\nPASS: Message structure is correct.")
    return message


es_alert = {
    "instrument": "ES",
    "direction": "BEARISH",
    "timestamp": "Oct 16, 2026 | 9:30 AM ET",
    "zone_label": "Sell Zone",
    "zone_low": "7803.0",
    "zone_high": "7812.25",
    "entry": "7803.0",
    "stop": "7812.25",
    "targets": ["7774.75", "7766.25", "7728.0"],
    "risk_points": "9.25",
    "reward_risk": "8:1",
}

nq_alert = {
    "instrument": "NQ",
    "direction": "BEARISH",
    "timestamp": "Oct 16, 2026 | 9:00 AM ET",
    "zone_label": "Sell Zone",
    "zone_low": "30163.25",
    "zone_high": "30211.0",
    "entry": "30163.25",
    "stop": "30211.0",
    "targets": ["29959.25", "29911.25", "29635.7"],
    "risk_points": "47.75",
    "reward_risk": "11.05:1",
}

if __name__ == "__main__":
    run_test("ES SAMPLE ALERT", es_alert)
    run_test("NQ SAMPLE ALERT", nq_alert)

    print("\nAll formatting tests passed.")
