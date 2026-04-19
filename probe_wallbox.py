"""Standalone script to probe Wallbox BLE API and dump raw responses."""

import asyncio
import json
import random
from bleak import BleakClient, BleakScanner

DEVICE_NAME = "WB874354"

UART_SERVICE_UUID = "331a36f5-2459-45ea-9d95-6142f0c4b307"
UART_RX_CHAR_UUID = "a9da6040-0823-4995-94ec-9ce41ca28833"
UART_TX_CHAR_UUID = "a73e9a10-628f-4494-a099-12efaf72258f"

# Methods to probe — focused on status, energy, and power meter data
METHODS_TO_PROBE = {
    "GET_STATUS": "r_dat",
    "GET_SESSIONS_INFO": "r_ses",
    "GET_SESSION": "r_log",
    "GET_POWER_BOOST": "r_hsh",
    "GET_POWER_BOOST_STATUS": "r_dca",
    "GET_POWER_INFUSION": "g_pwi",
    "GET_POWER_SHARING": "g_psh",
    "GET_ECO_SMART_CONFIGURATION": "g_ecos",
    "GET_DISCHARGE_SESSION": "r_dis",
    "GET_MAX_AVAILABLE_CURRENT": "r_fsI",
    "GET_MID_CONFIGURATION": "g_mid",
    "GET_SERIAL_NUMBER": "r_sn_",
    "GET_CHARGER_VERSIONS": "fw_v_",
    "GET_LOCK_STATUS": "r_lck",
    "GET_GROUNDING_STATUS": "r_wel",
    "GET_GRID_CODE": "r_gcd",
}

rx_queue: asyncio.Queue = asyncio.Queue()


def notification_handler(sender, data):
    rx_queue.put_nowait(data)


def build_frame(method: str, parameter=None) -> bytes:
    request_id = random.randint(1, 999)
    payload = {"met": method, "par": parameter, "id": request_id}
    data = json.dumps(payload, separators=[",", ":"]).encode("utf8")
    frame = b"EaE" + bytes([len(data)]) + data
    checksum = sum(c for c in frame) % 256
    return frame + bytes([checksum]), request_id


async def get_response(request_id, timeout=5):
    data = bytearray()
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        remaining = deadline - asyncio.get_event_loop().time()
        try:
            chunk = await asyncio.wait_for(rx_queue.get(), timeout=remaining)
            data += chunk
            try:
                parsed = json.loads(data)
                if parsed.get("id") == request_id:
                    return parsed
                # Wrong ID, reset
                data = bytearray()
            except (json.JSONDecodeError, ValueError):
                # Incomplete data, keep reading
                pass
        except asyncio.TimeoutError:
            break
    return None


async def send_request(client, method: str, parameter=None):
    # Drain any leftover notifications
    while not rx_queue.empty():
        rx_queue.get_nowait()

    frame, request_id = build_frame(method, parameter)
    uart_service = client.services.get_service(UART_SERVICE_UUID)
    rx_char = uart_service.get_characteristic(UART_RX_CHAR_UUID)
    await client.write_gatt_char(rx_char, frame, response=True)
    return await get_response(request_id)


async def main():
    print(f"Scanning for {DEVICE_NAME} or UART service UUID...")
    device = await BleakScanner.find_device_by_filter(
        lambda d, adv: (d.name and DEVICE_NAME in d.name)
        or UART_SERVICE_UUID in (adv.service_uuids or []),
        timeout=15,
    )

    if not device:
        print(f"Device not found! Make sure {DEVICE_NAME} is powered on and in range.")
        print("Listing all visible BLE devices:")
        devices = await BleakScanner.discover(timeout=10)
        for d in sorted(devices, key=lambda x: x.name or ""):
            print(f"  {d.name or '(unnamed)'} — {d.address}")
        return

    print(f"Found device: {device.name} ({device.address})")
    print(f"Connecting...")

    async with BleakClient(device) as client:
        print(f"Connected! (paired={client.is_connected})")

        try:
            await client.pair()
            print("Paired successfully.")
        except Exception as e:
            print(f"Pairing note: {e} (may already be paired, continuing...)")

        await client.start_notify(UART_TX_CHAR_UUID, notification_handler)
        print("Subscribed to notifications.\n")
        print("=" * 70)

        for name, method_code in METHODS_TO_PROBE.items():
            print(f"\n--- {name} (met: {method_code}) ---")
            try:
                response = await send_request(client, method_code)
                if response:
                    print(json.dumps(response, indent=2))
                else:
                    print("  (no response / timeout)")
            except Exception as e:
                print(f"  ERROR: {e}")

            # Small delay between requests
            await asyncio.sleep(0.5)

        print("\n" + "=" * 70)
        print("Done! Review the responses above for energy/power meter data.")


if __name__ == "__main__":
    asyncio.run(main())
